# Tarefas para Entrega — Chromasistem

Documento com **cada tarefa** que precisamos entregar, explicada de forma direta. Ordem de execução é a mesma da entrega: fazer na sequência abaixo.

---

## Visão geral

| # | Tarefa | O que entrega |
|:-:|---|---|
| 1 | Controle remoto | Acesso ao sistema de fora da rede local (túnel/nuvem) |
| 2 | Sistema de cores | Mais cores (100+) e pré-visualização da mistura |
| 3 | Pause / Resume | Pausar e retomar impressão com estado salvo |
| 4 | Detecção e skip de falhas | Receber erro da impressora, pular peça, resolver/retomar/cancelar |
| 5 | Fatiador integrado | Enviar .stl do front → backend chama Orca → G-code na fila |
| 6 | Redesign UX | Interface mais clara e responsiva |
| 7 | Pontos de monitoramento | Exibir mensagens da impressora (lista definida pelo chefe) |

---

## 1. Controle remoto

**Objetivo:** O usuário acessar e controlar o Chromasistem de **fora da rede local** (ex.: de casa ou outro escritório), com segurança.

**O que fazer:**

- Garantir que o **login** (usuário/senha) seja usado também no acesso externo.
- Implementar **acesso externo**: preferência do cliente é **túnel** (ex.: Cloudflare Tunnel ou similar); alternativa é evoluir para solução em **nuvem** (ver documento `controle-remoto-nuvem.md`).
- Usar **HTTPS** no acesso externo.
- Ter **rate limiting** e **logs de acesso** para segurança.
- Se houver câmera, oferecer **streaming ao vivo** (reaproveitar o que já existe de time-lapse).

**Entrega:** Conseguir acessar o sistema de outro lugar (fora da rede do cliente), fazer login e usar as funções principais. Demo ao vivo vale como validação.

---

## 2. Sistema de cores (Colorir / Mistura)

**Objetivo:** Sair de ~19 cores e chegar a **100+ cores** com **pré-visualização** da mistura no front.

**O que fazer:**

- **Backend:** algoritmo de mistura (porcentagem por filamento) e geração dos comandos G-code corretos. Não existe documentação oficial porcentagem → G-code; usar classificações já feitas e testes para expandir.
- **Frontend:** permitir ajustar **porcentagem de cada filamento** e mostrar **pré-visualização** da cor (simulação por camada). Cliente aceita que a cor real possa variar em relação ao preview (filamento, qualidade etc.).
- Color picker visual, preview da cor, % por filamento e, se possível, salvar combinações favoritas.

**Entrega:** Interface com preview da cor e impressão com a cor esperada (evidência: screenshot + foto da peça).

---

## 3. Pause / Resume

**Objetivo:** Pausar a impressão no meio, manter estado (posição, temperatura, linha do G-code) e **retomar** de onde parou.

**O que fazer:**

- **Backend:** comando de pausa (G-code M0/M1 ou M600), **salvar estado** (posição X/Y/Z, temperatura, linha atual) e comando de retomada que usa esse estado.
- **Frontend:** botão Pause e Resume no dashboard; mostrar estado (pausado/rodando). Opções ao pausar: manter temperatura, pause frio, troca de filamento.
- Cuidados: manter temperatura do bico ao pausar (evitar entupir), retrair filamento quando fizer sentido, voltar à posição exata ao resumir.

**Entrega:** Vídeo mostrando pausa no meio da impressão e retomada correta.

---

## 4. Detecção e skip de falhas

**Objetivo:** Quando der erro na impressão, o **sistema receber** esse erro, o usuário poder **pular a peça com defeito** ou **resolver → marcar resolvido → retomar** (ou cancelar). Ver qual peça pular com base numa **visualização da mesa**.

**O que fazer:**

- **Backend:**  
  - Implementar a **comunicação** para receber o erro da impressora (hoje o erro **não entra no código**; cliente vai enviar exemplo de payload).  
  - OctoPrint no Raspberry pode ser o canal que já fala com a impressora; integrar com o Python.  
  - Endpoint/lógica para “pular item atual”, “resolver problema”, “problema resolvido”, “retomar”, “cancelar”.  
  - Salvar **log** de itens pulados e ações.  
  - Catálogo de erros: não existe; cliente envia os que “geralmente acontecem”.

