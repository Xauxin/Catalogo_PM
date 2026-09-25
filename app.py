import streamlit as st
import toml
from st_pages import get_nav_from_toml

from utils.auth import (
    fazer_logout,
    gerar_url_oauth,
    login_com_senha_mestra,
    obter_app_url,
    obter_role_usuario,
    obter_senha_mestra,
    obter_supabase_config,
    obter_usuario_atual,
    processar_codigo_oauth,
)
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

# =====================================================================
# 1. PROCESSAMENTO DE RETORNO OAUTH (GOOGLE / META)
# =====================================================================
codigo_oauth = st.query_params.get("code")
if codigo_oauth and not st.session_state.get("auth_ok", False):
    with st.spinner("Validando autenticação..."):
        dados_usuario = processar_codigo_oauth(codigo_oauth)
        if dados_usuario:
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Não foi possível autenticar através do provedor. Verifique se sua conta está ativa.")


# =====================================================================
# 2. ROTEAMENTO DINÂMICO DE PÁGINAS POR PAPEL (RBAC)
# =====================================================================
def carregar_paginas_por_role(role_usuario: str):
    """
    Retorna as páginas de acordo com a role do usuário:
    - visitante: Catálogo de Bordados (vitrine aberta sem filtros) e Entrar/Cadastrar.
    - cliente: Catálogo de Bordados (como Home com busca e filtros) e Gerar Bordado.
    - admin: Acesso total a todas as telas operacionais e administrativas.
    """
    if role_usuario == "visitante":
        return [
            st.Page("pages/pecas.py", title="Catálogo de Bordados", icon="🏷️", default=True),
            st.Page("pages/login.py", title="Entrar / Cadastrar", icon="🔑"),
        ]
    elif role_usuario == "cliente":
        return [
            st.Page("pages/pecas.py", title="Catálogo de Bordados", icon="🏷️", default=True),
            st.Page("pages/gerar_bordado.py", title="Gerar Bordado", icon="🖊"),
        ]
    else:  # admin
        try:
            return get_nav_from_toml("pages_sections.toml")
        except Exception:
            return [
                st.Page("pages/home.py", title="Home", icon="🏠", default=True),
                st.Page("pages/visualizar_lotes.py", title="Visualizar Lotes", icon="📑"),
                st.Page("pages/gerar_bordado_em_lote.py", title="Gerar Lotes de Bordado", icon="📋"),
                st.Page("pages/gerar_bordado.py", title="Gerar Bordado", icon="🖊"),
                st.Page("pages/gerar_lote.py", title="Gerar Lote", icon="📦"),
                st.Page("pages/pecas.py", title="Catálogo", icon="🏷️"),
                st.Page("pages/configuracoes.py", title="Configurações", icon="⚙️"),
            ]


# =====================================================================
# 3. NAVEGAÇÃO E SESSÃO DO USUÁRIO
# =====================================================================
role_atual = obter_role_usuario()
usuario = obter_usuario_atual()
autenticado = st.session_state.get("auth_ok", False)

nav_filtrada = carregar_paginas_por_role(role_atual)
pg = st.navigation(nav_filtrada)

with st.sidebar:
    st.markdown("---")
    if autenticado:
        nome_user = usuario.get("nome") if usuario else ("Administrador" if role_atual == "admin" else "Cliente")
        email_user = usuario.get("email") if usuario else ""
        badge_cor = "#e63946" if role_atual == "admin" else "#2a9d8f"
        badge_label = "👑 Admin" if role_atual == "admin" else "👤 Cliente"

        st.markdown(
            f"""
            <div style="padding:8px 12px; background:rgba(128,128,128,0.1); border-radius:6px; margin-bottom:8px;">
                <div style="font-weight:600; font-size:13px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{nome_user}</div>
                <div style="font-size:11px; color:#888; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{email_user}</div>
                <div style="margin-top:4px;"><span style="background:{badge_cor}; color:#fff; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:600;">{badge_label}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sair da Conta", width="stretch", key="btn_global_logout"):
            fazer_logout()
    else:
        st.markdown(
            """
            <div style="padding:10px 12px; background:rgba(42,157,143,0.12); border-radius:8px; border:1px solid rgba(42,157,143,0.3); margin-bottom:10px;">
                <div style="font-weight:600; font-size:13px; color:#2a9d8f;">🌐 Modo Visitante</div>
                <div style="font-size:11px; color:#aaa; margin-top:4px;">Faça login para desbloquear filtros de busca e geração de bordados.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Entrar / Cadastrar", type="primary", width="stretch", key="btn_side_login"):
            st.switch_page("pages/login.py")

# Executa a página selecionada
pg.run()
