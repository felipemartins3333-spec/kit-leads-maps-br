import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import tratar_csv as t  # noqa: E402


class TesteTelefone(unittest.TestCase):
    def assertTel(self, bruto, tipo, e164="", formatado="", ddd_padrao=None):
        r = t.normalizar_telefone(bruto, ddd_padrao)
        self.assertEqual(r["tipo"], tipo, f"{bruto!r} -> {r}")
        self.assertEqual(r["e164"], e164, f"{bruto!r} -> {r}")
        if formatado:
            self.assertEqual(r["formatado"], formatado)
        return r

    # --- celular de 9 dígitos
    def test_celular_com_parenteses(self):
        r = self.assertTel("(77) 99999-0001", "celular", "+5577999990001", "(77) 99999-0001")
        self.assertEqual(r["whatsapp"], "https://wa.me/5577999990001")

    def test_celular_sem_pontuacao(self):
        self.assertTel("77999990001", "celular", "+5577999990001")

    def test_celular_com_mais55(self):
        self.assertTel("+55 77 99999-0001", "celular", "+5577999990001")

    def test_celular_com_55_sem_mais(self):
        self.assertTel("5577999990001", "celular", "+5577999990001")

    def test_celular_com_zero_de_tronco(self):
        self.assertTel("077 99999-0001", "celular", "+5577999990001")

    def test_prefixo_internacional_0055(self):
        self.assertTel("0055 77 99999-0001", "celular", "+5577999990001")

    # --- fixo de 8 dígitos
    def test_fixo_8_digitos(self):
        r = self.assertTel("(77) 3421-0001", "fixo", "+557734210001", "(77) 3421-0001")
        self.assertEqual(r["whatsapp"], "", "fixo NÃO ganha link de WhatsApp")

    def test_fixo_com_mais55(self):
        self.assertTel("+55 (11) 2345-6789", "fixo", "+551123456789")

    def test_ddd_55_nao_e_confundido_com_pais(self):
        # DDD 55 (Santa Maria/RS): "55 3220 1234" tem 10 dígitos, o 55 é DDD
        self.assertTel("(55) 3220-1234", "fixo", "+555532201234")
        self.assertTel("(55) 99999-0001", "celular", "+5555999990001")

    # --- sem DDD
    def test_sem_ddd_sem_padrao_e_invalido(self):
        r = self.assertTel("3421-0001", "invalido")
        self.assertEqual(r["motivo"], "sem DDD")
        self.assertEqual(self.assertTel("99999-0001", "invalido")["motivo"], "sem DDD")

    def test_sem_ddd_com_ddd_padrao(self):
        self.assertTel("3421-0001", "fixo", "+557734210001", ddd_padrao="77")
        self.assertTel("99999-0001", "celular", "+5577999990001", ddd_padrao="77")

    # --- 0800
    def test_0800(self):
        r = self.assertTel("0800 123 4567", "0800", "", "0800 123 4567")
        self.assertEqual(r["whatsapp"], "")

    def test_0800_colado(self):
        self.assertTel("08001234567", "0800")

    # --- inválidos
    def test_invalidos(self):
        casos = [
            "123", "abc", "(77) 9999-0001 99",       # tamanho
            "(00) 99999-0001", "(20) 99999-0001",    # DDD inexistente
            "(77) 89999-0001",                       # 9 dígitos que não começa com 9
            "(77) 9421-0001",                        # 8 dígitos começando com 9 (celular antigo)
            "(77) 99999-9999",                       # todos os dígitos iguais após o DDD
            "+1 415 555 0100",                       # número dos EUA
        ]
        for c in casos:
            with self.subTest(c=c):
                r = t.normalizar_telefone(c)
                self.assertEqual(r["tipo"], "invalido", f"{c!r} -> {r}")
                self.assertEqual(r["e164"], "")
                self.assertEqual(r["whatsapp"], "")
                self.assertTrue(r["motivo"])

    def test_vazio(self):
        for c in ("", None, "   "):
            self.assertEqual(t.normalizar_telefone(c)["tipo"], "vazio")


class TesteEmail(unittest.TestCase):
    def test_extrai_de_formatos_diferentes(self):
        self.assertEqual(t.limpar_emails("a@empresa.com.br, B@Empresa.com.br; a@empresa.com.br"),
                         ["a@empresa.com.br", "b@empresa.com.br"])
        self.assertEqual(t.limpar_emails('["contato@loja.com.br"]'), ["contato@loja.com.br"])

    def test_descarta_lixo(self):
        lixo = "logo@2x.png, foto@site.jpg, x@sentry.io, noreply@loja.com, no-reply@loja.com, " \
               "seuemail@dominio.com.br, nome@dominio.com, a@example.com, user@wixpress.com"
        self.assertEqual(t.limpar_emails(lixo), [])

    def test_resto_de_escape_json(self):
        self.assertEqual(t.limpar_emails("u003econtato@loja.com.br"), ["contato@loja.com.br"])

    def test_exemplo_so_na_demo(self):
        self.assertEqual(t.limpar_emails("a@example.com", permitir_exemplo=True), ["a@example.com"])
        self.assertEqual(t.limpar_emails("a@example.com"), [])


