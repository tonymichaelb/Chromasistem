#!/usr/bin/env bash
#
# Configura o Raspberry Pi para o hotspot automático do Chromasistem
# (wifi_manager.py em modo monitor + serviço systemd croma-wifi).
#
# Uso:
#   sudo CHROMA_HOME=/caminho/do/Chromasistem ./scripts/setup_raspberry_wifi_hotspot.sh
#   sudo CHROMA_USER=pi ./scripts/setup_raspberry_wifi_hotspot.sh   # se a detecção do usuário falhar
#
# Opcional: não iniciar o serviço ao final
#   sudo NO_START=1 ./scripts/setup_raspberry_wifi_hotspot.sh
#
# País para regulatório Wi-Fi (hostapd): padrão BR
#   sudo WIFI_COUNTRY=US ./scripts/setup_raspberry_wifi_hotspot.sh
#
# Forçar interface (se não for wlan0):
#   Edite o unit: Environment=WIFI_IFACE=wlan1
#
# Nome do systemd do app (Flask + front); padrão chromasistem.service
#   sudo CHROMA_APP_SERVICE=croma.service ./scripts/setup_raspberry_wifi_hotspot.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="${CHROMA_HOME:-$DEFAULT_ROOT}"
CHROMA_APP_SERVICE="${CHROMA_APP_SERVICE:-chromasistem.service}"

SERVICE_NAME="croma-wifi.service"
SUDOERS_DROPIN="/etc/sudoers.d/croma-chromasistem-wifi"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}"

die() {
  echo "❌ $*" >&2
  exit 1
}

info() { echo "➜ $*"; }
ok() { echo "✅ $*"; }

if [[ "$(id -u)" -ne 0 ]]; then
  die "Execute como root: sudo $0"
fi

if [[ -n "${CHROMA_USER:-}" ]]; then
  TARGET_USER="$CHROMA_USER"
elif [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
  TARGET_USER="$SUDO_USER"
else
  TARGET_USER="$(getent passwd | awk -F: '$3 >= 1000 && $1 != "nobody" && $6 ~ /^\/home\// { print $1; exit }')"
fi

[[ -n "$TARGET_USER" && "$TARGET_USER" != "root" ]] || \
  die "Defina o usuário do app: CHROMA_USER=pi sudo $0"

[[ -f "${PROJECT_ROOT}/wifi_manager.py" ]] || \
  die "wifi_manager.py não encontrado em: ${PROJECT_ROOT}"

WIFI_PY="/usr/bin/python3 ${PROJECT_ROOT}/wifi_manager.py"

info "Projeto: ${PROJECT_ROOT}"
info "Usuário (NOPASSWD p/ API Wi-Fi): ${TARGET_USER}"

export DEBIAN_FRONTEND=noninteractive
info "Instalando pacotes (apt)..."
apt-get update -qq
apt-get install -y --no-install-recommends \
  hostapd \
  dnsmasq \
  network-manager \
  wireless-tools \
  iw

# O wifi_manager inicia seu próprio dnsmasq com -C /tmp/dnsmasq.conf.
# O serviço systemd "dnsmasq" costuma ocupar a porta 53 e quebrar DHCP do hotspot.
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

# Em algumas imagens o hostapd vem masked; o wifi_manager invoca o binário diretamente.
systemctl unmask hostapd 2>/dev/null || true
systemctl disable --now hostapd 2>/dev/null || true

chmod +x "${PROJECT_ROOT}/wifi_manager.py"

info "Garantindo NetworkManager ativo..."
systemctl enable NetworkManager
systemctl start NetworkManager

info "Instalando regras sudo (${SUDOERS_DROPIN})..."
SUDOERS_TMP="$(mktemp)"
trap 'rm -f "$SUDOERS_TMP"' EXIT

cat > "$SUDOERS_TMP" << EOF
# Chromasistem — Wi-Fi / hotspot (gerado por setup_raspberry_wifi_hotspot.sh)
${TARGET_USER} ALL=(ALL) NOPASSWD: ${WIFI_PY} *
${TARGET_USER} ALL=(ALL) NOPASSWD: /usr/bin/nmcli
${TARGET_USER} ALL=(ALL) NOPASSWD: /usr/sbin/hostapd
${TARGET_USER} ALL=(ALL) NOPASSWD: /usr/sbin/dnsmasq
${TARGET_USER} ALL=(ALL) NOPASSWD: /sbin/ip
${TARGET_USER} ALL=(ALL) NOPASSWD: /bin/systemctl stop NetworkManager
${TARGET_USER} ALL=(ALL) NOPASSWD: /bin/systemctl start NetworkManager
${TARGET_USER} ALL=(ALL) NOPASSWD: /usr/bin/killall hostapd
${TARGET_USER} ALL=(ALL) NOPASSWD: /usr/bin/killall dnsmasq
${TARGET_USER} ALL=(ALL) NOPASSWD: /bin/systemctl stop dnsmasq
${TARGET_USER} ALL=(ALL) NOPASSWD: /usr/sbin/iw
EOF

visudo -cf "$SUDOERS_TMP" || die "sudoers inválido — abortando"
install -m 0440 -o root -g root "$SUDOERS_TMP" "$SUDOERS_DROPIN"
ok "sudoers OK"

WIFI_COUNTRY="${WIFI_COUNTRY:-BR}"

info "Instalando unit systemd (${UNIT_PATH})..."
cat > "$UNIT_PATH" << EOF
[Unit]
Description=Croma WiFi Manager - Hotspot automático (Chromasistem)
After=network-online.target NetworkManager.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}
Environment=WIFI_COUNTRY=${WIFI_COUNTRY}
# Descomente se a interface não for detectada (ex.: wlan1):
# Environment=WIFI_IFACE=wlan1
ExecStart=/usr/bin/python3 ${PROJECT_ROOT}/wifi_manager.py monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

if [[ -n "${NO_START:-}" ]]; then
  info "NO_START=1 — serviço habilitado, mas não iniciado."
  ok "Configuração concluída."
  exit 0
fi

rfkill unblock wifi 2>/dev/null || true

# Firewall comum em Raspberry Pi OS: liberar HTTP/SSH para clientes do hotspot.
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi "Status: active"; then
  info "UFW ativo — liberando 80/tcp e 22/tcp para 10.0.0.0/24 (hotspot)..."
  ufw allow from 10.0.0.0/24 to any port 80 proto tcp comment "chromasistem-hotspot" 2>/dev/null || true
  ufw allow from 10.0.0.0/24 to any port 22 proto tcp comment "ssh-hotspot" 2>/dev/null || true
fi

systemctl restart "$SERVICE_NAME"

ok "Serviço ${SERVICE_NAME} ativo."
echo ""
echo "────────────────────────────────────────────────────────────"
echo " Hotspot padrão (wifi_manager.py):"
echo "   SSID:     Croma-3D-Printer"
echo "   Senha:    croma1234"
echo "   IP do Pi: 10.0.0.1"
echo ""
echo " Interface web (porta padrão do app: PORT=80 → http://10.0.0.1 )"
echo " Se usar PORT=5000 ou outro, ajuste a URL."
echo ""
echo " Logs Wi-Fi:  sudo journalctl -u ${SERVICE_NAME} -f"
echo " Logs app:    sudo journalctl -u ${CHROMA_APP_SERVICE} -n 80 --no-pager"
echo " Teste no Pi: ping -c1 10.0.0.1 && curl -I http://127.0.0.1/"
echo " País Wi-Fi:  WIFI_COUNTRY=${WIFI_COUNTRY} (hostapd; use US, DE, etc. se necessário)"
echo "────────────────────────────────────────────────────────────"
