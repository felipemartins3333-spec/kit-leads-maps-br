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
    return {"segmentos": segmentos, "cidades": cidades, "consultas": consultas, "avisos": avisos,
            "quantidade": quantidade, "profundidade": profundidade, "email": bool(dados.get("email"))}


def comando_busca(pedido, pasta):
    cmd = [sys.executable, "-I", str(KIT), "buscar", "--segmentos", *pedido["segmentos"],
           "--cidades", *pedido["cidades"], "--pasta", str(pasta)]
    if pedido["quantidade"]:
        cmd += ["--quantidade", str(pedido["quantidade"])]
    if pedido["profundidade"] > 1:
        cmd += ["--profundidade", str(pedido["profundidade"])]
    if pedido["email"]:
        cmd.append("--email")
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

    def _ultimas_linhas(self, n=4):
        try:
            texto = self.trabalho["log"].read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        linhas = [_ANSI.sub("", l).strip() for l in texto.splitlines() if l.strip()]
        return linhas[-n:]

    def status(self):
        t = self.trabalho
        atual = None
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


def pagina(token):
    trocas = [("__ESTILO_BASE__", visual.ESTILO_BASE), ("__MARCA__", visual.MARCA_SVG),
              ("__ICONES_JSON__", gerar_relatorio.json_seguro_para_html(visual.ICONES)),
              ("__ICONE_BUSCA__", visual.icone_svg("busca")),
              ("__TOKEN__", token)]
    html = MODELO
    for a, b in trocas:
        html = html.replace(a, b)
    return html


CSP_APP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; "
           "img-src data:; form-action 'none'; base-uri 'none'; frame-ancestors 'none'")


def criar_servidor(estado, token, porta=PORTA_PADRAO, hosts_extras=()):
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
            if urlsplit(self.path).path != "/api/buscar":
                return self._responder(404, "Não encontrado")
            tamanho = int(self.headers.get("Content-Length") or 0)
            if tamanho <= 0 or tamanho > 10_000:
                return self._json(400, {"erro": "Pedido inválido."})
            try:
                dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
                if not isinstance(dados, dict):
                    raise ValueError("Pedido inválido.")
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
    ap.add_argument("--porta", type=int, default=PORTA_PADRAO)
    ap.add_argument("--sem-navegador", action="store_true", help="não abre o navegador sozinho")
    a = ap.parse_args(argv)
    token = secrets.token_urlsafe(24)
    no_codespace = os.environ.get("CODESPACES") == "true"
    extras = (".app.github.dev",) if no_codespace else ()
    estado = Estado(pasta_resultados or (RAIZ / "resultados"))
    servidor = criar_servidor(estado, token, a.porta, extras)
    porta = servidor.server_address[1]
    link = link_publico(porta, token)
    print("\n  KIT DE LEADS · TELA DE BUSCA", flush=True)
    print("  " + "─" * 28, flush=True)
    print(f"  Abra este link no navegador (ele tem a sua chave de acesso; não compartilhe):\n\n  {link}\n", flush=True)
    if no_codespace:
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
