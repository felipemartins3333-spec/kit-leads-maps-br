#!/usr/bin/env bash
# teste-real.sh — roda o teste real do kit na SUA máquina (3 consultas, -depth 1, sem proxy).
#
# O que faz, em ordem:
#   1. confere a máquina (arquitetura, memória, espaço em disco, Docker);
#   2. baixa a imagem oficial do motor, só se houver espaço;
#   3. Teste 1: coleta SEM e-mail (idioma pt-BR; se vier 0 linhas, repete com pt);
#   4. Teste 2: coleta COM e-mail, medindo o tempo;
#   5. gera resultados/relatorio-teste.txt (só números, sem dados de empresas).
#
# Uso:   bash scripts/teste-real.sh              (teste completo)
#        bash scripts/teste-real.sh --so-checar  (só confere a máquina, não baixa nem coleta)

set -u
cd "$(dirname "$0")/.." || exit 1

IMAGEM="gosom/google-maps-scraper"
CONSULTAS="examples/consultas-teste.txt"
MIN_LIVRE_GB=5   # a imagem tem ~2 GB; a folga extra é para o Docker descompactar (estimativa nossa)
SO_CHECAR=0
[ "${1:-}" = "--so-checar" ] && SO_CHECAR=1

dizer() { printf '%s\n' "$*"; }
parar() { printf '\n[PAROU] %s\n' "$*"; exit 1; }

dizer "=== Kit de leads Google Maps — teste real ==="
dizer "Este teste faz no máximo 3 consultas, sem proxy. Leia o aviso sobre os termos do Google e a LGPD no README."
dizer ""

# ---------- 1. Conferir a máquina ----------
ARQ="$(uname -m)"
case "$ARQ" in
  x86_64|aarch64|arm64) dizer "[ok] Arquitetura: $ARQ (a imagem oficial existe para amd64 e arm64)" ;;
  *) parar "Arquitetura $ARQ não é coberta pela imagem oficial (só amd64 e arm64). Veja o plano B em docs/teste-no-chromebook.md." ;;
esac

RAM_MB="$(awk '/^MemTotal:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)"
if [ "${RAM_MB:-0}" -lt 3000 ]; then
  dizer "[aviso] Memória: ${RAM_MB} MB. Com menos de ~3 GB o navegador do motor pode travar (estimativa nossa; o teste vai dizer)."
else
  dizer "[ok] Memória: ${RAM_MB} MB"
fi

LIVRE_GB="$(df -Pk . | awk 'NR==2 {print int($4/1048576)}')"
dizer "[info] Espaço livre aqui: ${LIVRE_GB} GB"

command -v python3 >/dev/null 2>&1 || parar "Python 3 não encontrado. Instale com: sudo apt install python3"
dizer "[ok] Python: $(python3 --version 2>&1)"

if ! command -v docker >/dev/null 2>&1; then
  parar "O Docker não está instalado. Siga o passo 3 de docs/teste-no-chromebook.md (vem da documentação oficial do Docker) e rode este script de novo."
fi
ERRO_DOCKER="$(docker info 2>&1 >/dev/null)"
if [ -n "$ERRO_DOCKER" ] && ! docker info >/dev/null 2>&1; then
  case "$ERRO_DOCKER" in
    *"permission denied"*)
      parar "O Docker existe, mas o seu usuário não tem permissão. Veja o passo 4 de docs/teste-no-chromebook.md (grupo 'docker'), saia e entre de novo no terminal." ;;
    *"Cannot connect"*|*"failed to connect"*|*"daemon"*)
      parar "O Docker está instalado, mas o serviço não está ligado. Tente: sudo systemctl start docker (e confira com: sudo systemctl status docker)." ;;
    *) parar "O Docker não respondeu. Mensagem dele: $ERRO_DOCKER" ;;
  esac
fi
dizer "[ok] Docker: $(docker --version 2>&1)"

[ -f "$CONSULTAS" ] || parar "Não achei $CONSULTAS."
N_CONSULTAS="$(grep -c -v -E '^\s*(#|$)' "$CONSULTAS")"
if [ "$N_CONSULTAS" -gt 3 ]; then
  parar "$CONSULTAS tem $N_CONSULTAS consultas. O teste aceita no máximo 3 (regra do projeto: testes pequenos)."
fi
dizer "[ok] Consultas de teste: $N_CONSULTAS (arquivo $CONSULTAS)"

if ! docker image inspect "$IMAGEM" >/dev/null 2>&1; then
  if [ "$LIVRE_GB" -lt "$MIN_LIVRE_GB" ]; then
    parar "Falta espaço: a imagem tem ~2 GB e a folga mínima é ${MIN_LIVRE_GB} GB livres; você tem ${LIVRE_GB} GB. Libere espaço e tente de novo."
  fi
  NECESSITA_BAIXAR=1
else
  NECESSITA_BAIXAR=0
  dizer "[ok] A imagem $IMAGEM já está baixada."
fi

if [ "$SO_CHECAR" = 1 ]; then
  dizer ""
  dizer "Checagem concluída (modo --so-checar): nada foi baixado nem coletado."
  exit 0
