#!/usr/bin/env python3
"""Tela do kit no navegador: preencher a busca, acompanhar o andamento e abrir os resultados.

Roda SÓ no seu computador (endereço 127.0.0.1) e só abre com o link que tem a chave secreta,
para que nenhum site da internet consiga disparar buscas pelo seu navegador. Só usa a
biblioteca padrão do Python. Normalmente é aberta por:  python3 scripts/kit.py abrir
"""
import argparse
import http.server
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

import gerar_relatorio  # noqa: E402
import painel  # noqa: E402
import planejar_consultas  # noqa: E402
import resumo_teste  # noqa: E402
import visual  # noqa: E402

KIT = AQUI / "kit.py"
MODELO = (AQUI / "modelo_interface.html").read_text(encoding="utf-8")
PORTA_PADRAO = 8765
# opção da tela -> (quantidade final, profundidade de rolagem no Maps)
QUANTIDADES = {"20": (20, 1), "60": (60, 1), "120": (120, 2), "todas": (None, 2)}
MAX_SEGMENTOS, MAX_BAIRROS, MAX_TEXTO = 5, 8, 80
TEMPOS_MIN = (10, 30, 60)
RAIOS_KM = (1, 3, 5, 10)
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _lista(texto, maximo):
    itens = [re.sub(r"\s+", " ", i).strip() for i in re.split(r"[,;\n]", texto or "")]
    itens = [i for i in itens if i]
    if len(itens) > maximo:
        raise ValueError(f"Use no máximo {maximo} itens separados por vírgula.")
    for i in itens:
        if len(i) > MAX_TEXTO:
            raise ValueError(f"Texto longo demais: “{i[:30]}…”.")
    return itens


def montar_pedido(dados):
    """Valida o formulário da tela. Devolve dict com segmentos, cidades, quantidade, profundidade, email."""
    segmentos = _lista(dados.get("segmentos"), MAX_SEGMENTOS)
    if not segmentos:
        raise ValueError("Diga o que você procura (ex.: estúdios de pilates).")
    cidade = re.sub(r"\s+", " ", str(dados.get("cidade") or "")).strip()
    if not cidade:
        raise ValueError("Diga a cidade com a UF (ex.: Curitiba PR).")
    if len(cidade) > MAX_TEXTO:
        raise ValueError("Nome da cidade longo demais.")
    cidade_norm, _ = planejar_consultas.normalizar_cidade(cidade)
    bairros = _lista(dados.get("bairros"), MAX_BAIRROS)
    cidades = [cidade_norm] + [f"{b}, {cidade_norm}" for b in bairros]
    consultas, avisos = planejar_consultas.montar(segmentos, cidades)   # pode levantar ValueError
    if len(consultas) > planejar_consultas.LIMITE_PADRAO:
        raise ValueError(f"São {len(consultas)} buscas; o limite é {planejar_consultas.LIMITE_PADRAO}. "
                         "Use menos segmentos ou bairros.")
    chave = str(dados.get("quantidade") or "60")
    if chave not in QUANTIDADES:
        raise ValueError("Quantidade inválida.")
    quantidade, profundidade = QUANTIDADES[chave]
    try:
        tempo = int(dados.get("tempo") or 30)
    except (TypeError, ValueError):
        tempo = 0
    if tempo not in TEMPOS_MIN:
        raise ValueError("Tempo máximo inválido.")
    ponto, raio, rapido = None, None, bool(dados.get("rapido"))
    if dados.get("ponto") is not None:
        p = dados.get("ponto")
        try:
            lat, lon = float(p["lat"]), float(p["lon"])
        except (TypeError, KeyError, ValueError):
            raise ValueError("Ponto do mapa inválido.") from None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Ponto do mapa inválido.")
        ponto = (round(lat, 6), round(lon, 6))
        try:
            raio = int(dados.get("raio") or 3)
        except (TypeError, ValueError):
            raio = 0
        if raio not in RAIOS_KM:
            raise ValueError("Raio inválido.")
    if rapido and not ponto:
        raise ValueError("O modo rápido precisa de um ponto marcado no mapa.")
    return {"segmentos": segmentos, "cidades": cidades, "consultas": consultas, "avisos": avisos,
            "quantidade": quantidade, "profundidade": profundidade, "email": bool(dados.get("email")),
            "redes": bool(dados.get("redes")), "tempo": tempo, "ponto": ponto, "raio": raio, "rapido": rapido}


