# Pause/Resume — melhorias a partir do feedback do cliente

Documento de análise (visão sênior) do que precisa ser alterado após os testes do cliente. **Não é a implementação** — é o plano antes de iniciar.

**Referências:** [pause-resume.md](pause-resume.md), [tasks.md](tasks.md) (seção 3).

---

## 1. Problemas relatados pelo cliente

| # | Problema | Expectativa do cliente |
|---|----------|-------------------------|
| 1 | Ao pausar, o bico fica parado em cima da peça; por estar quente, o material escorre e pinga na peça. | Ao pausar: retrair o bico, recolher (subir Z) e ir para um cantinho (posição de “estacionamento”). Ao retomar: voltar à posição de trabalho e continuar. |
| 2 | *(Pausa fria já existe; cliente será orientado a usar — sem alteração neste escopo.)* | — |
| 3 | Ao retomar, o bico estava frio (esfriou manualmente); a impressão começou sem esperar o bico esquentar e não esquentaria automaticamente. | Ao retomar: se o bico (e/ou mesa) estiver abaixo da temperatura de impressão, **esperar o reaquecimento** (M109/M190) antes de continuar enviando G-code. |

---

## 2. Análise do que já existe no código

### 2.1 Estacionar ao pausar / voltar ao retomar (problema 1)

- **Hoje:** Ao entrar em pausa, a thread apenas:
  - Salva estado (posição M114, temperaturas M105, offset no arquivo).
  - Se opção for `cold`: envia M104 S0 e M140 S0.
  - Se opção for `filament_change`: envia M600.
- **Não há:** retração do filamento, subida do Z, movimento para um “cantinho” (park). O bico permanece em cima da peça.

**O que falta:** Sequência de **park na pausa** e **unpark no resume**:

- **Na pausa (na thread, logo após salvar o estado):**
  1. Retrair filamento (ex.: `G91` + `G1 E-5 F300` ou valor configurável).
  2. Subir Z para não arrastar na peça (ex.: `G91` + `G1 Z10` ou Z relativo configurável).
  3. Ir para posição de estacionamento (ex.: canto da mesa — X e Y configuráveis, ex. X0 Y0 ou X220 Y220).
  4. Manter `G90` ao final para o próximo uso.
- **No resume (no backend, antes de limpar `print_paused` e a thread continuar):**
  1. (Se for reaquecer, fazer isso primeiro — ver item 3.)
  2. Movimento de volta: ir para a posição salva (X, Y, Z) com G0/G1.
  3. “Desretrair” o mesmo valor usado na retração (ex.: `G91` + `G1 E5 F300`).
  4. Voltar para `G90` e seguir com o envio do G-code do arquivo.

**Decisões de desenho:**

- Valores de retração (mm), subida Z (mm) e posição de park (X, Y) devem ser **configuráveis** (variáveis de ambiente ou config no backend), com defaults seguros (ex.: retração 5 mm, Z +10 mm, park X0 Y0 ou no canto oposto da peça).
- A posição de retorno (X, Y, Z, E) já é salva em `print_pause_state`; usar esses valores no unpark.
- Garantir que a sequência de park use **modo relativo (G91)** só onde for necessário (retração, Z) e **absoluto (G90)** para X/Y de park e para o retorno.

### 2.2 Retomar sem esperar reaquecimento (problema 3)

- **Hoje:** O reaquecimento no resume só acontece quando `pause_option == 'cold'` (e há `target_nozzle`/`target_bed` salvos). Se o usuário pausou com “Manter temperatura” e depois **esfriou manualmente** o bico, ao clicar em Retomar o backend **não** reaquece; a thread continua enviando G-code e a impressora pode imprimir a frio.

**O que falta:** No resume, **sempre** que houver estado de pausa com temperaturas alvo (target_nozzle, target_bed):

- Obter temperatura atual (M105, parsear resposta).
- Se temperatura atual do bico &lt; alvo (ex.: com margem de 5 °C), enviar M109 (e opcionalmente M104) e **esperar** até o alvo (já temos timeout 300 s no M109/M190).
- O mesmo para a mesa: se atual &lt; alvo, M140 + M190 e esperar.
- Só depois disso limpar `print_paused` e deixar a thread continuar.

