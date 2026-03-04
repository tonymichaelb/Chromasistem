#!/bin/bash

# Script de execução em PRODUÇÃO para Raspberry Pi
# Sistema Croma - com frontend React
# Uso: ./run-prod.sh          # build + inicia servidor
#       ./run-prod.sh --build  # apenas gera o build (útil antes de usar systemd)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "================================================"
echo "   Croma - Produção (Raspberry Pi)"
echo "   Frontend React + Backend Flask"
echo "================================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "app.py" ]; then
    echo "Erro: Execute este script no diretório do projeto"
    exit 1
fi

# Atualizar código (branch feat/skip-and-failures-feature)
if [ -d ".git" ]; then
    echo "Atualizando código..."
    git fetch origin 2>/dev/null || true
    git checkout feat/skip-and-failures-feature 2>/dev/null || true
    git pull origin feat/skip-and-failures-feature 2>/dev/null || true
fi

# Criar diretórios necessários
echo "Criando diretórios..."
mkdir -p gcode_files static/thumbnails
chmod +x install.sh run.sh run-prod.sh 2>/dev/null || true

# Ambiente virtual Python
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
fi

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Verificando dependências Python..."
pip install --upgrade pip -q
pip install -r requirements.txt

# Node.js e build do React
if ! command -v node &>/dev/null; then
    echo ""
    echo "⚠️  Node.js não encontrado!"
    echo "   Para rodar o frontend React, instale:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "   sudo apt install -y nodejs"
    echo ""
    echo "   Ou use os templates antigos (sem React): o build será ignorado."
    echo ""
fi

if command -v node &>/dev/null && [ -d "front-react" ]; then
    echo "Instalando dependências do frontend React..."
    (cd front-react && npm ci --silent 2>/dev/null || npm install)
    echo "Gerando build do React para produção (aguarde ~1 min)..."
    (cd front-react && npm run build)
    if [ -f "front-react/dist/index.html" ]; then
        echo "✓ Build React gerado em front-react/dist/"
    else
        echo "⚠️  Build falhou - o sistema usará os templates HTML antigos"
    fi
else
    echo "⚠️  Node.js ou pasta front-react não encontrado - usando templates antigos"
fi

if [ "$1" = "--build" ]; then
    echo "✓ Build concluído. Para iniciar o servidor:"
    echo "  sudo -E env PATH=\$PATH python app.py"
    echo ""
    echo "Ou configure o systemd (croma.service) e reinicie."
    exit 0
fi

echo ""
echo "Iniciando servidor na porta 80..."
echo "Acesse: http://localhost ou http://[IP-DO-RASPBERRY]"
echo "Pressione Ctrl+C para parar"
echo "================================================"
echo ""

# Porta 80 requer root no Linux
# IMPORTANTE: cd para PROJECT_DIR garante que app.py encontre front-react/dist (path relativo a __file__)
if [ "$(id -u)" -eq 0 ]; then
    exec python app.py
else
    exec sudo -E env "PATH=$PATH" bash -c "cd '$PROJECT_DIR' && exec python app.py"
fi
