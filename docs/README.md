# Sistema Croma - Monitoramento de Impressora 3D

Sistema de monitoramento e controle de impressora 3D para Raspberry Pi 2W.

## Funcionalidades

- ✅ Sistema de autenticação (login e registro de usuários)
- ✅ Painel de controle em tempo real
- ✅ Monitoramento de temperatura (bico e mesa)
- ✅ Controle de impressão (Iniciar, Pausar, Retomar, Parar)
- ✅ Visualização de progresso da impressão
- ✅ Interface moderna e responsiva
- ✅ **Gerenciador de arquivos G-Code**
- ✅ **Upload de arquivos** (drag & drop)
- ✅ **Integração com OrcaSlicer**
- ✅ **Histórico de impressões por arquivo**

## Requisitos

- Python 3.8 ou superior
- Raspberry Pi 2W (ou qualquer sistema Linux/macOS/Windows para desenvolvimento)
- Impressora 3D com conexão serial/USB

## Instalação

### 1. Clone ou copie os arquivos para o Raspberry Pi

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute o sistema

```bash
python app.py
```

### 4. Acesse o sistema

Abra o navegador e acesse:
- Local: http://localhost:5000
- Na rede local: http://[IP-DO-RASPBERRY]:5000

## Estrutura do Projeto

```
.
├── app.py                      # Backend Flask
├── requirements.txt            # Dependências Python
├── croma.db                    # Banco de dados SQLite (criado automaticamente)
├── templates/
│   ├── login.html              # Página de login
│   ├── register.html           # Página de registro
│   └── dashboard.html          # Painel de controle
└── static/
    ├── css/
    │   └── style.css           # Estilos CSS
    └── images/
        └── logo-branca.png     # Logo do sistema Croma
```

## Configuração da Impressora

### Para conectar com a impressora 3D real:

1. Identifique a porta serial da impressora:
```bash
ls /dev/tty*
# Geralmente será /dev/ttyUSB0 ou /dev/ttyACM0
```

2. Modifique o arquivo `app.py` para incluir a conexão serial real
3. Ajuste os parâmetros de baudrate conforme sua impressora (geralmente 115200)

### Integração com OctoPrint (Opcional)

Se preferir usar OctoPrint como backend, você pode integrar usando a API do OctoPrint:
- Instale OctoPrint no Raspberry Pi
- Configure as chamadas de API no `app.py` para comunicar com OctoPrint

## Uso

### Primeiro Acesso

1. Acesse o sistema
2. Clique em "Criar conta"
3. Digite usuário e senha
4. Faça login

### Controles Disponíveis

- **Iniciar**: Inicia uma nova impressão
- **Pausar**: Pausa a impressão atual
- **Retomar**: Retoma uma impressão pausada
- **Parar**: Cancela a impressão atual

### Monitoramento

O sistema atualiza automaticamente a cada 2 segundos:
- Temperatura do bico e mesa
- Progresso da impressão
- Tempo decorrido e restante
- Status da conexão

## Segurança

- As senhas são criptografadas com SHA-256
- Sistema de sessão seguro
- Autenticação obrigatória para todas as funcionalidades

## Desenvolvimento

O sistema está configurado em modo de demonstração. Para uso em produção:

1. Desative o modo debug no `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

2. Configure um servidor WSGI (Gunicorn, uWSGI)
3. Use HTTPS para conexões seguras
4. Configure firewall adequadamente

## Documentação (índice)

| Pasta | Conteúdo |
|-------|----------|
| [tarefas/](tarefas/) | Tarefas para entrega, ordem de execução, critérios de aceite |
| [projeto/](projeto/) | Análise técnica, doc técnico, definições, visão do projeto |
| [sistema-cores/](sistema-cores/) | Algoritmos do sistema de cores (100+) |
| [infra-instalacao/](infra-instalacao/) | Controle remoto, instalação Raspberry Pi, Wi‑Fi, serial, sensor de filamento, OrcaSlicer |
| [outros/](outros/) | Outros documentos |

## Contribuições

Sistema desenvolvido para controle de impressora 3D com Raspberry Pi.

## Licença

MIT License - Livre para uso pessoal e comercial.