def comando_busca(pedido, pasta):
    cmd = [sys.executable, "-I", str(KIT), "buscar", "--segmentos", *pedido["segmentos"],
           "--cidades", *pedido["cidades"], "--pasta", str(pasta)]
    if pedido["quantidade"]:
        cmd += ["--quantidade", str(pedido["quantidade"])]
    if pedido["profundidade"] > 1:
        cmd += ["--profundidade", str(pedido["profundidade"])]
    if pedido["email"]:
        cmd.append("--email")
    if pedido.get("redes"):
        cmd.append("--redes-sociais")
    if pedido.get("tempo") and pedido["tempo"] != 30:
        cmd += ["--tempo-maximo", str(pedido["tempo"])]
    if pedido.get("ponto"):
        lat, lon = pedido["ponto"]
        cmd += [f"--ponto={lat},{lon}", "--raio", str(pedido["raio"])]
        if pedido.get("rapido"):
            cmd.append("--modo-rapido")
    return cmd


def _executar_de_verdade(cmd, log):
    ambiente = dict(os.environ, NO_COLOR="1", PYTHONIOENCODING="utf-8")
    with open(log, "w", encoding="utf-8") as f:
        return subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(RAIZ), env=ambiente)


class Estado:
    """Guarda a busca em andamento (uma por vez) e responde o que a tela pergunta."""

    def __init__(self, pasta_resultados, executar=_executar_de_verdade):
        self.pasta_resultados = Path(pasta_resultados)
        self.executar = executar
        self.trava = threading.Lock()
        self.trabalho = None

    def _nova_pasta(self):
        base = self.pasta_resultados / f"busca-{datetime.now():%Y%m%d-%H%M%S}"
        pasta, n = base, 2
        while pasta.exists():
            pasta = base.with_name(f"{base.name}-{n}")
            n += 1
        return pasta

    def iniciar(self, dados):
        pedido = montar_pedido(dados)
        with self.trava:
            if self.trabalho and self.trabalho["proc"].poll() is None:
                return None, "Já tem uma busca em andamento. Espere terminar (uma busca por vez evita bloqueio do Google)."
            pasta = self._nova_pasta()
            pasta.mkdir(parents=True)
            log = pasta / "andamento.log"
            proc = self.executar(comando_busca(pedido, pasta), log)
            self.trabalho = {"proc": proc, "pasta": pasta, "log": log, "inicio": time.time(), "pedido": pedido}
        return pasta.name, None

    def apagar(self, nome):
        with self.trava:
            t = self.trabalho
            if t and t["proc"].poll() is None and t["pasta"].name == nome:
                return False, "Essa busca ainda está rodando. Espere terminar para apagar."
            ok, msg = painel.apagar_busca(self.pasta_resultados, nome)
            if ok and t and t["pasta"].name == nome:
                self.trabalho = None
            return ok, msg

    def _ultimas_linhas(self, n=4):
        try:
            texto = self.trabalho["log"].read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        linhas = [_ANSI.sub("", l).strip() for l in texto.splitlines() if l.strip()]
        return linhas[-n:]

    def _busca_externa(self):
        """Busca rodando fora da tela (pelo Claude ou pelo terminal): o kit.py grava andamento.json."""
        melhor = None
        for arq in self.pasta_resultados.glob("busca-*/andamento.json"):
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
                inicio = float(dados.get("inicio", 0))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if time.time() - inicio > 3 * 3600:      # sobra de busca interrompida: ignora
                continue
            if not melhor or inicio > melhor[1]:
                melhor = (arq.parent, inicio, dados.get("consultas") or [])
        if not melhor:
            return None
        pasta, inicio, consultas = melhor
        try:
            linhas = len(resumo_teste.ler_linhas(pasta / "bruto.csv"))
        except Exception:
            linhas = None
        return {"pasta": pasta.name, "rodando": True, "segundos": int(time.time() - inicio),
                "empresas_ate_agora": linhas, "consultas": [str(c) for c in consultas][:30], "avisos": [],
                "origem": "claude"}

    def status(self):
        t = self.trabalho
        atual = None
        if not (t and t["proc"].poll() is None):
            externa = self._busca_externa()
            if externa:
                buscas = [_busca_json(b) for b in painel.coletar(self.pasta_resultados)]
                return {"atual": externa, "buscas": buscas}
        if t:
            rodando = t["proc"].poll() is None
            pasta = t["pasta"]
            linhas = None
            try:
                linhas = len(resumo_teste.ler_linhas(pasta / "bruto.csv"))
            except Exception:
                linhas = None
            atual = {"pasta": pasta.name, "rodando": rodando, "segundos": int(time.time() - t["inicio"]),
                     "empresas_ate_agora": linhas, "consultas": t["pedido"]["consultas"],
                     "avisos": t["pedido"]["avisos"]}
            if not rodando:
                atual["codigo"] = t["proc"].poll()
                busca = painel.ler_busca(pasta)
                atual["resultado"] = _busca_json(busca) if busca else None
                if not busca:
                    atual["mensagens"] = self._ultimas_linhas(8)
        buscas = [_busca_json(b) for b in painel.coletar(self.pasta_resultados)]
        return {"atual": atual, "buscas": buscas}


