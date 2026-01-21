#!/bin/bash

# Script de execução rápida para desenvolvimento/teste local
# Sistema Croma

echo "================================================"
echo "   Iniciando Sistema Croma"
echo "   Monitoramento de Impressora 3D"
echo "================================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "app.py" ]; then
    echo "Erro: Execute este script no diretório do projeto"
    exit 1
fi

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    
    echo "Instalando dependências..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Ativando ambiente virtual..."
    source venv/bin/activate
fi

echo ""
echo "Iniciando servidor Flask..."
echo ""
echo "Acesse o sistema em:"
echo "  → http://localhost:5000"
echo "  → http://127.0.0.1:5000"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo "================================================"
echo ""

# Executar o aplicativo
python app.py
