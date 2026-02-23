# **Alinhamento de Tarefas – Chroma (Freelance)**

Documento único para alinhar o **passo a passo** e o **backlog completo** do projeto. Nada fica de fora: tudo que está em `analise-tecnica.md` e `doc-tecnico.md` está refletido aqui.

**Contexto:** Desenvolvimento no **Chromasistem** (este repositório) – projeto atual em uso, com interface melhor e funcionando melhor. Front em **web e app**. Entrega **tudo de uma vez** – sem prioridade para alinhar com o chefe; segue o passo a passo lógico abaixo.

---

## **Passo a passo lógico (ordem de execução)**

Entrega tudo na sequência abaixo. **Iniciar pelo passo 1.**

| Passo | O quê | Por quê | Observações |
| --- | --- | --- | --- |
| 1 | **Controle Remoto** | Acesso externo (túnel/VPN), HTTPS, streaming câmera. | Validar como funcionaria todos sistemas em nuvem, ou se possivel uma alternativa que funcione sem nuvem |
| 2 | **Sistema de Cores** (Colorir/Mistura) | 100% local, referência no Chromasistem, entrega visível rápido. | Referencia: OctoPrint |
| 3 | **Pause/Resume** | Usa Serial Manager já existente; base para operação. | Referencia: OctoPrint |
| 4 | **Detecção e Skip de Falhas** | Depende de fluxo de impressão; botão manual primeiro, automação depois. | Referencia: OctoPrint |
| **5** | **Fatiador Integrado** | Upload .stl → OrcaSlicer CLI → G-code na fila; endpoint + UI. |  |
| 6 | **Redesign UX** (web e app) | Unifica tudo: dashboard, arquivos, terminal, cores, responsivo/PWA. |  |
| **7** | **Pontos de monitoramento** | Quando o chefe passar a lista de msgs da impressora; backend + exibição no front. |  |

**Próxima ação:** iniciar **Passo 1 – Controle Remoto** no Chromasistem (backend + infra); em seguida Passo 2 – Sistema de Cores (backend + front).

---

## **1. Tarefas de hoje (alinhamento e preparação)**

**Status:** Preparação concluída. Passo a passo definido; iniciar desenvolvimento pelo Passo 1 – Controle Remoto, depois Passo 2 – Sistema de Cores.

### **1.1 Documentação e ambiente**