def _busca_json(b):
    return {"pasta": b["pasta"], "quando": b["quando"].strftime("%d/%m/%Y às %H:%M"), "consultas": b["consultas"],
            "empresas": b["empresas"], "zap": b["zap"], "site": b["site"], "email": b["email"],
            "relatorio": f"/resultados/{b['pasta']}/relatorio.html" if b["tem_relatorio"] else None,
            "planilha": f"/resultados/{b['pasta']}/leads-excel.csv" if b["tem_excel"] else None}


PASTA_BUSCA = re.compile(r"^busca-\d{8}-\d{6}(-\d+)?$")


def pontos_da_busca(pasta_resultados, nome, limite=3000):
    """Coordenadas e o mínimo para o mapa da tela. Só aceita nomes de pasta de busca válidos."""
    if not PASTA_BUSCA.match(nome or ""):
        return None
    arq = Path(pasta_resultados) / nome / "leads-tratados.csv"
    if not arq.is_file():
        return None
    pontos = []
    for l in resumo_teste.ler_linhas(arq)[:limite]:
        try:
            lat, lon = float(l.get("latitude") or ""), float(l.get("longitude") or "")
        except ValueError:
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
            continue
        pontos.append({"nome": l.get("nome", ""), "categoria": l.get("categoria", ""),
                       "zap": (l.get("whatsapp") or "").startswith("https://wa.me/"),
                       "nota": l.get("nota", ""), "lat": lat, "lon": lon})
    return pontos


def pagina(token):
    trocas = [("__ESTILO_BASE__", visual.ESTILO_BASE), ("__MARCA__", visual.MARCA_SVG),
              ("__ICONES_JSON__", gerar_relatorio.json_seguro_para_html(visual.ICONES)),
              ("__ICONE_BUSCA__", visual.icone_svg("busca")),
              ("__TOKEN__", token),
              ("__MAPLIBRE_CSS__", gerar_relatorio.css_do_mapa()),
              ("__MAPLIBRE_JS__", gerar_relatorio.js_do_mapa())]
    html = MODELO
    for a, b in trocas:
        html = html.replace(a, b)
    return html


CSP_APP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; worker-src blob:; child-src blob:; "
           "font-src data:; connect-src 'self' https://tiles.openfreemap.org; img-src data: blob: https://tiles.openfreemap.org; "
           "form-action 'none'; base-uri 'none'; frame-ancestors 'none'")


