#!/bin/bash
#
# Chromasistem - Túnel Cloudflare (URL fixa com domínio)
# Expõe o Chromasistem por uma URL HTTPS fixa (ex.: chroma.seudominio.com.br).
# Requer domínio no Cloudflare e criação do túnel no dashboard.
#
# Uso (no Raspberry, usuário pi):
#   export CLOUDFLARE_TUNNEL_TOKEN=seu_token
#   cd /home/pi/Chromasistem && ./scripts/setup-tunnel-cloudflare.sh
# Ou coloque o token em scripts/.cloudflare-token (não versionado).
#
# Pré-requisitos:
#   - Chromasistem já em execução (./run-prod.sh ou systemd)
#   - Domínio no Cloudflare; criar túnel em Zero Trust > Access > Tunnels
#   - Configurar hostname (ex.: chroma.seudominio.com.br) no fluxo do túnel
#   - Token de instalação do túnel (variável ou arquivo .cloudflare-token)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/app.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../app.py" ]; then
    PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    echo "Erro: app.py não encontrado. Execute a partir da raiz do projeto ou de scripts/"
    exit 1
fi

CLOUDFLARED_DIR="$PROJECT_DIR/scripts/.cloudflared"
TUNNEL_PORT="${TUNNEL_PORT:-80}"
TOKEN_FILE="$SCRIPT_DIR/.cloudflare-token"
# Atualize esta versão conforme releases: https://github.com/cloudflare/cloudflared/releases
CLOUDFLARED_VERSION="${CLOUDFLARED_VERSION:-2026.3.0}"

echo "================================================"
echo "   Chromasistem - Túnel Cloudflare (URL fixa)"
echo "   Projeto: $PROJECT_DIR"
echo "   Porta local: $TUNNEL_PORT"
echo "================================================"
echo ""

# Token: variável de ambiente, arquivo ou prompt
if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    TUNNEL_TOKEN="$CLOUDFLARE_TUNNEL_TOKEN"
elif [ -f "$TOKEN_FILE" ]; then
    TUNNEL_TOKEN="$(cat "$TOKEN_FILE")"
elif [ -f "$PROJECT_DIR/scripts/.cloudflare-token" ]; then
    TUNNEL_TOKEN="$(cat "$PROJECT_DIR/scripts/.cloudflare-token")"
else
    echo "Token do túnel não encontrado."
    echo "Defina CLOUDFLARE_TUNNEL_TOKEN ou crie o arquivo scripts/.cloudflare-token com o token."
    echo "Obtenha o token em: Cloudflare Zero Trust > Access > Tunnels > Create tunnel > Cloudflared"
    echo ""
    read -r -p "Cole o token do túnel (ou Enter para sair): " TUNNEL_TOKEN
    if [ -z "$TUNNEL_TOKEN" ]; then
        exit 1
    fi
fi

# Dependências para download
if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
    echo "Instale curl ou wget: sudo apt install -y curl"
    exit 1
fi

# Detectar arquitetura (Raspberry Pi: aarch64 ou armv7l)
ARCH="$(uname -m)"
case "$ARCH" in
    aarch64|arm64)
        CLOUDFLARED_ARCH="arm64"
        ;;
    armv7l|armhf)
        CLOUDFLARED_ARCH="arm"
        ;;
    x86_64)
        CLOUDFLARED_ARCH="amd64"
        ;;
    i386|i686)
        CLOUDFLARED_ARCH="386"
        ;;
    *)
        echo "Arquitetura não suportada: $ARCH"
        exit 1
        ;;
esac

# Nome do binário no release (linux-arm64, linux-arm, linux-amd64, linux-386)
CLOUDFLARED_BINARY="cloudflared-linux-${CLOUDFLARED_ARCH}"
CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/${CLOUDFLARED_BINARY}"
CLOUDFLARED_BIN="$CLOUDFLARED_DIR/cloudflared"

# Instalar cloudflared se não existir
if [ ! -x "$CLOUDFLARED_BIN" ]; then
    echo "Instalando cloudflared ${CLOUDFLARED_VERSION} (${CLOUDFLARED_ARCH})..."
    mkdir -p "$CLOUDFLARED_DIR"
    cd "$CLOUDFLARED_DIR"
    if command -v curl &>/dev/null; then
        curl -sSL -o "cloudflared" "$CLOUDFLARED_URL"
    else
        wget -q -O "cloudflared" "$CLOUDFLARED_URL"
    fi
    chmod +x cloudflared
    cd "$PROJECT_DIR"
    echo "Cloudflared instalado em $CLOUDFLARED_DIR"
fi

echo "Iniciando túnel Cloudflare (encaminha para http://127.0.0.1:$TUNNEL_PORT)"
echo "A URL fixa é a configurada no dashboard do Cloudflare para este túnel."
echo "================================================"
echo ""

# O token já contém a configuração do túnel (incl. hostname e porta de destino).
# Se o túnel foi criado com "Public Hostname" apontando para http://localhost:80, está correto.
exec "$CLOUDFLARED_BIN" tunnel run --token "$TUNNEL_TOKEN"
