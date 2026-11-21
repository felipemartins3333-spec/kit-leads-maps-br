#!/usr/bin/env python3
"""kit.py — o comando principal do kit de leads (Windows, Mac, Linux e Codespace).

Comandos:
  verificar   confere a máquina (memória, espaço, Python, Docker) e diz o que falta
  preparar    baixa a imagem oficial do motor (~2 GB), só se houver espaço
  testar      teste pequeno: 3 consultas, -depth 1, sem e-mail e com e-mail; gera um
              relatório só com números (resultados/relatorio-teste.txt)
  buscar      busca de verdade: segmentos x cidades (ou um arquivo de consultas) ->
              CSV tratado + CSV para Excel + relatório HTML
  atualizar   baixa a versão nova do kit (git) e a versão do motor que ela usa
  limpar      remove o motor do computador (libera ~2 GB); pede confirmação
  painel      (re)gera resultados/painel.html, com todas as suas buscas
  refinar     refaz a lista de uma busca sem coletar de novo (tirar categorias, quantidade)
  abrir       abre a TELA no navegador: preencher a busca, acompanhar e abrir os resultados

Exemplos (no Windows, troque "python3" por "py"):
  python3 scripts/kit.py verificar
  python3 scripts/kit.py preparar
  python3 scripts/kit.py testar
  python3 scripts/kit.py buscar --segmentos "clínicas odontológicas" --cidades "Vitória da Conquista BA"
  python3 scripts/kit.py buscar --consultas minhas-consultas.txt --email
  python3 scripts/kit.py atualizar
  python3 scripts/kit.py limpar

Aviso: coletar dados do Google Maps de forma automática pode contrariar os termos do
Google, e contatos de empresas podem ser dados pessoais (LGPD). Comece pequeno.
Só usa a biblioteca padrão do Python.
"""
import argparse
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_relatorio  # noqa: E402
import painel  # noqa: E402
import planejar_consultas  # noqa: E402
import resumo_teste  # noqa: E402
import tratar_csv  # noqa: E402

IMAGEM_REPO = "gosom/google-maps-scraper"
# Versão FIXA do motor: a mesma em que todas as flags usadas foram conferidas com -h.
# Trocar só depois de testar a nova versão (o "latest" muda sem aviso).
VERSAO_MOTOR = "v1.18.2"
IMAGEM = f"{IMAGEM_REPO}:{VERSAO_MOTOR}"
VOLUME_CACHE = "gmaps-playwright-cache"
MIN_LIVRE_GB = 5            # a imagem tem ~2 GB; folga para o Docker descompactar (estimativa nossa)
RAM_RECOMENDADA_MB = 3000   # abaixo disso o navegador do motor pode travar (estimativa nossa)
LIMITE_TESTE = 3
INATIVIDADE = "3m"          # flag -exit-on-inactivity do motor (confirmada com -h)
TEMPO_MAXIMO_S = 30 * 60    # trava de segurança por execução do motor
INTERVALO_PROGRESSO_S = 20  # a cada quantos segundos mostrar o progresso
CONSULTAS_TESTE = RAIZ / "examples" / "consultas-teste.txt"
PASTA_RESULTADOS = RAIZ / "resultados"


# ------------------------------------------------------------------ utilidades

def so():
    return platform.system()  # 'Linux', 'Darwin' (Mac) ou 'Windows'


def comando_python():
    return "py" if so() == "Windows" else "python3"


# ------------------------------------------------------------- terminal bonito
# Cores e moldura só quando há uma pessoa olhando o terminal (não quando outro programa,
# como o Claude, lê a saída). NO_COLOR desliga as cores.
COR = False
INTERATIVO = False
_CORES_TAG = {"[ok]": "32", "[aviso]": "33", "[falta]": "31", "[erro]": "31", "[PAROU]": "31",
              "[info]": "36", "[kit]": "36", "[motor]": "36"}
_RE_TAG = re.compile(r"^(\s*)(\[[^\]]+\])(.*)$", re.S)
_RE_TITULO = re.compile(r"^=== Kit de leads — (.+) ===$")


