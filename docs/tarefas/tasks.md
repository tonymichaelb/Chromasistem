# Tarefas para Entrega — Chromasistem

Documento único com **cada tarefa** a entregar, ordem de execução, critérios de aceite e referências. Consolida o que antes estava em `tarefas-para-entrega.md` e `alinhamento-tarefas.md`.

---

## Visão geral

| # | Tarefa | O que entrega |
|:-:|---|---|
| 1 | Controle remoto | Acesso ao sistema de fora da rede local (túnel/nuvem) |
| 2 | Sistema de cores | Mais cores (100+) e pré-visualização da mistura — **Implementado** ✅ |
| 3 | Pause / Resume | Pausar e retomar impressão com estado salvo — **Implementado** ✅ |
| 4 | Detecção e skip de falhas | Receber erro da impressora, pular peça, resolver/retomar/cancelar — **Implementado** ✅ |
| 5 | Fatiador integrado | Enviar .stl do front → backend chama Orca → G-code na fila |
| 6 | Redesign UX | Interface mais clara e responsiva |
| 7 | Pontos de monitoramento | Exibir mensagens da impressora (lista definida pelo chefe) |

---

## Ordem de execução (e por quê)

| Passo | Tarefa | Motivo |
|:-:|---|---|
| 1 | Controle remoto | Validar acesso externo/nuvem desde o início; HTTPS, streaming câmera |
| 2 | Sistema de cores | Entrega visível e testável local — **Implementado** ✅ |
| 3 | Pause / Resume | Base operacional; usa Serial Manager já existente (ref. OctoPrint) — **Implementado** ✅ |
| 4 | Detecção e skip | Depende do fluxo de impressão; botão manual primeiro — **Implementado** ✅ |
| 5 | Fatiador integrado | Fluxo completo: .stl → Orca CLI → G-code na fila |
| 6 | Redesign UX | Unifica experiência de todas as telas; responsivo/PWA |
| 7 | Pontos de monitoramento | Quando a lista de mensagens da impressora estiver definida |

---

## 1. Controle remoto

**Objetivo:** O usuário acessar e controlar o Chromasistem de **fora da rede local** (ex.: de casa ou outro escritório), com segurança.

**O que fazer:**

- Garantir que o **login** (usuário/senha) seja usado também no acesso externo.
- Implementar **acesso externo**: preferência por **túnel** (ex.: Cloudflare Tunnel ou similar); alternativa é evoluir para solução em **nuvem** (ver documento [controle-remoto-nuvem.md](../infra-instalacao/controle-remoto-nuvem.md)).
- Usar **HTTPS** no acesso externo.
- Ter **rate limiting** e **logs de acesso** para segurança.
- Se houver câmera, oferecer **streaming ao vivo** (reaproveitar o que já existe de time-lapse).

**Entrega:** Acessar o sistema de outro lugar (fora da rede local), fazer login e usar as funções principais. Demo ao vivo vale como validação.

---

## 2. Sistema de cores (Colorir / Mistura) — ✅ Implementado (pronto para teste)

**Objetivo:** Sair de ~19 cores e chegar a **100+ cores** com **pré-visualização** da mistura no front.

**O que foi entregue:**

- **Frontend:** Color picker em destaque na tela Colorir (“Cor personalizada — qualquer cor (100+)”) e na tela Mistura (“Sugerir mistura a partir de uma cor”). O usuário escolhe qualquer cor; o sistema calcula as porcentagens Ciano/Magenta/Amarelo (A, B, C) e mostra a prévia. Tons claros vs escuros geram porcentagens diferentes (luminosidade incorporada).
- **Algoritmos (frontend):** RGB → HSV (luminosidade) e RGB → CMY (proporção dos 3 filamentos), com blend por luminosidade para variar tons. Detalhes em [algoritmos-sistema-cores.md](../sistema-cores/algoritmos-sistema-cores.md).
- **Backend:** Sem alteração; continua recebendo e enviando M182 para a impressora (APIs existentes).
- **Evidência de entrega:** testar na impressora; screenshot da interface + foto da peça com a cor esperada.

**Referência (algoritmos):** [algoritmos-sistema-cores.md](../sistema-cores/algoritmos-sistema-cores.md).

---

## 3. Pause / Resume — ✅ Implementado (pronto para teste)

**Objetivo:** Pausar a impressão no meio, manter estado (posição, temperatura, linha do G-code) e **retomar** de onde parou. Essa base é também o que permite o fluxo da tarefa 4 (falhas): “Resolver problema → Problema resolvido → **Retomar**” (ver [definicoes-cliente.md](../projeto/definicoes-cliente.md) §5).

