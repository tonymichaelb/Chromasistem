#!/bin/sh
# Wrapper para rodar o túnel Cloudflare (usado pelo systemd).
# Crie o arquivo .cloudflare-token.env com:
#   CLOUDFLARE_TUNNEL_TOKEN=seu_token
# Não versionar .cloudflare-token.env

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.cloudflare-token.env"
CLOUDFLARED_BIN="$SCRIPT_DIR/.cloudflared/cloudflared"

if [ ! -f "$ENV_FILE" ]; then
    echo "Crie o arquivo .cloudflare-token.env com CLOUDFLARE_TUNNEL_TOKEN=seu_token"
    exit 1
fi
if [ ! -x "$CLOUDFLARED_BIN" ]; then
    echo "Execute primeiro: ./scripts/setup-tunnel-cloudflare.sh (uma vez) para instalar o cloudflared"
    exit 1
fi

. "$ENV_FILE"
exec "$CLOUDFLARED_BIN" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN"
