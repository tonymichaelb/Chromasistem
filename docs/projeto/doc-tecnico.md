> Guia de Desenvolvimento
> 
> 
> **Data:** 19 de Janeiro de 2026
> 
> **Para:** Desenvolvedor responsável
> 
> **Objetivo:** Saber exatamente o que fazer, onde fazer e como validar
> 

---

## **📁 Mapa dos Projetos**

### **Qual projeto mexer em cada situação?**

| Projeto | URL | Vou Mexer? | Para quê serve |
| --- | --- | --- | --- |
| **Chromasistem** | (este repositório) | ✅ **SIM** | Projeto principal em uso – interface melhor, funcionando melhor. TUDO será feito aqui |
| **Gabiru** | [github.com/tonymichaelb/Gabiru](https://github.com/tonymichaelb/Gabiru) | ❌ Não | Referência / projeto anterior |
| **OctoPrint** | [github.com/OctoPrint/OctoPrint](https://github.com/OctoPrint/OctoPrint) | ❌ Não | Apenas referência para consultar como funcionalidades são feitas |
| **3D Slicer** | [github.com/Slicer/Slicer](https://github.com/Slicer/Slicer) | ❌ Não | Apenas referência sobre fatiamento |

> 💡 Resumo: O **Chromasistem** é o projeto atual do cliente (interface melhor, em uso). Todo o desenvolvimento será nele.
> 

---

## **🏗️ Estrutura do Chromasistem**

### **Stack Tecnológica**

| Camada | Tecnologia |
| --- | --- |
| Backend | Python 3.10+ com Flask |
| Frontend | JavaScript vanilla + HTML + CSS (templates Jinja2) |
| Servidor | Werkzeug (Flask dev) / produção conforme deploy |
| Hardware | Raspberry Pi Zero 2 W (ou máquina local) |
| Comunicação | Serial USB (pyserial) + REST API |

### **Pastas do Projeto**

| Pasta/Arquivo | O que tem |
| --- | --- |
| `app.py` | Entry point — importa core/ e routes/, inicia o servidor |
| `core/` | Lógica de negócio: config, estado global, banco, serial, filamento, G-code, thread de impressão |
| `routes/` | Rotas Flask (Blueprints): auth, páginas, printer API, files API, WiFi API |
| `front-react/` | Frontend React (src/ para dev, dist/ para produção) |
| `templates/` | Templates Jinja2 (fallback sem build React) |
| `static/` | CSS, JS, imagens, thumbnails |
| `scripts/` | Scripts de execução e instalação (.sh) |
| `gcode_files/` | Arquivos G-code enviados |
| `docs/` | Documentação do projeto |
| `requirements.txt` | Dependências Python |
| `croma.service` | Unit systemd para deploy no Pi |

**Detalhe dos módulos `core/`:**

| Módulo | Responsabilidade |
| --- | --- |
| `config.py` | Flask app, CORS, constantes, variáveis de ambiente |
| `state.py` | Estado mutável compartilhado (ex.: `print_paused`, `printer_serial`) |
| `database.py` | Inicialização do SQLite, hash de senha |
| `printer.py` | Conexão serial, `send_gcode`, leitura de temperatura/posição |
| `filament.py` | Sensor de filamento (GPIO / Marlin M119) |
| `gcode.py` | Parsing de G-code, thumbnails, metadados, OrcaSlicer CLI |
| `print_engine.py` | Thread de impressão (envio linha a linha, pause/park, skip) |

**Detalhe dos módulos `routes/`:**

| Módulo | Endpoints |
| --- | --- |
| `auth.py` | `/api/login`, `/api/register`, `/api/logout`, `/api/me`, `/api/version` |
| `pages.py` | `/`, `/dashboard`, `/files`, `/terminal`, `/colorir`, `/mistura`, `/fatiador`, `/wifi` |
| `printer_api.py` | `/api/printer/*` (status, pause, resume, stop, gcode, brush, mixture, filament) |
| `files_api.py` | `/api/files/*` (list, upload, delete, print, download, preview), `/api/slicer/slice` |
| `wifi_api.py` | `/api/wifi/*` (scan, connect, status, saved, forget) |

---

## **🖥️ Como Rodar o Projeto Localmente**

### **Passo 1: Clonar o Repositório**

Clonar o Chromasistem (este repositório) para sua máquina.

### **Passo 2: Instalar Dependências Python**

Na raiz do projeto, criar um ambiente virtual Python e instalar as dependências do `requirements.txt` (ex.: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`).

### **Passo 3: Iniciar o Servidor**

Rodar `python app.py` (servidor Flask na porta 80 por padrão).

### **Passo 4: Acessar**

Abrir `http://localhost` ou `http://localhost:80` no navegador.

### **Observação Importante**

Sem a impressora conectada, algumas funcionalidades não vão funcionar (conexão serial). Mas você consegue desenvolver e testar a maior parte do sistema.

---

## **📋 Features a Desenvolver**

### **Feature 1: Sistema de Detecção e Skip de Falhas**

**Onde desenvolver:** Chromasistem (backend + frontend)

**O que precisa fazer:**

1. **Backend:**
    - Criar endpoint para receber notificação de falha
    - Implementar lógica para pular item atual e ir para o próximo
    - Salvar log de itens pulados
2. **Frontend:**
    - Adicionar botão manual "Pular item com defeito"
    - Mostrar indicador visual de itens pulados
    - Exibir histórico de falhas
3. **Opcional (avançado):**
    - Integrar câmera para detecção automática via imagem
    - Usar biblioteca de visão computacional (OpenCV)

**Como testar sem impressora:**

- Simular comandos G-code no backend
- Criar mock de "item com defeito" para testar o skip

**Como validar com impressora:**

- Equipe Manaus grava vídeo mostrando item sendo pulado

---

### **Feature 2: Expansão do Sistema de Cores**

**Onde desenvolver:** Chromasistem (backend + frontend)

**O que precisa fazer:**

1. **Backend:**
    - Criar algoritmo de mistura de cores (RGB/HSL)
    - Calcular proporções de cada filamento (ex: 30% vermelho, 50% azul, 20% branco)
    - Gerar comando G-code com as proporções corretas
2. **Frontend:**
    - Criar color picker visual
    - Mostrar preview da cor resultante
    - Exibir porcentagem de cada filamento
    - Interface para salvar combinações favoritas
3. **Lógica de cores:**
    - Com 3 filamentos e proporções de 10% em 10%, teoricamente temos 1.331 combinações
    - Na prática, filtrar para 100-200 cores visualmente distintas

**Como testar sem impressora:**

- 100% testável localmente
- É apenas lógica + interface visual

**Como validar com impressora:**

- Foto da peça impressa comparando com preview do sistema

---

### **Feature 3: Sistema de Pause/Resume**

**Onde desenvolver:** Chromasistem (backend)

**O que precisa fazer:**

1. **Backend:**
    - Implementar comando de pause (G-code M0 ou M1)
    - Salvar estado atual (posição X/Y/Z, temperatura, linha do G-code)
    - Implementar comando de resume que retoma do ponto salvo
2. **Frontend:**
    - Botão de Pause/Resume no dashboard
    - Mostrar estado atual (pausado/rodando)
    - Opções ao pausar: trocar filamento, ajustar temperatura
3. **Cuidados:**
    - Manter temperatura do bico enquanto pausado (evitar entupimento)
    - Retrair filamento antes de pausar
    - Retornar à posição exata ao resumir

**Como testar sem impressora:**

- Criar mock que simula envio de comandos G-code
- Verificar se estado é salvo e restaurado corretamente

**Como validar com impressora:**

- Vídeo pausando no meio da impressão e retomando

---

### **Feature 4: Redesign da Interface**

**Onde desenvolver:** Chromasistem (frontend)

**O que precisa fazer:**

1. **Análise:**
    - Mapear telas atuais e pontos de confusão
    - Definir fluxos principais do usuário
2. **Design:**
    - Criar layout mais limpo e moderno
    - Melhorar hierarquia visual
    - Adicionar feedback visual (loading, sucesso, erro)
3. **Implementação:**
    - Refatorar CSS para design system consistente
    - Melhorar responsividade (funcionar bem no celular)
    - Organizar JavaScript em componentes

**Como testar:**

- 100% testável localmente no navegador
- Testar em diferentes tamanhos de tela

**Como validar:**

- Screenshots para aprovação do cliente

---

### **Feature 5: Fatiador Integrado**

**Onde desenvolver:** Chromasistem (backend + frontend)

**O que precisa fazer:**

1. **Backend:**
    - Instalar OrcaSlicer ou PrusaSlicer no Raspberry Pi
    - Criar endpoint que recebe arquivo 3D (.stl, .obj)
    - Chamar o fatiador via linha de comando
    - Retornar G-code gerado
2. **Frontend:**
    - Criar tela de upload de arquivo 3D
    - Mostrar opções básicas de fatiamento (qualidade, preenchimento)
    - Exibir preview do resultado (se possível)
    - Botão para enviar direto para impressão
3. **Fluxo:**
    - Usuário faz upload do .stl
    - Sistema fatia em background
    - G-code gerado vai para fila de impressão

**Como testar sem impressora:**

- Testar localmente a geração de G-code
- Verificar se arquivo é gerado corretamente

**Como validar com impressora:**

- Imprimir uma peça do início ao fim usando só o sistema

---

### **Feature 6: Controle Remoto**

**Onde desenvolver:** Chromasistem (backend + infra)

**O que precisa fazer:**

1. **Autenticação:**
    - Adicionar login com usuário/senha
    - Implementar JWT ou sessão segura
2. **Acesso Externo (escolher uma opção):**
    - **Opção A - Cloudflare Tunnel:** Mais simples, grátis
    - **Opção B - ngrok:** Simples, plano gratuito com limitações
    - **Opção C - VPN própria:** Mais seguro, mais complexo
3. **Segurança:**
    - HTTPS obrigatório
    - Rate limiting para evitar ataques
    - Logs de acesso
4. **Streaming de Câmera:**
    - Reaproveitar base do time-lapse que já existe
    - Criar endpoint de streaming ao vivo

**Como testar sem impressora:**

- Testar autenticação localmente
- Testar acesso via túnel

**Como validar:**

- Demonstração ao vivo acessando de fora da rede local

---

## **🔄 Fluxo de Desenvolvimento**

### **Ciclo para Cada Feature**

```
1. Desenvolver localmente
      ↓
2. Testar com simulação/mock
      ↓
3. Commit + Push no GitHub
      ↓
4. Deploy no Raspberry Pi (ex.: croma.service; configurar auto-update se desejado)
      ↓
5. Equipe Manaus testa na impressora real
      ↓
6. Feedback (funciona / tem bug / precisa ajuste)
      ↓
7. Se OK → Feature entregue ✅
   Se não → Voltar ao passo 1

```

### **Tempo Médio por Ciclo**

- Desenvolvimento: 1-3 dias
- Teste remoto: 1-2 dias
- **Total por iteração: 2-5 dias**

---

## **🧪 O Que Dá Para Testar Sem Impressora**

| Feature | % Testável Local |
| --- | --- |
| Sistema de Cores | 100% |
| Interface/UX | 100% |
| Fatiador | 90% (só não imprime) |
| Autenticação/Remoto | 80% |
| Pause/Resume | 60% (mock de comandos) |
| Detecção de Falhas | 50% (sem câmera real) |

---

## **📡 O Que Preciso da Equipe em Manaus**

| Necessidade | Por quê |
| --- | --- |
| Acesso SSH ao Raspberry Pi | Debug remoto, ver logs |
| Pessoa para testes | Rodar impressões de validação |
| Envio de vídeos/fotos | Evidência de funcionamento |
| Resposta em até 48h | Não travar o desenvolvimento |

---

## **🛠️ Ferramentas Necessárias**

### **No Meu Computador**

| Ferramenta | Para quê |
| --- | --- |
| Python 3.10+ | Rodar backend |
| Node.js (opcional) | Se migrar frontend |
| Git | Versionamento |
| VS Code ou similar | Editor |
| Postman ou Insomnia | Testar APIs |

### **No Raspberry Pi (já tem)**

| Ferramenta | Status |
| --- | --- |
| Python 3.10+ | ✅ Instalado |
| Flask | ✅ Instalado |
| ffmpeg | ✅ Instalado (time-lapse) |
| Git | ✅ Instalado (auto-update) |

---

## **📚 Referências Úteis**

### **Para Consultar Como Fazer**

| Assunto | Onde Olhar |
| --- | --- |
| Comandos G-code | [RepRap Wiki](https://reprap.org/wiki/G-code) |
| Como OctoPrint faz pause | [OctoPrint GitHub](https://github.com/OctoPrint/OctoPrint) - buscar por "pause" |
| Fatiadores CLI | Documentação do OrcaSlicer/PrusaSlicer |
| WebSocket Python | Documentação FastAPI WebSocket |
| Visão computacional | OpenCV Python docs |

### **Documentação do Chromasistem**

O README e os arquivos em `docs/` explicam:

- Como rodar localmente
- Como fazer deploy no Pi (ex.: croma.service)
- Funcionalidades atuais (dashboard, arquivos, colorir, terminal, Wi‑Fi)
- Variáveis de ambiente disponíveis

---

## **✅ Checklist Antes de Começar**

- [ ]  Clonar repositório Chromasistem
- [ ]  Rodar localmente com sucesso
- [ ]  Ter acesso SSH ao Pi em Manaus
- [ ]  Definir contato técnico em Manaus
- [ ]  Ter canal de comunicação (WhatsApp/Slack)
- [ ]  Contrato assinado
- [ ]  Entrada de 20% recebida

---

## **📅 Ordem Sugerida de Desenvolvimento**

1. **Primeiro:** Sistema de Cores (100% local, entrega rápida)
2. **Segundo:** Pause/Resume (usa estrutura existente)
3. **Terceiro:** Detecção de Falhas (mais complexo)
4. **Quarto:** Interface/UX (pode fazer em paralelo)
5. **Quinto:** Fatiador Integrado
6. **Sexto:** Controle Remoto

---

**Este documento é seu guia de execução.**

**O documento de proposta é para apresentar ao cliente/chefe.**