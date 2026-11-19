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
            self.assertIn('id="categoria"', conteudo)
            self.assertIn("Qualidade dos contatos", conteudo)
            self.assertIn('id="copiar"', conteudo)
            self.assertIn("a coleta não encontrou", conteudo)

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


class TesteVersaoFixa(unittest.TestCase):
    def test_motor_com_versao_fixa(self):
        self.assertTrue(kit.IMAGEM.startswith(kit.IMAGEM_REPO + ":v"))
        self.assertNotIn("latest", kit.IMAGEM)
        self.assertIn(kit.IMAGEM, kit.montar_comando("/tmp/q.txt", "/tmp/o", "a.csv"))


class TesteProgresso(unittest.TestCase):
    def test_formatar_tempo(self):
        self.assertEqual(kit.formatar_tempo(40), "40 s")
        self.assertEqual(kit.formatar_tempo(95), "1 min 35 s")

    def test_texto(self):
        self.assertIn("até agora: 12", kit.texto_progresso(30, 12))
        self.assertIn("ainda trabalhando", kit.texto_progresso(30, 0))
        self.assertIn("ainda trabalhando", kit.texto_progresso(30, None))

    def test_mostra_andamento_e_conta_linhas(self):
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "x.csv"
            script = ("import time,sys\n"
                      "p=sys.argv[1]\n"
                      "open(p,'w').write('title,phone\\nA,1\\n'); time.sleep(1.5)\n"
                      "open(p,'a').write('B,2\\n'); time.sleep(1.5)\n")
            falso = [sys.executable, "-c", script, str(destino)]
            saida = io.StringIO()
            with mock.patch.object(kit, "montar_comando", return_value=falso), \
                 mock.patch.object(kit, "devolver_dono"), \
                 mock.patch.object(kit, "INTERVALO_PROGRESSO_S", 1), redirect_stdout(saida):
                m = kit.rodar_motor("t", "q.txt", d, "x.csv", "pt-BR", False, 1)
            self.assertEqual(m["linhas_csv"], 2)
            self.assertEqual(m["codigo_saida"], 0)
            self.assertIn("até agora", saida.getvalue())


