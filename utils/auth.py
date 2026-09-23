import streamlit as st


def verificar_autenticacao() -> bool:
    """
    Verifica se o acesso está autenticado.
    Se 'APP_PASSWORD' estiver definida nos secrets:
      - Exige a senha para qualquer acesso.
      - Adiciona botão '🚪 Sair do Sistema' na barra lateral.
      - Interrompe a execução (st.stop()) caso não esteja autenticado.
    Se 'APP_PASSWORD' não estiver configurada, o acesso é livre.
    """
    senha_mestra = None
    try:
        if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
            senha_mestra = st.secrets["APP_PASSWORD"]
    except Exception:
        senha_mestra = None

    # Se não houver senha definida nos secrets, o acesso é livre
    if not senha_mestra:
        return True

    # Se já autenticado na sessão atual
    if st.session_state.get("auth_ok", False):
        # Renderiza o botão de logout na barra lateral
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Sair do Sistema", use_container_width=True, key="btn_global_logout"):
                st.session_state["auth_ok"] = False
                st.rerun()
        return True

    # Caso não autenticado: limpa tela e exibe login centralizado
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

    # Interrompe a execução de todo o restante da página
    st.stop()
    return False