fi

# ---------- 2. Baixar a imagem ----------
mkdir -p resultados
if [ "$NECESSITA_BAIXAR" = 1 ]; then
  dizer ""
  dizer "Baixando a imagem oficial (~2 GB). Pode levar alguns minutos..."
  docker pull "$IMAGEM" || parar "Não consegui baixar a imagem. Confira a internet e tente de novo."
fi

MOTOR_VERSAO="$(docker run --rm -e DISABLE_TELEMETRY=1 "$IMAGEM" -version 2>&1 | tail -n 1)"
DIGEST="$(docker image inspect --format '{{index .RepoDigests 0}}' "$IMAGEM" 2>/dev/null || echo desconhecido)"
{
  echo "data=$(date +%Y-%m-%d)"
  echo "so=$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-desconhecido}")"
  echo "arquitetura=$ARQ"
  echo "ram_mb=$RAM_MB"
  echo "disco_livre_gb=$LIVRE_GB"
  echo "docker=$(docker --version 2>&1)"
  echo "motor_versao=$MOTOR_VERSAO"
  echo "imagem_digest=$DIGEST"
  echo "python=$(python3 --version 2>&1)"
} > resultados/ambiente.txt
: > resultados/medicoes.tsv
dizer "[ok] Motor: $MOTOR_VERSAO"

# ---------- 3. Função que roda um teste ----------
LINHAS=0
rodar() {  # nome  idioma  email(0|1)  arquivo.csv
  local nome="$1" lang="$2" email="$3" arq="$4" extra=() ini fim seg cod
  [ "$email" = 1 ] && extra+=(-email)
  rm -f "resultados/$arq"
  dizer ""
  dizer ">>> $nome (idioma: $lang, e-mail: $([ "$email" = 1 ] && echo sim || echo não)) ..."
  ini="$(date +%s)"
  timeout 20m docker run --rm \
    -e DISABLE_TELEMETRY=1 \
    -v gmaps-playwright-cache:/opt \
    -v "$PWD/$CONSULTAS:/queries.txt:ro" \
    -v "$PWD/resultados:/out" \
    "$IMAGEM" \
    -input /queries.txt -results "/out/$arq" \
    -depth 1 -lang "$lang" -exit-on-inactivity 3m \
    ${extra[@]+"${extra[@]}"} > "resultados/${arq%.csv}.log" 2>&1
  cod=$?
  fim="$(date +%s)"
  seg=$((fim - ini))
  # O motor roda como root dentro do contêiner; devolve os arquivos ao seu usuário (mesma imagem, sem baixar nada).
  docker run --rm -e DISABLE_TELEMETRY=1 --entrypoint chown -v "$PWD/resultados:/out" "$IMAGEM" \
    -R "$(id -u):$(id -g)" /out >/dev/null 2>&1
  # Atenção: o motor sai com código 0 mesmo sem coletar nada. Por isso contamos as linhas do CSV.
  LINHAS="$(python3 -I scripts/resumo_teste.py --linhas "resultados/$arq")"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$nome" "$lang" "$email" "$seg" "$LINHAS" "$cod" "$arq" >> resultados/medicoes.tsv
  dizer "    tempo: ${seg}s | linhas coletadas: ${LINHAS} | código de saída do motor: ${cod}"
}

# ---------- 4. Os testes ----------
LANG_OK=""
rodar "teste1-sem-email" "pt-BR" 0 "teste1-sem-email.csv"
if [ "$LINHAS" -gt 0 ]; then
  LANG_OK="pt-BR"
else
  dizer "    Veio 0 linha com pt-BR. Repetindo com o idioma 'pt'..."
  rodar "teste1b-sem-email-pt" "pt" 0 "teste1b-sem-email-pt.csv"
  [ "$LINHAS" -gt 0 ] && LANG_OK="pt"
fi

if [ -z "$LANG_OK" ]; then
  dizer ""
  dizer "Nenhuma linha coletada com pt-BR nem com pt. Causas prováveis (veja resultados/*.log):"
  if grep -q "ERR_NAME_NOT_RESOLVED" resultados/*.log 2>/dev/null; then
    dizer "  - o contêiner não conseguiu resolver google.com (internet, DNS, VPN ou firewall da rede)."
  fi
  dizer "  - o Google pode ter pedido confirmação/bloqueado o acesso temporariamente;"
  dizer "  - pouca memória, o navegador do motor pode ter travado."
  dizer "Teste 2 NÃO foi executado. O relatório abaixo mostra o que foi medido."
else
  dizer ""
  dizer "Idioma que funcionou: $LANG_OK"
  rodar "teste2-com-email" "$LANG_OK" 1 "teste2-com-email.csv"
fi

# ---------- 5. Relatório (só números) ----------
dizer ""
python3 -I scripts/resumo_teste.py
dizer ""
dizer "Pronto. Cole no chat o conteúdo de resultados/relatorio-teste.txt (ele não tem nomes, telefones nem e-mails)."
dizer "Não cole os arquivos .csv nem os .log: eles têm dados de empresas."