class TesteAtualizar(unittest.TestCase):
    def _git(self, *args, cwd):
        import subprocess
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    def test_pasta_sem_git(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(kit.atualizar_kit(d)[0], "zip")

    @unittest.skipUnless(__import__("shutil").which("git"), "precisa do git")
    def test_ja_atual_atualizado_e_alterado(self):
        with tempfile.TemporaryDirectory() as d:
            origem, copia = Path(d) / "origem", Path(d) / "copia"
            origem.mkdir()
            ident = ["-c", "user.name=t", "-c", "user.email=t@example.com"]
            self._git("init", "-q", "-b", "main", cwd=origem)
            (origem / "a.txt").write_text("1")
            self._git("add", ".", cwd=origem)
            self._git(*ident, "commit", "-q", "-m", "1", cwd=origem)
            self._git("clone", "-q", str(origem), str(copia), cwd=d)
            self.assertEqual(kit.atualizar_kit(copia)[0], "ja_atual")
            (origem / "a.txt").write_text("2")
            self._git(*ident, "commit", "-q", "-am", "2", cwd=origem)
            self.assertEqual(kit.atualizar_kit(copia)[0], "atualizado")
            self.assertEqual((copia / "a.txt").read_text(), "2")
            (copia / "a.txt").write_text("mexi")
            self.assertEqual(kit.atualizar_kit(copia)[0], "alterado")
            self.assertEqual((copia / "a.txt").read_text(), "mexi", "não pode apagar mudanças da pessoa")


class TesteLimpar(unittest.TestCase):
    def _rodar_falso(self, chamadas):
        from types import SimpleNamespace

        def rodar(cmd, **kw):
            chamadas.append(cmd)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return rodar

    def test_sem_confirmacao_nao_remove_nada(self):
        from unittest import mock
        chamadas = []
        imagens = [(kit.IMAGEM, "abc", "2GB")]
        with mock.patch.object(kit, "checar_docker", return_value=(True, "Docker")), \
             mock.patch.object(kit, "listar_imagens_motor", return_value=imagens), \
             mock.patch.object(kit, "rodar", side_effect=self._rodar_falso(chamadas)), \
             mock.patch("builtins.input", return_value="não"):
            self.assertEqual(kit.main(["limpar"]), 1)
        self.assertFalse(any(c[:3] == ["docker", "image", "rm"] for c in chamadas))
        self.assertFalse(any(c[:3] == ["docker", "volume", "rm"] for c in chamadas))

    def test_antigas_preserva_versao_atual(self):
        from unittest import mock
        chamadas = []
        imagens = [(kit.IMAGEM, "abc", "2GB"), (kit.IMAGEM_REPO + ":latest", "def", "2GB")]
        with mock.patch.object(kit, "checar_docker", return_value=(True, "Docker")), \
             mock.patch.object(kit, "listar_imagens_motor", return_value=imagens), \
             mock.patch.object(kit, "rodar", side_effect=self._rodar_falso(chamadas)):
            self.assertEqual(kit.main(["limpar", "--antigas", "--sim"]), 0)
        removidas = [c[3] for c in chamadas if c[:3] == ["docker", "image", "rm"]]
        self.assertEqual(removidas, [kit.IMAGEM_REPO + ":latest"])
        self.assertFalse(any(c[:3] == ["docker", "volume", "rm"] for c in chamadas), "--antigas não mexe no cache")


class TestePainel(unittest.TestCase):
    def test_painel_com_busca_e_vazio(self):
        import painel
        import tratar_csv
        import gerar_relatorio
        demo = Path(kit.RAIZ) / "examples" / "demo-leads.csv"
        with tempfile.TemporaryDirectory() as d:
            vazio = painel.gerar_painel(d).read_text(encoding="utf-8")
            self.assertIn("Nenhuma busca ainda", vazio)
            busca = Path(d) / "busca-20261119-101500"
            busca.mkdir()
            (Path(d) / "outra-pasta").mkdir()   # pastas que não são busca são ignoradas
            saida, _ = tratar_csv.tratar(tratar_csv.ler_csv(demo))
            tratados, _excel = tratar_csv.salvar(saida, busca, "leads")
            (busca / "consultas.txt").write_text("academias em Salvador BA\npilates em Salvador BA\n", encoding="utf-8")
            (busca / "relatorio.html").write_text(gerar_relatorio.gerar(gerar_relatorio.ler_linhas(tratados), "x"),
                                                  encoding="utf-8")
            conteudo = painel.gerar_painel(d).read_text(encoding="utf-8")
            self.assertIn("academias em Salvador BA", conteudo)
            self.assertIn("+ 1 consulta", conteudo)
            self.assertIn('href="busca-20261119-101500/relatorio.html"', conteudo)
            self.assertIn("<b>20</b>", conteudo)
            self.assertNotIn("<script", conteudo, "o painel não usa JavaScript")
            self.assertEqual(len(painel.coletar(d)), 1)


class TesteTerminal(unittest.TestCase):
    def test_sem_cor_para_programas(self):
        from unittest import mock
        with mock.patch.object(kit, "COR", False):
            titulo = kit.formatar_linha("=== Kit de leads — teste ===")
            self.assertIn("KIT DE LEADS · TESTE", titulo)
            self.assertNotIn("\033[", titulo)
            self.assertEqual(kit.formatar_linha("[ok] tudo certo"), "[ok] tudo certo")

    def test_com_cor_para_pessoas(self):
        from unittest import mock
        with mock.patch.object(kit, "COR", True):
            self.assertIn("\033[1;32m[ok]\033[0m", kit.formatar_linha("[ok] tudo certo"))
            self.assertIn("\033[1;31m[falta]", kit.formatar_linha("[falta] Docker"))

    def test_margem(self):
        self.assertEqual(kit._com_margem("a\n\nb"), "  a\n\n  b")


class TesteConsultasNoRelatorio(unittest.TestCase):
    def test_consulta_maliciosa_vira_texto(self):
        import gerar_relatorio
        pagina = gerar_relatorio.gerar([], "t", ["<script>alert(1)</script> em X BA"])
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; em X BA", pagina)
        self.assertNotIn("<script>alert(1)</script>", pagina)
        self.assertNotRegex(pagina, r"__[A-Z_]+__", "nenhum marcador pode sobrar na página")


class TesteRefinar(unittest.TestCase):
    def test_refinar_sem_coletar_de_novo(self):
        import csv as _csv
        import shutil as _sh
        demo = Path(kit.RAIZ) / "examples" / "demo-leads.csv"
        with tempfile.TemporaryDirectory() as d:
            busca = Path(d) / "busca-20261119-101500"
            busca.mkdir()
            _sh.copy(demo, busca / "bruto.csv")
            (busca / "consultas.txt").write_text("academias em Cidade Modelo BA\n", encoding="utf-8")
            r = kit.main(["refinar", "--pasta", str(busca), "--excluir-categorias", "Academia", "--quantidade", "5"])
            self.assertEqual(r, 0)
            with open(busca / "leads-tratados.csv", newline="", encoding="utf-8") as f:
                linhas = list(_csv.DictReader(f))
            self.assertEqual(len(linhas), 5)
            self.assertNotIn("Academia", [l["categoria"] for l in linhas])
            self.assertTrue((busca / "todas-excel.csv").exists(), "a lista inteira fica guardada")
            self.assertTrue((busca / "relatorio.html").exists())
            self.assertTrue((Path(d) / "painel.html").exists(), "o painel fica na pasta de resultados")
            # refinar de novo sem quantidade: some o arquivo 'todas' (não fica dado velho)
            self.assertEqual(kit.main(["refinar", "--pasta", str(busca)]), 0)
            self.assertFalse((busca / "todas-excel.csv").exists())

    def test_refinar_pasta_sem_bruto(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(kit.main(["refinar", "--pasta", d]), 1)

    def test_buscar_quantidade_invalida(self):
        self.assertEqual(kit.main(["buscar", "--segmentos", "a", "--cidades", "X BA", "--quantidade", "0"]), 2)


class TesteVersao(unittest.TestCase):
    def test_ignora_moldura(self):
        saida = ("╔══════════╗\n║ 🌍 Google Maps Scraper ║\n╚══════════╝\n\nv1.18.2-146aefe\n"
                 "╔══╗\n╚══╝\n")
        self.assertEqual(kit.extrair_versao(saida), "v1.18.2-146aefe")
        self.assertEqual(kit.extrair_versao("╚═════╝"), "desconhecida")


if __name__ == "__main__":
    unittest.main()