def linha(**kw):
    base = {"title": "Empresa Fictícia", "phone": "", "website": "", "emails": "", "place_id": ""}
    base.update(kw)
    return base


class TesteTratamento(unittest.TestCase):
    def test_deduplica_por_place_id_e_telefone(self):
        entrada = [
            linha(title="A", place_id="p1", phone="(77) 99999-0001"),
            linha(title="A de novo", place_id="p1", phone="(77) 99999-0002"),   # mesmo place_id
            linha(title="B", place_id="p2", phone="77 99999 0001"),             # mesmo telefone de A
            linha(title="C", place_id="p3", phone="(77) 3421-0003"),
        ]
        saida, est = t.tratar(entrada)
        self.assertEqual([l["nome"] for l in saida], ["A", "C"])
        self.assertEqual(est["duplicadas_place_id"], 1)
        self.assertEqual(est["duplicadas_telefone"], 1)

    def test_0800_nao_deduplica(self):
        entrada = [linha(title="A", place_id="a", phone="0800 123 4567"),
                   linha(title="B", place_id="b", phone="0800 123 4567")]
        self.assertEqual(len(t.tratar(entrada)[0]), 2)

    def test_sem_nome_e_descartado(self):
        saida, est = t.tratar([linha(title="  ")])
        self.assertEqual((saida, est["sem_nome"]), ([], 1))

    def test_limpeza_de_site_e_campos(self):
        saida, _ = t.tratar([linha(website="loja.com.br/?utm_source=maps&x=1", title="  Loja \n  Tal ",
                                   review_rating="4.5", review_count="120")])
        self.assertEqual(saida[0]["site"], "https://loja.com.br/?x=1")
        self.assertEqual(saida[0]["nome"], "Loja Tal")
        self.assertEqual((saida[0]["nota"], saida[0]["avaliacoes"]), ("4.5", "120"))

    def test_excel_br(self):
        saida, _ = t.tratar([linha(title="=CMD()", review_rating="4.5", phone="(77) 99999-0001")])
        with tempfile.TemporaryDirectory() as d:
            _, excel = t.salvar(saida, d, "x")
            cru = excel.read_bytes()
            self.assertTrue(cru.startswith(b"\xef\xbb\xbf"), "precisa de BOM UTF-8")
            linhas = list(csv.reader(io.StringIO(cru.decode("utf-8-sig")), delimiter=";"))
        cab, dados = linhas[0], linhas[1]
        self.assertEqual(dados[cab.index("nota")], "4,5")
        self.assertEqual(dados[cab.index("nome")], "'=CMD()", "texto que começa com = não pode virar fórmula")
        self.assertNotIn("telefone_e164", cab)


class TesteEscolherEFiltrar(unittest.TestCase):
    def linhas(self):
        return [
            {"nome": "Só fixo", "categoria": "Academia", "telefone": "(77) 3421-0001", "whatsapp": "", "site": "",
             "email": "", "nota": "", "avaliacoes": ""},
            {"nome": "Completo", "categoria": "Estúdio de pilates", "telefone": "(77) 99999-0002",
             "whatsapp": "https://wa.me/5577999990002", "site": "https://a.com.br", "email": "a@a.com.br",
             "nota": "4.8", "avaliacoes": "10"},
            {"nome": "Zap e muitas avaliações", "categoria": "estudio de PILATES", "telefone": "(77) 99999-0003",
             "whatsapp": "https://wa.me/5577999990003", "site": "", "email": "", "nota": "4.1", "avaliacoes": "300"},
            {"nome": "Zap e poucas", "categoria": "Personal trainer", "telefone": "(77) 99999-0004",
             "whatsapp": "https://wa.me/5577999990004", "site": "", "email": "", "nota": "4.1", "avaliacoes": "3"},
        ]

    def test_melhores_por_contato_e_avaliacoes(self):
        nomes = [l["nome"] for l in t.selecionar_melhores(self.linhas(), 3)]
        self.assertEqual(nomes, ["Completo", "Zap e muitas avaliações", "Zap e poucas"])

    def test_sem_quantidade_mantem_todas_ordenadas(self):
        self.assertEqual(len(t.selecionar_melhores(self.linhas(), None)), 4)

    def test_excluir_categoria_sem_acento_e_caixa(self):
        nomes = [l["nome"] for l in t.filtrar_categorias(self.linhas(), excluir=["ACADEMIA", "personal trainer"])]
        self.assertEqual(nomes, ["Completo", "Zap e muitas avaliações"])

    def test_somente_categoria(self):
        nomes = [l["nome"] for l in t.filtrar_categorias(self.linhas(), somente=["Estúdio de Pilates"])]
        self.assertEqual(nomes, ["Completo", "Zap e muitas avaliações"])

    def test_contar_categorias(self):
        self.assertEqual(t.contar_categorias(self.linhas())[0][1], 1)
        self.assertEqual(len(t.contar_categorias(self.linhas())), 4)


if __name__ == "__main__":
    unittest.main()
