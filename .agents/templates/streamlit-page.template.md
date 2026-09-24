# Template: Página Streamlit Padronizada

Esqueleto copiável para criação de novas páginas no sistema **SVVDST**.

```python
import streamlit as st
from utils.auth import verificar_autenticacao
from core.repository import CatalogoRepository, LoteRepository

# 1. Configuração da Página
st.set_page_config(
    page_title="<TituloDaPagina>",
    page_icon="<Icone>",
    layout="wide"
)

# 2. Barreira de Autenticação Obrigatória
verificar_autenticacao()

# 3. Cabeçalho Principal (sem emojis decorativos)
st.title("<TituloDaPagina>")
st.caption("<SubtituloOuDescricaoDaPagina>")

# 4. Estado da Sessão (se necessário)
if "<chave_estado>" not in st.session_state:
    st.session_state["<chave_estado>"] = None

# 5. Estrutura de Abas / Seções
tab_listagem, tab_cadastro = st.tabs(["Listagem", "Novo Registro"])

with tab_listagem:
    st.subheader("Registros Cadastrados")
    try:
        dados = CatalogoRepository.<metodo_listagem>()
        if not dados:
            st.info("Nenhum registro encontrado.")
        else:
            for item in dados:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{item.nome}**")
                    with col2:
                        with st.popover("Ações"):
                            st.write("Editar ou remover:")
                            if st.button("Excluir", key=f"btn_del_{item.id}", type="secondary"):
                                CatalogoRepository.<metodo_deletar>(item.id)
                                st.success("Removido com sucesso!")
                                st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

with tab_cadastro:
    with st.form("form_novo_<entidade>", clear_on_submit=True):
        st.subheader("Preencha as informações:")
        campo_nome = st.text_input("Nome", placeholder="Ex: Modelo A")
        
        btn_salvar = st.form_submit_button("Salvar", type="primary", use_container_width=True)
        if btn_salvar:
            if not campo_nome.strip():
                st.error("O campo Nome é obrigatório.")
            else:
                CatalogoRepository.<metodo_salvar>(campo_nome.strip())
                st.success("Cadastrado com sucesso!")
                st.rerun()
```
