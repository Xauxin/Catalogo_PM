import streamlit as st


def obter_senha_mestra() -> str | None:
    """Retorna a senha mestra configurada em st.secrets, se existir."""
    try:
        if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
            return st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    return None


def verificar_autenticacao() -> bool:
    """Verifica se a sessão está autenticada nas subpáginas. Se não estiver, interrompe."""
    senha_mestra = obter_senha_mestra()
    if not senha_mestra:
        return True

    if not st.session_state.get("auth_ok", False):
        st.error("🔒 Acesso restrito. Faça login na página inicial para acessar este módulo.")
        st.stop()
        return False
    return True