**Contexto (definições do projeto):** A comunicação com a impressora é via **terminal/serial** (Python envia comandos; não é apenas USB genérico). Pause/Resume usa esse mesmo canal (G-code M0/M1 ou M600, etc.).

**O que foi entregue:**

- **Backend:** Ao pausar, a thread salva estado na tabela `print_pause_state`: posição (M114), temperaturas alvo (M105), offset no G-code. Opções: manter temperatura (padrão), pausa fria (M104 S0 / M140 S0), troca de filamento (M600). Ao retomar, se pausa foi fria, reaquecimento (M109/M190). APIs: `POST /api/printer/pause` com body `{ "option": "keep_temp"|"cold"|"filament_change" }`, `POST /api/printer/resume`. Status retorna `state: "paused"` quando pausado.
- **Frontend:** Botões Pausar e Retomar; estado (Imprimindo / Pausado / Ocioso). Modal ao clicar Pausar com as três opções. Botões habilitados conforme estado.
- **Cuidados:** Temperatura mantida por padrão; pausa fria desliga aquecedores; retomada reaquece quando foi fria. Impressão continua do próximo comando no arquivo.

**Entrega:** Vídeo mostrando pausa no meio da impressão e retomada correta.

---

## 4. Detecção e skip de falhas — ✅ Implementado (pronto para teste)

**Objetivo:** Quando der erro na impressão, o **sistema receber** esse erro, o usuário poder **pular a peça com defeito** ou **resolver → marcar resolvido → retomar** (ou cancelar). Ver qual peça pular com base numa **visualização da mesa**.

**O que foi entregue:**

- **Backend:**  
  - Endpoint **`POST /api/printer/failure`** para receber notificação de falha (payload flexível: `code`, `message`, `source`; integração OctoPrint futura).  
  - Endpoints **`POST /api/printer/failure/resolve`**, **`POST /api/printer/failure/resolved`** (resolver problema e retomar).  
  - **`POST /api/printer/skip-object`** (body opcional `object_id`) para pular item; thread avança no G-code até próximo marcador `;object`/`;layer` sem enviar linhas.  
  - **`GET /api/printer/bed-preview`**: retorna dimensões da mesa e lista de objetos (bbox em mm) parseados do G-code (Orca/Prusa com Label Objects).  
  - **`GET /api/printer/failure-history`**: lista de entradas do log (detected, skipped, resolved, cancelled).  
  - Tabela **`print_failure_log`**; status com `state: "failure"`, `failure_detected`, `failure_message`, `skipped_objects_count`.  
  - Cancelar = reutilizar `POST /api/printer/stop` (limpa estado de falha).

- **Frontend (React):**  
  - Card **"Falha detectada"** com mensagem e botões: **Pular item com defeito**, **Resolver problema**, **Problema resolvido — Retomar**, **Cancelar**.  
  - Modal **"Pular item com defeito"** com **visualização 2D da mesa** (SVG, retângulos por objeto); seleção de peça e botão **"Pular este objeto"**; se não houver objetos no G-code, botão **"Pular item atual"**.  
  - Indicador **"Itens pulados nesta impressão: N"** e botões **Histórico** / **Ver histórico de falhas**; modal com lista de entradas do log.

- **Referência:** [deteccao-skip-falhas.md](deteccao-skip-falhas.md) (guia de implementação e o que o cliente deve testar).

- **Observação:** Bambu A1/A1 mini não suportam skip no firmware; FlashForge AD5X já pula. Para visualização da mesa com várias peças, o G-code deve ser fatiado com **Label Objects** ativo (OrcaSlicer/PrusaSlicer).

**Entrega:** Fluxo em que o erro chega ao sistema, o usuário escolhe pular/resolver/retomar/cancelar e, quando for pular, consegue ver a mesa e escolher a peça. Evidência em vídeo (ver cenários em [deteccao-skip-falhas.md](deteccao-skip-falhas.md) §8).


---

## 5. Fatiador integrado

**Objetivo:** Do **front**, o usuário envia um arquivo **.stl** (ou .obj); o **backend** chama o Orca (ou outro fatiador), gera o G-code e coloca na **fila de impressão**. Sem embedar o Orca no front — front só manda comando; Python fala com o fatiador.

**O que fazer:**

- **Backend:**  
  - Endpoint que recebe arquivo 3D (.stl, .obj).  
  - Chamar o fatiador (Orca/PrusaSlicer) via **linha de comando** (subprocess).  
  - Orca hoje roda na **máquina local**; se no futuro rodar em servidor/nuvem, é aceitável.  
  - Devolver o G-code gerado e **enviar para a fila** que já existe no Chromasistem.

