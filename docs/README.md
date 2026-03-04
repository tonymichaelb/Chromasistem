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

O backend foi dividido em módulos para facilitar manutenção. O `app.py` é apenas o ponto de entrada.

```
.
├── app.py                      # Entry point — importa core/ e routes/, inicia o servidor
├── core/                       # Lógica de negócio (backend)
│   ├── config.py               # Flask app, CORS, constantes, variáveis de ambiente
│   ├── state.py                # Estado mutável compartilhado entre módulos
│   ├── database.py             # Inicialização do SQLite (tabelas, admin padrão)
│   ├── printer.py              # Comunicação serial (send_gcode, connect, status, temps)
│   ├── filament.py             # Sensor de filamento (GPIO / Marlin M119)
│   ├── gcode.py                # Parsing de G-code, thumbnails, metadados, OrcaSlicer CLI
│   └── print_engine.py         # Thread de impressão (envio G-code linha a linha)
├── routes/                     # Rotas Flask organizadas por Blueprints
│   ├── auth.py                 # /api/login, /api/register, /api/logout, /api/me
│   ├── pages.py                # Páginas HTML (/, /dashboard, /files, /terminal, etc.)
│   ├── printer_api.py          # /api/printer/* (status, pause, resume, stop, gcode, brush, etc.)
│   ├── files_api.py            # /api/files/* (list, upload, delete, print, download, preview) + /api/slicer/slice
│   └── wifi_api.py             # /api/wifi/* (scan, connect, status, saved, forget)
├── front-react/                # Frontend React (src/ para dev, dist/ para produção)
├── templates/                  # Templates Jinja2 (fallback quando build React não existe)
├── static/                     # CSS, JS, imagens, thumbnails
├── scripts/                    # Scripts de execução e instalação (.sh)
│   ├── run.sh                  # Dev local
│   ├── run-prod.sh             # Produção (Raspberry Pi)
│   └── install.sh              # Instalação de dependências do sistema
├── gcode_files/                # Arquivos G-code enviados pelo usuário
├── docs/                       # Documentação do projeto
├── requirements.txt            # Dependências Python
├── croma.db                    # Banco SQLite (criado automaticamente)
└── croma.service               # Unit systemd para deploy no Pi
```

### Onde mexer para cada tipo de alteração

| Quero alterar… | Arquivo(s) |
|---|---|
| Constantes, portas, env vars | `core/config.py` |
| Tabelas do banco, migração | `core/database.py` |
| Comunicação serial, envio de G-code | `core/printer.py` |
| Sensor de filamento | `core/filament.py` |
| Parsing de G-code, thumbnails, slicer | `core/gcode.py` |
| Lógica da thread de impressão (pause, skip, progresso) | `core/print_engine.py` |
| APIs da impressora (status, pause, resume, brush, etc.) | `routes/printer_api.py` |
| APIs de arquivos (upload, delete, imprimir) | `routes/files_api.py` |
| Autenticação (login, registro) | `routes/auth.py` |
| Páginas HTML / assets React | `routes/pages.py` |
| Wi-Fi (scan, connect) | `routes/wifi_api.py` |
| Estado global (flags, caches) | `core/state.py` |
| Frontend React | `front-react/src/` |

### Convenção de estado compartilhado

O estado mutável (variáveis globais como `print_paused`, `printer_serial`, etc.) fica em `core/state.py`. Todos os módulos acessam via:

```python
import core.state as st
st.print_paused = True   # modifica
if st.print_paused: ...  # lê
```

## Configuração da Impressora

### Para conectar com a impressora 3D real:

1. Identifique a porta serial da impressora:
```bash
ls /dev/tty*
# Geralmente será /dev/ttyUSB0 ou /dev/ttyACM0
```

2. Ajuste os parâmetros em `core/config.py` (SERIAL_PORT, SERIAL_BAUDRATE) ou via variáveis de ambiente
3. Baudrate padrão: 115200

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