- [x]  [x] **1.1.1** Ler `README.md`, `doc-tecnico.md` e `analise-tecnica.md`.
- [x]  [x] **1.1.2** Chromasistem (projeto atual) rodando em [**http://localhost**](http://localhost/) (porta 80).
- [x]  [x] **1.1.3** Anotações preenchidas abaixo.
- [x]  [x] **1.1.4** Sem prioridade para alinhar com o chefe – entregar tudo na ordem do passo a passo lógico acima.

**Anotações – o que já existe no Chromasistem e será mantido/expandido (com base nos prints):**

- **Dashboard:** Status da impressora (Estado OCIOSO, Conexão DESCONECTADO, Filamento SENSOR DESABILITADO) com badges; botões Conectar/Desconectar. Painel Temperatura (Bico e Mesa: atual + alvo). Progresso (arquivo, %, tempo decorrido/restante). Controles Iniciar / Pausar / Retomar / Parar em grid 2x2. Card “Arquivos G-Code Recentes” com “Ver Todos” e botão “Fazer Upload”. Layout em cards escuros, nav com logo Croma + links + “Bem-vindo, usuário” + Sair.
- **Arquivos:** Título “Gerenciador de Arquivos G-Code” + subtítulo. Área drag-and-drop “Arraste e solte seu arquivo G-Code aqui” + “ou” + “Selecionar Arquivo”. Formatos aceitos: .gcode, .gco, .g (máx. 100MB). Seção “Meus Arquivos G-Code” com busca “Buscar arquivo...” e botão Atualizar. **Integração OrcaSlicer:** passos numerados (Preferences → Network; configurar URL do servidor), URL `http://.../api/files/upload` com botão Copiar – manter/expandir endpoint e doc no Chromasistem.
- **Colorir:** “Sistema de Pincéis e Tintas”. Status “Pincel Selecionado: Pincel N - Sem cor (clique em uma tinta para aplicar)”. Grid de **Pincéis 1 a 19** (limite atual de 19 cores – alvo de expansão no backlog). Grid de **Tintas 1 a 19** (swatches com ícone de edição). Seleção visual (destaque rosa no pincel ativo). Referência direta para a feature “Expansão do Sistema de Cores” no Chromasistem.
- **Terminal:** Dois painéis. **Esquerda – Controle manual:** Distância (0.1 / 1 / 10 / 100 mm), Eixos X/Y (Y+, Y-, X-, X+, Home), Eixo Z (Z+, Z-, Home Z), Extrusora (Extrudar, Retrair, Pre-aquecer), botão “Home All (X, Y, Z)”. **Direita – Terminal G-code:** área de log, input “Digite comando G-code”, Enviar, Limpar; comandos rápidos M105 (Temp), M114 (Pos), M115 (Info), M503 (Config), M119 (Endstops). Outra tela: Controle de Temperatura (Bico/Mesa com input, Definir, Off, presets PLA/ABS/PETG/TPU, Desligar Tudo) + gráfico “Temperatura em tempo real” (Bico/Mesa atual e target). Footer com versão (ex.: 8a5c1f5). Reaproveitar: layout, comandos rápidos, controle de movimento e temperatura no Chromasistem.
- **Wi‑Fi:** (não apareceu nos prints; conferir tela Wi‑Fi no Chromasistem para lista de redes e configuração.)

### **1.2 Alinhamento técnico**

- [x]  [x] **1.2.1** Ordem de execução definida (passo a passo lógico acima) – sem dependência de alinhamento de prioridade.
- [ ]  [ ] **1.2.2** (Opcional) Repositório oficial do Chromasistem (projeto atual) registrado.
- [ ]  [ ] **1.2.3** (Opcional) Se equipe Manaus: canal de comunicação, quem testa, prazo de feedback.

### **1.3 Entregáveis de hoje**

- [x]  [x] **1.3.1** README geral (`README.md`).
- [x]  [x] **1.3.2** Este documento (`TAREFAS-ALINHAMENTO.md`) com backlog completo e passo a passo lógico.
- [ ]  [ ] **1.3.3** (Quando quiser) Enviar ao chefe: README + TAREFAS-ALINHAMENTO.

---

## **2. Backlog completo (todas as tarefas dos docs)**

Todas as tarefas abaixo são feitas **no Chromasistem** (backend e/ou frontend). OctoPrint é referência para funcionalidades.

---

### **Fase 1 – Críticos (MVP) | 4–6 semanas**

### **2.1 Sistema de Detecção e Skip de Falhas**

| Prioridade | Estimativa | Ref. |
| --- | --- | --- |
| P1 | 40–60h | analise-tecnica §1, doc-tecnico Feature 1 |

**Backend:**

- [ ]  Endpoint para receber notificação de falha.
- [ ]  Lógica para pular item atual e ir para o próximo.
- [ ]  Salvar log de itens pulados.
- [ ]  (Opcional) Monitoramento via câmera/sensores.
- [ ]  (Opcional) Lógica de detecção de anomalias (visão computacional ou threshold).
- [ ]  Padrão Strategy para diferentes métodos de detecção (escalável).

**Frontend:**

- [ ]  Botão manual "Pular item com defeito".
- [ ]  Indicador visual de itens pulados.
- [ ]  Histórico de falhas.
- [ ]  Interface de confirmação manual opcional (skip).

**Teste sem impressora:** Mock de "item com defeito" e comandos G-code simulados.

**Validação:** Equipe Manaus grava vídeo com item sendo pulado.

**Critério de aceite:** Sistema detecta falha (simulada ou real) e pula item; evidência em vídeo.

---

### **2.2 Expansão do Sistema de Cores (3 filamentos → 100–200+ cores)**

| Prioridade | Estimativa | Ref. |
| --- | --- | --- |
| P1 | 30–45h | analise-tecnica §2, doc-tecnico Feature 2 |

**Backend:**

- [ ]  Algoritmo de mistura de cores (RGB/HSL).
- [ ]  Cálculo de proporções por filamento (ex.: 30% vermelho, 50% azul, 20% branco).
- [ ]  Geração de comando G-code com proporções corretas.
- [ ]  (Opcional) Interpolação de cores / degradê.

**Frontend:**

- [ ]  Color picker visual (referência: Chromasistem `colorir.html`, `mistura.html`).
- [ ]  Preview da cor resultante.
- [ ]  Exibir % de cada filamento.
- [ ]  Interface para salvar combinações favoritas.
- [ ]  Filtrar para 100–200 cores visualmente distintas na prática.

**Teste:** 100% local (lógica + UI).

**Validação:** Foto da peça impressa vs preview do sistema.

**Critério de aceite:** UI com preview correto; impressão com cor esperada; screenshot + foto da peça.

---

### **Fase 2 – Operacional | 3–4 semanas**

### **2.3 Sistema de Pause/Resume**

| Prioridade | Estimativa | Ref. |
| --- | --- | --- |
| P2 | 15–25h | analise-tecnica §3, doc-tecnico Feature 3 |

**Backend:**

- [ ]  Comando de pause (G-code M0/M1 ou M600).
- [ ]  Salvar estado: posição X/Y/Z, temperatura, linha atual do G-code.
- [ ]  Comando de resume que retoma do ponto salvo.
- [ ]  Verificação de estado ao retomar.

**Frontend:**

- [ ]  Botão Pause/Resume no dashboard.
- [ ]  Mostrar estado (pausado/rodando).
- [ ]  Opções ao pausar: pause simples (manter temp), pause frio, pause para troca de filamento, ajustar temperatura.

**Cuidados:** Manter temperatura do bico ao pausar; retrair filamento antes de pausar; retornar à posição exata ao resumir.

**Teste:** Mock de comandos G-code; estado salvo e restaurado.

**Validação:** Vídeo pausando no meio da impressão e retomando.

**Critério de aceite:** Pausa mantém estado; retoma corretamente; vídeo da operação.

---

### **2.4 Redesign da Interface / UX (web e app)**

| Prioridade | Estimativa | Ref. |
| --- | --- | --- |
| P2 | 30–45h (Opção A Vanilla) / 50–70h (Opção B Framework) | analise-tecnica §4, doc-tecnico Feature 4 |

**Análise:**

- [ ]  Mapear telas atuais e pontos de confusão.
- [ ]  Definir fluxos principais do usuário.

**Design:**

- [ ]  Layout mais limpo e moderno (design system).
- [ ]  Melhor hierarquia visual.
- [ ]  Feedback visual (loading, sucesso, erro).
- [ ]  Dashboard intuitivo de status.
- [ ]  Visualização clara das cores/filamentos (color picker).
- [ ]  Fluxo simplificado de configuração.
- [ ]  Mobile-friendly para monitoramento remoto.

**Implementação (escolher uma):**

- **Opção A – Vanilla JS:** Refatorar CSS, responsividade, componentização manual em JS.
- **Opção B – Framework:** Migrar para React/Vue/Svelte (recomendado para v2.0).

**Teste:** 100% no navegador; vários tamanhos de tela.

**Validação:** Screenshots para aprovação do cliente.

**Critério de aceite:** Interface aprovada pelo cliente; screenshot + OK formal.

---

### **Fase 3 – Nice-to-Have | 3–4 semanas**

### **2.5 Fatiador Integrado**

| Prioridade | Estimativa | Ref. |
| --- | --- | --- |
| P3 | 20–30h | analise-tecnica §5, doc-tecnico Feature 5 |

**Backend:**

- [ ]  OrcaSlicer ou PrusaSlicer no Pi (ou CLI disponível).
- [ ]  Endpoint que recebe arquivo 3D (.stl, .obj).
- [ ]  Chamar fatiador via linha de comando (subprocess).
- [ ]  Retornar G-code gerado (e enviar para fila de impressão existente).

**Frontend:**

- [ ]  Tela de upload de arquivo 3D.
- [ ]  Opções básicas de fatiamento (qualidade, preenchimento).
- [ ]  Preview do resultado (se possível).
- [ ]  Botão para enviar G-code direto para impressão.

**Fluxo:** Upload .stl → fatiar em background → G-code na fila do Print Manager.

**Teste:** Geração de G-code local; arquivo correto.

**Validação:** Imprimir uma peça do início ao fim só pelo sistema; log + impressão OK.

**Critério de aceite:** G-code correto gerado e enviado para impressão; evidência de impressão OK.

---

### **2.6 Controle Remoto**

| Prioridade | Estimativa | Ref. |
| --- | --- | --- |
| P3 | 25–35h | analise-tecnica §6, doc-tecnico Feature 6 |

**Backend/Infra:**

- [ ]  Autenticação: login já existe (JWT); garantir uso em acesso externo.
- [ ]  Escolher e implementar acesso externo: Cloudflare Tunnel (simples) / ngrok / VPN / servidor relay.
- [ ]  HTTPS obrigatório.
- [ ]  Rate limiting e logs de acesso.
- [ ]  Streaming de câmera ao vivo (reaproveitar base do time-lapse).

**Teste:** Auth local; túnel funcionando.

**Validação:** Demo acessando de fora da rede local.

**Critério de aceite:** Acesso externo funcionando com autenticação; demo ao vivo.

---

### **Itens a incluir quando definidos**

### **2.7 Pontos de monitoramento da impressora**

- [ ]  Receber do chefe a lista de mensagens/pontos que a impressora deve enviar.
- [ ]  Backend: receber e expor essas mensagens (API/WebSocket).
- [ ]  Frontend: exibir onde fizer sentido (dashboard, alertas, etc.).

---

### **Tarefas transversais (não esquecer)**

### **2.8 Critérios de qualidade (analise-tecnica)**

- [ ]  Clean Code: SOLID, DRY, KISS; padrão do Chromasistem.
- [ ]  Documentação: README + docstrings Python.
- [ ]  Testes: pytest para lógica crítica (cores, detecção).
- [ ]  Versionamento: Git flow, commits semânticos.
- [ ]  Escalabilidade: módulos preparados para N impressoras.
- [ ]  Manutenibilidade: código legível; comentários PT-BR/EN.
- [ ]  Compatibilidade: manter funcionamento no Raspberry Pi Zero 2 W.

### **2.9 Checklist pré-contrato (analise-tecnica)**

- [ ]  Acesso ao repositório Chromasistem (push).
- [ ]  Acesso SSH ao Raspberry Pi em Manaus.
- [ ]  Contato direto com pessoa técnica em Manaus.
- [ ]  Contrato assinado com milestones.
- [ ]  Entrada de 20% recebida.
- [ ]  Canal de comunicação definido (Slack/WhatsApp/Discord).
- [ ]  Prazo de resposta acordado (máx. 48h).

### **2.10 Requisitos da equipe Manaus (doc-tecnico + analise-tecnica)**

- [ ]  Acesso SSH ao Pi (debug, logs).
- [ ]  Pessoa para testes manuais (1–2h/semana).
- [ ]  Envio de vídeos/fotos dos testes reais.
- [ ]  Feedback documentado (funciona / bug / ajuste) em até 48h.

### **2.11 Ferramentas (doc-tecnico)**

**Local:** Python 3.10+, Git, editor, Postman/Insomnia; Node opcional se migrar frontend.

**Pi (já tem):** Python 3.10+, FastAPI/Uvicorn, ffmpeg, Git (auto-update).

**Referências:** RepRap Wiki (G-code), OctoPrint (pause), OrcaSlicer/PrusaSlicer (CLI), FastAPI WebSocket, OpenCV (visão).

---

## **3. Resumo: passo a passo = ordem de execução (entregar tudo)**

| Passo | Tarefa | Est. (h) |
| --- | --- | --- |
| 1 | **Controle Remoto** | 25–35 |
| 2 | **Sistema de Cores** | 30–45 |
| 3 | **Pause/Resume** | 15–25 |
| 4 | **Detecção e Skip de Falhas** | 40–60 |
| 5 | **Fatiador Integrado** | 20–30 |
| 6 | **Redesign UX** (web e app) | 30–45 |
| 7 | **Pontos de monitoramento** | Quando definidos |

**Total estimado:** 160–240h (+ buffer 20% → 192–288h).

---

## **4. Critérios de aceite por módulo (evidência)**

| Módulo | Critério de “pronto” | Evidência |
| --- | --- | --- |
| Cores | Preview correto na UI + impressão com cor esperada | Screenshot + foto da peça |
| Detecção | Sistema detecta falha e pula item | Vídeo da impressão |
| Pause | Pausa mantém estado; retoma corretamente | Vídeo da operação |
| UX | Interface aprovada pelo cliente | Screenshot + OK formal |
| Fatiador | G-code correto gerado e enviado | Log + impressão OK |
| Remoto | Acesso externo com autenticação | Demo ao vivo |

---

## **5. Ciclo de desenvolvimento (cada feature)**

1. Desenvolver no **Chromasistem** (local).
2. Testar com mock/simulação quando não houver impressora.
3. Commit + push no repositório do Chromasistem.
4. Deploy no Pi (configurar auto-update no Chromasistem se necessário; ver croma.service).
5. Teste real na impressora (equipe Manaus).
6. Feedback → ajustes → feature entregue quando critério de aceite for atendido.

**Tempo médio por ciclo:** desenvolvimento 1–3 dias + teste remoto 1–2 dias ≈ **2–5 dias por iteração**.

---

## **6. Referência rápida**

- **Onde desenvolver:** sempre no **Chromasistem** (este repositório).
- **Chromasistem:** referência de telas e fluxos (Colorir, Mistura, Arquivos, Dashboard, Wi‑Fi); adaptar para FastAPI, não copiar direto.
- **Documentos:** `analise-tecnica.md` (escopo, estimativas, riscos), `doc-tecnico.md` (guia do dev), `README.md` (visão do workspace), este arquivo (backlog e alinhamento).

---

## **7. Checklist “Hoje”**

- [x]  Chromasistem (projeto atual) rodando localmente.
- [x]  Chromasistem explorado como referência e anotações preenchidas.
- [x]  Passo a passo lógico definido (Remoto → Cores → Pause → Detecção → Fatiador → UX → Monitoramento).
- [x]  Próximo passo: **iniciar Passo 1 – Controle Remoto no Chromasistem** (depois Passo 2 – Sistema de Cores).
- [ ]  (Opcional) Enviar README + TAREFAS-ALINHAMENTO ao chefe quando quiser.

---

*Documento de alinhamento – atualizar conforme novos combinados. Nada dos docs analise-tecnica e doc-tecnico foi omitido no backlog.*