#!/bin/bash
#
# Chromasistem - Túnel ngrok (URL pública temporária para testes)
# Expõe a porta do Chromasistem (padrão 80) via HTTPS. A URL muda ao reiniciar.
# Para URL fixa com domínio, use: scripts/setup-tunnel-cloudflare.sh
#
# Uso (no Raspberry, usuário pi):
#   cd /home/pi/Chromasistem && ./scripts/setup-tunnel-ngrok.sh
#
# Pré-requisitos:
#   - Chromasistem já em execução (./run-prod.sh ou systemd)
#   - Authtoken ngrok: https://dashboard.ngrok.com/get-started/your-authtoken
#   - Defina NGROK_AUTHTOKEN ou rode: ngrok config add-authtoken <token>
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

NGROK_DIR="$PROJECT_DIR/scripts/.ngrok"
TUNNEL_PORT="${TUNNEL_PORT:-80}"
NGROK_BIN="$NGROK_DIR/ngrok"

echo "================================================"
echo "   Chromasistem - Túnel ngrok (testes)"
echo "   Projeto: $PROJECT_DIR"
echo "   Porta local: $TUNNEL_PORT"
echo "================================================"
echo ""

# Dependências para download
if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
    echo "Instale curl ou wget: sudo apt install -y curl"
    exit 1
fi
if ! command -v unzip &>/dev/null; then
    echo "Instale unzip: sudo apt install -y unzip"
    exit 1
fi

# Detectar arquitetura (Raspberry Pi: aarch64 ou armv7l)
ARCH="$(uname -m)"
case "$ARCH" in
    aarch64|arm64)
        NGROK_ARCH="arm64"
        ;;
    armv7l|armhf)
        NGROK_ARCH="arm"
        ;;
    x86_64)
        NGROK_ARCH="amd64"
        ;;
    *)
        echo "Arquitetura não suportada: $ARCH"
        exit 1
        ;;
esac

# Instalar ngrok se não existir
if [ ! -x "$NGROK_BIN" ]; then
    echo "Instalando ngrok ($NGROK_ARCH)..."
    mkdir -p "$NGROK_DIR"
    cd "$NGROK_DIR"
    # ngrok v3 stable (Equinox)
    NGROK_TGZ="ngrok-v3-stable-linux-${NGROK_ARCH}.tgz"
    NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/${NGROK_TGZ}"
    if command -v curl &>/dev/null; then
        curl -sSL -o "$NGROK_TGZ" "$NGROK_URL"
    else
        wget -q -O "$NGROK_TGZ" "$NGROK_URL"
    fi
    tar xzf "$NGROK_TGZ"
    rm -f "$NGROK_TGZ"
    cd "$PROJECT_DIR"
    echo "Ngrok instalado em $NGROK_DIR"
fi

# Authtoken: variável de ambiente ou config existente
if [ -n "$NGROK_AUTHTOKEN" ]; then
    export NGROK_CONFIG_PATH="$NGROK_DIR/ngrok.yml"
    mkdir -p "$NGROK_DIR"
    if [ ! -f "$NGROK_CONFIG_PATH" ] || ! grep -q "authtoken" "$NGROK_CONFIG_PATH" 2>/dev/null; then
        "$NGROK_BIN" config add-authtoken "$NGROK_AUTHTOKEN" --config "$NGROK_CONFIG_PATH"
    fi
elif [ ! -f "$HOME/.config/ngrok/ngrok.yml" ] && [ ! -f "$NGROK_DIR/ngrok.yml" ]; then
    echo ""
    echo "Authtoken não configurado."
    echo "1. Crie uma conta em https://ngrok.com e copie o token: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. Defina a variável: export NGROK_AUTHTOKEN=seu_token"
    echo "   Ou execute: $NGROK_BIN config add-authtoken seu_token"
    echo ""
    exit 1
fi

if [ -n "$NGROK_CONFIG_PATH" ]; then
    export NGROK_CONFIG_PATH
elif [ -f "$NGROK_DIR/ngrok.yml" ]; then
    export NGROK_CONFIG_PATH="$NGROK_DIR/ngrok.yml"
fi

echo "Iniciando túnel para http://127.0.0.1:$TUNNEL_PORT"
echo "A URL HTTPS será exibida abaixo (muda a cada reinício). Para URL fixa, use setup-tunnel-cloudflare.sh"
echo "================================================"
echo ""

exec "$NGROK_BIN" http "$TUNNEL_PORT"
