import requests
import logging
import time
import json

from django.db.models import ExpressionWrapper, F, Q, Sum, Value, Count
from django.db import models, transaction, OperationalError
from django.views.decorators.http import require_GET
from django.db.models.functions import Coalesce
from django.utils.text import slugify
from django.http import JsonResponse
from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import (
    System,
    Server,
    SystemStatus,
    SystemDowntime,
    SystemStatusHistory,
)


logger = logging.getLogger(__name__)


def check_url(url):
    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=5)
        status_code = response.status_code
    except requests.RequestException:
        status_code = 0
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
    return status_code, elapsed_ms


def get_status_string(status_code):
    if status_code == 200:
        return "UP"
    elif status_code == 403:
        return "FORBIDDEN"
    else:
        return "DOWN"


def _cache_key_for_system(name: str) -> str:
    slug = slugify(name) or "system"
    return f"system-status-last:{slug}"


def notify_discord(name: str, url: str, status_str: str, status_code: int | None) -> None:
    webhook_url = getattr(settings, "DISCORD_WEBHOOK_URL", None)
    if not webhook_url:
        logger.debug("DISCORD_WEBHOOK_URL não configurado; ignorando aviso para %s", name)
        return

    failure_statuses = {"DOWN"}
    cache_key = _cache_key_for_system(name)
    last_status = cache.get(cache_key)
    cache.set(cache_key, status_str, timeout=24 * 3600)

    message = None
    local_now_str = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")

    if status_str in failure_statuses:
        if last_status == status_str:
            pass
        readable_code = status_code or "sem resposta"
        message = {
            "content": (
                ":rotating_light: Sistema **{name}** está com status **{status}**.\n"
                "URL: {url}\n"
                "Código HTTP: {code}\n"
                "Verificado em: {checked_at}"
            ).format(
                name=name,
                status=status_str,
                url=url,
                code=readable_code,
                checked_at=local_now_str,
            )
        }
    elif last_status in failure_statuses and status_str == "UP":
        message = {
            "content": (
                ":white_check_mark: Sistema **{name}** voltou a ficar disponível.\n"
                "URL: {url}\n"
                "Verificado em: {checked_at}"
            ).format(
                name=name,
                url=url,
                checked_at=local_now_str,
            )
        }

    if not message:
        return

    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        if not (200 <= response.status_code < 300):
            logger.error("Falha ao enviar webhook Discord (%s): %s", response.status_code, getattr(response, 'text', ''))
        response.raise_for_status()
        logger.info("Notificação Discord enviada para '%s' (%s)", name, status_str)
    except requests.RequestException:
        logger.exception("Falha ao enviar notificação para o Discord para %s", name)


def index(request):
    return render(request, 'monitor/index.html')


@require_GET
def systems_list(request):
    servers_data = {}
    for server in Server.objects.all():
        systems = server.systems.select_related("current_status").all()
        servers_data[server.name] = []
        for system in systems:
            try:
                current_status = system.current_status
            except SystemStatus.DoesNotExist:
                current_status = None
            servers_data[server.name].append(
                {
                    "name": system.name,
                    "url": system.url,
                    "status": current_status.status if current_status else None,
                    "checked_at": timezone.localtime(current_status.checked_at).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if current_status
                    else None,
                }
            )
    return JsonResponse(servers_data)


