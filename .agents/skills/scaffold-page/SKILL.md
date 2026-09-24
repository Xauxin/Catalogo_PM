---
name: scaffold-page
description: Criação coordenada de uma nova tela completa no Streamlit, configurando autenticação, roteamento no pages_sections.toml e métodos de repositório necessários.
---

# Skill: Scaffold de Nova Página no Streamlit

Esta habilidade orienta o agente na geração completa e coordenada de uma nova página funcional para o sistema **SVVDST**.

## Passos Coordenados de Execução

1. **Definição da Página e Identificador:**
   - Obter o nome de arquivo `pages/<modulo>.py`.
   - Obter o título da página e o emoji/ícone para o menu.

2. **Criação do Arquivo de Apresentação:**
   - Criar `pages/<modulo>.py` com:
     - `st.set_page_config(layout="wide")`
     - Invocação imediata de `verificar_autenticacao()` de `utils.auth`.
     - Layout com colunas, containers compactos (`border=True`) e tabs.

3. **Inclusão no Menu de Roteamento:**
   - Atualizar [`pages_sections.toml`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/pages_sections.toml) inserindo:
     ```toml
     [[pages]]
     path = "./pages/<modulo>.py"
     name = "<Título da Página>"
     icon = "<Ícone>"
     ```

4. **Verificação de Métodos no Repositório:**
   - Checar se as operações de banco necessárias já existem em [`core/repository.py`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py).
   - Se não existirem, implementar os métodos estáticos correspondentes respeitando context managers e eager loading.

5. **Validação:**
   - Executar validação de sintaxe e dependências para garantir ausência de erros de importação.
