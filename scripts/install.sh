#!/bin/bash

# Script de instalação para Raspberry Pi 2W
# Sistema Croma - Monitoramento de Impressora 3D

echo "================================================"
echo "   Instalação do Sistema Croma"
echo "   Monitoramento de Impressora 3D"
echo "================================================"
echo ""

# Atualizar sistema
echo "Atualizando sistema..."
sudo apt-get update
sudo apt-get upgrade -y

# Instalar Python 3 e pip
echo "Instalando Python 3 e pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Criar ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Criar diretório para logo se não existir
mkdir -p static/images

echo ""
echo "================================================"
echo "   Instalação concluída!"
echo "================================================"
echo ""
echo "Para executar o sistema:"
echo "1. Ative o ambiente virtual:"
echo "   source venv/bin/activate"
echo ""
echo "2. Coloque o arquivo logo-branca.png em:"
echo "   static/images/logo-branca.png"
echo ""
echo "3. Execute o servidor:"
echo "   python app.py"
echo ""
echo "4. Acesse no navegador:"
echo "   http://localhost:5000"
echo "   ou"
echo "   http://[IP-DO-RASPBERRY]:5000"
echo ""
echo "================================================"
