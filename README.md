# Chromasistem

Sistema de monitoramento e controle de impressora 3D (Raspberry Pi 2W). Inclui painel em tempo real, upload de G-code, sistema de cores (Colorir/Mistura), integração OrcaSlicer e mais.

## Início rápido

```bash
pip install -r requirements.txt
python app.py
```

Acesse: http://localhost

## Estrutura do projeto

```
├── app.py                  # Entry point (importa core/ e routes/)
├── core/                   # Lógica de negócio (backend)
│   ├── config.py           # Flask app, constantes, variáveis de ambiente
│   ├── state.py            # Estado mutável compartilhado (globals)
│   ├── database.py         # Inicialização do banco SQLite
│   ├── printer.py          # Comunicação serial (send_gcode, connect, status)
│   ├── filament.py         # Sensor de filamento (GPIO / Marlin)
│   ├── gcode.py            # Parsing de G-code, thumbnails, metadata, slicer
│   └── print_engine.py     # Thread de impressão (envio linha a linha)
├── routes/                 # Rotas Flask (Blueprints)
│   ├── auth.py             # Login, registro, logout
│   ├── pages.py            # Páginas HTML e assets React
│   ├── printer_api.py      # APIs /api/printer/* (status, pause, resume, etc.)
│   ├── files_api.py        # APIs /api/files/* e /api/slicer/*
│   └── wifi_api.py         # APIs /api/wifi/*
├── front-react/            # Frontend React (dev + build)
├── templates/              # Templates Jinja2 (fallback sem React)
├── static/                 # CSS, JS, imagens
├── scripts/                # Scripts de execução e instalação (.sh)
├── docs/                   # Documentação completa
└── requirements.txt        # Dependências Python
```

## Documentação

Toda a documentação está em **[docs/](docs/)**:

- **[docs/README.md](docs/README.md)** — visão do projeto, instalação e índice da documentação
- **[docs/tarefas/](docs/tarefas/)** — tarefas para entrega
- **[docs/projeto/](docs/projeto/)** — análise técnica, doc técnico, definições
- **[docs/sistema-cores/](docs/sistema-cores/)** — algoritmos do sistema de cores
- **[docs/infra-instalacao/](docs/infra-instalacao/)** — instalação, Raspberry Pi, Wi‑Fi, serial, sensor, OrcaSlicer

## Licença

MIT License.
