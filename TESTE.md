# 🧪 Guia de Teste Rápido - Sistema Croma

## Testar Localmente no Mac

### Passo 1: Executar o Sistema

```bash
cd "/Users/tonymichaelbatistadelima/Documents/Novo modo Wi-Fi de cores"
./run.sh
```

Aguarde a mensagem:
```
* Running on http://0.0.0.0:5000
```

### Passo 2: Acessar no Navegador

Abra seu navegador e acesse:
```
http://localhost:5000
```

### Passo 3: Criar Conta

1. Você verá a tela de login com o logo Croma
2. Clique em **"Criar conta"**
3. Digite:
   - **Usuário**: admin
   - **Senha**: 123456
   - **Confirmar Senha**: 123456
4. Clique em **"Criar Conta"**

### Passo 4: Explorar o Dashboard

Após o login, você verá:

#### 📊 Status da Impressora
- Estado: "Imprimindo" (simulado)
- Conexão: "Conectado" (simulado)

#### 🌡️ Temperaturas
- **Bico**: 200°C / 210°C (simulado)
- **Mesa**: 60°C / 60°C (simulado)

#### 📈 Progresso
- Arquivo: modelo_3d.gcode
- Progresso: 45.5%
- Tempo Decorrido: 01:23:45
- Tempo Restante: 01:45:30

#### ⏯️ Controles
Teste os botões:
- **▶️ Iniciar** - Mostra notificação de sucesso
- **⏸️ Pausar** - Pausa a impressão (simulado)
- **▶️ Retomar** - Retoma a impressão (simulado)
- **⏹️ Parar** - Para a impressão (simulado)

### Passo 5: Testar Logout

Clique no botão **"Sair"** no canto superior direito para fazer logout.

---

## ✅ Checklist de Funcionalidades

Teste cada item:

- [ ] Página de login carrega corretamente
- [ ] Logo Croma aparece
- [ ] Link "Criar conta" funciona
- [ ] Validação de senha (mínimo 6 caracteres)
- [ ] Confirmação de senha funciona
- [ ] Registro cria conta com sucesso
- [ ] Login funciona com credenciais corretas
- [ ] Login falha com credenciais incorretas
- [ ] Dashboard carrega após login
- [ ] Dados de temperatura aparecem
- [ ] Barra de progresso é visível
- [ ] Botões de controle respondem
- [ ] Notificações aparecem ao clicar nos botões
- [ ] Logout funciona corretamente
- [ ] Não é possível acessar dashboard sem login

---

## 🎨 Testar Responsividade

### Desktop
- Abra em tela cheia
- Verifique se todos os cards aparecem lado a lado

### Tablet/Mobile
- Redimensione a janela do navegador
- Os cards devem se empilhar verticalmente
- Botões devem ficar em coluna única

---

## 🔧 Comandos Úteis

### Ver Logs em Tempo Real
O servidor mostra logs no terminal onde você executou `./run.sh`

### Parar o Servidor
Pressione `Ctrl + C` no terminal

### Reiniciar o Servidor
```bash
./run.sh
```

### Limpar Banco de Dados (Começar do Zero)
```bash
rm croma.db
./run.sh
```

---

## 🧪 Testar API Diretamente

### Usando curl (Terminal):

#### Criar Usuário
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"123456"}'
```

#### Fazer Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"123456"}' \
  -c cookies.txt
```

#### Obter Status (requer login)
```bash
curl -X GET http://localhost:5000/api/printer/status \
  -b cookies.txt
```

#### Pausar Impressão
```bash
curl -X POST http://localhost:5000/api/printer/pause \
  -b cookies.txt
```

---

## 📱 Testar em Dispositivos Móveis

### Encontrar IP do seu Mac:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Acessar do celular/tablet:
```
http://[SEU-IP]:5000
```

Exemplo: `http://192.168.1.100:5000`

---

## ⚠️ Problemas Comuns

### Porta 5000 já está em uso
**Erro**: `Address already in use`

**Solução**:
```bash
# Encontrar e matar processo na porta 5000
lsof -ti:5000 | xargs kill -9

# Ou mudar a porta no app.py para 8080
```

### Módulo Flask não encontrado
**Erro**: `ModuleNotFoundError: No module named 'flask'`

**Solução**:
```bash
pip install -r requirements.txt
```

### Permissão negada ao executar script
**Erro**: `Permission denied`

**Solução**:
```bash
chmod +x run.sh
chmod +x install.sh
```

### Logo não aparece
**Verificar**: O arquivo `static/images/logo-branca.png` existe?

```bash
ls -la static/images/
```

---

## 🎯 Próximos Passos

Após testar localmente com sucesso:

1. ✅ Sistema funciona no Mac
2. 📦 Transferir para Raspberry Pi
3. 🔧 Executar instalação no Pi
4. 🔌 Conectar impressora 3D
5. ⚙️ Configurar comunicação serial
6. 🚀 Usar em produção!

---

## 📞 Dicas de Teste

### Teste de Segurança
1. Tente acessar `/dashboard` sem fazer login
   - Deve redirecionar para `/login`

2. Tente criar usuário com senha curta
   - Deve mostrar erro "mínimo 6 caracteres"

3. Tente criar usuário duplicado
   - Deve mostrar erro "usuário já existe"

### Teste de Interface
1. Verifique se todas as cores estão corretas (gradiente azul/preto)
2. Teste todos os botões
3. Verifique se as notificações aparecem e desaparecem
4. Confirme que os dados atualizam (modo simulado)

### Teste de Performance
1. Deixe o dashboard aberto por alguns minutos
2. Verifique se não há vazamento de memória
3. Observe se as atualizações continuam funcionando

---

## ✨ Tudo Funcionando?

Se todos os testes passaram, seu sistema Croma está pronto para uso! 🎉

**Próximo passo**: Instalar no Raspberry Pi seguindo o guia [INSTALACAO_RASPBERRY.md](INSTALACAO_RASPBERRY.md)

---

**Boa sorte com suas impressões 3D! 🖨️✨**
