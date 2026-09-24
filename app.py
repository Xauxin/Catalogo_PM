import streamlit as st
from st_pages import get_nav_from_toml

from utils.auth import obter_senha_mestra
from utils.ecosystem_data import load_ecosystem_data

st.set_page_config(layout="wide")

# CSS global compacto para padrão 16:9 em tela única
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.4rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 4px 12px;
        font-size: 0.85rem;
    }
    h1, h2, h3, h4, h5 {
        margin-top: 0rem !important;
        margin-bottom: 0.25rem !important;
        padding: 0rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

FONTES_DISPONIVEIS, ESPECIALIDADES_PRONTAS, ESPACAMENTO_LOCAL = load_ecosystem_data()


def pagina_login():
    """Tela de login centralizada exibida quando o usuário não estiver autenticado."""
    senha_mestra = obter_senha_mestra()
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.container(border=True):
            st.subheader("Acesso Restrito")
            st.caption("Digite a senha de acesso da confecção para entrar:")
            senha_digitada = st.text_input("Senha", type="password", key="input_senha_sistema")
            if st.button("Entrar no Sistema", type="primary", use_container_width=True, key="btn_entrar_sistema"):
                if senha_digitada == senha_mestra:
                    st.session_state["auth_ok"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")


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
            if st.button("Sair do Sistema", use_container_width=True, key="btn_global_logout"):
                st.session_state["auth_ok"] = False
                st.rerun()

# Executa a página selecionada diretamente sem duplicação de título
pg.run()