def criar_servidor(estado, token, porta=PORTA_PADRAO, hosts_extras=(), exigir_chave=True):
    """exigir_chave=False: modo do painel Browser do Claude Desktop (abre http://localhost:PORTA sem chave).
    Continua: só 127.0.0.1, só Host localhost, e o POST exige o cabeçalho X-Kit-Chave que só a própria
    página conhece (um site de fora não consegue ler a página nem mandar esse cabeçalho)."""
    class Atendente(http.server.BaseHTTPRequestHandler):
        server_version = "KitLeads"
        sys_version = ""

        def log_message(self, *args):   # silencioso: nada de endereço/dados no terminal
            pass

        # --- segurança -------------------------------------------------------
        def _host_ok(self):
            host = (self.headers.get("Host") or "").lower()
            porta_atual = self.server.server_address[1]
            permitidos = {f"127.0.0.1:{porta_atual}", f"localhost:{porta_atual}"}
            return host in permitidos or any(host.endswith(s) for s in hosts_extras)

        def _cookie(self):
            nome = f"kit_chave_{self.server.server_address[1]}"
            for parte in (self.headers.get("Cookie") or "").split(";"):
                k, _, v = parte.strip().partition("=")
                if k == nome:
                    return v
            return ""

        def _autorizado(self):
            if not exigir_chave:
                return True
            return secrets.compare_digest(self._cookie(), token)

        def _responder(self, codigo, corpo, tipo="text/html; charset=utf-8", extras=None):
            dados = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            for k, v in (extras or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(dados)

        def _json(self, codigo, obj):
            self._responder(codigo, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

        def _negado(self):
            self._responder(403, "<!doctype html><meta charset=utf-8><title>Acesso negado</title>"
                                 "<p style='font:16px system-ui;margin:40px'>Abra a tela pelo link completo que o kit "
                                 "mostrou no terminal (ele tem uma chave de acesso).</p>")

        # --- rotas -----------------------------------------------------------
        def do_GET(self):
            if not self._host_ok():
                return self._negado()
            partes = urlsplit(self.path)
            if partes.path == "/" and "t" in parse_qs(partes.query):
                if secrets.compare_digest(parse_qs(partes.query)["t"][0], token):
                    nome = f"kit_chave_{self.server.server_address[1]}"
                    return self._responder(303, "", extras={
                        "Location": "/", "Set-Cookie": f"{nome}={token}; Path=/; HttpOnly; SameSite=Strict"})
                return self._negado()
            if not self._autorizado():
                return self._negado()
            if partes.path == "/":
                return self._responder(200, pagina(token), extras={"Content-Security-Policy": CSP_APP})
            if partes.path == "/api/estado":
                return self._json(200, estado.status())
            if partes.path == "/api/pontos":
                nome = (parse_qs(partes.query).get("pasta") or [""])[0]
                pontos = pontos_da_busca(estado.pasta_resultados, nome)
                if pontos is None:
                    return self._json(404, {"erro": "Busca não encontrada."})
                return self._json(200, {"pasta": nome, "pontos": pontos})
            if partes.path.startswith("/resultados/"):
                return self._arquivo(unquote(partes.path[len("/resultados/"):]))
            self._responder(404, "Não encontrado")

        def _arquivo(self, relativo):
            base = estado.pasta_resultados.resolve()
            alvo = (base / relativo).resolve()
            try:
                alvo.relative_to(base)
            except ValueError:
                return self._responder(404, "Não encontrado")
            if not alvo.is_file() or alvo.suffix.lower() not in (".html", ".csv"):
                return self._responder(404, "Não encontrado")
            if alvo.suffix.lower() == ".csv":
                return self._responder(200, alvo.read_bytes(), "text/csv; charset=utf-8",
                                       {"Content-Disposition": f'attachment; filename="{alvo.name}"'})
            self._responder(200, alvo.read_bytes())

        def do_POST(self):
            if not self._host_ok() or not self._autorizado():
                return self._negado()
            # Só a própria tela manda este cabeçalho; outro site não consegue (o navegador bloqueia).
            if not secrets.compare_digest(self.headers.get("X-Kit-Chave") or "", token):
                return self._negado()
            rota = urlsplit(self.path).path
            if rota not in ("/api/buscar", "/api/apagar"):
                return self._responder(404, "Não encontrado")
            tamanho = int(self.headers.get("Content-Length") or 0)
            if tamanho <= 0 or tamanho > 10_000:
                return self._json(400, {"erro": "Pedido inválido."})
            try:
                dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
                if not isinstance(dados, dict):
                    raise ValueError("Pedido inválido.")
                if rota == "/api/apagar":
                    ok, msg = estado.apagar(str(dados.get("pasta") or ""))
                    return self._json(200 if ok else 400, {"mensagem": msg} if ok else {"erro": msg})
                pasta, erro = estado.iniciar(dados)
            except (ValueError, json.JSONDecodeError) as e:
                return self._json(400, {"erro": str(e) or "Pedido inválido."})
            if erro:
                return self._json(409, {"erro": erro})
            self._json(200, {"pasta": pasta})

    ultimo_erro = None
    for p in ([porta] if porta == 0 else range(porta, porta + 10)):
        try:
            return http.server.ThreadingHTTPServer(("127.0.0.1", p), Atendente)
        except OSError as e:
            ultimo_erro = e
    raise OSError(f"Não consegui abrir a tela: as portas {porta} a {porta + 9} estão ocupadas ({ultimo_erro}).")


def link_publico(porta, token):
    """No Codespace, o endereço que o navegador do Chromebook enxerga é o encaminhado pelo GitHub."""
    nome, dominio = os.environ.get("CODESPACE_NAME"), os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    if os.environ.get("CODESPACES") == "true" and nome and dominio:
        return f"https://{nome}-{porta}.{dominio}/?t={token}"
    return f"http://127.0.0.1:{porta}/?t={token}"


def main(argv=None, pasta_resultados=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=None, help="porta (padrão: variável PORT ou 8765)")
    ap.add_argument("--sem-navegador", action="store_true", help="não abre o navegador sozinho")
    ap.add_argument("--sem-chave", action="store_true",
                    help="para o painel Browser do Claude Desktop: abre em http://localhost:PORTA sem chave no link")
    a = ap.parse_args(argv)
    porta_pedida = a.porta if a.porta is not None else int(os.environ.get("PORT") or PORTA_PADRAO)
    token = secrets.token_urlsafe(24)
    no_codespace = os.environ.get("CODESPACES") == "true"
    extras = (".app.github.dev",) if (no_codespace and not a.sem_chave) else ()
    estado = Estado(pasta_resultados or (RAIZ / "resultados"))
    servidor = criar_servidor(estado, token, porta_pedida, extras, exigir_chave=not a.sem_chave)
    porta = servidor.server_address[1]
    link = f"http://localhost:{porta}/" if a.sem_chave else link_publico(porta, token)
    print("\n  KIT DE LEADS · TELA DE BUSCA", flush=True)
    print("  " + "─" * 28, flush=True)
    if a.sem_chave:
        print(f"  Tela no painel do Claude Desktop (só este computador acessa):\n\n  {link}\n", flush=True)
    else:
        print(f"  Abra este link no navegador (ele tem a sua chave de acesso; não compartilhe):\n\n  {link}\n", flush=True)
    if no_codespace and not a.sem_chave:
        print("  No Codespace: se o link não abrir, vá na aba Portas, clique no globo da porta "
              f"{porta} e acrescente ?t={token} no fim do endereço.", flush=True)
    print("  Para fechar a tela: Ctrl+C neste terminal.\n", flush=True)
    if not a.sem_navegador and not no_codespace:
        try:
            webbrowser.open(link)
        except Exception:
            pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Tela fechada. As buscas e relatórios continuam em resultados/.", flush=True)
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