@require_GET
def system_status(request):
    url = request.GET.get("url")
    name = request.GET.get("name")

    if not url or not name:
        return JsonResponse({"error": "Parâmetros ausentes"}, status=400)

    status_code, elapsed_ms = check_url(url)
    status_str = get_status_string(status_code)
    now = timezone.now()

    notify_discord(name, url, status_str, status_code)

    system = System.objects.filter(name=name).first()
    if not system:
        return JsonResponse({"error": "Sistema não encontrado"}, status=404)

    # Tentar evitar bloqueio SQLite com retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # 1️⃣ Atualiza status atual
                obj = SystemStatus.objects.filter(system=system).first()
                if obj:
                    obj.status = status_str
                    obj.status_code = status_code
                    obj.checked_at = now
                    obj.save(update_fields=["status", "status_code", "checked_at"])
                else:
                    SystemStatus.objects.create(
                        system=system,
                        status=status_str,
                        status_code=status_code,
                        checked_at=now,
                    )

                # 2️⃣ Histórico de status
                SystemStatusHistory.objects.create(
                    system=system,
                    status=status_str,
                    status_code=status_code,
                    checked_at=now,
                )

                # 3️⃣ Controle de downtime
                active_downtime = SystemDowntime.objects.filter(
                    system=system, ended_at__isnull=True
                ).first()

                if status_str == "UP":
                    if active_downtime:
                        active_downtime.ended_at = now
                        active_downtime.save(update_fields=["ended_at"])
                elif status_str in {"DOWN", "FORBIDDEN"}:
                    if active_downtime:
                        if active_downtime.status != status_str:
                            active_downtime.status = status_str
                            active_downtime.save(update_fields=["status"])
                    else:
                        SystemDowntime.objects.create(
                            system=system,
                            status=status_str,
                            started_at=now,
                        )
            break  # saiu do loop se tudo correu bem

        except OperationalError:
            # SQLite pode travar, então damos uma pequena pausa e tentamos de novo
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            else:
                return JsonResponse({"error": "Database locked, tente novamente."}, status=500)

    # 4️⃣ Resposta final
    return JsonResponse({
        "name": name,
        "url": url,
        "status": status_str,
        "response_ms": elapsed_ms,
        "checked_at": timezone.localtime(now).strftime("%Y-%m-%d %H:%M:%S"),
    })

@require_GET
def dashboard_summary(request):
    now = timezone.now()
    statuses = SystemStatus.objects.all()
    counts = {
        "active": statuses.filter(status="UP").count(),
        "forbidden": statuses.filter(status="FORBIDDEN").count(),
        "down": statuses.exclude(status__in=["UP", "FORBIDDEN"]).count(),
    }

    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30

    since = now - timedelta(days=days)

    relevant_downtimes = SystemDowntime.objects.filter(
        Q(started_at__gte=since)
        | Q(ended_at__gte=since)
        | Q(ended_at__isnull=True)
    )

    duration_expr = ExpressionWrapper(
        Coalesce(F("ended_at"), Value(now, output_field=models.DateTimeField()))
        - F("started_at"),
        output_field=models.DurationField(),
    )

    downtime_totals = (
        relevant_downtimes.annotate(duration=duration_expr)
        .values("system__name")
        .annotate(total_duration=Sum("duration"))
        .order_by("-total_duration")[:10]
    )

    chart_data = []
    for item in downtime_totals:
        total_duration = item.get("total_duration")
        if total_duration is None:
            continue
        chart_data.append(
            {
                "name": item["system__name"],
                "total_minutes": round(total_duration.total_seconds() / 60, 2),
            }
        )

    return JsonResponse(
        {
            "counts": counts,
            "downtime_chart": chart_data,
            "detail_anchor": "#main-container",
        }
    )
    
def dashboard(request):
    now = timezone.now()
    last_24h = now - timedelta(hours=24)

    systems = System.objects.select_related("current_status")
    # Carrega servidores com sistemas e status atual para o grid por servidor
    servers = Server.objects.prefetch_related(
        models.Prefetch(
            'systems',
            queryset=System.objects.select_related('current_status')
        )
    )
    total = systems.count()
    up = SystemStatus.objects.filter(status="UP").count()
    down = SystemStatus.objects.filter(status="DOWN").count()
    forbidden = SystemStatus.objects.filter(status="FORBIDDEN").count()

    histories = (
        SystemStatusHistory.objects.filter(checked_at__gte=last_24h)
        .values("checked_at__hour")
        .annotate(
            total=Count("id"),
            ups=Count("id", filter=Q(status="UP")),
        )
        .order_by("checked_at__hour")
    )

    labels, data = [], []
    for h in range(24):
        item = next((i for i in histories if i["checked_at__hour"] == h), None)
        if item:
            uptime = (item["ups"] / item["total"]) * 100
        else:
            uptime = 0
        labels.append(f"{h:02d}h")
        data.append(round(uptime, 2))

    # Garante que sejam JSON válidos no template
    chart_labels = json.dumps(labels)
    chart_data = json.dumps(data)

    context = {
        "systems": systems,
        "servers": servers,
        "up": up,
        "down": down,
        "forbidden": forbidden,
        "total": total,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }
    return render(request, "monitor/dashboard.html", context)