- **Frontend:**  
  - Tela de **upload** de arquivo 3D.  
  - Opções básicas de fatiamento (qualidade, preenchimento etc.).  
  - Botão para enviar o G-code gerado direto para impressão.

**Entrega:** Upload de .stl → G-code gerado → impressão concluída pelo sistema (log + evidência de impressão OK).

- **Guia de uso e teste (cliente):** [fatiador-integrado.md](fatiador-integrado.md) — como usar a tela Fatiador, configurar o Orca, testar e registrar a evidência.

---

## 6. Redesign UX (web e app)

**Objetivo:** Interface mais **clara**, **moderna** e **responsiva** (incluindo uso em celular para monitoramento).

**O que fazer:**

- Mapear telas atuais e pontos de confusão; definir fluxos principais.
- Layout mais limpo, hierarquia visual melhor, feedback claro (loading, sucesso, erro).
- Dashboard intuitivo, visualização clara de cores/filamentos, fluxo de configuração simples.
- Refatorar CSS e melhorar responsividade (mobile-friendly). Manter stack atual (Vanilla JS) a menos que se combine migração com o chefe.

**Entrega:** Interface aprovada (screenshot + OK formal).

---

## 7. Pontos de monitoramento da impressora

**Objetivo:** Mostrar no sistema as **mensagens/eventos** que a impressora envia (lista a ser definida pelo chefe).

**O que fazer:**

- Receber do chefe a **lista de mensagens/pontos** que a impressora deve enviar.
- **Backend:** receber e expor essas mensagens (API e/ou WebSocket).
- **Frontend:** exibir onde fizer sentido (dashboard, alertas, histórico).

**Entrega:** Lista implementada e visível no front conforme combinado.

---

## Critérios de aceite por módulo (evidência)

| Módulo | Critério de “pronto” | Evidência |
|--------|----------------------|-----------|
| Cores | Preview correto na UI + impressão com cor esperada | Screenshot + foto da peça |
| Detecção e skip | Sistema recebe erro e pula item; usuário escolhe peça na mesa | Vídeo da impressão |
| Pause / Resume | Pausa mantém estado; retoma corretamente | Vídeo da operação |
| UX | Interface aprovada | Screenshot + OK formal |
| Fatiador | G-code gerado e enviado para impressão | Log + impressão OK |
| Controle remoto | Acesso externo com autenticação | Demo ao vivo |
| Monitoramento | Lista de mensagens definida e exibida no front | Conforme combinado |

---

## Ciclo de desenvolvimento (por feature)

1. Desenvolver no **Chromasistem** (local).
2. Testar com mock/simulação quando não houver impressora.
3. Commit + push no repositório.
4. Deploy no Pi (auto-update via croma.service se configurado).
5. Teste real na impressora.
6. Ajustes até o critério de aceite ser atendido.

**Tempo médio por ciclo:** desenvolvimento 1–3 dias + teste 1–2 dias ≈ 2–5 dias por iteração.

---

## Tarefas transversais (qualidade e ambiente)

- **Código:** Clean Code (SOLID, DRY, KISS); documentação (README + docstrings); testes (pytest para lógica crítica); versionamento (Git, commits semânticos).
- **Escalabilidade:** módulos preparados para N impressoras quando fizer sentido.
- **Compatibilidade:** manter funcionamento no Raspberry Pi Zero 2 W.
- **Ferramentas:** Python 3.10+, Git; no Pi: ffmpeg, fatiador CLI (Orca/PrusaSlicer). Referências: RepRap Wiki (G-code), OctoPrint (pause, skip), OrcaSlicer/PrusaSlicer (CLI).

---

## Referências rápidas

- **Escopo e estimativas:** [analise-tecnica.md](../projeto/analise-tecnica.md), [doc-tecnico.md](../projeto/doc-tecnico.md)
- **Definições do projeto:** [definicoes-cliente.md](../projeto/definicoes-cliente.md)
- **Controle remoto e nuvem:** [controle-remoto-nuvem.md](../infra-instalacao/controle-remoto-nuvem.md)
- **Algoritmos do sistema de cores:** [algoritmos-sistema-cores.md](../sistema-cores/algoritmos-sistema-cores.md)

**Onde desenvolver:** sempre no **Chromasistem** (este repositório). Telas e fluxos de referência: Colorir, Mistura, Arquivos, Dashboard, Terminal, Wi‑Fi.

---

*Documento único de tarefas para entrega — Chromasistem. Atualizar conforme novos combinados.*
