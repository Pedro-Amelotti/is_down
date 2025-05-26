# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime
from django.views.decorators.http import require_GET

# Lista de sistemas a serem monitorados
systems = [
    # {"name": "Proxmox VE", "url": "http://10.46.75.2:8006/"},
    # {"name": "Proxmox BS", "url": "http://10.46.75.3:8007/"},
    {"name": "Intranet", "url": "http://10.46.75.5/intranet/index.php/pt-br/"},
    {"name": "Sisbol", "url": "http://10.46.75.6/band/"},
    {"name": "P2", "url": "http://10.46.75.7/controle_p2/"},
    {"name": "Nextcloud", "url": "http://10.46.75.8"},
    {"name": "Sped Consulta 1", "url": "http://10.46.75.9/sped/administracao/sessao/eb/logon.jsp"},
    {"name": "Nextcloud-BIs", "url": "http://10.46.75.10/nextcloud/"},
    {"name": "SIS-COM", "url": "http://10.46.75.11/"},
    {"name": "Arranchamento", "url": "http://10.46.75.12/"},
    {"name": "GLPI", "url": "http://10.46.75.13/"},
    {"name": "Papiro", "url": "http://10.46.75.14:8080/"},
    # {"name": "Siscofis", "url": "http://10.46.75.15"},
    {"name": "Sped Consulta 2", "url": "http://10.46.75.16/sped/administracao/sessao/eb/logon.jsp"},
    {"name": "SPED", "url": "http://sped3.1bec.eb.mil.br/#/login"},
]

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def index(request):
    return render(request, 'monitor/index.html')

def status(request):
    results = []
    for system in systems:
        is_up = check_url(system['url'])
        results.append({
            "name": system['name'],
            "url": system['url'],
            "status": "UP" if is_up else "DOWN",
            "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse(results, safe=False)

@require_GET
def systems_list(request):
    # Retorna apenas nome e url, sem status
    return JsonResponse([{"name": s["name"], "url": s["url"]} for s in systems], safe=False)

@require_GET
def system_status(request):
    url = request.GET.get("url")
    name = request.GET.get("name")
    if not url or not name:
        return JsonResponse({"error": "Parâmetros ausentes"}, status=400)
    is_up = check_url(url)
    return JsonResponse({
        "name": name,
        "url": url,
        "status": "UP" if is_up else "DOWN",
        "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def glpi_assistencias(request):
    return render(request, 'monitor/glpi_assistencias.html')


