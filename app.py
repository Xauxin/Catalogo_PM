import streamlit as st
from st_pages import get_nav_from_toml

from utils.auth import obter_senha_mestra
from utils.ecosystem_data import load_ecosystem_data

st.set_page_config(layout="wide")

FONTES_DISPONIVEIS, ESPECIALIDADES_PRONTAS, ESPACAMENTO_LOCAL = load_ecosystem_data()


def pagina_login():
    """Tela de login centralizada exibida quando o usuário não estiver autenticado."""
    senha_mestra = obter_senha_mestra()
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.container(border=True):
            st.subheader("🔒 Acesso Restrito")
            st.caption("Digite a senha de acesso da confecção para entrar:")
            senha_digitada = st.text_input("Senha", type="password", key="input_senha_sistema")
            if st.button("Entrar no Sistema", type="primary", use_container_width=True, key="btn_entrar_sistema"):
                if senha_digitada == senha_mestra:
                    st.session_state["auth_ok"] = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta. Tente novamente.")


senha_mestra = obter_senha_mestra()
autenticado = st.session_state.get("auth_ok", False) or (senha_mestra is None)

if not autenticado:
    # Quando NÃO autenticado: st.navigation oculta todas as páginas do sistema
    login_page = st.Page(pagina_login, title="Acesso Restrito", icon="🔒")
    pg = st.navigation([login_page], position="hidden")
else:
    # Quando AUTENTICADO: carrega a navegação completa com os ícones do pages_sections.toml
    nav = get_nav_from_toml("pages_sections.toml")
    pg = st.navigation(nav)

    # Exibe o botão de logout na barra lateral se houver senha configurada
    if senha_mestra:
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Sair do Sistema", use_container_width=True, key="btn_global_logout"):
                st.session_state["auth_ok"] = False
                st.rerun()

st.title(pg.title)
pg.run()
