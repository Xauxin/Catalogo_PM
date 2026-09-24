# Instrução: Adicionar Nova Página ao Streamlit

Este roteiro descreve o fluxo sequencial para criar uma nova tela no sistema, garantindo integração com a autenticação global, menu de navegação e repositórios de dados.

---

## Pré-requisitos
- Ter clareza sobre o propósito da tela (ex: relatório financeiro, cadastro técnico, configurações).
- Ter definido o ícone e o título de exibição.

---

## Roteiro Passo a Passo

### 1. Criar o Arquivo da Página em `pages/`
Crie o arquivo `pages/[nome_da_pagina].py` utilizando o esqueleto base de página:

```python
import streamlit as st
from utils.auth import verificar_autenticacao

# 1. Configuração da Página
st.set_page_config(page_title="[Título da Página]", page_icon="[Ícone]", layout="wide")

# 2. Barreira de Autenticação Obrigatória
verificar_autenticacao()

# 3. Cabeçalho
st.title("[Ícone] [Título da Página]")
st.caption("[Breve descrição da finalidade da tela]")

# 4. Conteúdo / Abas
tab1, tab2 = st.tabs(["[Aba 1]", "[Aba 2]"])

with tab1:
    st.info("Conteúdo em desenvolvimento...")
```

### 2. Registrar a Página no `pages_sections.toml`
Abra o arquivo [`pages_sections.toml`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/pages_sections.toml) e adicione a nova seção ao final:

```toml
[[pages]]
path = "./pages/[nome_da_pagina].py"
name = "[Nome para o Menu]"
icon = "[Ícone correspondente]"
```

### 3. Conectar a Camada de Repositório (se houver dados)
Importe o repositório adequado no topo da página:
```python
from core.repository import CatalogoRepository  # ou LoteRepository
```
Carregue os dados com tratamento de exceção seguro:
```python
try:
    dados = CatalogoRepository.<metodo_de_busca>()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    dados = []
```

### 4. Validação Manual
1. Inicie a aplicação via terminal: `streamlit run app.py`
2. Certifique-se de que a página surge no menu lateral com o ícone correto.
3. Teste o acesso sem autenticação (deve bloquear e pedir login).
4. Teste a renderização após o login.
