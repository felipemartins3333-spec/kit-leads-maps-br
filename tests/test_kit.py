import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import kit  # noqa: E402


class TesteComando(unittest.TestCase):
    def test_flags_obrigatorias(self):
        cmd = kit.montar_comando("/tmp/q.txt", "/tmp/out", "a.csv")
        self.assertEqual(cmd[:3], ["docker", "run", "--rm"])
        self.assertIn("DISABLE_TELEMETRY=1", cmd)
        i = cmd.index(kit.IMAGEM)
        motor = cmd[i + 1:]
        self.assertEqual(motor, ["-input", "/queries.txt", "-results", "/out/a.csv", "-depth", "1",
                                 "-lang", "pt-BR", "-exit-on-inactivity", "3m"])
        self.assertNotIn("-email", cmd)
        self.assertNotIn("-p", cmd, "o kit nunca publica porta")

    def test_email_e_profundidade(self):
        cmd = kit.montar_comando("/tmp/q.txt", "/tmp/out", "a.csv", idioma="pt", email=True, profundidade=2)
        self.assertEqual(cmd[-1], "-email")
        self.assertEqual(cmd[cmd.index("-depth") + 1], "2")
        self.assertEqual(cmd[cmd.index("-lang") + 1], "pt")

    def test_consultas_somente_leitura(self):
        cmd = kit.montar_comando("/tmp/q.txt", "/tmp/out", "a.csv")
        montagens = [cmd[i + 1] for i, x in enumerate(cmd) if x == "--mount"]
        self.assertTrue(any("target=/queries.txt" in m and m.endswith(",readonly") for m in montagens))
        self.assertTrue(any(m.startswith("type=volume") and "target=/opt" in m for m in montagens))

    def test_caminho_com_virgula_usa_v(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a,b"
            p.mkdir()
            arg = kit._montagem_bind(p, "/out")
            self.assertEqual(arg[0], "-v")
            self.assertTrue(arg[1].endswith(":/out"))

    def test_nome_do_conteiner(self):
        cmd = kit.montar_comando("/tmp/q.txt", "/tmp/out", "a.csv", nome="kit-leads-1-x")
        self.assertEqual(cmd[cmd.index("--name") + 1], "kit-leads-1-x")


class TesteErrosDocker(unittest.TestCase):
    def test_windows_desligado(self):
        msg = "error during connect: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified."
        self.assertIn("Docker Desktop", kit.classificar_erro_docker(msg, "Windows"))

    def test_mac_desligado(self):
        msg = "Cannot connect to the Docker daemon at unix:///Users/x/.docker/run/docker.sock. Is the docker daemon running?"
        self.assertIn("Docker Desktop", kit.classificar_erro_docker(msg, "Darwin"))

    def test_linux_desligado(self):
        msg = "failed to connect to the docker API at unix:///var/run/docker.sock"
        self.assertIn("systemctl", kit.classificar_erro_docker(msg, "Linux"))

    def test_sem_permissao(self):
        msg = "permission denied while trying to connect to the Docker daemon socket"
        self.assertIn("permissão", kit.classificar_erro_docker(msg, "Linux"))

    def test_outro_erro(self):
        self.assertIn("Mensagem dele", kit.classificar_erro_docker("algo estranho", "Linux"))


class TesteConsultas(unittest.TestCase):
    def test_contar_ignora_vazias_e_comentarios(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.txt"
            p.write_text("# comentário\n\nacademias em Salvador BA\n  \nbares em Salvador BA\n", encoding="utf-8")
            self.assertEqual(kit.contar_consultas(p), 2)

    def test_arquivo_de_teste_do_repo_respeita_limite(self):
        self.assertLessEqual(kit.contar_consultas(kit.CONSULTAS_TESTE), kit.LIMITE_TESTE)

    def test_testar_recusa_mais_de_3(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.txt"
            p.write_text("a em X BA\nb em X BA\nc em X BA\nd em X BA\n", encoding="utf-8")
            self.assertEqual(kit.main(["testar", "--consultas", str(p), "--mostrar-comando"]), 1)



class TesteNaMaquinaReal(unittest.TestCase):
    """Rodam no sistema de verdade (no GitHub Actions: Windows, Mac e Linux)."""

    def test_mede_memoria(self):
        self.assertGreater(kit.ram_mb(), 0, "a leitura de memória precisa funcionar neste sistema")

    def test_verificar_nao_quebra(self):
        info = kit.verificar(silencioso=True)
        for chave in ("arquitetura", "ram_mb", "disco_livre_gb", "python", "docker_ok", "faltas"):
            self.assertIn(chave, info)

    def test_fluxo_da_demo(self):
        import gerar_relatorio
        import tratar_csv
        demo = Path(kit.RAIZ) / "examples" / "demo-leads.csv"
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(tratar_csv.main([str(demo), "--saida-pasta", d]), 0)
            tratados = Path(d) / "demo-leads-tratados.csv"
            excel = Path(d) / "demo-leads-excel.csv"
            self.assertTrue(excel.read_bytes().startswith(b"\xef\xbb\xbf"))
            html = Path(d) / "r.html"
            self.assertEqual(gerar_relatorio.main([str(tratados), "--saida", str(html)]), 0)
            conteudo = html.read_text(encoding="utf-8")
            self.assertIn("connect-src 'none'", conteudo)
            self.assertIn("Odonto Sorriso de Mentira", conteudo)

    def test_mostrar_comando_com_caminho_deste_sistema(self):
        self.assertEqual(kit.main(["testar", "--mostrar-comando"]), 0)


class TesteCodespace(unittest.TestCase):
    def test_codespace_sem_docker_sugere_rebuild(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"CODESPACES": "true"}), mock.patch("shutil.which", return_value=None):
            ok, msg = kit.checar_docker()
        self.assertFalse(ok)
        self.assertIn("Rebuild Container", msg)

    def test_devcontainer_docker_ce_no_trixie(self):
        import json
        dc = json.loads((Path(kit.RAIZ) / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))
        dind = dc["features"]["ghcr.io/devcontainers/features/docker-in-docker:4"]
        if "trixie" in dc["image"]:
            self.assertIs(dind.get("moby"), False, "Moby não existe para Debian trixie: use moby=false")


if __name__ == "__main__":
    unittest.main()
