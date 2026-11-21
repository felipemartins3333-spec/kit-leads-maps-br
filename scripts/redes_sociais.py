#!/usr/bin/env python3
"""Procura Instagram, Facebook e LinkedIn na página inicial do site de cada empresa.

Código próprio do kit (o motor não traz redes sociais). Só biblioteca padrão do Python.

Cuidados:
- visita só a PÁGINA INICIAL de sites que a própria empresa publicou no Google Maps;
- só http/https, só endereços públicos da internet (nada de 127.0.0.1, rede da casa/empresa etc.),
  conferido também em cada redirecionamento;
- tempo limite curto, lê no máximo ~800 KB por site, poucas conexões ao mesmo tempo;
- guarda o resultado em redes.json na pasta da busca (o 'refinar' reaproveita sem visitar de novo).

Redes sociais de empresas podem ter dados pessoais (LGPD): use com finalidade clara.
"""
import concurrent.futures
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

REDES = ("instagram", "facebook", "linkedin")
TEMPO_S = 8
MAX_BYTES = 800_000
CONEXOES = 6
AGENTE = "Mozilla/5.0 (compatible; kit-leads-maps-br; +https://github.com/felipemartins3333-spec/kit-leads-maps-br)"

_PADROES = {
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]{2,30})/?(?=[\"'\s<>?#]|$)", re.I),
    "facebook": re.compile(r"https?://(?:www\.|m\.|pt-br\.)?(?:facebook|fb)\.com/([A-Za-z0-9_.\-]{3,80})/?(?=[\"'\s<>?#]|$)", re.I),
    "linkedin": re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(company|in|school)/([A-Za-z0-9_\-%.]{2,100})/?(?=[\"'\s<>?#]|$)", re.I),
}
# Caminhos que são botões de compartilhar, plugins ou páginas do próprio site da rede, não perfis.
_LIXO = {
    "instagram": {"p", "reel", "reels", "explore", "accounts", "stories", "tv", "about", "developer", "legal"},
    "facebook": {"sharer", "sharer.php", "share", "share.php", "dialog", "plugins", "tr", "login", "home.php",
                 "profile.php", "pages", "groups", "events", "watch", "help", "policies", "privacy", "business",
                 "permalink.php", "photo.php", "story.php", "hashtag", "ads", "legal"},
}


def endereco_publico(host):
    """True só se TODOS os IPs do nome forem públicos (evita acessar a rede interna de quem usa)."""
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, OSError):
        return False
    if not infos:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0].split("%")[0])
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True


def _url_ok(url):
    p = urlsplit(url)
    return p.scheme in ("http", "https") and endereco_publico(p.hostname)


class _Redirecionar(urllib.request.HTTPRedirectHandler):
    max_redirections = 4

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _url_ok(newurl):
            raise urllib.error.URLError("redirecionamento para endereço não público")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_ABRIR = urllib.request.build_opener(_Redirecionar())


def baixar_pagina(url, verificar_endereco=True):
    """Texto da página (até MAX_BYTES) ou '' se não deu."""
    if not re.match(r"^https?://", url or "", re.I):
        return ""
    if verificar_endereco and not _url_ok(url):
        return ""
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "text/html,*/*;q=0.5"})
    try:
        with _ABRIR.open(req, timeout=TEMPO_S) as r:
            tipo = r.headers.get("Content-Type", "")
            if tipo and "html" not in tipo.lower():
                return ""
            dados = r.read(MAX_BYTES)
            cs = r.headers.get_content_charset() or "utf-8"
    except Exception:
        return ""
    try:
        return dados.decode(cs, errors="replace")
    except LookupError:
        return dados.decode("utf-8", errors="replace")


def extrair(html):
    """{'instagram': url, 'facebook': url, 'linkedin': url} com o primeiro perfil válido de cada rede."""
    html = (html or "").replace("\\/", "/")
    achou = {}
    for m in _PADROES["instagram"].finditer(html):
        nome = m.group(1).rstrip(".")
        if nome.lower() not in _LIXO["instagram"]:
            achou["instagram"] = f"https://www.instagram.com/{nome}/"
            break
    for m in _PADROES["facebook"].finditer(html):
        nome = m.group(1)
        if nome.lower() not in _LIXO["facebook"] and not nome.isdigit():
            achou["facebook"] = f"https://www.facebook.com/{nome}"
            break
    for m in _PADROES["linkedin"].finditer(html):
        achou["linkedin"] = f"https://www.linkedin.com/{m.group(1).lower()}/{m.group(2)}/"
        break
    return achou


def procurar(sites, baixar=baixar_pagina, conexoes=CONEXOES, ao_avancar=None):
    """{site: {rede: url}} para cada site (sem repetir). ao_avancar(feitos, total) mostra o andamento."""
    unicos = sorted({s for s in sites if s})
    resultado, feitos = {}, 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, conexoes)) as ex:
        futuros = {ex.submit(lambda s: extrair(baixar(s)), s): s for s in unicos}
        for f in concurrent.futures.as_completed(futuros):
            try:
                resultado[futuros[f]] = f.result()
            except Exception:
                resultado[futuros[f]] = {}
            feitos += 1
            if ao_avancar:
                ao_avancar(feitos, len(unicos))
    return resultado


def ler_cache(pasta):
    try:
        dados = json.loads((Path(pasta) / "redes.json").read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar_cache(pasta, cache):
    (Path(pasta) / "redes.json").write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")


def aplicar(linhas, cache):
    """Preenche as colunas instagram/facebook/linkedin a partir do cache. Devolve quantas linhas têm alguma."""
    com = 0
    for l in linhas:
        achado = cache.get(l.get("site") or "", {}) if l.get("site") else {}
        for r in REDES:
            v = achado.get(r, "") if isinstance(achado, dict) else ""
            l[r] = v if isinstance(v, str) and v.startswith("https://") else ""
        com += 1 if any(l[r] for r in REDES) else 0
    return com
