# 🔗 Integração Croma + OrcaSlicer

## Guia Completo de Configuração

### 📋 Visão Geral

Este guia mostra como configurar o OrcaSlicer para enviar arquivos G-code diretamente para o sistema Croma, eliminando a necessidade de transferência manual de arquivos.

---

## 🚀 Configuração Rápida

### Passo 1: Acesse a página de Arquivos

1. Faça login no Croma
2. Clique em **"Arquivos"** no menu superior
3. Role até a seção **"Integração com OrcaSlicer"**

### Passo 2: Configure o OrcaSlicer

#### No OrcaSlicer:

1. Abra **Preferences** (Preferências)
2. Vá para a aba **Network** (Rede)
3. Clique em **Add** (Adicionar) para criar novo servidor

#### Configure os seguintes campos:

```
Nome do Servidor: Croma 3D Printer
Tipo: Custom API
URL: http://localhost:8080/api/files/upload
(ou http://[IP-DO-RASPBERRY]:8080/api/files/upload)
```

---

## 📡 Configuração Detalhada

### Opção 1: Acesso Local (mesmo computador)

**URL do Servidor:**
```
http://localhost:8080/api/files/upload
```

**Quando usar:** 
- OrcaSlicer rodando no mesmo computador que o Croma
- Desenvolvimento e testes

### Opção 2: Acesso na Rede Local

**URL do Servidor:**
```
http://[IP-DO-RASPBERRY]:8080/api/files/upload
```

**Exemplo:**
```
http://192.168.1.100:8080/api/files/upload
```

**Como descobrir o IP:**
```bash
# No Raspberry Pi
hostname -I

# Ou via interface web do Croma
# O IP aparece nas instruções de integração
```

### Opção 3: Acesso Remoto (Internet)

**URL do Servidor:**
```
https://seu-dominio.com:8080/api/files/upload
```

**Requisitos:**
- Port forwarding configurado no roteador (porta 8080)
- DNS dinâmico ou IP fixo
- HTTPS configurado (recomendado por segurança)

---

## 🔐 Autenticação (Atual)

**Status:** Baseado em sessão de navegador

**Como funciona:**
1. Faça login no Croma pelo navegador
2. Mantenha o navegador aberto
3. Envie arquivos do OrcaSlicer
4. O sistema usa a mesma sessão do navegador

**Limitação atual:** É necessário estar logado no navegador

**Futura implementação:** Token de API para autenticação direta

---

## 📤 Como Enviar Arquivos

### Método 1: Botão "Upload" no OrcaSlicer

1. Prepare seu modelo no OrcaSlicer
2. Clique em **Slice** (Fatiar)
3. Clique no botão **Upload** (⬆️)
4. Selecione **"Croma 3D Printer"**
5. O arquivo será enviado automaticamente

### Método 2: Upload Manual

1. Exporte o G-code: **File → Export G-code**
2. Acesse **Croma → Arquivos**
3. Arraste e solte o arquivo ou clique em **"Selecionar Arquivo"**
4. Aguarde o upload concluir

---

## 🎯 Recursos do Gerenciador de Arquivos

### 📂 Funcionalidades Disponíveis

- ✅ **Upload de arquivos** (.gcode, .gco, .g)
- ✅ **Arrastar e soltar** (drag & drop)
- ✅ **Listagem de arquivos** com informações detalhadas
- ✅ **Busca por nome** de arquivo
- ✅ **Iniciar impressão** diretamente do arquivo
- ✅ **Download de arquivos**
- ✅ **Exclusão de arquivos**
- ✅ **Histórico de impressões** (contador)
- ✅ **Data de upload** e última impressão

### 📊 Informações Exibidas

Para cada arquivo você vê:
- 📄 Nome do arquivo
- 📦 Tamanho do arquivo
- 📅 Data e hora do upload
- 🖨️ Número de vezes impresso
- ⏱️ Data da última impressão

---

## 🛠️ API Endpoints Disponíveis

### Upload de Arquivo
```
POST /api/files/upload
Content-Type: multipart/form-data
Body: file=[arquivo.gcode]
```

### Listar Arquivos
```
GET /api/files/list
Response: JSON com lista de arquivos
```

### Iniciar Impressão
```
POST /api/files/print/{file_id}
Response: Confirmação de início
```

### Download de Arquivo
```
GET /api/files/download/{file_id}
Response: Arquivo G-code
```

### Deletar Arquivo
```
DELETE /api/files/delete/{file_id}
Response: Confirmação de exclusão
```

---

## 🔧 Solução de Problemas

### Erro: "Não foi possível conectar ao servidor"

**Possíveis causas:**
1. Croma não está rodando
2. IP/URL incorreto
3. Porta bloqueada por firewall

**Soluções:**
```bash
# Verificar se Croma está rodando
lsof -i:8080

# Verificar IP do Raspberry Pi
hostname -I

# Liberar porta no firewall
sudo ufw allow 8080
```

### Erro: "Não autenticado"

**Causa:** Sessão expirou ou não está logado

**Solução:**
1. Faça login no navegador
2. Mantenha o navegador aberto
3. Tente enviar novamente

### Erro: "Tipo de arquivo não permitido"

**Causa:** Formato de arquivo incorreto

**Solução:**
- Use apenas arquivos .gcode, .gco ou .g
- Verifique se o arquivo foi exportado corretamente

### Upload muito lento

**Causas:**
- Arquivo muito grande (>100MB)
- Rede lenta
- WiFi com sinal fraco

**Soluções:**
- Use conexão cabeada (Ethernet)
- Aproxime dispositivos do roteador
- Comprima G-code (remova comentários)

---

## 📱 Acesso Remoto Seguro

### Configuração HTTPS (Recomendado)

Para acesso via internet, use HTTPS:

1. **Obtenha um certificado SSL:**
   - Let's Encrypt (gratuito)
   - Self-signed certificate (desenvolvimento)

2. **Configure reverse proxy:**
```nginx
server {
    listen 443 ssl;
    server_name croma.seudominio.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Configure port forwarding:**
   - Porta externa: 443 (HTTPS)
   - Porta interna: 8080
   - IP: [IP do Raspberry Pi]

---

## 💡 Dicas e Boas Práticas

### 📝 Organização de Arquivos

- Use nomes descritivos: `Vaso_PLA_0.2mm.gcode`
- Inclua configurações importantes no nome
- Delete arquivos antigos regularmente

### 🚀 Fluxo de Trabalho Recomendado

1. **Design** → Seu software CAD favorito
2. **Fatiar** → OrcaSlicer
3. **Upload** → Botão upload direto para Croma
4. **Monitorar** → Dashboard do Croma
5. **Imprimir** → Clique em "Imprimir" no arquivo

### ⚡ Performance

- Mantenha no máximo 50 arquivos armazenados
- Arquivos G-code grandes (>50MB) podem demorar para carregar
- Use compactação quando possível

---

## 🔄 Futuras Melhorias

Recursos planejados:

- [ ] Token de API para autenticação sem navegador
- [ ] Pré-visualização 3D do G-code
- [ ] Estimativa de tempo e material
- [ ] Organização em pastas
- [ ] Tags e favoritos
- [ ] Upload múltiplo
- [ ] Compressão automática
- [ ] Sincronização com nuvem
- [ ] Histórico detalhado de impressões

---

## 📞 Suporte

Problemas ou dúvidas?

1. Verifique os logs do servidor
2. Teste o upload manual pelo navegador
3. Confirme conectividade de rede
4. Verifique permissões de arquivo

---

**Sistema Croma v1.0**  
Integração OrcaSlicer para impressão 3D simplificada
