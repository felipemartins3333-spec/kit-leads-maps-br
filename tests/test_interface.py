import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import interface  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
TOKEN = "chave-de-teste-123"


class ProcFalso:
    def __init__(self):
        self.terminou = None

    def poll(self):
        return self.terminou


class TesteMontarPedido(unittest.TestCase):
    def test_bairros_viram_cidades(self):
        p = interface.montar_pedido({"segmentos": "estúdios de pilates", "cidade": "Curitiba/PR",
                                     "bairros": "Batel, Água Verde", "quantidade": "60", "email": True})
        self.assertEqual(p["cidades"], ["Curitiba PR", "Batel, Curitiba PR", "Água Verde, Curitiba PR"])
        self.assertEqual((p["quantidade"], p["profundidade"], p["email"]), (60, 1, True))

    def test_todas_usa_profundidade_2(self):
        p = interface.montar_pedido({"segmentos": "a", "cidade": "Salvador BA", "quantidade": "todas"})
        self.assertEqual((p["quantidade"], p["profundidade"]), (None, 2))

    def test_erros(self):
        for dados in ({"segmentos": "", "cidade": "X BA"}, {"segmentos": "a", "cidade": ""},
                      {"segmentos": "a", "cidade": "X BA", "quantidade": "999"},
                      {"segmentos": "a,b,c,d,e,f", "cidade": "X BA"},
                      {"segmentos": "a #!#ID", "cidade": "X BA"}):
            with self.subTest(dados=dados):
                with self.assertRaises(ValueError):
                    interface.montar_pedido(dados)

    def test_comando_usa_so_flags_do_kit(self):
        p = interface.montar_pedido({"segmentos": "a", "cidade": "X BA", "quantidade": "120", "email": True})
        cmd = interface.comando_busca(p, Path("/tmp/x"))
        self.assertIn("buscar", cmd)
        self.assertEqual(cmd[cmd.index("--quantidade") + 1], "120")
        self.assertEqual(cmd[cmd.index("--profundidade") + 1], "2")
        self.assertIn("--email", cmd)


    def test_opcoes_avancadas(self):
        p = interface.montar_pedido({"segmentos": "a", "cidade": "X BA", "redes": True, "tempo": "10",
                                     "ponto": {"lat": -12.97, "lon": -38.5}, "raio": 5, "rapido": True})
        cmd = interface.comando_busca(p, Path("/tmp/x"))
        self.assertIn("--redes-sociais", cmd)
        self.assertEqual(cmd[cmd.index("--tempo-maximo") + 1], "10")
        self.assertIn("--ponto=-12.97,-38.5", cmd)
        self.assertEqual(cmd[cmd.index("--raio") + 1], "5")
        self.assertIn("--modo-rapido", cmd)
        simples = interface.comando_busca(interface.montar_pedido({"segmentos": "a", "cidade": "X BA"}), Path("/x"))
        for flag in ("--redes-sociais", "--tempo-maximo", "--raio", "--modo-rapido"):
            self.assertNotIn(flag, simples)

    def test_opcoes_avancadas_invalidas(self):
        base = {"segmentos": "a", "cidade": "X BA"}
        for extra in ({"tempo": "999"}, {"rapido": True}, {"ponto": {"lat": 100, "lon": 0}},
                      {"ponto": {"lat": "x", "lon": 0}}, {"ponto": {"lat": 1, "lon": 1}, "raio": 7},
                      {"ponto": "-12,-38"}):
            with self.subTest(extra=extra):
                with self.assertRaises(ValueError):
                    interface.montar_pedido(dict(base, **extra))


