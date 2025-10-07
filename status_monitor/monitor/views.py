import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from .models import (
    Server,
    System,
    SystemDowntime,
    SystemStatus,
    SystemStatusHistory,
)


logger = logging.getLogger(__name__)


def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except requests.RequestException:
        return 0  # Retorna 0 em caso de erro de conexão ou timeout


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
        return

    failure_statuses = {"DOWN"}
    cache_key = _cache_key_for_system(name)
    last_status = cache.get(cache_key)
    cache.set(cache_key, status_str, timeout=24 * 3600)

    message = None

    if status_str in failure_statuses:
        if last_status == status_str:
            return
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
                checked_at=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                checked_at=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        }

    if not message:
        return

    try:
        response = requests.post(webhook_url, json=message, timeout=5)
        response.raise_for_status()
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

    status_code = check_url(url)
    status_str = get_status_string(status_code)
    now = timezone.now()

    notify_discord(name, url, status_str, status_code)

    system = System.objects.filter(name=name).first()
    if system:
        SystemStatus.objects.update_or_create(
            system=system,
            defaults={
                "status": status_str,
                "status_code": status_code if status_code is not None else None,
                "checked_at": now,
            },
        )

        SystemStatusHistory.objects.create(
            system=system,
            status=status_str,
            status_code=status_code if status_code is not None else None,
            checked_at=now,
        )

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

    return JsonResponse(
        {
            "name": name,
            "url": url,
            "status": status_str,
            "checked_at": timezone.localtime(now).strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


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