def preparar_terminal():
    global COR, INTERATIVO
    INTERATIVO = bool(getattr(sys.stdout, "isatty", lambda: False)())
    COR = INTERATIVO and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"
    if COR and os.name == "nt":   # Windows: liga as cores do console (Windows 10 ou mais novo)
        try:
            import ctypes
            k = ctypes.windll.kernel32
            h = k.GetStdHandle(-11)
            modo = ctypes.c_uint32()
            if not (k.GetConsoleMode(h, ctypes.byref(modo)) and k.SetConsoleMode(h, modo.value | 0x0004)):
                COR = False
        except Exception:
            COR = False


def _ansi(codigo, texto):
    return f"\033[{codigo}m{texto}\033[0m" if COR else texto


def formatar_linha(msg):
    m = _RE_TITULO.match(msg)
    if m:
        texto = f"KIT DE LEADS · {m.group(1).upper()}"
        return "\n  " + _ansi("1;36", texto) + "\n  " + _ansi("2", "─" * len(texto))
    m = _RE_TAG.match(msg)
    if m and m.group(2) in _CORES_TAG:
        return m.group(1) + _ansi("1;" + _CORES_TAG[m.group(2)], m.group(2)) + m.group(3)
    if msg.startswith(">>> "):
        return _ansi("1", msg)
    return msg


def _com_margem(texto, margem="  "):
    return "\n".join((margem + l) if l.strip() else l for l in texto.split("\n"))


def dizer(msg=""):
    formatada = formatar_linha(msg)
    print(formatada if _RE_TITULO.match(msg) else _com_margem(formatada), flush=True)


def andamento(texto, final=False):
    """Linha de andamento: no terminal de uma pessoa, atualiza no lugar; senão, uma linha por vez."""
    if INTERATIVO:
        limpar = "\033[K" if COR else "   "
        sys.stdout.write("\r  " + _ansi("36", texto.strip()) + limpar + ("\n" if final else ""))
        sys.stdout.flush()
    elif not final:
        dizer(texto)


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


def formatar_tempo(segundos):
    segundos = int(segundos)
    if segundos < 60:
        return f"{segundos} s"
    return f"{segundos // 60} min {segundos % 60:02d} s"


def contar_parcial(caminho):
    """Conta as linhas de um CSV que o motor ainda está escrevendo. None se não der para ler agora."""
    try:
        return len(resumo_teste.ler_linhas(caminho))
    except (csv.Error, OSError, UnicodeDecodeError):
        return None


def texto_progresso(segundos, linhas):
    if linhas:
        return f"    ... {formatar_tempo(segundos)} | empresas no arquivo até agora: {linhas}"
    return f"    ... {formatar_tempo(segundos)} | ainda trabalhando (as empresas podem aparecer só no fim)"


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
        if os.environ.get("CODESPACES") == "true":
            return False, ("Este Codespace abriu sem a configuração do kit (sem Docker). Reconstrua: aperte "
                           "Ctrl+Shift+P, escolha 'Codespaces: Rebuild Container' e espere terminar. "
                           "Se continuar, apague este Codespace e crie outro.")
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
        return extrair_versao(r.stdout + "\n" + r.stderr)
    except (OSError, subprocess.TimeoutExpired):
        return "desconhecida"


def extrair_versao(texto):
    """O motor imprime uma moldura decorativa junto da versão; pegamos só o 'v1.2.3...'."""
    m = re.search(r"\bv\d+\.\d+\.\d+[\w.-]*", texto or "")
    return m.group(0) if m else "desconhecida"


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
    if pv < (3, 9):
        out(f"[falta] Python {info['python']}: o kit precisa do Python 3.9 ou mais novo.")
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
            out(f"[ok] Motor ({IMAGEM}) já baixado.")
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
    dizer("    coletando... (Ctrl+C para parar)" if INTERATIVO else
          f"    coletando... (mostro o andamento a cada {INTERVALO_PROGRESSO_S} s; Ctrl+C para parar)")
    intervalo = 2 if INTERATIVO else INTERVALO_PROGRESSO_S
    ultima_contagem, linhas_agora = -999.0, None
    inicio = time.monotonic()
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        try:
            while True:
                try:
                    proc.wait(timeout=intervalo)
                    codigo = proc.returncode
                    break
                except subprocess.TimeoutExpired:
                    decorrido = time.monotonic() - inicio
                    if decorrido > TEMPO_MAXIMO_S:
                        parar_conteiner(nome_conteiner, proc)
                        codigo = "tempo_esgotado"
                        break
                    if decorrido - ultima_contagem >= 10:      # ler o CSV no máximo a cada 10 s
                        linhas_agora, ultima_contagem = contar_parcial(destino), decorrido
                    andamento(texto_progresso(decorrido, linhas_agora))
        except KeyboardInterrupt:
            # Parar o "docker run" não para o contêiner: paramos explicitamente.
            parar_conteiner(nome_conteiner, proc)
            devolver_dono(pasta)
            raise
    segundos = int(round(time.monotonic() - inicio))
    andamento("", final=True)
    devolver_dono(pasta)
    # O motor sai com código 0 mesmo sem coletar nada: contamos as linhas do CSV.
    linhas = len(resumo_teste.ler_linhas(destino))
    dizer(f"    tempo: {segundos}s | linhas coletadas: {linhas} | código de saída do motor: {codigo}")
    return {"teste": nome_teste, "lang": idioma, "email": int(email), "segundos": segundos,
            "linhas_csv": linhas, "codigo_saida": codigo, "arquivo": arquivo}


