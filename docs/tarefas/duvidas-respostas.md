1. Arquitetura / Funcionamento Atual

- Hoje tudo roda local? (Front, API Python e Orca estão na mesma máquina/rede?)
    
    R: Sim
    
- As impressoras ficam em redes separadas ou todas na mesma rede local?
    
    R: Na mesma rede
    
- Onde o Orca (fatiador) roda atualmente? Desktop do cliente, Raspberry ou nuvem?
    
    R: Maquina local
    
- Fluxo completo ao clicar em “Imprimir”:
    
    Front → POST na API Python → Python aciona Orca → Orca gera G-code → Python envia para impressora? (confirmar detalhes)
    
    R: O Fatiador envia apenas o arquivo g-code para a impressora e o python envia para a impressora via terminal
    
- A comunicação Python → impressora é via USB/serial local ou outro protocolo?
    
    R: Via terminal
    
- Qual conexão física a impressora usa para receber o G-code? (USB A/B, serial TTL, etc)
    
    R: USB ( conexao raspberry com a placa da impressora ) , serial ( comandos do python para a impressora ) 
    

---

![🌍](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f30d/72.png)

2. Controle Remoto / Acesso Externo

- Precisam acessar/controlar impressoras que estão fora da rede local (ex: rede do cliente)?
    
    R: Hoje expoe a porta da impressora para acessar de fora ( o ideal seria tudo em nuvem ) 
    
- Preferem alguma solução específica? (VPN, DDNS, túnel reverso, etc)
    
    R: Preferencia tunel mas pode utilizar outra opção
    

---

![🧩](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f9e9/72.png)

3. Integração do Fatiador (Orca / Arkslicer)

- Querem embutir o fatiador no front-end (tipo embed) ou apenas fazer upload e processar no backend?
    
    R: Isso, do front enviar comandos para o fatiador, não embedar o fatiador direto no front ( python > orca ) 
    
- O Orca é open-source e pode rodar em servidor/nuvem?
R: Nunca foi visto rodar em servidor/nuvem, mas, caso conseguir eles aceitam ( estavam até vendo outro fatiador que roda em nuvem, verificar opções )
    
    Ou obrigatoriamente precisa rodar na máquina do cliente?
    
    R: Não tem essa obrigatoriedade, eles tentaram achar algo em nuvem 
    

---

![🎨](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f3a8/72.png)

4. Mistura de Cores e Pré-visualização

- O front deve permitir ajustar porcentagem de cada filamento para gerar pré-visualização?
    
    R: Sim
    
- A prévia esperada é uma simulação aproximada por camada?
    
    R: Sim, mas pode ter algumas variações que ficará diferente do front, isso vai ser inevitavel ( dificilmente vai ser possivel uma mistura fiel ao que vamos mostrar no front ) 
    
- Existe documentação de como as porcentagens viram comandos no G-code?
    
    Ou precisamos descobrir via testes? 
    
    R: Não tem uma doc oficial sobre como as porcentagem viram comandos g-code, porem ja tem algumas classificações feitas, porem para classificar mais precisa de mais testes
    
    Obs: Dependendo do filamento (qualidade, etc) pode ser que tenha alteração na cor final.
    

---

![⚠️](https://fonts.gstatic.com/s/e/notoemoji/17.0/26a0_fe0f/72.png)

5. Detecção de Falhas / Skip / Monitoramento

- Quando ocorre erro na impressão, qual é o formato da resposta? (podem enviar exemplo de payload JSON?)
R: Exemplo vai ser enviado, mas, hoje não é recebido esse erro dentro do código, precisa fazer a comunicação entre a impressora 

Obs: O OctoPrint que comunica o erro da impressora, hoje a impressora só comunica via display. O OctoPrint instalado no raspberry possibilita a comunicação de maneira fácil com o python
- Existe catálogo de códigos de erro?
R: Não, mas tem os erros que acontecem geralmente ( iram mandar os que geralmente acontecem )
- Desejam botão de “Skip” no front quando houver erro?
R: Sim, e também ter as opções ( Resolver problema, problema resolvido, retomar ) entao tem que ter a possibiilidade nao só de pular mas de tentar resolver o problema e afirmar que o problema foi resolvido e ai sim retomar, mas, tem uns que vai precisar cancelar a impressão mesmo

Obs: Teria que ter a opção de visualizar qual peça pular, uma simulacao real das pecas na impressora, pois pode ter o cenario de varias peças e saber qual pular

Um dos desafios é: o bico pode ficar grudado em um item, arrastar pro outro e fazer a maior bagunça com erros e mesmo assim não notificar o sistema, nao emite nenhuma mensagem, sempre nesse mundo de impressora 3d tem alguem pra acompanhar, entao a ideia de visualizar a mesa é pra escolher qual peça continuar por esse fato 

Fazer pesquisas de como seria possivel visualizar a previa da mesa no frontend

Hoje tem a bambulab lab a1, a1 mini ( essas duas não pulam ) flashforge AD5X essa ja pula ( será enviado foto da evidencia de como a flashforge pula )
    
    (Pular peça atual? Continuar fila? Consumir filamento mesmo assim?)
    
- Podemos ter acesso a logs ou endpoint para simular falhas e testar no front?
R: Não tem como e a impressora só emite o erro no display e o app ( octoPrint e outros ) ,  interpreta e exibe a mensagem

---

![📷](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f4f7/72.png)

6. Testes e Evidências

- Conseguem enviar fotos e vídeos da impressora imprimindo e dos resultados finais?
Sera enviado
Ja foi enviado ( whatsapp )

---

![📚](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f4da/72.png)

7. Documentação Técnica

- Existe README, documentação da API ou lista de endpoints disponível?
R: Dentro do chromasistem

---

![🌐](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f310/72.png)

8. Infraestrutura / Rede / IP

- As máquinas (Raspberry / mini-PC) terão IP dinâmico?
R: Sim
- Já existe DDNS ou solução para manter conexão estável?
R: Não, hoje foi configurado dentro do chromasistem para quando a impressora perder conexão ela tentar automaticamente se conectar em outra rede, porem ainda não funciona, mas foi implementado.
- Autorizam instalar um agente para manter conexão com a nuvem (keepalive / atualização de IP)?
R: Sim