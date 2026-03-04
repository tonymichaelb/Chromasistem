# 🎨 Sistema Croma - Visão Geral do Projeto

```
   ██████╗██████╗  ██████╗ ██╗   ██╗ █████╗ 
  ██╔════╝██╔══██╗██╔═══██╗████╗ ████║██╔══██╗
  ██║     ██████╔╝██║   ██║██╔████╔██║███████║
  ██║     ██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║
  ╚██████╗██║  ██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
   ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝
```

## 📋 Visão Geral

Sistema completo de monitoramento e controle de impressora 3D desenvolvido para **Raspberry Pi 2W**.

### ✨ Funcionalidades Principais

| Funcionalidade | Status | Descrição |
|----------------|--------|-----------|
| 🔐 Autenticação | ✅ Completo | Sistema de login e registro de usuários |
| 🎛️ Painel de Controle | ✅ Completo | Interface em tempo real com dados da impressora |
| 🌡️ Monitoramento | ✅ Completo | Temperatura do bico e mesa aquecida |
| ⏯️ Controles | ✅ Completo | Iniciar, Pausar, Retomar, Parar impressão |
| 📊 Progresso | ✅ Completo | Barra de progresso e estimativa de tempo |
| 📱 Responsivo | ✅ Completo | Funciona em desktop, tablet e smartphone |

---

## 📁 Estrutura do Projeto

```
Chromasistem/
│
├── 📄 app.py                          # Entry point (importa core/ e routes/)
├── 📁 core/                           # Lógica de negócio (backend)
│   ├── config.py                      # Flask app, constantes, variáveis de ambiente
│   ├── state.py                       # Estado mutável compartilhado (globals)
│   ├── database.py                    # Inicialização do banco SQLite
│   ├── printer.py                     # Comunicação serial, send_gcode, temps
│   ├── filament.py                    # Sensor de filamento (GPIO / Marlin)
│   ├── gcode.py                       # Parsing G-code, thumbnails, slicer
│   └── print_engine.py                # Thread de impressão
├── 📁 routes/                         # Rotas Flask (Blueprints)
│   ├── auth.py                        # Login, register, logout
│   ├── pages.py                       # Páginas HTML + assets React
│   ├── printer_api.py                 # APIs /api/printer/*
│   ├── files_api.py                   # APIs /api/files/* e /api/slicer/*
│   └── wifi_api.py                    # APIs /api/wifi/*
├── 📄 requirements.txt                # Dependências Python
├── 📄 README.md                       # Documentação principal
├── 📄 .gitignore                      # Arquivos ignorados pelo Git
│
├── 📁 scripts/                        # Scripts de execução e instalação
│   ├── run.sh                         # Execução rápida (dev)
│   ├── run-prod.sh                    # Produção (Raspberry Pi)
│   └── install.sh                     # Instalação de dependências
├── 🔧 croma.service                   # Serviço systemd para autostart
│
├── 📁 templates/                      # Templates HTML
│   ├── login.html                     # Página de login
│   ├── register.html                  # Página de registro
│   └── dashboard.html                 # Painel principal
│
└── 📁 static/                         # Arquivos estáticos
    ├── 📁 css/
    │   └── style.css                  # Estilos CSS personalizados
    └── 📁 images/
        └── logo-branca.png            # Logo do sistema Croma
```

---

## 🚀 Como Usar

### Para Desenvolvimento Local (Mac/PC):

```bash
# 1. Entre no diretório
cd "Novo modo Wi-Fi de cores"

# 2. Execute o script
./run.sh
```

### Para Raspberry Pi:

```bash
# 1. Transfira os arquivos para o Raspberry Pi
# 2. Execute a instalação
./install.sh

# 3. Inicie o sistema
source venv/bin/activate
python app.py
```

Consulte [INSTALACAO_RASPBERRY.md](../infra-instalacao/INSTALACAO_RASPBERRY.md) para instruções detalhadas.

---

## 🎨 Interface do Sistema

### Tela de Login
- Logo Croma centralizada
- Campos de usuário e senha
- Link para criar nova conta
- Design moderno com gradiente escuro

### Tela de Registro
- Formulário de criação de conta
- Validação de senha (mínimo 6 caracteres)
- Confirmação de senha
- Redirecionamento automático após sucesso

### Painel de Controle (Dashboard)
- **Status da Impressora**: Estado e conexão
- **Temperaturas**: Bico e mesa com valores atuais/alvo
- **Progresso**: Barra visual, tempo decorrido e restante
- **Controles**: Botões para Iniciar, Pausar, Retomar, Parar
- **Upload**: Área para carregar arquivos G-Code
- Atualização automática a cada 2 segundos

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3 + Flask |
| Frontend | HTML5 + CSS3 + JavaScript |
| Banco de Dados | SQLite |
| Autenticação | Session-based + SHA-256 |
| Comunicação Serial | PySerial |
| API | RESTful JSON |

---

## 🔐 Segurança

- ✅ Senhas criptografadas com SHA-256
- ✅ Sessões seguras com chave secreta aleatória
- ✅ Validação de entrada de dados
- ✅ Proteção contra SQL Injection
- ✅ Autenticação obrigatória para todas as rotas

---

## 📊 Endpoints da API

### Autenticação
- `POST /api/login` - Fazer login
- `POST /api/register` - Criar nova conta
- `POST /api/logout` - Fazer logout

### Controle da Impressora
- `GET /api/printer/status` - Obter status atual
- `POST /api/printer/start` - Iniciar impressão
- `POST /api/printer/pause` - Pausar impressão
- `POST /api/printer/resume` - Retomar impressão
- `POST /api/printer/stop` - Parar impressão

---

## 🎯 Roadmap Futuro (Melhorias Possíveis)

- [ ] Integração com webcam para monitoramento visual
- [ ] Histórico de impressões
- [ ] Gráficos de temperatura em tempo real
- [ ] Notificações push quando impressão concluir
- [ ] Upload de arquivos G-Code
- [ ] Controle de múltiplas impressoras
- [ ] Aplicativo mobile nativo
- [ ] Integração com Telegram/Discord
- [ ] Estimativa de custo de material
- [ ] Time-lapse automático

---

## 📱 Acesso Remoto

### Na Rede Local:
```
http://[IP-DO-RASPBERRY]:5000
```

### Via Internet (com configuração adicional):
1. Configure port forwarding no roteador
2. Use serviço de DNS dinâmico
3. Implemente HTTPS para segurança

---

## 🐛 Resolução de Problemas

| Problema | Solução |
|----------|---------|
| Porta 5000 ocupada | Mude para porta 8080 no app.py |
| Sem acesso remoto | Verifique firewall e permissões |
| Erro serial | Adicione usuário ao grupo dialout |
| Banco não cria | Verifique permissões de escrita |

---

## 📝 Notas Importantes

⚠️ **Modo Demonstração**: O sistema está configurado com dados simulados. Para usar com impressora real, é necessário implementar a comunicação serial.

⚠️ **Debug Mode**: Desative o modo debug (`debug=False`) em produção.

⚠️ **Segurança**: Em ambientes de produção, use HTTPS e senhas fortes.

---

## 📞 Informações do Sistema

- **Nome**: Croma
- **Versão**: 1.0.0
- **Plataforma**: Raspberry Pi 2W
- **Porta**: 5000
- **Licença**: MIT
- **Autor**: Sistema desenvolvido para controle de impressora 3D

---

## 🎉 Pronto para Usar!

O sistema está completamente funcional e pronto para ser implantado no seu Raspberry Pi 2W.

**Boas impressões! 🖨️✨**
