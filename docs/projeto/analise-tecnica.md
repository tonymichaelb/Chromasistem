> Documento de Escopo Técnico
> 
> 
> **Data:** 16 de Janeiro de 2026
> 

---

## **📌 Contexto do Projeto**

O **ChromaColors** é um sistema de variação de cores para impressoras 3D, projeto atual: **Chromasistem** (este repositório) – interface melhor e em uso; evolução de base estilo OctoPrint com código próprio. O projeto já está em uso em **2 empresas** e possui pontos críticos pendentes de desenvolvimento para entrega.

**Código Base:**

- **Chromasistem** (este repositório) - Projeto atual em uso (Python Flask + HTML/CSS/JS)

**Tecnologias de Referência:**

- [OctoPrint](https://github.com/OctoPrint/OctoPrint) - Interface de controle de impressoras 3D
- [3D Slicer](https://github.com/Slicer/Slicer) - Software de fatiamento e visualização
- OrcaSlicer - Fatiador atualmente em uso

---

## **🔍 Análise do Código Base (Chromasistem)**

### **Stack Tecnológica Atual**

| Camada | Tecnologia | % do Código |
| --- | --- | --- |
| Backend | Python (Flask) | ~45% |
| Frontend | JavaScript Vanilla | 30.1% |
| Markup | HTML | 14.0% |
| Deploy | Shell Scripts | 6.3% |
| Estilos | CSS | 4.1% |

### **Funcionalidades JÁ Implementadas ✅**

| Feature | Status | Observação |
| --- | --- | --- |
| Conexão Serial | ✅ Funcional | Comunicação USB com impressora |
| Upload G-code | ✅ Funcional | Upload e execução de arquivos |
| Status Real-time | ✅ Funcional | WebSocket implementado |
| Time-lapse | ✅ Funcional | Captura frames + gera MP4 |
| Deploy Raspberry Pi | ✅ Funcional | Pi Zero 2 W com systemd |
| Auto-connect | ✅ Funcional | Reconecta automaticamente |
| Wi-Fi Hotspot | ✅ Funcional | Fallback para configuração |
| Auto-update | ✅ Funcional | Git pull via timer |

### **Funcionalidades PENDENTES ❌**

| Feature | Status | Citado no README |
| --- | --- | --- |
| Chroma/Palette (Cores) | ❌ Não implementado | "ponto de extensão" |
| Detecção de Falhas | ❌ Não implementado | - |
| Pause/Resume | ❌ Não implementado | - |
| Controle Remoto (Internet) | ❌ Não implementado | Apenas rede local |

### **Estrutura do Projeto**

```
Chromasistem/
├── app.py             # Entry point (importa core/ e routes/)
├── core/              # Lógica de negócio: config, state, DB, serial, filamento, G-code, thread
├── routes/            # Rotas Flask (Blueprints): auth, pages, printer, files, wifi
├── front-react/       # Frontend React (src/ dev, dist/ produção)
├── templates/         # Templates Jinja2 (fallback sem React)
├── static/            # CSS, JS, imagens
├── scripts/           # Scripts .sh (run, install, etc.)
├── gcode_files/       # Arquivos G-code enviados
├── docs/              # Documentação
├── requirements.txt
├── croma.service      # Unit systemd para Pi
└── README.md
```

### **Pontos Positivos do Código Existente**

1. **Arquitetura simples** - Fácil de entender e estender
2. **WebSocket pronto** - Base para features real-time
3. **Deploy automatizado** - CI/CD básico funcional
4. **Documentação razoável** - README com instruções claras

### **Pontos de Atenção**

1. **Frontend vanilla JS** - Pode dificultar features complexas de UI
2. **Sem testes automatizados** - Risco em refatorações
3. **Chroma/Palette não iniciado** - Feature crítica do zero

---

## **🚨 Pontos Críticos Identificados**

| # | Problema | Impacto | Prioridade |
| --- | --- | --- | --- |
| 1 | Sistema não ignora itens com defeito | Desperdício de material e tempo | 🔴 Crítico |
| 2 | Limite de 19 cores com 3 filamentos | Limitação comercial do produto | 🔴 Crítico |
| 3 | Impossível pausar/retomar impressão | Operação inflexível | 🟠 Alto |
| 4 | UX do site deficiente | Experiência ruim do cliente final | 🟠 Alto |
| 5 | Ausência de fatiador próprio | Dependência de software terceiro | 🟡 Médio |
| 6 | Sem controle remoto | Limitação operacional | 🟡 Médio |

---

## **📋 Análise Detalhada por Módulo**

### **1. 🛑 Sistema de Detecção e Skip de Falhas**

**Situação Atual:**

Se 10 itens estão sendo impressos e 2 apresentam defeito, a impressora continua a impressão defeituosa sem ignorar.

**Solução Proposta:**

- Implementar sistema de monitoramento via câmera/sensores
- Criar lógica de detecção de anomalias (visão computacional ou threshold de sensores)
- Desenvolver comando de "skip" para pular item defeituoso e continuar no próximo
- Interface de confirmação manual opcional

**Referência:** Bambu Lab já possui essa funcionalidade nativa.

| Métrica | Valor |
| --- | --- |
| **Complexidade** | 🔴 Alta |
| **Horas Estimadas** | 40-60h |
| **Dependências** | Acesso ao firmware/API da impressora, possível hardware adicional |
| **Escalável** | ✅ Sim - Padrão Strategy para diferentes métodos de detecção |

---

### **2. 🎨 Expansão do Sistema de Cores (3 Filamentos → +19 Cores)**

**Situação Atual:**

Com 3 filamentos, o sistema gera apenas 19 cores.

**Solução Proposta:**

- Desenvolver algoritmo de **color mixing** com gradientes e proporções
- Criar interface visual mostrando **% de cada cor** para resultado final
- Implementar **color picker** com preview da cor resultante
- Expandir para sistema de **interpolação de cores** (degradê)

**Cálculo Teórico:**

- Com proporções de 10% em 10%: cada filamento pode ter 11 valores (0%, 10%, ..., 100%)
- Combinações possíveis: `11³ = 1.331 cores` (teórico)
- Na prática, considerando limitações físicas: **100-200 cores distintas** é alcançável

| Métrica | Valor |
| --- | --- |
| **Complexidade** | 🟠 Média-Alta |
| **Horas Estimadas** | 30-45h |
| **Dependências** | Entender limitação atual (firmware ou software?) |
| **Escalável** | ✅ Sim - Pode expandir para N filamentos |

---

### **3. ⏸️ Sistema de Pause/Resume**

**Situação Atual:**

Não é possível pausar a impressão para reconfigurar e retomar.

**Solução Proposta:**

- ✅ Serial/API do Chromasistem já envia comandos G-code
- Implementar comandos de pause (M0/M1 ou M600)
- Salvar estado da impressão (posição XYZ, temperatura, layer atual)
- Interface de pause com opções:
    - Pause simples (manter temperatura)
    - Pause frio (desligar aquecimento)
    - Pause para troca de filamento
- Sistema de resume com verificação de estado

**Referência:** OctoPrint já possui isso via plugin ou nativo.

| Métrica | Valor |
| --- | --- |
| **Complexidade** | 🟡 Média |
| **Horas Estimadas** | 15-25h |
| **Dependências** | Compatibilidade com firmware da impressora |
| **Escalável** | ✅ Sim |
| **Aproveita Chromasistem** | ✅ Serial + WebSocket/API |

---

### **4. 🖥️ Redesign da Interface/UX**

**Situação Atual:**

Interface atual em JavaScript vanilla + HTML/CSS (4.1% do código).

**Solução Proposta:**

**Opção A - Melhorar Vanilla JS (Conservadora):**

- Auditoria de UX (identificar pain points)
- Redesign CSS com design system moderno
- Componentização manual em JS
- Responsividade mobile

**Opção B - Migrar para Framework (Moderna):**

- Migrar para React/Vue/Svelte
- Maior esforço inicial, melhor manutenção futura
- Componentes reutilizáveis nativos

**Foco do Redesign:**

- Dashboard intuitivo de status da impressão
- Visualização clara das cores/filamentos (color picker)
- Fluxo simplificado de configuração
- Mobile-friendly para monitoramento remoto

| Métrica | Opção A | Opção B |
| --- | --- | --- |
| **Complexidade** | 🟡 Média | 🟠 Média-Alta |
| **Horas Estimadas** | 30-45h | 50-70h |
| **Manutenibilidade** | Regular | Alta |
| **Recomendação** | ✅ MVP | Para v2.0 |

---

### **5. 🔪 Fatiador Integrado**

**Situação Atual:**

Dependência do OrcaSlicer (software externo).

**Solução Proposta:**

**Opção A - Integração via CLI (Recomendado):**

- Integrar OrcaSlicer/PrusaSlicer via linha de comando
- ✅ Backend Python do Chromasistem facilita subprocess
- Criar interface web que chama o slicer em background
- Usuário faz tudo sem sair do sistema
- G-code gerado vai direto pro Print Manager existente

**Opção B - Desenvolvimento Próprio:**

- ⚠️ **NÃO RECOMENDADO** - Fatiadores são projetos de anos
- Complexidade absurda para pouco ganho

| Métrica | Opção A | Opção B |
| --- | --- | --- |
| **Complexidade** | 🟡 Média | 🔴 Extrema |
| **Horas Estimadas** | 20-30h | 500h+ |
| **Viabilidade** | ✅ Alta | ❌ Baixa |
| **Aproveita Chromasistem** | ✅ Backend + Upload |  |

---

### **6. 🌐 Controle Remoto**

**Situação Atual:**

Chromasistem funciona apenas em rede local (http://...:80).

**Solução Proposta:**

- ✅ WebSocket já implementado - reaproveitar
- Adicionar autenticação (JWT ou similar)
- Opções de acesso externo:
    - **Opção A:** Túnel reverso (ngrok, Cloudflare Tunnel) - Mais simples
    - **Opção B:** VPN + acesso direto - Mais seguro
    - **Opção C:** Servidor relay na cloud - Mais robusto
- Streaming de câmera (já tem base no time-lapse)

**Referência:** OctoPrint Anywhere, Obico

| Métrica | Valor |
| --- | --- |
| **Complexidade** | 🟠 Média-Alta |
| **Horas Estimadas** | 25-35h |
| **Dependências** | Infraestrutura de rede, segurança |
| **Escalável** | ✅ Sim |
| **Aproveita Chromasistem** | ✅ WebSocket + base de câmera |

---

## **⏱️ Resumo de Estimativas**

| Módulo | Horas (Min) | Horas (Max) | Prioridade | Aproveita Código |
| --- | --- | --- | --- | --- |
| Detecção/Skip de Falhas | 40h | 60h | 🔴 P1 | Parcial (WebSocket) |
| Expansão de Cores | 30h | 45h | 🔴 P1 | Não (do zero) |
| Pause/Resume | 15h | 25h | 🟠 P2 | Sim (Serial Manager) |
| Redesign UX | 30h | 45h | 🟠 P2 | Parcial (estrutura) |
| Fatiador Integrado | 20h | 30h | 🟡 P3 | Sim (backend pronto) |
| Controle Remoto | 25h | 35h | 🟡 P3 | Sim (WebSocket) |
| **TOTAL** | **160h** | **240h** |  |  |

**Buffer de Segurança (20%):** +32h a +48h

**Total com Buffer:** **192h - 288h**

> 💡 Nota: Estimativas ajustadas considerando código base do Chromasistem já funcional. O WebSocket, Serial Manager e deploy no Pi já estão prontos, reduzindo esforço de infraestrutura.
> 

---

## **🏗️ Arquitetura do Chromasistem (Atual + Extensões)**

```
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (JavaScript Vanilla + HTML/CSS)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Dashboard│ │  Color   │ │ Slicer   │ │   Remote     │   │
│  │  Status  │ │  Picker  │ │   UI     │ │   Control    │   │
│  │    ✅    │ │    🆕    │ │    🆕    │ │     🆕       │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
└───────┼────────────┼────────────┼──────────────┼────────────┘
        │            │            │              │
        └────────────┴────────────┴──────────────┘
                         │
              [WebSocket ✅ + REST API ✅]
                         │
┌────────────────────────┼────────────────────────────────────┐
│              BACKEND (Python Flask)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐      │
│  │  Print   │ │  Color   │ │  Slicer  │ │  Defect   │      │
│  │  Manager │ │  Engine  │ │  Bridge  │ │  Detector │      │
│  │    ✅    │ │    🆕    │ │    🆕    │ │    🆕     │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘      │
│       │            │            │             │             │
│  ┌────┴────────────┴────────────┴─────────────┴────┐       │
│  │              Serial Manager ✅                   │       │
│  └──────────────────────┬──────────────────────────┘       │
└─────────────────────────┼───────────────────────────────────┘
                          │
               [Serial/USB Connection ✅]
                          │
┌─────────────────────────┼───────────────────────────────────┐
│          RASPBERRY PI ZERO 2 W (Deploy ✅)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ systemd  │ │ Time-    │ │ Wi-Fi    │ │  Auto    │       │
│  │ Service  │ │  lapse   │ │ Hotspot  │ │  Update  │       │
│  │    ✅    │ │    ✅    │ │    ✅    │ │    ✅    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                          │
               [USB Connection]
                          │
┌─────────────────────────┼───────────────────────────────────┐
│               IMPRESSORA 3D + HARDWARE                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Firmware │ │  Câmera  │ │ Sensores │                    │
│  │  G-code  │ │ (opt) 🆕 │ │ (opt) 🆕 │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘

Legenda: ✅ = Já implementado | 🆕 = A desenvolver

```

---

## **✅ Critérios de Qualidade**

| Aspecto | Compromisso |
| --- | --- |
| **Clean Code** | SOLID, DRY, KISS - Mantendo padrão do Chromasistem |
| **Documentação** | Expandir README + docstrings Python |
| **Testes** | pytest para lógica crítica (cores, detecção) |
| **Versionamento** | Git flow com commits semânticos |
| **Escalabilidade** | Modular, preparado para N impressoras |
| **Manutenibilidade** | Código legível + comentários em PT-BR/EN |
| **Compatibilidade** | Manter funcionamento no Raspberry Pi Zero 2 W |

---

## **⚠️ Riscos e Dependências**

| Risco | Probabilidade | Mitigação |
| --- | --- | --- |
| Firmware da impressora fechado | 🟡 Média | Verificar comandos G-code compatíveis |
| Hardware p/ detecção de falhas | 🟠 Alta | Definir se usa câmera ou sensores |
| Frontend vanilla JS limitado | 🟡 Média | Avaliar migração parcial p/ framework |
| Recursos limitados do Pi Zero 2 W | 🟡 Média | Testes de performance constantes |
| Escopo creep | 🔴 Alta | Contrato fechado por módulo |
| Dev anterior pode voltar | 🟢 Baixa | Documentar tudo para handoff |

### **Dependências Técnicas**

| Dependência | Tipo | Criticidade |
| --- | --- | --- |
| Python 3.10+ | Runtime | 🔴 Crítica |
| Flask | Framework | 🔴 Crítica |
| ffmpeg | Software | 🟡 Média (time-lapse) |
| rpicam-still ou fswebcam | Software | 🟠 Alta (detecção) |
| Conexão USB com impressora | Hardware | 🔴 Crítica |
| Raspberry Pi Zero 2 W | Hardware | 🔴 Crítica |

---

## **📅 Sugestão de Faseamento**

### **Fase 1 - Críticos (MVP)**

**Duração:** 4-6 semanas

- ✅ Detecção e Skip de Falhas
- ✅ Expansão do Sistema de Cores

### **Fase 2 - Operacional**

**Duração:** 3-4 semanas

- ✅ Pause/Resume
- ✅ Redesign UX

### **Fase 3 - Nice-to-Have**

**Duração:** 3-4 semanas

- ✅ Fatiador Integrado
- ✅ Controle Remoto

---

## **🔄 Metodologia de Desenvolvimento Remoto**

> ⚠️ Contexto: A impressora 3D está com a equipe terceira em Manaus, enquanto o desenvolvimento será feito remotamente.
> 

### **Desafio Principal**

Desenvolver e testar software para hardware que não está fisicamente disponível.

### **Estratégia de Desenvolvimento**

### **1. Ambiente de Desenvolvimento Local**

```
┌─────────────────────────────────────────────────────────┐
│                    MEU AMBIENTE (Remoto)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Backend    │  │   Frontend   │  │   Mock/Sim   │  │
│  │ Chromasistem │  │ Chromasistem │  │  Impressora  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                │                  │          │
│         └────────────────┴──────────────────┘          │
│                          │                              │
│              [Testes Unitários + Simulação]             │
└─────────────────────────────────────────────────────────┘
                           │
                    [Git Push + Deploy]
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              AMBIENTE MANAUS (Equipe Terceira)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Raspberry   │──│  Impressora  │──│   Câmera/    │  │
│  │     Pi       │  │      3D      │  │   Sensores   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                          │                              │
│              [Teste Real + Validação + Vídeo]           │
└─────────────────────────────────────────────────────────┘

```

### **2. Fases do Ciclo de Desenvolvimento**

| Fase | Responsável | Local | Entregável |
| --- | --- | --- | --- |
| **1. Desenvolvimento** | Eu | Remoto | Código no GitHub |
| **2. Testes Unitários** | Eu | Remoto | Testes passando |
| **3. Simulação** | Eu | Remoto | Mock funcionando |
| **4. Deploy** | Automático | Git → Pi | Código no Pi |
| **5. Teste Real** | Equipe Manaus | Manaus | Vídeo/Evidência |
| **6. Validação** | Cliente | - | Aceite formal |

### **3. Ferramentas de Simulação**

Para desenvolver SEM a impressora física:

| Módulo | Como Simular |
| --- | --- |
| **Sistema de Cores** | 100% simulável - Lógica pura + UI |
| **Pause/Resume** | Mock de comandos G-code |
| **Fatiador** | CLI do OrcaSlicer roda em qualquer máquina |
| **Detecção de Falhas** | Imagens/vídeos de teste + algoritmo |
| **Controle Remoto** | Simulação WebSocket local |
| **UI/UX** | 100% simulável |

> 💡 Nota: Aproximadamente 70-80% do desenvolvimento pode ser feito e validado sem a impressora física.
> 

### **4. Processo de Validação com Equipe Manaus**

```
[Eu desenvolvo] → [Push no Git] → [Auto-deploy no Pi] → [Equipe testa] → [Feedback/Vídeo]
      │                                                        │
      └──────────── Ciclo de 24-48h por iteração ──────────────┘

```

**Requisitos para a Equipe de Manaus:**

- [ ]  Acesso SSH ao Raspberry Pi (para debug remoto)
- [ ]  Pessoa disponível para testes manuais (1-2h por semana)
- [ ]  Envio de vídeos/fotos dos testes reais
- [ ]  Feedback documentado (funciona/não funciona/bug)

### **Critérios de Aceite por Módulo**

| Módulo | Critério de "Pronto" | Evidência Necessária |
| --- | --- | --- |
| **Cores** | UI mostra preview correto + impressão com cor esperada | Screenshot + Foto da peça |
| **Detecção** | Sistema detecta falha simulada e pula item | Vídeo da impressão |
| **Pause** | Pausa, mantém estado, retoma corretamente | Vídeo da operação |
| **UX** | Interface aprovada pelo cliente | Screenshot + OK formal |
| **Fatiador** | Gera G-code correto e envia para impressão | Log + Impressão OK |
| **Remoto** | Acesso externo funcionando com autenticação | Demo ao vivo |

---

### **Proteções para o Desenvolvedor**

1. **Definição Clara de "Pronto"**
    - Documentado no contrato
    - Evidência por vídeo/foto quando necessário
2. **Limite de Revisões**
    - Até 2 rodadas de ajustes por módulo incluídas
    - Ajustes extras definidos em conjunto
3. **Prazo de Validação**
    - Cliente tem **5 dias úteis** para validar cada entrega
    - Sem resposta = aceite automático

### **Proteções para o Cliente**

1. **Código no Repositório Deles**
    - Transparência total do progresso
    - Não depende de mim para acessar
2. **Documentação**
    - README atualizado
    - Comentários no código
3. **Handoff**
    - 1 reunião de passagem de conhecimento por fase
    - Outro dev consegue continuar se necessário

---

## **📋 Checklist Pré-Contrato**

Antes de começar, garantir:

- [ ]  Acesso ao repositório Chromasistem (push)
- [ ]  Acesso SSH ao Raspberry Pi em Manaus
- [ ]  Contato direto com pessoa técnica em Manaus
- [ ]  Contrato assinado com milestones
- [ ]  Entrada de 20% recebida
- [ ]  Canal de comunicação definido (Slack/WhatsApp/Discord)
- [ ]  Prazo de resposta acordado (máx 48h)

---

## **📚 Referências**

- **Código Base:** Chromasistem (este repositório)
- **Referência OctoPrint:** [OctoPrint - GitHub](https://github.com/OctoPrint/OctoPrint)
- **Referência 3D Slicer:** [Slicer - GitHub](https://github.com/Slicer/Slicer)
- **Fatiador Atual:** OrcaSlicer

---