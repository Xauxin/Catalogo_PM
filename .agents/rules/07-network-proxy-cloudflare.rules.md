# Regra de Rede, Proxy Reverso, Cloudflare e WebSocket

## 1. Declaração da Regra
Quando a aplicação Streamlit for exposta para a internet através de túneis, proxies reversos (como Cloudflare) ou gateways de CGNAT, a infraestrutura e os arquivos de configuração do Streamlit **DEVEM** aderir a diretrizes estritas para viabilizar conexões bidirecionais de WebSocket sem quedas, bloqueios de origem ou loops de carregamento.

---

## 2. Arquitetura de Rede e Modo SSL/TLS

1. **Cloudflare SSL/TLS Encryption Mode (Flexible):**
   * Quando o tráfego público do Cloudflare for roteado para um IP/Porta de Gateway ou túnel que entrega HTTP cru para a máquina local (sem certificado SSL configurado localmente no Uvicorn/Streamlit), o modo de criptografia no Cloudflare **DEVE ser "Flexible"**.
   * O envio de requisições HTTPS criptografadas diretamente para uma porta HTTP sem terminação TLS dispara o erro de baixo nível `Invalid HTTP request received` e `WinError 10054` no servidor local.

2. **Handshake e Suporte a WebSockets no Cloudflare:**
   * No painel da Cloudflare (em *Network*), o recurso **WebSockets** deve permanecer ativado (`ON`).

---

## 3. Diretrizes Mandatórias em `.streamlit/config.toml`

Ao operar atrás de proxy reverso ou subdomínio personalizado, o arquivo `.streamlit/config.toml` deve conter obrigatoriamente:

```toml
[server]
port = 8502
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false

[browser]
gatherUsageStats = false
```

### Justificativas Técnicas:
* **`enableCORS = false` & `enableXsrfProtection = false`:** Impede que o Streamlit rejeite handshakes de WebSocket vindos do domínio público (ex: `catalogo.pontomatriz.com`) cujo cabeçalho `Origin` difira do `Host` interno ou `localhost`.
* **`enableWebsocketCompression = false`:** Essencial para evitar corrupção e descarte de quadros WebSocket compactados (`permessage-deflate`) por proxies intermediários e redes residuais, prevenindo desconexões silenciosas e interfaces travadas.
* **Ciclo de Reinício:** Qualquer alteração em `config.toml` exige reinicialização do processo do Streamlit (`Ctrl+C` e `streamlit run app.py`) para que o servidor Uvicorn carregue as novas diretivas de rede.

---

## 4. Redirecionamento e Callbacks OAuth (Google / Meta / Supabase)

1. **Variável `APP_URL` em `.streamlit/secrets.toml`:**
   * Para que o fluxo de login via OAuth redirecione o usuário de volta para o domínio público (com HTTPS) e não para `http://localhost:8502`, a chave `APP_URL` **DEVE** estar preenchida:
     ```toml
     APP_URL = "https://catalogo.pontomatriz.com"
     ```
   * O helper `obter_app_url()` em `utils/auth.py` lê essa chave prioritariamente.

2. **Configuração de URLs no Painel do Supabase:**
   * No painel do Supabase (*Authentication* -> *URL Configuration*):
     * **Site URL:** Deve ser configurada com a URL pública (`https://catalogo.pontomatriz.com`).
     * **Redirect URLs:** Devem conter a raiz e o wildcard (`https://catalogo.pontomatriz.com` e `https://catalogo.pontomatriz.com/**`).
