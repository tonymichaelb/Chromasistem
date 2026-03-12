# Túnel de Acesso Remoto — Chromasistem

Este documento descreve como expor o Chromasistem na internet para acesso de qualquer lugar, sem abrir portas no roteador. Dois fluxos estão disponíveis:

- **Testes (ngrok):** URL HTTPS temporária que muda a cada reinício.
- **Produção (Cloudflare Tunnel):** URL fixa com domínio (ex.: `chroma.seudominio.com.br`).

Para o contexto geral (túnel vs. “tudo em nuvem”), veja [controle-remoto-nuvem.md](controle-remoto-nuvem.md).

---

## Pré-requisitos

- Chromasistem em execução no Raspberry Pi (porta 80), por exemplo:
  - `cd /home/pi/Chromasistem && ./run-prod.sh`, ou
  - Serviço systemd `croma.service` ativo.
- Usuário no Pi: `pi`. Projeto em `/home/pi/Chromasistem`.
- Variável opcional: `TUNNEL_PORT` — porta local do app (padrão: `80`). Use se o app rodar em outra porta (ex.: `PORT=5000`).

---

## 1. Testes: URL pública com ngrok

Serve para validar o acesso remoto. A URL HTTPS é gerada pelo ngrok e **muda cada vez que o túnel é reiniciado**.

### 1.1 Obter authtoken

1. Crie uma conta em [ngrok](https://ngrok.com) (grátis).
2. No dashboard: [Your authtoken](https://dashboard.ngrok.com/get-started/your-authtoken).
3. Copie o token.

### 1.2 Configurar o token no Pi

Uma das opções:

- **Variável de ambiente (recomendado):**
  ```bash
  export NGROK_AUTHTOKEN=seu_token_aqui
  ```
- **Config padrão do ngrok:** após instalar, rode uma vez:
  ```bash
  /home/pi/Chromasistem/scripts/.ngrok/ngrok config add-authtoken seu_token_aqui
  ```
  (O script instala o ngrok em `scripts/.ngrok/` na primeira execução.)

### 1.3 Executar o túnel ngrok

No Raspberry (com o Chromasistem já rodando):

```bash
cd /home/pi/Chromasistem
./scripts/setup-tunnel-ngrok.sh
```

A URL HTTPS (ex.: `https://xxxx.ngrok-free.app`) aparece no terminal. Use-a no navegador para acessar o Chromasistem de qualquer lugar.

- Para parar: `Ctrl+C`.
- A URL não é fixa: ao rodar o script de novo, outra URL pode ser gerada.

---

## 2. Produção: URL fixa com Cloudflare Tunnel

Para uma URL fixa (ex.: `chroma.seudominio.com.br`), use o Cloudflare Tunnel. É necessário ter um **domínio** gerenciado no Cloudflare.

### 2.1 Domínio no Cloudflare

1. Adicione o domínio em [Cloudflare](https://dash.cloudflare.com) (ou use um já existente).
2. Aponte os nameservers do domínio para os do Cloudflare.

### 2.2 Criar o túnel no dashboard

1. Acesse **Zero Trust** (ou [one.dash.cloudflare.com](https://one.dash.cloudflare.com)).
2. **Access** > **Tunnels** > **Create a tunnel**.
3. Nome do túnel (ex.: `chromasistem`).
4. Escolha **Cloudflared** como conector.
5. Na etapa de configuração:
   - **Public Hostname:** adicione um hostname (ex.: `chroma.seudominio.com.br`) e escolha o domínio.
   - **Service:** tipo `HTTP`, endereço `localhost`, porta `80` (ou a porta em que o Chromasistem roda).
6. Finalize e copie o **token de instalação** exibido (único para esse túnel).

### 2.3 Configurar o token no Pi

Uma das opções:

- **Variável de ambiente (recomendado):**
  ```bash
  export CLOUDFLARE_TUNNEL_TOKEN=seu_token_aqui
  ```
- **Arquivo local (não versionado):** crie o arquivo com o token:
  ```bash
  echo 'seu_token_aqui' > /home/pi/Chromasistem/scripts/.cloudflare-token
  chmod 600 /home/pi/Chromasistem/scripts/.cloudflare-token
  ```
  O arquivo `scripts/.cloudflare-token` está no `.gitignore` e não deve ser commitado.

### 2.4 Executar o túnel Cloudflare

No Raspberry (com o Chromasistem já rodando):

```bash
cd /home/pi/Chromasistem
./scripts/setup-tunnel-cloudflare.sh
```

Se o token não estiver em variável nem em arquivo, o script pede para colar o token no terminal.

Acesso pela URL fixa configurada no dashboard (ex.: `https://chroma.seudominio.com.br`).

- Para parar: `Ctrl+C`.

### 2.5 (Opcional) Túnel no boot com systemd

Para o túnel subir automaticamente após o Chromasistem:

1. Crie um arquivo de ambiente com o token (não versionado):
   ```bash
   echo 'CLOUDFLARE_TUNNEL_TOKEN=seu_token_aqui' > /home/pi/Chromasistem/scripts/.cloudflare-token.env
   chmod 600 /home/pi/Chromasistem/scripts/.cloudflare-token.env
   ```

2. O projeto já inclui o wrapper `scripts/run-cloudflare-tunnel.sh`, que lê o token de `.cloudflare-token.env` e executa o cloudflared. Certifique-se de que está executável: `chmod +x /home/pi/Chromasistem/scripts/run-cloudflare-tunnel.sh`

3. Crie o unit em `/etc/systemd/system/croma-tunnel.service`:

   ```ini
   [Unit]
   Description=Chromasistem Cloudflare Tunnel
   After=network-online.target croma.service
   Wants=network-online.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/Chromasistem
   ExecStart=/home/pi/Chromasistem/scripts/run-cloudflare-tunnel.sh
   Restart=on-failure
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. Recarregue e habilite o serviço:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now croma-tunnel.service
   ```

---

## Resumo dos scripts

| Script | Uso | URL |
|--------|-----|-----|
| `scripts/setup-tunnel-ngrok.sh` | Testes | Temporária (ex.: `https://xxxx.ngrok-free.app`) |
| `scripts/setup-tunnel-cloudflare.sh` | Produção (domínio) | Fixa (ex.: `https://chroma.seudominio.com.br`) |

Ambos instalam o binário na primeira execução (em `scripts/.ngrok/` e `scripts/.cloudflared/`). Esses diretórios e arquivos de token estão no `.gitignore`.

---

## Solução de problemas

- **"Authtoken não configurado" (ngrok):** defina `NGROK_AUTHTOKEN` ou rode `ngrok config add-authtoken <token>` com o binário em `scripts/.ngrok/`.
- **"Token do túnel não encontrado" (Cloudflare):** defina `CLOUDFLARE_TUNNEL_TOKEN` ou crie `scripts/.cloudflare-token`.
- **Não conecta ao Chromasistem:** confirme que o app está rodando na porta 80 (ou em `TUNNEL_PORT`) no mesmo Pi, e que no Cloudflare o Service está como `http://localhost:80`.
- **Arquitetura não suportada:** os scripts detectam `aarch64`, `armv7l`, `x86_64`. Em outros ambientes, pode ser necessário instalar ngrok/cloudflared manualmente e ajustar o script.