Assim, tanto “pausa fria” quanto “manter temperatura” com resfriamento manual passam a reaquecer antes de continuar.

**Detalhe de implementação:**

- O resume hoje é feito no endpoint `POST /api/printer/resume`. A leitura de `print_pause_state` e o envio de M109/M190 já existem para o caso `cold`. Basta estender: para **qualquer** pausa que tenha `target_nozzle`/`target_bed` salvos, consultar M105 e, se a temperatura atual estiver abaixo do alvo (ou abaixo de um threshold, ex. alvo − 5), executar M109 (bico) e M190 (mesa) com wait antes de retornar sucesso e a thread continuar.

---

## 3. Ordem sugerida de implementação

1. **Reaquecimento no resume (problema 3)**  
   - Alterar `printer_resume()` em `app.py`: sempre que houver `print_pause_state` com target_nozzle/target_bed, obter temperatura atual (M105); se bico/mesa abaixo do alvo, enviar M109/M190 e esperar; depois limpar pausa.  
   - Teste: pausar com “Manter temperatura”, esfriar manualmente o bico, retomar → deve reaquecer e só então continuar.

2. **Park ao pausar / unpark ao retomar (problema 1)**  
   - Definir constantes ou config (retração mm, Z relativo mm, park X, Y).  
   - Na thread, logo após salvar o estado de pausa (e antes de aplicar cold/M600): enviar sequência retração → Z up → G0 park (X,Y) → G90.  
   - No `printer_resume()`, após o reaquecimento (se houver): enviar sequência G0 até (pos_x, pos_y) → G0 Z pos_z → desretração (G91, G1 E+retract, G90).  
   - Garantir que a posição salva (pos_x, pos_y, pos_z, pos_e) e o valor de retração usado fiquem coerentes para o unpark (e que o E seja restaurado corretamente para o próximo G1 do arquivo).  
   - Teste: pausar → bico deve ir para o canto; retomar → deve voltar à posição e continuar.

---

## 4. Riscos e cuidados

- **Park/Unpark:** Valores de retração e posição de park dependem da impressora e do filamento. Usar defaults conservadores e, idealmente, configuração por variáveis de ambiente (ex.: `PAUSE_RETRACT_MM`, `PAUSE_Z_LIFT_MM`, `PAUSE_PARK_X`, `PAUSE_PARK_Y`) para o cliente ajustar sem mexer no código.
- **Ordem dos comandos:** Na pausa, a sequência deve ser: salvar estado (incluindo posição atual) → retrair → subir Z → ir para park. No resume: reaquecer (se necessário) → voltar para (X,Y) → voltar Z → desretrair → continuar. Qualquer inversão pode causar arraste na peça ou E incorreto.
- **Compatibilidade:** Algumas firmwares podem interpretar G92 E de forma diferente. Preferir “desretração” pelo mesmo valor absoluto usado na retração (G91 + G1 E+valor) em vez de G92 E, para não quebrar o E absoluto do próximo comando do arquivo.

---

## 5. Resumo

| Problema | Causa atual | Ação |
|----------|-------------|------|
| Bico em cima da peça na pausa, pingando | Não há park: thread só salva estado e opcionalmente desliga temperatura. | Implementar park (retração + Z up + movimento para canto) na pausa e unpark (volta à posição + desretração) no resume; parâmetros configuráveis. |
| Retomar com bico frio sem reaquecer | Reaquecimento no resume só quando `pause_option == 'cold'`. | No resume, sempre que houver target_nozzle/target_bed, comparar com M105 e, se estiver abaixo do alvo, executar M109/M190 e esperar antes de continuar. |

**Implementado:** (1) reaquecimento no resume sempre que temperatura atual estiver abaixo do alvo (M105 + M109/M190); (2) park na pausa (retração, Z up, G0 para PAUSE_PARK_X/Y) e unpark no resume (volta à posição salva + desretração). Variáveis de ambiente: `PAUSE_RETRACT_MM`, `PAUSE_Z_LIFT_MM`, `PAUSE_PARK_X`, `PAUSE_PARK_Y`. (Pausa fria já existia; sem alteração de UX/doc.)