- **Frontend:**  
  - Botão **“Pular item com defeito”** e opções: **Resolver problema**, **Problema resolvido**, **Retomar**, **Cancelar**.  
  - **Visualização da mesa** (simulação das peças na impressora) para o usuário **escolher qual peça pular** quando houver várias.  
  - Indicador de itens pulados e histórico de falhas.  
  - Pesquisa de como fazer a **prévia da mesa no frontend** (cliente reforçou essa necessidade).

- Observação: Bambu A1/A1 mini não pulam; FlashForge AD5X já pula (cliente envia evidência em foto).

**Entrega:** Fluxo em que o erro chega ao sistema, o usuário escolhe pular/resolver/retomar/cancelar e, quando for pular, consegue ver a mesa e escolher a peça. Evidência em vídeo.

---

## 5. Fatiador integrado

**Objetivo:** Do **front**, o usuário envia um arquivo **.stl** (ou .obj); o **backend** chama o Orca (ou outro fatiador), gera o G-code e coloca na **fila de impressão**. Sem embedar o Orca no front — front só manda comando; Python fala com o fatiador.

**O que fazer:**

- **Backend:**  
  - Endpoint que recebe arquivo 3D (.stl, .obj).  
  - Chamar o fatiador (Orca/PrusaSlicer) via **linha de comando** (subprocess).  
  - Orca hoje roda na **máquina local** do cliente; se no futuro rodar em servidor/nuvem, o cliente aceita.  
  - Devolver o G-code gerado e **enviar para a fila** que já existe no Chromasistem.

- **Frontend:**  
  - Tela de **upload** de arquivo 3D.  
  - Opções básicas de fatiamento (qualidade, preenchimento etc.).  
  - Botão para enviar o G-code gerado direto para impressão.

**Entrega:** Upload de .stl → G-code gerado → impressão concluída pelo sistema (log + evidência de impressão OK).

---

## 6. Redesign UX (web e app)

**Objetivo:** Interface mais **clara**, **moderna** e **responsiva** (incluindo uso em celular para monitoramento).

**O que fazer:**

- Mapear telas atuais e pontos de confusão; definir fluxos principais.
- Layout mais limpo, hierarquia visual melhor, feedback claro (loading, sucesso, erro).
- Dashboard intuitivo, visualização clara de cores/filamentos, fluxo de configuração simples.
- Refatorar CSS e melhorar responsividade (mobile-friendly). Manter stack atual (Vanilla JS) a menos que se combine migração com o chefe.

**Entrega:** Interface aprovada pelo cliente (screenshot + OK formal).

---

## 7. Pontos de monitoramento da impressora

**Objetivo:** Mostrar no sistema as **mensagens/eventos** que a impressora envia (lista a ser definida pelo chefe).

**O que fazer:**

- Receber do chefe a **lista de mensagens/pontos** que a impressora deve enviar.
- **Backend:** receber e expor essas mensagens (API e/ou WebSocket).
- **Frontend:** exibir onde fizer sentido (dashboard, alertas, histórico).

**Entrega:** Lista implementada e visível no front conforme combinado.

---

## Ordem de execução (resumo)

1. **Controle remoto** — permite validar acesso externo/nuvem desde o início.  
2. **Sistema de cores** — entrega visível e boa parte testável local.  
3. **Pause / Resume** — base operacional para impressão.  
4. **Detecção e skip** — usa fluxo de impressão e comunicação com impressora.  
5. **Fatiador integrado** — fluxo completo: .stl → G-code → fila.  
6. **Redesign UX** — unifica a experiência de todas as telas.  
7. **Pontos de monitoramento** — assim que a lista do chefe estiver definida.

---

## Referências rápidas

- **Escopo e estimativas:** `analise-tecnica.md`, `doc-tecnico.md`
- **Definições do cliente:** `definicoes-cliente.md`
- **Backlog detalhado e checklist:** `alinhamento-tarefas.md`
- **Controle remoto e nuvem:** `controle-remoto-nuvem.md`

---

*Documento de tarefas para entrega do freelance Chromasistem. Atualizar conforme novos combinados.*
