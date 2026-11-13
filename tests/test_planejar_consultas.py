import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import planejar_consultas as p  # noqa: E402


class TesteCidade(unittest.TestCase):
    def test_formatos_de_uf(self):
        for entrada in ("Vitória da Conquista BA", "Vitória da Conquista/BA", "Vitória da Conquista - BA",
                        "Vitória da Conquista, ba", "  Vitória   da Conquista   BA "):
            with self.subTest(entrada=entrada):
                self.assertEqual(p.normalizar_cidade(entrada), ("Vitória da Conquista BA", True))

    def test_sem_uf(self):
        self.assertEqual(p.normalizar_cidade("Salvador"), ("Salvador", False))

    def test_final_que_nao_e_uf_nao_e_cortado(self):
        # "Ilha de Itaparica": "ca" não é UF; "Embu das Artes" não termina em UF
        self.assertEqual(p.normalizar_cidade("Embu das Artes"), ("Embu das Artes", False))
        self.assertEqual(p.normalizar_cidade("Rio Branco AC"), ("Rio Branco AC", True))


class TesteMontar(unittest.TestCase):
    def test_produto_cartesiano_sem_repetidos(self):
        c, av = p.montar(["clínicas odontológicas ", "Clínicas Odontológicas", "academias em"],
                         ["Salvador BA", "Vitória da Conquista/BA"])
        self.assertEqual(c, [
            "clínicas odontológicas em Salvador BA", "academias em Salvador BA",
            "clínicas odontológicas em Vitória da Conquista BA", "academias em Vitória da Conquista BA"])
        self.assertEqual(av, [])

    def test_aviso_sem_uf(self):
        _, av = p.montar(["academias"], ["Salvador"])
        self.assertEqual(len(av), 1)
        self.assertIn("sem UF", av[0])

    def test_marcador_reservado_do_motor(self):
        with self.assertRaises(ValueError):
            p.montar(["academias #!#ID"], ["Salvador BA"])


class TesteCLI(unittest.TestCase):
    def rodar(self, *args):
        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "c.txt"
            cod = p.main([*args, "--saida", str(saida)])
            return cod, (saida.read_text(encoding="utf-8") if saida.exists() else None)

    def test_gera_arquivo(self):
        cod, txt = self.rodar("--segmentos", "academias", "--cidades", "Salvador BA")
        self.assertEqual((cod, txt), (0, "academias em Salvador BA\n"))

    def test_limite_bloqueia_e_nao_salva(self):
        cod, txt = self.rodar("--segmentos", "a", "b", "c", "d", "--cidades", "Salvador BA", "--teste")
        self.assertEqual((cod, txt), (1, None))

    def test_faltando_argumentos(self):
        self.assertEqual(self.rodar("--segmentos", "a")[0], 2)


if __name__ == "__main__":
    unittest.main()
