
#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando Chromasistem (sem hotspot automático)..."

# Apenas desbloqueia Wi‑Fi e tenta garantir que a interface esteja up; não liga hotspot.
rfkill unblock wifi || true
ip link set wlan0 up 2>/dev/null || true

# Inicia aplicação diretamente
echo "🚀 Iniciando servidor web..."
cd /home/pi/Chromasistem
exec /home/pi/Chromasistem/venv/bin/python app.py
