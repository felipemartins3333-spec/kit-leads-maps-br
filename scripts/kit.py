#!/usr/bin/env python3
"""kit.py — o comando principal do kit de leads (Windows, Mac, Linux e Codespace).

Comandos:
  verificar   confere a máquina (memória, espaço, Python, Docker) e diz o que falta
  preparar    baixa a imagem oficial do motor (~2 GB), só se houver espaço
  testar      teste pequeno: 3 consultas, -depth 1, sem e-mail e com e-mail; gera um
              relatório só com números (resultados/relatorio-teste.txt)
  buscar      busca de verdade: segmentos x cidades (ou um arquivo de consultas) ->
              CSV tratado + CSV para Excel + relatório HTML

Exemplos (no Windows, troque "python3" por "py"):
  python3 scripts/kit.py verificar
  python3 scripts/kit.py preparar
  python3 scripts/kit.py testar
  python3 scripts/kit.py buscar --segmentos "clínicas odontológicas" --cidades "Vitória da Conquista BA"
  python3 scripts/kit.py buscar --consultas minhas-consultas.txt --email

Aviso: coletar dados do Google Maps de forma automática pode contrariar os termos do
Google, e contatos de empresas podem ser dados pessoais (LGPD). Comece pequeno.
Só usa a biblioteca padrão do Python.
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_relatorio  # noqa: E402
import planejar_consultas  # noqa: E402
import resumo_teste  # noqa: E402
import tratar_csv  # noqa: E402

IMAGEM = "gosom/google-maps-scraper"
VOLUME_CACHE = "gmaps-playwright-cache"
MIN_LIVRE_GB = 5            # a imagem tem ~2 GB; folga para o Docker descompactar (estimativa nossa)
RAM_RECOMENDADA_MB = 3000   # abaixo disso o navegador do motor pode travar (estimativa nossa)
LIMITE_TESTE = 3
INATIVIDADE = "3m"          # flag -exit-on-inactivity do motor (confirmada com -h)
TEMPO_MAXIMO_S = 30 * 60    # trava de segurança por execução do motor
CONSULTAS_TESTE = RAIZ / "examples" / "consultas-teste.txt"
PASTA_RESULTADOS = RAIZ / "resultados"


# ------------------------------------------------------------------ utilidades

def so():
    return platform.system()  # 'Linux', 'Darwin' (Mac) ou 'Windows'


def comando_python():
    return "py" if so() == "Windows" else "python3"


def dizer(msg=""):
    print(msg, flush=True)


def ram_mb():
    try:
        s = so()
        if s == "Linux":
            for ln in Path("/proc/meminfo").read_text().splitlines():
                if ln.startswith("MemTotal:"):
                    return int(ln.split()[1]) // 1024
        if s == "Darwin":
            r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=10)
            return int(r.stdout.strip()) // (1024 * 1024)
        if s == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMORYSTATUSEX()
            m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return int(m.ullTotalPhys // (1024 * 1024))
    except Exception:
        pass
    return 0


def livre_gb(pasta):
    try:
        return shutil.disk_usage(str(pasta)).free // (1024 ** 3)
    except OSError:
        return 0


def contar_consultas(caminho):
    linhas = Path(caminho).read_text(encoding="utf-8-sig").splitlines()
    return len([l for l in linhas if l.strip() and not l.strip().startswith("#")])


def classificar_erro_docker(mensagem, sistema=None):
    """Traduz o erro do 'docker info' para português simples."""
    sistema = sistema or so()
    m = (mensagem or "").lower()
    if "permission denied" in m:
        return ("O Docker existe, mas o seu usuário não tem permissão para usá-lo. "
                "Veja 'Usar o Docker sem sudo' em docs/instalacao.md, depois feche e abra o terminal.")
    sinais_desligado = ("cannot connect", "failed to connect", "error during connect",
                        "is the docker daemon running", "docker_engine", "dockerdesktoplinuxengine",
                        "the system cannot find the file specified", "no such file or directory")
    if any(s in m for s in sinais_desligado):
        if sistema in ("Windows", "Darwin"):
            return ("O Docker Desktop está instalado, mas não está aberto. Abra o Docker Desktop, espere ele "
                    "terminar de iniciar e rode este comando de novo.")
        return ("O Docker está instalado, mas o serviço não está ligado. Tente: sudo systemctl start docker "
                "(no Codespace: feche e reabra o Codespace).")
    return "O Docker não respondeu. Mensagem dele: " + (mensagem or "").strip()[:300]


def rodar(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def checar_docker():
    if not shutil.which("docker"):
        return False, "O Docker não está instalado. Siga docs/instalacao.md (parte 'Instalar o Docker')."
    try:
        r = rodar(["docker", "info"], timeout=60)
    except subprocess.TimeoutExpired:
        return False, "O Docker demorou demais para responder. Se acabou de abrir o Docker Desktop, espere 1 minuto."
    if r.returncode != 0:
        return False, classificar_erro_docker(r.stderr or r.stdout)
    v = rodar(["docker", "--version"], timeout=30).stdout.strip()
    return True, v


def imagem_presente():
    try:
        return rodar(["docker", "image", "inspect", IMAGEM], timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def versao_motor():
    try:
        r = rodar(["docker", "run", "--rm", "-e", "DISABLE_TELEMETRY=1", IMAGEM, "-version"], timeout=120)
        linhas = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        return linhas[-1].strip() if linhas else "desconhecida"
    except (OSError, subprocess.TimeoutExpired):
        return "desconhecida"


def digest_imagem():
    try:
        r = rodar(["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", IMAGEM], timeout=60)
        return r.stdout.strip() or "desconhecido"
    except (OSError, subprocess.TimeoutExpired):
        return "desconhecido"


# ----------------------------------------------------------------- verificar

def verificar(silencioso=False):
    """Confere a máquina. Devolve um dict com o que achou e a lista do que falta."""
    out = (lambda *_: None) if silencioso else dizer
    info = {"faltas": []}
    arq = platform.machine().lower()
    info["arquitetura"] = arq
    if arq in ("x86_64", "amd64", "aarch64", "arm64"):
        out(f"[ok] Processador: {arq} (a imagem oficial do motor existe para amd64 e arm64)")
    else:
        out(f"[falta] Processador {arq}: a imagem oficial só existe para amd64 e arm64.")
        info["faltas"].append("processador não suportado")

    ram = ram_mb()
    info["ram_mb"] = ram
    if ram and ram < RAM_RECOMENDADA_MB:
        out(f"[aviso] Memória: {ram} MB. Com menos de ~3 GB o navegador do motor pode travar (estimativa nossa).")
    elif ram:
        out(f"[ok] Memória: {ram} MB")
    else:
        out("[aviso] Não consegui medir a memória desta máquina.")

    livre = livre_gb(RAIZ)
    info["disco_livre_gb"] = livre
    out(f"[info] Espaço livre na pasta do kit: {livre} GB")

    pv = sys.version_info
    info["python"] = platform.python_version()
    if pv < (3, 8):
        out(f"[falta] Python {info['python']}: o kit precisa do Python 3.8 ou mais novo.")
        info["faltas"].append("Python antigo")
    else:
        out(f"[ok] Python: {info['python']}")

    ok, msg = checar_docker()
    info["docker_ok"] = ok
    info["docker"] = msg if ok else ""
    if ok:
        out(f"[ok] Docker: {msg}")
        info["imagem"] = imagem_presente()
        if info["imagem"]:
            out(f"[ok] Imagem do motor ({IMAGEM}) já baixada.")
        elif livre < MIN_LIVRE_GB:
            out(f"[falta] Espaço: a imagem do motor tem ~2 GB e pedimos {MIN_LIVRE_GB} GB livres; há {livre} GB.")
            info["faltas"].append("espaço em disco")
        else:
            out(f"[info] A imagem do motor ainda não foi baixada. Próximo passo: {comando_python()} scripts/kit.py preparar")
    else:
        out(f"[falta] {msg}")
        info["faltas"].append("Docker")
        info["imagem"] = False
    return info


def cmd_verificar(_a):
    dizer("=== Kit de leads — verificação da máquina ===")
    info = verificar()
    dizer()
    if info["faltas"]:
        dizer("Falta resolver: " + ", ".join(info["faltas"]) + ". Veja docs/instalacao.md.")
        return 1
    dizer("Tudo certo para usar o kit.")
    return 0


# ------------------------------------------------------------------ preparar

def garantir_imagem(info):
    if info.get("imagem"):
        return True
    if info["disco_livre_gb"] < MIN_LIVRE_GB:
        dizer(f"Falta espaço: pedimos {MIN_LIVRE_GB} GB livres antes de baixar a imagem (~2 GB).")
        return False
    dizer("Baixando a imagem oficial do motor (~2 GB). Pode levar alguns minutos...")
    r = subprocess.run(["docker", "pull", IMAGEM])
    if r.returncode != 0:
        dizer("Não consegui baixar a imagem. Confira a internet e tente de novo.")
        return False
    return True


def cmd_preparar(_a):
    dizer("=== Kit de leads — preparar o motor ===")
    info = verificar()
    if not info["docker_ok"]:
        dizer("\nResolva o Docker primeiro (veja docs/instalacao.md).")
        return 1
    if not garantir_imagem(info):
        return 1
    dizer(f"[ok] Motor pronto. Versão: {versao_motor()}")
    dizer(f"Próximo passo: {comando_python()} scripts/kit.py testar")
    return 0


# ----------------------------------------------------------- rodar o motor

def _montagem_bind(origem, destino, somente_leitura=False):
    origem = str(Path(origem).resolve())
    if "," in origem:   # vírgula quebra o --mount; usa a sintaxe -v
        return ["-v", f"{origem}:{destino}" + (":ro" if somente_leitura else "")]
    return ["--mount", f"type=bind,source={origem},target={destino}" + (",readonly" if somente_leitura else "")]


def montar_comando(consultas, pasta_saida, arquivo_saida, idioma="pt-BR", email=False,
                   profundidade=1, nome=None):
    """Monta o 'docker run' do motor. Flags do motor confirmadas com -h (v1.18.2)."""
    cmd = ["docker", "run", "--rm"]
    if nome:
        cmd += ["--name", nome]
    cmd += ["-e", "DISABLE_TELEMETRY=1",
            "--mount", f"type=volume,source={VOLUME_CACHE},target=/opt"]
    cmd += _montagem_bind(consultas, "/queries.txt", somente_leitura=True)
    cmd += _montagem_bind(pasta_saida, "/out")
    cmd += [IMAGEM, "-input", "/queries.txt", "-results", f"/out/{arquivo_saida}",
            "-depth", str(int(profundidade)), "-lang", idioma, "-exit-on-inactivity", INATIVIDADE]
    if email:
        cmd.append("-email")
    return cmd


def devolver_dono(pasta):
    """No Linux o motor grava como root; devolve os arquivos ao usuário (mesma imagem, nada novo baixado)."""
    if so() != "Linux" or not hasattr(os, "getuid"):
        return
    cmd = ["docker", "run", "--rm", "-e", "DISABLE_TELEMETRY=1", "--entrypoint", "chown"]
    cmd += _montagem_bind(pasta, "/out")
    cmd += [IMAGEM, "-R", f"{os.getuid()}:{os.getgid()}", "/out"]
    try:
        rodar(cmd, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        pass


def rodar_motor(nome_teste, consultas, pasta, arquivo, idioma, email, profundidade, mostrar_comando=False):
    nome_conteiner = f"kit-leads-{os.getpid()}-{nome_teste}"
    cmd = montar_comando(consultas, pasta, arquivo, idioma, email, profundidade, nome=nome_conteiner)
    dizer(f"\n>>> {nome_teste} (idioma: {idioma}, e-mail: {'sim' if email else 'não'}, profundidade: {profundidade})")
    if mostrar_comando:
        dizer("    comando: " + subprocess.list2cmdline(cmd))
        return {"teste": nome_teste, "lang": idioma, "email": int(email), "segundos": 0,
                "linhas_csv": 0, "codigo_saida": "simulado", "arquivo": arquivo}
    destino = Path(pasta) / arquivo
    if destino.exists():
        destino.unlink()
    log = Path(pasta) / (Path(arquivo).stem + ".log")
    dizer("    coletando... (o terminal pode ficar parado vários minutos; é normal)")
    inicio = time.monotonic()
    with log.open("w", encoding="utf-8", errors="replace") as f:
        try:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=TEMPO_MAXIMO_S)
            codigo = r.returncode
        except subprocess.TimeoutExpired:
            rodar(["docker", "stop", nome_conteiner], timeout=120)
            codigo = "tempo_esgotado"
    segundos = int(round(time.monotonic() - inicio))
    devolver_dono(pasta)
    # O motor sai com código 0 mesmo sem coletar nada: contamos as linhas do CSV.
    linhas = len(resumo_teste.ler_linhas(destino))
    dizer(f"    tempo: {segundos}s | linhas coletadas: {linhas} | código de saída do motor: {codigo}")
    return {"teste": nome_teste, "lang": idioma, "email": int(email), "segundos": segundos,
            "linhas_csv": linhas, "codigo_saida": codigo, "arquivo": arquivo}


def explicar_zero_linhas(pasta):
    dizer("\nNenhuma linha coletada. Causas prováveis:")
    logs = " ".join(p.read_text(encoding="utf-8", errors="replace") for p in Path(pasta).glob("*.log"))
    if "ERR_NAME_NOT_RESOLVED" in logs:
        dizer("  - o motor não conseguiu acessar google.com (internet, DNS, VPN ou firewall da rede);")
    dizer("  - o Google pode ter pedido confirmação ou limitado o acesso temporariamente")
    dizer("    (mais comum em servidores na nuvem, como Codespace ou VPS);")
    dizer("  - pouca memória: o navegador do motor pode ter travado.")


def registrar_ambiente(pasta, info):
    linhas = [f"data={datetime.now():%Y-%m-%d}",
              f"so={platform.system()} {platform.release()}",
              f"arquitetura={info.get('arquitetura', '')}",
              f"ram_mb={info.get('ram_mb', 0)}",
              f"disco_livre_gb={info.get('disco_livre_gb', 0)}",
              f"docker={info.get('docker', '')}",
              f"motor_versao={versao_motor()}",
              f"imagem_digest={digest_imagem()}",
              f"python={info.get('python', '')}",
              f"codespace={'sim' if os.environ.get('CODESPACES') == 'true' else 'não'}"]
    (Path(pasta) / "ambiente.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")


# -------------------------------------------------------------------- testar

def cmd_testar(a):
    dizer("=== Kit de leads — teste pequeno (máx. 3 consultas, -depth 1, sem proxy) ===")
    dizer("Aviso: coletar do Google Maps pode contrariar os termos do Google; contatos envolvem LGPD.")
    consultas = Path(a.consultas) if a.consultas else CONSULTAS_TESTE
    if not consultas.exists():
        dizer(f"Não achei o arquivo de consultas: {consultas}")
        return 1
    n = contar_consultas(consultas)
    if n == 0 or n > LIMITE_TESTE:
        dizer(f"O arquivo {consultas} tem {n} consultas; o teste aceita de 1 a {LIMITE_TESTE}.")
        return 1
    pasta = PASTA_RESULTADOS
    pasta.mkdir(parents=True, exist_ok=True)

    if a.mostrar_comando:
        dizer("(modo --mostrar-comando: nada será executado)")
        rodar_motor("teste1-sem-email", consultas, pasta, "teste1-sem-email.csv", "pt-BR", False, 1, True)
        rodar_motor("teste2-com-email", consultas, pasta, "teste2-com-email.csv", "pt-BR", True, 1, True)
        return 0

    info = verificar()
    if info["faltas"] or not garantir_imagem(info):
        dizer("\nResolva o que falta (veja docs/instalacao.md) e rode de novo.")
        return 1
    registrar_ambiente(pasta, info)
    medicoes = []
    m = rodar_motor("teste1-sem-email", consultas, pasta, "teste1-sem-email.csv", "pt-BR", False, 1)
    medicoes.append(m)
    idioma_ok = "pt-BR" if m["linhas_csv"] > 0 else ""
    if not idioma_ok:
        dizer("    Veio 0 linha com pt-BR. Repetindo com o idioma 'pt'...")
        m = rodar_motor("teste1b-sem-email-pt", consultas, pasta, "teste1b-sem-email-pt.csv", "pt", False, 1)
        medicoes.append(m)
        idioma_ok = "pt" if m["linhas_csv"] > 0 else ""
    if idioma_ok:
        dizer(f"\nIdioma que funcionou: {idioma_ok}")
        medicoes.append(rodar_motor("teste2-com-email", consultas, pasta, "teste2-com-email.csv",
                                    idioma_ok, True, 1))
    else:
        explicar_zero_linhas(pasta)
        dizer("O teste com e-mail NÃO foi executado.")

    campos = ["teste", "lang", "email", "segundos", "linhas_csv", "codigo_saida", "arquivo"]
    (pasta / "medicoes.tsv").write_text(
        "".join("\t".join(str(x[c]) for c in campos) + "\n" for x in medicoes), encoding="utf-8")
    relatorio = resumo_teste.gerar_relatorio(pasta)
    (pasta / "relatorio-teste.txt").write_text(relatorio, encoding="utf-8")
    dizer("\n" + relatorio)
    dizer("Pronto. O arquivo resultados/relatorio-teste.txt tem só números (sem nomes, telefones ou e-mails)")
    dizer("e pode ser colado no chat. Não cole os .csv nem os .log: eles têm dados de empresas.")
    return 0


# -------------------------------------------------------------------- buscar

def cmd_buscar(a):
    dizer("=== Kit de leads — busca ===")
    dizer("Aviso: coletar do Google Maps pode contrariar os termos do Google; telefones e e-mails")
    dizer("de empresas podem ser dados pessoais (LGPD). Use com finalidade clara e respeite quem pedir para sair.")
    if not 1 <= a.profundidade <= 10:
        dizer("A profundidade vai de 1 a 10.")
        return 2
    if a.consultas:
        origem = Path(a.consultas)
        if not origem.exists():
            dizer(f"Não achei o arquivo de consultas: {origem}")
            return 1
        texto = origem.read_text(encoding="utf-8-sig")
        consultas = [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]
    else:
        if not a.segmentos or not a.cidades:
            dizer("Informe --segmentos e --cidades, ou um arquivo com --consultas.")
            return 2
        consultas, avisos = planejar_consultas.montar(a.segmentos, a.cidades)
        for av in avisos:
            dizer(f"[aviso] {av}")
    if not consultas:
        dizer("Nenhuma consulta para rodar.")
        return 1
    if len(consultas) > a.limite:
        dizer(f"São {len(consultas)} consultas, acima do limite de {a.limite}. Reduza ou use --limite "
              f"(mais consultas = mais tempo e mais risco de o Google limitar o acesso).")
        return 1
    if a.profundidade > 3:
        dizer(f"[aviso] Profundidade {a.profundidade}: mais resultados por consulta, mas bem mais tempo e risco de bloqueio.")

    pasta = PASTA_RESULTADOS / f"busca-{datetime.now():%Y%m%d-%H%M%S}"
    pasta.mkdir(parents=True, exist_ok=True)
    arq_consultas = pasta / "consultas.txt"
    arq_consultas.write_text("\n".join(consultas) + "\n", encoding="utf-8")
    dizer(f"{len(consultas)} consulta(s):")
    for c in consultas:
        dizer(f"  - {c}")

    if a.mostrar_comando:
        rodar_motor("busca", arq_consultas, pasta, "bruto.csv", a.idioma, a.email, a.profundidade, True)
        return 0

    info = verificar(silencioso=True)
    if info["faltas"]:
        dizer("\nFalta resolver: " + ", ".join(info["faltas"]) + f". Rode: {comando_python()} scripts/kit.py verificar")
        return 1
    if not garantir_imagem(info):
        return 1
    m = rodar_motor("busca", arq_consultas, pasta, "bruto.csv", a.idioma, a.email, a.profundidade)
    if m["linhas_csv"] == 0:
        explicar_zero_linhas(pasta)
        return 1

    saida, est = tratar_csv.tratar(tratar_csv.ler_csv(pasta / "bruto.csv"), a.ddd_padrao)
    padrao, excel = tratar_csv.salvar(saida, pasta, "leads")
    html = pasta / "relatorio.html"
    html.write_text(gerar_relatorio.gerar(gerar_relatorio.ler_linhas(padrao), "Lista de leads"), encoding="utf-8")
    dizer(f"\nEmpresas: {est['finais']} (de {est['lidas']} coletadas; "
          f"{est['duplicadas_place_id'] + est['duplicadas_telefone']} duplicadas removidas)")
    dizer(f"Telefone: {est['celular']} celular, {est['fixo']} fixo, {est['0800']} 0800, "
          f"{est['sem_telefone'] + est['telefone_invalido']} sem telefone válido")
    dizer(f"Com site: {est['com_site']} | com e-mail: {est['com_email']}"
          + ("" if a.email else " (rode com --email para procurar e-mails nos sites)"))
    dizer(f"\nAbra o relatório (duplo clique): {html}")
    dizer(f"Planilha para Excel: {excel}")
    dizer(f"Tempo total da coleta: {m['segundos']}s")
    return 0


# ---------------------------------------------------------------------- main

def main(argv=None):
    for fluxo in (sys.stdout, sys.stderr):   # acentos corretos no terminal do Windows
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando")
    sub.add_parser("verificar", help="confere a máquina e diz o que falta")
    sub.add_parser("preparar", help="baixa a imagem oficial do motor (~2 GB)")
    t = sub.add_parser("testar", help="teste pequeno (máx. 3 consultas) com relatório só de números")
    t.add_argument("--consultas", help=f"arquivo de consultas (padrão: {CONSULTAS_TESTE.relative_to(RAIZ)})")
    t.add_argument("--mostrar-comando", action="store_true", help="só mostra os comandos, não executa")
    b = sub.add_parser("buscar", help="busca segmentos x cidades e gera relatório HTML e planilha")
    b.add_argument("--segmentos", nargs="+", default=[])
    b.add_argument("--cidades", nargs="+", default=[])
    b.add_argument("--consultas", help="arquivo com uma consulta por linha (no lugar de segmentos/cidades)")
    b.add_argument("--email", action="store_true", help="também procura e-mails nos sites (mais lento)")
    b.add_argument("--profundidade", type=int, default=1, help="rolagem da lista do Maps, 1 a 10 (padrão 1)")
    b.add_argument("--idioma", default="pt-BR", help="idioma do Google (padrão pt-BR)")
    b.add_argument("--limite", type=int, default=planejar_consultas.LIMITE_PADRAO,
                   help=f"máximo de consultas (padrão {planejar_consultas.LIMITE_PADRAO})")
    b.add_argument("--ddd-padrao", help="DDD para telefones que vierem sem DDD (ex.: 77)")
    b.add_argument("--mostrar-comando", action="store_true", help="só mostra o comando, não executa")
    a = ap.parse_args(argv)
    acoes = {"verificar": cmd_verificar, "preparar": cmd_preparar, "testar": cmd_testar, "buscar": cmd_buscar}
    if a.comando not in acoes:
        ap.print_help()
        return 2
    try:
        return acoes[a.comando](a)
    except KeyboardInterrupt:
        dizer("\nInterrompido. Os arquivos já gerados continuam em resultados/.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
