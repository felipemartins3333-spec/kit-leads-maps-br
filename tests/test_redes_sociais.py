import http.server
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import redes_sociais  # noqa: E402

PAGINA = """<html><body>
<a href="https://www.facebook.com/sharer/sharer.php?u=x">compartilhar</a>
<a href="https://instagram.com/p/ABC123/">post</a>
<a href="https://www.instagram.com/estudio.exemplo/">Instagram</a>
<a href='https://pt-br.facebook.com/EstudioExemplo'>Facebook</a>
<script>var x = "https:\\/\\/www.linkedin.com\\/company\\/estudio-exemplo\\/";</script>
</body></html>"""


class TesteExtrair(unittest.TestCase):
    def test_acha_perfis_e_ignora_botoes(self):
        r = redes_sociais.extrair(PAGINA)
        self.assertEqual(r["instagram"], "https://www.instagram.com/estudio.exemplo/")
        self.assertEqual(r["facebook"], "https://www.facebook.com/EstudioExemplo")
        self.assertEqual(r["linkedin"], "https://www.linkedin.com/company/estudio-exemplo/")

    def test_pagina_sem_redes(self):
        self.assertEqual(redes_sociais.extrair("<p>nada</p>"), {})
        self.assertEqual(redes_sociais.extrair(None), {})

    def test_aplicar_e_cache(self):
        with tempfile.TemporaryDirectory() as d:
            redes_sociais.gravar_cache(d, {"https://a.com.br": {"instagram": "https://www.instagram.com/a/",
                                                                "facebook": "javascript:alert(1)"}})
            cache = redes_sociais.ler_cache(d)
        linhas = [{"site": "https://a.com.br"}, {"site": ""}]
        self.assertEqual(redes_sociais.aplicar(linhas, cache), 1)
        self.assertEqual(linhas[0]["instagram"], "https://www.instagram.com/a/")
        self.assertEqual(linhas[0]["facebook"], "", "só aceita https://")
        self.assertEqual(linhas[1]["linkedin"], "")

    def test_procurar_sem_repetir(self):
        vistos = []

        def baixar(url):
            vistos.append(url)
            return PAGINA
        r = redes_sociais.procurar(["https://a.com", "https://a.com", "", "https://b.com"], baixar=baixar)
        self.assertEqual(sorted(vistos), ["https://a.com", "https://b.com"])
        self.assertIn("instagram", r["https://b.com"])


class TesteSeguranca(unittest.TestCase):
    def test_nao_acessa_rede_interna(self):
        for host in ("127.0.0.1", "localhost", "10.0.0.1", "192.168.0.1", "169.254.169.254", "", None):
            with self.subTest(host=host):
                self.assertFalse(redes_sociais.endereco_publico(host))
        self.assertEqual(redes_sociais.baixar_pagina("http://127.0.0.1:9/"), "")
        self.assertEqual(redes_sociais.baixar_pagina("file:///etc/passwd"), "")
        self.assertEqual(redes_sociais.baixar_pagina("ftp://exemplo.com/"), "")

    def test_baixa_html_com_limite(self):
        class A(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                corpo = PAGINA.encode() + b" " * (redes_sociais.MAX_BYTES * 2)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), A)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{srv.server_address[1]}/"
            self.assertEqual(redes_sociais.baixar_pagina(url), "", "endereço local é recusado")
            texto = redes_sociais.baixar_pagina(url, verificar_endereco=False)
            self.assertLessEqual(len(texto), redes_sociais.MAX_BYTES)
            self.assertIn("estudio.exemplo", texto)
        finally:
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main()
