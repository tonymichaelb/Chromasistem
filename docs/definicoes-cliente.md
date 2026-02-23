# Definições e Afirmações do Cliente (Chromasistem)

Documento que consolida **todas as definições e respostas do cliente** obtidas em alinhamento. Serve como referência única para escopo, arquitetura e decisões do projeto.

**Fonte:** respostas-chroma.pdf (alinhamento com o cliente).

---

## 1. Arquitetura e funcionamento atual

| # | Afirmação |
|---|-----------|
| 1.1 | **Tudo roda local hoje:** front, API Python e Orca estão na mesma máquina/rede. |
| 1.2 | **Impressoras na mesma rede:** todas as impressoras ficam na mesma rede local (não em redes separadas). |
| 1.3 | **Orca (fatiador) roda na máquina local** do cliente (não no Raspberry, não em nuvem). |
| 1.4 | **Fluxo ao imprimir:** o fatiador envia apenas o arquivo G-code para a impressora; o Python envia para a impressora **via terminal**. |
| 1.5 | **Comunicação Python → impressora:** via **terminal** (não apenas USB/serial genérico). |
| 1.6 | **Conexão física impressora:** **USB** (Raspberry com placa da impressora) e **serial** (comandos do Python para a impressora). |

---

## 2. Controle remoto e acesso externo

| # | Afirmação |
|---|-----------|
| 2.1 | **Hoje:** expõe a porta da impressora para acessar de fora. **Ideal do cliente:** tudo em nuvem. |
| 2.2 | **Preferência de solução:** **túnel** (reverso); outras opções podem ser consideradas. |

---

## 3. Integração do fatiador (Orca / outros)

| # | Afirmação |
|---|-----------|
| 3.1 | **Não embutir o fatiador no front:** do front enviar **comandos para o fatiador**; processamento no backend (Python → Orca). Não é embed do Orca no front. |
| 3.2 | **Orca em servidor/nuvem:** nunca foi visto rodar em servidor/nuvem; **se conseguirmos, o cliente aceita**. Estavam avaliando outro fatiador que roda em nuvem – verificar opções. |
| 3.3 | **Obrigatoriedade de rodar na máquina do cliente:** **não**. Não há obrigatoriedade; eles tentaram achar algo em nuvem. |

---

## 4. Mistura de cores e pré-visualização

| # | Afirmação |
|---|-----------|
| 4.1 | **Front deve permitir** ajustar porcentagem de cada filamento para gerar **pré-visualização**. **Sim.** |
| 4.2 | **Prévia esperada:** simulação aproximada por camada. **Sim**, com ressalva: pode haver **variações** em relação ao que o front mostra; difícilmente a mistura será fiel ao preview – **isso é aceito como inevitável**. |
| 4.3 | **Documentação porcentagem → G-code:** **não existe documentação oficial**. Já existem algumas classificações feitas; para classificar mais cores são necessários **mais testes**. |
| 4.4 | **Observação:** dependendo do filamento (qualidade, etc.) pode haver alteração na cor final. |

---

## 5. Detecção de falhas / Skip / Monitoramento

| # | Afirmação |
|---|-----------|
| 5.1 | **Formato do erro da impressão:** exemplo de payload será enviado pelo cliente. **Hoje o erro não é recebido dentro do código** – é preciso implementar a comunicação entre impressora e sistema. |
| 5.2 | **Contexto:** o **OctoPrint** é que comunica o erro da impressora; hoje a impressora só comunica via **display**. OctoPrint instalado no Raspberry possibilita comunicação mais fácil com o Python. |
| 5.3 | **Catálogo de códigos de erro:** **não existe**. O cliente irá enviar os erros que **geralmente acontecem**. |
| 5.4 | **Botão “Skip” no front:** **sim**. Além disso, o front deve ter as opções: **Resolver problema**, **Problema resolvido**, **Retomar**. Ou seja: não só pular, mas **tentar resolver** → **afirmar que foi resolvido** → **retomar**. Em alguns casos será necessário **cancelar** a impressão. |
| 5.5 | **Visualização de qual peça pular:** deve haver possibilidade de **visualizar qual peça pular**, com **simulação real das peças na impressora** (várias peças na mesa, saber qual pular). |
| 5.6 | **Desafio:** o bico pode ficar grudado em um item, arrastar para outro e causar erros **sem o sistema ser notificado** (não emite mensagem). No mundo de impressão 3D alguém precisa acompanhar; a ideia de **visualizar a mesa** é para escolher qual peça continuar por esse motivo. |
| 5.7 | **Pesquisa:** fazer pesquisas de como seria possível **visualizar a prévia da mesa no frontend**. |
| 5.8 | **Impressoras em uso:** Bambu Lab A1, A1 mini (essas duas **não pulam**); FlashForge AD5X **já pula** (será enviada foto como evidência de como a FlashForge pula). |
| 5.9 | **Logs/endpoint para simular falhas:** **não tem como** hoje; a impressora só emite o erro no display e em apps (OctoPrint e outros), que interpretam e exibem a mensagem. |

---

## 6. Testes e evidências

| # | Afirmação |
|---|-----------|
| 6.1 | **Fotos e vídeos** da impressora imprimindo e dos resultados finais: **serão enviados** pelo cliente. |
| 6.2 | Parte do material **já foi enviado** (WhatsApp). |

---

## 7. Documentação técnica

| # | Afirmação |
|---|-----------|
| 7.1 | **README, documentação da API ou lista de endpoints:** existem **dentro do Chromasistem** (projeto atual). |

---

## 8. Infraestrutura / Rede / IP

| # | Afirmação |
|---|-----------|
| 8.1 | **IP das máquinas (Raspberry / mini-PC):** **dinâmico**. |
| 8.2 | **DDNS ou solução para conexão estável:** **não existe** hoje. |
| 8.3 | **Reconexão automática:** foi configurado dentro do Chromasistem para, quando a impressora perder conexão, **tentar automaticamente conectar em outra rede**; **ainda não funciona**, mas já foi implementado. |
| 8.4 | **Agente para manter conexão com nuvem (keepalive / atualização de IP):** cliente **autoriza** instalar. **Sim.** |

---

## Resumo executivo

- **Arquitetura:** tudo local; Python + terminal para impressora; Orca na máquina local; USB/serial Raspberry ↔ impressora.
- **Remoto:** preferência por **túnel**; ideal é evoluir para **nuvem**.
- **Fatiador:** front envia comandos para o fatiador (Python → Orca); sem embed. Orca em nuvem/servidor é aceito se viável.
- **Cores:** pré-visualização por porcentagem; variações em relação ao preview aceitas; sem doc oficial porcentagem → G-code; mais testes para expandir classificações.
- **Falhas/Skip:** implementar recepção de erro da impressora (hoje não entra no código); botões Resolver / Resolvido / Retomar / Cancelar; visualização da mesa para escolher qual peça pular; pesquisa para prévia da mesa no front; OctoPrint no Raspberry facilita comunicação.
- **Evidências:** cliente envia/envia fotos e vídeos.
- **Docs:** README/API/endpoints dentro do Chromasistem.
- **Rede:** IP dinâmico; sem DDNS; reconexão automática implementada mas não funciona ainda; **autorizado** agente keepalive/atualização de IP para nuvem.

---

*Documento criado a partir das respostas do cliente (respostas-chroma.pdf). Atualizar este arquivo quando houver novas definições.*