class TesteServidor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.resultados = Path(self.tmp.name) / "resultados"
        busca = self.resultados / "busca-20261119-101500"
        busca.mkdir(parents=True)
        (busca / "relatorio.html").write_text("<p>relatorio</p>", encoding="utf-8")
        shutil.copy(RAIZ / "examples" / "demo-leads.csv", busca / "leads-tratados.csv")
        self.chamadas = []
        self.proc = ProcFalso()

        def executar(cmd, log):
            self.chamadas.append(cmd)
            return self.proc
        self.estado = interface.Estado(self.resultados, executar)
        self.srv = interface.criar_servidor(self.estado, TOKEN, porta=0)
        self.porta = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def pedir(self, metodo, caminho, corpo=None, cookie=True, chave=True, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        h = {"Host": host or f"127.0.0.1:{self.porta}"}
        if cookie:
            h["Cookie"] = f"kit_chave_{self.porta}={TOKEN}"
        if chave:
            h["X-Kit-Chave"] = TOKEN
        dados = None
        if corpo is not None:
            dados = json.dumps(corpo).encode()
            h["Content-Type"] = "application/json"
        c.request(metodo, caminho, body=dados, headers=h)
        r = c.getresponse()
        return r.status, r.read().decode("utf-8", "replace"), dict(r.getheaders())

    def test_sem_chave_e_negado(self):
        self.assertEqual(self.pedir("GET", "/", cookie=False)[0], 403)
        self.assertEqual(self.pedir("GET", "/api/estado", cookie=False)[0], 403)

    def test_link_com_chave_entra(self):
        status, _, cab = self.pedir("GET", f"/?t={TOKEN}", cookie=False)
        self.assertEqual(status, 303)
        self.assertIn("HttpOnly", cab["Set-Cookie"])
        self.assertIn("SameSite=Strict", cab["Set-Cookie"])
        self.assertEqual(self.pedir("GET", "/?t=errada", cookie=False)[0], 403)

    def test_pagina_e_estado(self):
        status, corpo, cab = self.pedir("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Nova busca", corpo)
        self.assertIn("window.mapaReserva", corpo, "a tela também tem o mapa reserva (sem WebGL)")
        self.assertIn("frame-ancestors 'none'", cab["Content-Security-Policy"])
        status, corpo, _ = self.pedir("GET", "/api/estado")
        d = json.loads(corpo)
        self.assertIsNone(d["atual"])
        self.assertEqual(d["buscas"][0]["relatorio"], "/resultados/busca-20261119-101500/relatorio.html")

    def test_host_estranho_e_negado(self):
        self.assertEqual(self.pedir("GET", "/", host="site-malicioso.com")[0], 403)

    def test_post_sem_cabecalho_da_tela_e_negado(self):
        status, _, _ = self.pedir("POST", "/api/buscar", {"segmentos": "a", "cidade": "X BA"}, chave=False)
        self.assertEqual(status, 403)
        self.assertEqual(self.chamadas, [])

    def test_busca_valida_e_uma_por_vez(self):
        status, corpo, _ = self.pedir("POST", "/api/buscar", {"segmentos": "pilates", "cidade": "Curitiba PR",
                                                               "bairros": "Batel", "quantidade": "60"})
        self.assertEqual(status, 200, corpo)
        cmd = self.chamadas[0]
        self.assertIn("Batel, Curitiba PR", cmd)
        status, corpo, _ = self.pedir("POST", "/api/buscar", {"segmentos": "a", "cidade": "X BA"})
        self.assertEqual(status, 409)
        atual = json.loads(self.pedir("GET", "/api/estado")[1])["atual"]
        self.assertTrue(atual["rodando"])
        self.proc.terminou = 0
        atual = json.loads(self.pedir("GET", "/api/estado")[1])["atual"]
        self.assertFalse(atual["rodando"])

    def test_apagar_busca(self):
        busca = self.resultados / "busca-20261119-101500"
        self.assertEqual(self.pedir("POST", "/api/apagar", {"pasta": "busca-20261119-101500"}, chave=False)[0], 403)
        for ruim in ("../resultados", "busca-x", "", "busca-20261119-101500/../..", "/etc"):
            with self.subTest(pasta=ruim):
                self.assertEqual(self.pedir("POST", "/api/apagar", {"pasta": ruim})[0], 400)
        self.assertTrue(busca.exists())
        (busca / "andamento.json").write_text("{}", encoding="utf-8")       # rodando pelo Claude
        self.assertEqual(self.pedir("POST", "/api/apagar", {"pasta": "busca-20261119-101500"})[0], 400)
        (busca / "andamento.json").unlink()
        status, corpo, _ = self.pedir("POST", "/api/apagar", {"pasta": "busca-20261119-101500"})
        self.assertEqual(status, 200, corpo)
        self.assertFalse(busca.exists())
        self.assertTrue(self.resultados.exists())

    def test_pedido_invalido(self):
        status, corpo, _ = self.pedir("POST", "/api/buscar", {"segmentos": "a", "cidade": ""})
        self.assertEqual(status, 400)
        self.assertIn("cidade", json.loads(corpo)["erro"])

    def test_arquivos_so_dentro_de_resultados(self):
        self.assertEqual(self.pedir("GET", "/resultados/busca-20261119-101500/relatorio.html")[0], 200)
        for caminho in ("/resultados/../../etc/passwd", "/resultados/%2e%2e/%2e%2e/etc/passwd",
                        "/resultados/busca-20261119-101500/../../x.csv"):
            with self.subTest(caminho=caminho):
                self.assertEqual(self.pedir("GET", caminho)[0], 404)
        status, _, cab = self.pedir("GET", "/resultados/busca-20261119-101500/leads-tratados.csv")
        self.assertEqual(status, 200)
        self.assertIn("attachment", cab["Content-Disposition"])

    def test_pontos_do_mapa(self):
        status, corpo, _ = self.pedir("GET", "/api/pontos?pasta=busca-20261119-101500")
        self.assertEqual(status, 200)
        d = json.loads(corpo)
        self.assertTrue(d["pontos"])
        self.assertEqual(set(d["pontos"][0]), {"nome", "categoria", "zap", "nota", "lat", "lon"},
                         "o mapa da tela só recebe o mínimo (sem telefone, e-mail ou site)")
        for ruim in ("../busca-20261119-101500", "busca-x", "", "busca-20261119-101500/../..", "%2e%2e"):
            with self.subTest(pasta=ruim):
                self.assertEqual(self.pedir("GET", "/api/pontos?pasta=" + ruim)[0], 404)
        self.assertEqual(self.pedir("GET", "/api/pontos?pasta=busca-20261119-101500", cookie=False)[0], 403)

    def test_csp_da_tela_so_libera_o_mapa(self):
        _, _, cab = self.pedir("GET", "/")
        csp = cab["Content-Security-Policy"]
        import re as _re
        self.assertEqual(set(_re.findall(r"https://[^ ;]+", csp)), {"https://tiles.openfreemap.org"})
        self.assertIn("font-src data:", csp)

    def test_link_no_codespace(self):
        from unittest import mock
        amb = {"CODESPACES": "true", "CODESPACE_NAME": "curly-enigma",
               "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev"}
        with mock.patch.dict("os.environ", amb):
            self.assertEqual(interface.link_publico(8765, "k"), "https://curly-enigma-8765.app.github.dev/?t=k")
        with mock.patch.dict("os.environ", {"CODESPACES": ""}):
            self.assertEqual(interface.link_publico(8765, "k"), "http://127.0.0.1:8765/?t=k")


class TesteModoClaudeDesktop(unittest.TestCase):
    """Modo do painel Browser do Claude Desktop: sem chave no link, mas ainda protegido."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.resultados = Path(self.tmp.name) / "resultados"
        self.resultados.mkdir()
        self.chamadas = []
        self.estado = interface.Estado(self.resultados, lambda cmd, log: (self.chamadas.append(cmd), ProcFalso())[1])
        self.srv = interface.criar_servidor(self.estado, TOKEN, porta=0, exigir_chave=False)
        self.porta = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def pedir(self, metodo, caminho, corpo=None, chave=False, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        h = {"Host": host or f"localhost:{self.porta}"}
        if chave:
            h["X-Kit-Chave"] = TOKEN
        dados = json.dumps(corpo).encode() if corpo is not None else None
        if dados:
            h["Content-Type"] = "application/json"
        c.request(metodo, caminho, body=dados, headers=h)
        r = c.getresponse()
        return r.status, r.read().decode("utf-8", "replace")

    def test_abre_sem_chave_no_link(self):
        self.assertEqual(self.pedir("GET", "/")[0], 200)
        self.assertEqual(self.pedir("GET", "/api/estado")[0], 200)

    def test_continua_protegido(self):
        self.assertEqual(self.pedir("GET", "/", host="site-malicioso.com")[0], 403)
        self.assertEqual(self.pedir("POST", "/api/buscar", {"segmentos": "a", "cidade": "X BA"})[0], 403)
        self.assertEqual(self.chamadas, [])
        self.assertEqual(self.pedir("POST", "/api/buscar", {"segmentos": "a", "cidade": "X BA"}, chave=True)[0], 200)

    def test_mostra_busca_feita_pelo_claude(self):
        import time as _t
        pasta = self.resultados / "busca-20261121-120000"
        pasta.mkdir()
        (pasta / "andamento.json").write_text(json.dumps({"inicio": _t.time() - 30, "consultas": ["pilates em Curitiba PR"]}),
                                             encoding="utf-8")
        atual = json.loads(self.pedir("GET", "/api/estado")[1])["atual"]
        self.assertTrue(atual["rodando"])
        self.assertEqual(atual["origem"], "claude")
        self.assertEqual(atual["consultas"], ["pilates em Curitiba PR"])
        (pasta / "andamento.json").write_text(json.dumps({"inicio": _t.time() - 5 * 3600, "consultas": []}),
                                             encoding="utf-8")
        self.assertIsNone(json.loads(self.pedir("GET", "/api/estado")[1])["atual"], "sobra antiga é ignorada")


if __name__ == "__main__":
    unittest.main()
