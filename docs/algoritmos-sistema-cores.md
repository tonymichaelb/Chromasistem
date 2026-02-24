# Algoritmos do sistema de cores (100+ cores)

Descrição de como funciona o cálculo da mistura de filamentos a partir de uma cor escolhida na interface. Tudo roda no **frontend**; o backend só recebe e envia o comando M182 para a impressora.

---

## 1. Visão geral

O usuário escolhe **qualquer cor** (color picker). O sistema calcula as **porcentagens** dos 3 filamentos (Ciano A, Magenta B, Amarelo C) que somam 100% e envia o comando **M182 A% B% C%** para a impressora. Dois efeitos importantes:

- **Matiz (tom da cor):** vermelho, azul, verde etc. → define a *proporção* entre os três filamentos.
- **Luminosidade (claro/escuro):** tons escuros geram uma mistura mais “neutra”; tons claros, mais próxima do matiz puro.

Assim, **vários tons da mesma cor** (ex.: vermelho claro e vermelho escuro) geram **porcentagens diferentes**, não mais a mesma receita para todos.

---

## 2. Algoritmos utilizados

### 2.1 RGB → HSV (luminosidade)

A cor escolhida vem em **RGB** (vermelho, verde, azul, 0–255). Primeiro calculamos **HSV** (matiz, saturação, valor) para obter a **luminosidade** da cor:

- **V (Value / valor):** é o “quão clara” a cor é (0 = preto, 1 = cor máxima).
- Fórmula: `V = max(R, G, B) / 255`.

Usamos esse **V** depois para misturar a receita da cor com uma mistura neutra (ver abaixo).

---

### 2.2 RGB → CMY (proporção Ciano / Magenta / Amarelo)

Os três filamentos são tratados como **Ciano (A), Magenta (B), Amarelo (C)**. O sistema já usava um modelo em que a “cor vista” é uma mistura aditiva desses três. A partir do RGB da cor escolhida, calculamos a proporção de cada um:

- Convertemos R, G, B para o intervalo 0–1.
- Proporções “brutas” (antes de normalizar):
  - Ciano:  `c = (G + B - R) / 2`
  - Magenta: `m = (R + B - G) / 2`
  - Amarelo: `y = (R + G - B) / 2`
- Cada valor é limitado entre 0 e 1.
- Normalizamos para que a soma seja 100% e obtemos as porcentagens **A, B, C** (inteiros) que vão no M182.

Isso dá a **receita do matiz**: qual proporção de cada filamento corresponde àquela cor, ignorando se ela é mais clara ou mais escura.

---

### 2.3 Incorporação da luminosidade (tons claros vs escuros)

Para que **tons escuros e claros da mesma cor** não fiquem com a mesma receita:

- **Mistura neutra:** 33% Ciano, 33% Magenta, 34% Amarelo (cinza).
- **Mistura do matiz:** resultado do passo anterior (A, B, C).
- **Mistura final:**
  - Cor **clara** (V alto): usa quase só a mistura do matiz.
  - Cor **escura** (V baixo): mistura mais a receita com a neutra.
  - Fórmula:  
    `mistura_final = V × (mistura do matiz) + (1 − V) × (mistura neutra)`  
    e em seguida os três valores são normalizados de novo para somar 100%.

Assim, por exemplo, vermelho vivo e vermelho escuro geram **A/B/C diferentes**; a cor real na impressora pode variar em relação ao preview (variação aceita no escopo).

---

## 3. G-code (M182)

Não há algoritmo novo no backend. O frontend já envia as porcentagens finais (A, B, C) para a API; o backend monta a string **M182 A% B% C%** e envia para a impressora via serial, como antes.

---

## 4. Resumo

- **Color picker:** o usuário escolhe qualquer cor; o sistema calcula automaticamente as % de cada filamento.
- **Preview:** a prévia da cor (no modal e na seção “Cor personalizada”) usa o mesmo modelo (CMY → RGB) para simular o resultado na tela.
- **Luminosidade:** tons mais escuros tendem a uma mistura mais neutra; tons mais claros, ao matiz da cor.
- **Envio:** o comando M182 com as porcentagens calculadas é enviado para a impressora; a cor real pode variar conforme filamento e qualidade.
