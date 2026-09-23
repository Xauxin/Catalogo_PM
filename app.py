import streamlit as st
from st_pages import get_nav_from_toml

from utils.ecosystem_data import load_ecosystem_data

st.set_page_config(layout="wide")

FONTES_DISPONIVEIS, ESPECIALIDADES_PRONTAS, ESPACAMENTO_LOCAL = load_ecosystem_data()


def verificar_autenticacao():
    """Se APP_PASSWORD estiver configurada em st.secrets, exige senha para liberar o sistema."""
    senha_mestra = None
    try:
        if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
            senha_mestra = st.secrets["APP_PASSWORD"]
    except Exception:
        senha_mestra = None

    if not senha_mestra:
        return True

    if st.session_state.get("auth_ok", False):
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.container(border=True):
            st.subheader("🔒 Acesso Restrito")
            st.caption("Digite a senha de acesso para continuar:")
            senha_digitada = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Entrar no Sistema", type="primary", use_container_width=True):
                if senha_digitada == senha_mestra:
                    st.session_state["auth_ok"] = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta. Tente novamente.")
    return False


if not verificar_autenticacao():
    st.stop()

# Navegação entre páginas
nav = get_nav_from_toml("pages_sections.toml")
pg = st.navigation(nav)
st.title(pg.title)
pg.run()
