import streamlit as st

from utils.auth import (
    fazer_logout,
    gerar_url_oauth,
    login_com_senha_mestra,
    obter_app_url,
    obter_role_usuario,
    obter_senha_mestra,
    obter_supabase_config,
    obter_usuario_atual,
)

st.set_page_config(page_title="Entrar no SVVDST", page_icon="🔑", layout="wide")

autenticado = st.session_state.get("auth_ok", False)
usuario = obter_usuario_atual()
role_atual = obter_role_usuario()

st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 1.4, 1])

with c2:
    with st.container(border=True):
        if autenticado:
            st.success(f"Você já está conectado como **{role_atual.capitalize()}**.")
            nome_u = usuario.get("nome") if usuario else "Administrador"
            email_u = usuario.get("email") if usuario else ""
            st.markdown(f"**Usuário:** {nome_u} ({email_u})")
            
            c_ir, c_sair = st.columns(2)
            with c_ir:
                if role_atual == "admin":
                    if st.button("Ir para o Painel ➔", type="primary", width="stretch", key="btn_login_ir_painel"):
                        st.switch_page("pages/home.py")
                else:
                    if st.button("Ir para o Catálogo ➔", type="primary", width="stretch", key="btn_login_ir_cat"):
                        st.switch_page("pages/pecas.py")
            with c_sair:
                if st.button("Sair da Conta", width="stretch", key="btn_login_sair"):
                    fazer_logout()
        else:
            st.subheader("Entrar ou Cadastrar-se")
            st.caption("Acesse sua conta para desbloquear filtros avançados e personalização de bordados.")

            url_supa, key_supa = obter_supabase_config()
            redirect_url = obter_app_url()

            if url_supa and key_supa:
                url_google = gerar_url_oauth("google", redirect_url)
                url_meta = gerar_url_oauth("facebook", redirect_url)

                col_g, col_m = st.columns(2)
                with col_g:
                    if url_google:
                        st.link_button("🔵 Google", url_google, width="stretch")
                with col_m:
                    if url_meta:
                        st.link_button("🔷 Meta", url_meta, width="stretch")

                st.markdown(
                    "<div style='text-align:center; color:#888; font-size:12px; margin:12px 0 8px 0;'>── ou com senha de acesso ──</div>",
                    unsafe_allow_html=True,
                )

            senha_mestra = obter_senha_mestra()
            senha_digitada = st.text_input("Senha de Acesso", type="password", key="input_senha_login_page")
            if st.button("Entrar no Sistema", type="primary", width="stretch", key="btn_entrar_login_page"):
                if senha_mestra and login_com_senha_mestra(senha_digitada):
                    st.rerun()
                elif not senha_mestra:
                    st.session_state["auth_ok"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
