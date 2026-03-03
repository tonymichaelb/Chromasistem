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

# Verificar e instalar dependências do front-react
if [ ! -d "front-react/node_modules" ]; then
    echo ""
    echo "Instalando dependências do frontend React..."
    (cd front-react && npm install)
fi

echo ""
echo "Iniciando backend (Flask) e frontend (React)..."
echo ""
echo "Acesse o sistema em:"
echo "  → http://localhost:5173"
echo "  → http://127.0.0.1:5173"
echo ""
echo "Pressione Ctrl+C para parar os servidores"
echo "================================================"
echo ""

# Função para encerrar ambos os processos ao receber Ctrl+C
cleanup() {
    echo ""
    echo "Parando servidores..."
    kill $FLASK_PID $FRONT_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Iniciar backend Flask em background (porta 80)
python app.py &
FLASK_PID=$!

# Aguardar um pouco para o Flask subir
sleep 2

# Iniciar frontend React em background (porta 5173)
(cd front-react && npm run dev) &
FRONT_PID=$!

# Aguardar até que o usuário pressione Ctrl+C
wait