def parar_conteiner(nome, proc):
    try:
        rodar(["docker", "stop", nome], timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()


def explicar_zero_linhas(pasta):
    dizer("\nNenhuma linha coletada. Causas prováveis:")
    logs = " ".join(p.read_text(encoding="utf-8", errors="replace") for p in Path(pasta).glob("*.log"))
    if "ERR_NAME_NOT_RESOLVED" in logs:
        dizer("  - o motor não conseguiu acessar google.com (internet, DNS, VPN ou firewall da rede);")
    dizer("  - o Google pode ter pedido confirmação ou limitado o acesso temporariamente")
    dizer("    (mais comum em servidores na nuvem, como Codespace ou VPS);")
    dizer("  - pouca memória: o navegador do motor pode ter travado.")
    dizer("O que tentar, nesta ordem:")
    dizer("  1. Confira o texto da busca: segmento + cidade + UF (ex.: 'academias em Salvador BA').")
    dizer("  2. Espere alguns minutos e rode de novo com menos consultas.")
    dizer("  3. Troque por um nome mais comum do segmento ou por bairros (ex.: 'academias em Pituba, Salvador BA').")
    dizer("  4. Só depois aumente a profundidade (--profundidade 2).")


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
    if a.quantidade is not None and a.quantidade < 1:
        dizer("A quantidade precisa ser 1 ou mais.")
        return 2
    if a.profundidade > 3:
        dizer(f"[aviso] Profundidade {a.profundidade}: mais resultados por consulta, mas bem mais tempo e risco de bloqueio.")

    pasta = Path(a.pasta) if a.pasta else PASTA_RESULTADOS / f"busca-{datetime.now():%Y%m%d-%H%M%S}"
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
    # A tela (kit.py abrir) mostra o andamento das buscas feitas pelo Claude/terminal por este arquivo.
    marcador = pasta / "andamento.json"
    marcador.write_text(json.dumps({"inicio": time.time(), "consultas": consultas}, ensure_ascii=False), encoding="utf-8")
    try:
        m = rodar_motor("busca", arq_consultas, pasta, "bruto.csv", a.idioma, a.email, a.profundidade)
    finally:
        try:
            marcador.unlink()
        except OSError:
            pass
    if m["linhas_csv"] == 0:
        explicar_zero_linhas(pasta)
        return 1

    finalizar_lista(pasta, consultas, a.ddd_padrao, a.quantidade, a.excluir_categorias, a.so_categorias,
                    com_email=a.email)
    dizer(f"Tempo total da coleta: {formatar_tempo(m['segundos'])}")
    dizer("\nO motor de coleta é o projeto aberto github.com/gosom/google-maps-scraper (Georgios Komninos).")
    dizer("Se a lista ajudou, deixar uma estrela lá é um jeito simples de apoiar quem fez.")
    return 0


def finalizar_lista(pasta, consultas, ddd_padrao=None, quantidade=None, excluir=None, somente=None,
                    com_email=True):
    """Do bruto.csv à lista final: trata, tira categorias fora do segmento, escolhe as N com contato
    mais completo, gera planilhas, relatório e painel. Usado por 'buscar' e 'refinar' (sem coletar de novo)."""
    pasta = Path(pasta)
    todas, est = tratar_csv.tratar(tratar_csv.ler_csv(pasta / "bruto.csv"), ddd_padrao)
    categorias = tratar_csv.contar_categorias(todas)
    filtradas = tratar_csv.filtrar_categorias(todas, excluir, somente)
    removidas_categoria = len(todas) - len(filtradas)
    for antigo in ("todas-tratados.csv", "todas-excel.csv"):
        if (pasta / antigo).exists():
            (pasta / antigo).unlink()
    if quantidade and len(filtradas) > quantidade:
        escolhidas = tratar_csv.selecionar_melhores(filtradas, quantidade)
        tratar_csv.salvar(tratar_csv.selecionar_melhores(filtradas, None), pasta, "todas")
    else:
        escolhidas = tratar_csv.selecionar_melhores(filtradas, None)
    padrao, excel = tratar_csv.salvar(escolhidas, pasta, "leads")
    html = pasta / "relatorio.html"
    html.write_text(gerar_relatorio.gerar(gerar_relatorio.ler_linhas(padrao), "Lista de leads", consultas),
                    encoding="utf-8")
    arq_painel = painel.gerar_painel(pasta.parent, comando_python())

    n = len(escolhidas)
    def conta(f):
        return sum(1 for l in escolhidas if f(l))
    dizer(f"\nColetadas: {est['lidas']} | duplicadas removidas: "
          f"{est['duplicadas_place_id'] + est['duplicadas_telefone']}"
          + (f" | fora do segmento removidas: {removidas_categoria}" if removidas_categoria else ""))
    if quantidade and len(filtradas) > quantidade:
        dizer(f"Na lista: as {n} com contato mais completo (de {len(filtradas)}). A lista inteira está em "
              f"{pasta / 'todas-excel.csv'}")
    elif quantidade and len(filtradas) < quantidade:
        dizer(f"[aviso] Você pediu {quantidade}, mas vieram {len(filtradas)}. Para mais, divida por bairros "
              f"ou aumente a profundidade.")
    dizer(f"Empresas na lista: {n}")
    dizer(f"Telefone: {conta(lambda l: l['tipo_telefone'] == 'celular')} celular, "
          f"{conta(lambda l: l['tipo_telefone'] == 'fixo')} fixo, {conta(lambda l: l['tipo_telefone'] == '0800')} 0800, "
          f"{conta(lambda l: not l['telefone'])} sem telefone válido")
    dizer(f"Com site: {conta(lambda l: l['site'])} | com e-mail: {conta(lambda l: l['email'])}"
          + ("" if com_email else " (rode com --email para procurar e-mails nos sites)"))
    if categorias:
        top = ", ".join(f"{c} ({q})" for c, q in categorias[:10])
        dizer(f"Categorias encontradas: {top}" + (" ..." if len(categorias) > 10 else ""))
        dizer(f"Para tirar categorias que não são do segmento, sem coletar de novo: "
              f"{comando_python()} scripts/kit.py refinar --pasta {pasta} --excluir-categorias \"Categoria 1\" \"Categoria 2\"")
    dizer(f"\nAbra o relatório (duplo clique): {html}")
    dizer(f"Planilha para Excel: {excel}")
    dizer(f"Painel com todas as suas buscas: {arq_painel}")
    return escolhidas


def cmd_abrir(a):
    """Abre a tela de busca no navegador (servidor local em 127.0.0.1, com chave no link)."""
    import interface
    info = verificar(silencioso=True)
    if info["faltas"]:
        dizer("[aviso] Falta resolver: " + ", ".join(info["faltas"]) + f". A tela abre, mas a busca só funciona depois. "
              f"Rode: {comando_python()} scripts/kit.py verificar")
    args = (["--porta", str(a.porta)] if a.porta else []) + (["--sem-navegador"] if a.sem_navegador else []) \
        + (["--sem-chave"] if a.sem_chave else [])
    return interface.main(args, PASTA_RESULTADOS)


def cmd_refinar(a):
    dizer("=== Kit de leads — refinar uma busca (sem coletar de novo) ===")
    pasta = Path(a.pasta)
    if not (pasta / "bruto.csv").exists():
        dizer(f"[falta] Não achei {pasta / 'bruto.csv'}. Use a pasta de uma busca, ex.: resultados/busca-AAAAMMDD-HHMMSS")
        return 1
    if not resumo_teste.ler_linhas(pasta / "bruto.csv"):
        dizer("[falta] Essa busca não tem nenhuma empresa coletada.")
        return 1
    consultas = []
    if (pasta / "consultas.txt").exists():
        consultas = [c.strip() for c in (pasta / "consultas.txt").read_text(encoding="utf-8-sig").splitlines() if c.strip()]
    finalizar_lista(pasta, consultas, a.ddd_padrao, a.quantidade, a.excluir_categorias, a.so_categorias)
    return 0


# ----------------------------------------------------------------- atualizar

def atualizar_kit(raiz):
    """Atualiza a pasta do kit pelo git. Devolve (situação, mensagem).
    situação: 'atualizado', 'ja_atual', 'zip', 'alterado', 'erro'."""
    raiz = Path(raiz)
    if not (raiz / ".git").exists() or not shutil.which("git"):
        return "zip", ("Esta pasta não veio pelo git (provavelmente pelo ZIP). Para atualizar, baixe o ZIP "
                       "de novo pelo GitHub e copie a sua pasta resultados/ para a pasta nova.")
    alterados = rodar(["git", "-C", str(raiz), "status", "--porcelain", "--untracked-files=no"], timeout=60)
    if alterados.stdout.strip():
        return "alterado", ("Você alterou arquivos do kit nesta pasta; para não apagar nada, não atualizei. "
                            "Peça ajuda ao Claude para guardar essas mudanças antes.")
    antes = rodar(["git", "-C", str(raiz), "rev-parse", "HEAD"], timeout=60).stdout.strip()
    r = rodar(["git", "-C", str(raiz), "pull", "--ff-only"], timeout=300)
    if r.returncode != 0:
        return "erro", "Não consegui atualizar pelo git. Mensagem: " + (r.stderr or r.stdout).strip()[:300]
    depois = rodar(["git", "-C", str(raiz), "rev-parse", "HEAD"], timeout=60).stdout.strip()
    if antes == depois:
        return "ja_atual", "O kit já estava na versão mais nova."
    return "atualizado", "Kit atualizado."


def cmd_atualizar(_a):
    dizer("=== Kit de leads — atualizar ===")
    situacao, msg = atualizar_kit(RAIZ)
    dizer(f"[kit] {msg}")
    if situacao == "atualizado":
        # O código novo pode usar outra versão do motor: quem prepara é o kit.py novo.
        dizer("Preparando o motor na versão que o kit novo usa...")
        return subprocess.run([sys.executable, "-I", str(RAIZ / "scripts" / "kit.py"), "preparar"]).returncode
    if situacao in ("erro", "alterado"):
        return 1
    info = verificar(silencioso=True)
    if not info["docker_ok"]:
        dizer(f"[motor] Docker indisponível agora; quando estiver ok, rode: {comando_python()} scripts/kit.py preparar")
        return 1
    if not garantir_imagem(info):
        return 1
    dizer(f"[motor] Em dia: {IMAGEM}.")
    dizer(f"Versões antigas do motor ocupam espaço. Para remover: {comando_python()} scripts/kit.py limpar --antigas")
    return 0


# -------------------------------------------------------------------- limpar

def listar_imagens_motor():
    """Lista [(nome, id, tamanho)] das imagens do motor neste computador."""
    r = rodar(["docker", "image", "ls", IMAGEM_REPO, "--format", "{{.Repository}}:{{.Tag}}|{{.ID}}|{{.Size}}"],
              timeout=60)
    itens = []
    for ln in r.stdout.splitlines():
        partes = ln.strip().split("|")
        if len(partes) == 3:
            nome, ident, tamanho = partes
            itens.append((ident if nome.endswith(":<none>") else nome, ident, tamanho))
    return itens


def cmd_limpar(a):
    dizer("=== Kit de leads — limpar o motor ===")
    ok, msg = checar_docker()
    if not ok:
        dizer(f"[falta] {msg}")
        return 1
    imagens = listar_imagens_motor()
    if a.antigas:
        imagens = [i for i in imagens if i[0] != IMAGEM]
    volume = False
    if not a.antigas:
        volume = rodar(["docker", "volume", "inspect", VOLUME_CACHE], timeout=60).returncode == 0
    if not imagens and not volume:
        dizer("Nada para remover.")
        return 0
    dizer("Vou remover do Docker:")
    for nome, _ident, tamanho in imagens:
        dizer(f"  - motor {nome} ({tamanho})")
    if volume:
        dizer(f"  - cache do navegador do motor (volume {VOLUME_CACHE})")
    dizer("A pasta resultados/ NÃO será apagada: são as suas listas. Apague à mão se quiser.")
    if not a.sim:
        try:
            resposta = input("Digite 'sim' para remover: ").strip().lower()
        except EOFError:
            resposta = ""
        if resposta != "sim":
            dizer("Cancelado. Nada foi removido.")
            return 1
    falhas = 0
    for nome, _ident, _tamanho in imagens:
        r = rodar(["docker", "image", "rm", nome], timeout=300)
        dizer(("[ok] removido: " if r.returncode == 0 else "[erro] não removido: ") + nome)
        falhas += r.returncode != 0
    if volume:
        r = rodar(["docker", "volume", "rm", VOLUME_CACHE], timeout=120)
        dizer(("[ok] removido: " if r.returncode == 0 else "[erro] não removido: ") + VOLUME_CACHE)
        falhas += r.returncode != 0
    if not a.antigas:
        dizer(f"Para usar o kit de novo depois: {comando_python()} scripts/kit.py preparar")
    return 1 if falhas else 0


# -------------------------------------------------------------------- painel

def cmd_painel(_a):
    dizer("=== Kit de leads — painel ===")
    destino = painel.gerar_painel(PASTA_RESULTADOS, comando_python())
    n = len(painel.coletar(PASTA_RESULTADOS))
    dizer(f"[ok] {n} busca(s) no painel.")
    dizer(f"Abra com duplo clique: {destino}")
    return 0


# ---------------------------------------------------------------------- main

def main(argv=None):
    for fluxo in (sys.stdout, sys.stderr):   # acentos corretos no terminal do Windows
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    preparar_terminal()
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
    b.add_argument("--quantidade", type=int, help="quantas empresas na lista final (as de contato mais completo)")
    b.add_argument("--pasta", help="pasta onde gravar esta busca (padrão: resultados/busca-AAAAMMDD-HHMMSS)")
    b.add_argument("--excluir-categorias", nargs="+", default=[], help="categorias que não são do segmento")
    b.add_argument("--so-categorias", nargs="+", default=[], help="manter só estas categorias")
    b.add_argument("--mostrar-comando", action="store_true", help="só mostra o comando, não executa")
    ab = sub.add_parser("abrir", help="abre a tela de busca no navegador")
    ab.add_argument("--porta", type=int, default=None, help="porta (padrão: variável PORT ou 8765)")
    ab.add_argument("--sem-navegador", action="store_true", help="só mostra o link, não abre o navegador")
    ab.add_argument("--sem-chave", action="store_true", help="modo do painel Browser do Claude Desktop (localhost, sem chave)")
    r = sub.add_parser("refinar", help="refaz a lista de uma busca sem coletar de novo (categorias, quantidade)")
    r.add_argument("--pasta", required=True, help="pasta da busca, ex.: resultados/busca-20261119-101500")
    r.add_argument("--quantidade", type=int, help="quantas empresas na lista final")
    r.add_argument("--excluir-categorias", nargs="+", default=[])
    r.add_argument("--so-categorias", nargs="+", default=[])
    r.add_argument("--ddd-padrao")
    sub.add_parser("atualizar", help="baixa a versão nova do kit e a versão do motor que ela usa")
    lp = sub.add_parser("limpar", help="remove o motor do computador (libera ~2 GB)")
    lp.add_argument("--antigas", action="store_true", help="remove só versões antigas do motor")
    lp.add_argument("--sim", action="store_true", help="não pergunta (para quem já confirmou)")
    sub.add_parser("painel", help="(re)gera resultados/painel.html com todas as suas buscas")
    a = ap.parse_args(argv)
    acoes = {"verificar": cmd_verificar, "preparar": cmd_preparar, "testar": cmd_testar, "buscar": cmd_buscar,
             "atualizar": cmd_atualizar, "limpar": cmd_limpar, "painel": cmd_painel, "refinar": cmd_refinar,
             "abrir": cmd_abrir}
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
