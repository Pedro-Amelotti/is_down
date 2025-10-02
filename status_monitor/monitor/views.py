# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime
from django.views.decorators.http import require_GET

# Lista de domínios para o primeiro servidor (198.211.109.216)
domains_server1 = [
    "adc.presgera.com", "arialief.com", "beard.presgera.com", "bg.arialief.com",
    "bg.en.presgera.com", "bg.feilaira.com", "bg.garaherb.com", "bg.goldenfrib.com",
    "bg.keskara.online", "bg.laellium.com", "bg.presgera.com", "bg.sciatilief.com",
    "blog.arialief.com", "cb.arialief.com", "cb.en.presgera.com", "cb.feilaira.com",
    "cb.goldenfrib.com", "cb.laellium.com", "cb.sciatilief.com", "cp.arialief.com",
    "cp.cucudrops.com", "cp.en.presgera.com", "cp.feilaira.com", "cp.goldenfrib.com",
    "cp.keskara.online", "cp.laellium.com", "cp.presgera.com", "cucudrops.com",
    "ds.arialief.com", "ds.en.presgera.com", "ds.feilaira.com", "ds.garaherb.com",
    "ds.laellium.com", "faq.arialief.com", "feilaira.com", "garaherb.com",
    "get.arialief.com", "get.garaherb.com", "get.goldenfrib.com", "get.keskara.online",
    "get.laellium.com", "get.presgera.com", "goldenfrib.com", "hml.arialief.com",
    "hml.cucudrops.com", "hml.feilaira.com", "hml.garaherb.com", "hml.goldenfrib.com",
    "hml.keskara.online", "hml.laellium.com", "hml.presgera.com", "hml.sciatilief.com",
    "homologacao.arialief.com", "idea.yufalti.com", "jan.yufalti.com", "keskara.online",
    "la.yufalti.com", "laellium.com", "lal.yufalti.com", "lct.presgera.com",
    "lee.yufalti.com", "mb1.yufalti.com", "media.presgera.com", "mioralab.com",
    "mrock.yufalti.com", "presgera.com", "sciatilief.com", "xmxcorp.com", "yufalti.com"
]

# Lista de domínios para o segundo servidor (198.211.109.215)
domains_server2 = [
    "adc.yufalti.com", "adc.zurylix.com", "alitoryn.com", "alphacur.com", "ariomyx.com",
    "basmontex.com", "beard.blinzador.com", "beard.kymezol.com", "bg.alphacur.com",
    "bg.blinzador.com", "bg.korvizol.com", "bg.kymezol.com", "bg.memyts.com",
    "bg.sc.alphacur.com", "blinzador.com", "cb.alphacur.com", "cb.blinzador.com",
    "cb.kymezol.com", "ceramiri.com", "dry.yufalti.com", "ds.alphacur.com",
    "ds.blinzador.com", "ds.kymezol.com", "ds.memyts.com", "elm.kryvenonline.com",
    "eln.kryvenonline.com", "en.alphacur.com", "everwellinsights.com", "farulena.com",
    "get.alphacur.com", "get.basmontex.com", "get.blinzador.com", "get.kymezol.com",
    "get.memyts.com", "get.zerevest.com", "hml.alitoryn.com", "hml.alphacur.com",
    "hml.ariomyx.com", "hml.blinzador.com", "hml.karylief.com", "hml.korvizol.com",
    "hml.kymezol.com", "hml.levhyn.com", "hml.mahgryn.com", "hml.memyts.com",
    "hml.nathurex.com", "hml.zerevest.com", "ic1.zurylix.com", "karylief.com",
    "korvizol.com", "kymezol.com", "lee1.zurylix.com", "lee2.zurylix.com", "levhyn.com",
    "lj.yundelo.com", "mahgryn.com", "mb2.yufalti.com", "memyts.com", "nathurex.com",
    "rock.kymezol.com", "thehealthnow.com", "thewellnesswize.com", "thewellspecialists.com",
    "wdl.yufalti.com", "wdl.zurylix.com", "wenzora.com", "yundelo.com", "zalovira.com",
    "zerevest.com", "zurylix.com"
]

# Agrupando os sistemas com os nomes corretos dos servidores
servers = {
    "servidor-produtos-principais": [{"name": d, "url": f"http://{d}"} for d in domains_server1],
    "servidor-produtos-principais-2": [{"name": d, "url": f"http://{d}"} for d in domains_server2],
}

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

def index(request):
    return render(request, 'monitor/index.html')

def status(request):
    results = {}
    for server_name, systems in servers.items():
        server_results = []
        for system in systems:
            status_code = check_url(system['url'])
            status_str = get_status_string(status_code)
            server_results.append({
                "name": system['name'],
                "url": system['url'],
                "status": status_str,
                "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        results[server_name] = server_results
    return JsonResponse(results)

@require_GET
def systems_list(request):
    # Retorna o dicionário de servidores com nome e url
    return JsonResponse(servers)

@require_GET
def system_status(request):
    url = request.GET.get("url")
    name = request.GET.get("name")
    if not url or not name:
        return JsonResponse({"error": "Parâmetros ausentes"}, status=400)

    status_code = check_url(url)
    status_str = get_status_string(status_code)

    return JsonResponse({
        "name": name,
        "url": url,
        "status": status_str,
        "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def glpi_assistencias(request):
    return render(request, 'monitor/glpi_assistencias.html')


