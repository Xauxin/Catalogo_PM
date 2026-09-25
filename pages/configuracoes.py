import streamlit as st

from core.repository import UsuarioRepository
from utils.auth import obter_supabase_config, obter_usuario_atual, verificar_autenticacao

# Barreira de Autenticação Rígida: apenas administradores podem acessar
verificar_autenticacao(role_minima="admin")

usuario_logado = obter_usuario_atual() or {}

st.title("⚙️ Configurações do Sistema")
st.caption("Painel centralizado de administração, controle de acesso e parâmetros do SVVDST.")

tab_roles, tab_integracoes, tab_geral = st.tabs([
    "👥 Perfis & Permissões (Roles)",
    "🔑 Provedores OAuth & Banco",
    "🏭 Parâmetros da Confecção",
])

# =====================================================================
# TAB 1: PERFIS & PERMISSÕES (ROLES)
# =====================================================================
with tab_roles:
    st.markdown("### Controle de Acesso Baseado em Funções (RBAC)")
    st.info(
        "**Níveis de Acesso:**\n"
        "- 👑 **Admin:** Acesso irrestrito a todas as telas, configurações, usuários, gestão de lotes, catálogo de peças e acervo.\n"
        "- 👤 **Cliente:** Acesso ao Catálogo de Bordados (como tela inicial com busca e filtros completos) e ao Gerador de Bordado.\n"
        "- 🌐 **Visitante:** Acesso público ao Catálogo de Bordados (sem filtros de busca) para incentivar o cadastro no sistema."
    )

    usuarios = UsuarioRepository.listar_usuarios()

    # Métricas de usuários
    total_users = len(usuarios)
    total_admins = sum(1 for u in usuarios if u.role == "admin")
    total_operadores = sum(1 for u in usuarios if u.role == "operador")
    total_clientes = sum(1 for u in usuarios if u.role == "cliente")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Usuários", total_users)
    m2.metric("Administradores", total_admins)
    m3.metric("Operadores", total_operadores)
    m4.metric("Clientes", total_clientes)

    st.markdown("---")

    col_edit, col_novo = st.columns([1.2, 1])

    with col_edit:
        with st.container(border=True):
            st.subheader("Editar Perfil de Usuário")
            if not usuarios:
                st.info("Nenhum usuário cadastrado até o momento.")
            else:
                opcoes_usuarios = {
                    f"{u.nome or 'Sem nome'} ({u.email}) - [{u.role.upper()}]": u
                    for u in usuarios
                }
                selecao = st.selectbox(
                    "Selecione o usuário para gerenciar",
                    options=list(opcoes_usuarios.keys()),
                    key="sel_usuario_gerenciar",
                )
                usuario_alvo = opcoes_usuarios[selecao]

                c_role, c_ativo = st.columns([1.5, 1])
                with c_role:
                    roles_disp = ["admin", "cliente", "visitante"]
                    idx_role = roles_disp.index(usuario_alvo.role) if usuario_alvo.role in roles_disp else 1
                    nova_role = st.selectbox(
                        "Papel / Função (Role)",
                        options=roles_disp,
                        index=idx_role,
                        format_func=lambda r: f"👑 {r.capitalize()}" if r == "admin" else (f"👤 {r.capitalize()}" if r == "cliente" else f"👀 {r.capitalize()}"),
                        key="sel_nova_role",
                    )
                with c_ativo:
                    novo_status = st.toggle(
                        "Conta Ativa",
                        value=usuario_alvo.ativo,
                        key="toggle_status_ativo",
                        help="Se desativado, o usuário será impedido de acessar o sistema.",
                    )

                # Prevenção de bloqueio: impedir que o admin logado remova a própria permissão de admin
                is_proprio_usuario = (usuario_logado.get("id") == usuario_alvo.id)
                if is_proprio_usuario and nova_role != "admin":
                    st.warning("⚠️ Você não pode remover sua própria permissão de Administrador.")

                if st.button("Salvar Alterações de Acesso", type="primary", width="stretch", key="btn_salvar_role"):
                    if is_proprio_usuario and nova_role != "admin":
                        st.error("Operação cancelada: você não pode rebaixar seu próprio perfil.")
                    else:
                        ok_role = UsuarioRepository.atualizar_role(usuario_alvo.id, nova_role)
                        ok_status = UsuarioRepository.atualizar_status_ativo(usuario_alvo.id, novo_status)
                        if ok_role and ok_status:
                            st.success(f"Permissões do usuário '{usuario_alvo.email}' atualizadas com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar dados do usuário.")

    with col_novo:
        with st.container(border=True):
            st.subheader("Pré-cadastrar Novo Perfil")
            st.caption(
                "Cadastre um e-mail antes do primeiro login. Quando a pessoa entrar via Google/Meta, "
                "já assumirá automaticamente o papel configurado."
            )
            email_pre = st.text_input("E-mail corporativo ou pessoal", placeholder="usuario@gmail.com", key="input_email_pre")
            nome_pre = st.text_input("Nome do colaborador ou cliente (opcional)", placeholder="Nome Completo", key="input_nome_pre")
            role_pre = st.selectbox(
                "Papel pré-atribuído",
                options=["cliente", "admin", "visitante"],
                format_func=lambda r: f"👤 {r.capitalize()}" if r == "cliente" else (f"👑 {r.capitalize()}" if r == "admin" else f"👀 {r.capitalize()}"),
                key="sel_role_pre",
            )

            if st.button("Pré-cadastrar Acesso", width="stretch", key="btn_salvar_pre_cadastro"):
                if not email_pre.strip() or "@" not in email_pre:
                    st.error("Informe um e-mail válido para o pré-cadastro.")
                else:
                    existente = UsuarioRepository.obter_por_email(email_pre)
                    if existente:
                        st.warning(f"O e-mail '{email_pre}' já está cadastrado com o papel '{existente.role}'.")
                    else:
                        import uuid
                        novo_id = f"pre_{uuid.uuid4().hex[:12]}"
                        UsuarioRepository.salvar_ou_atualizar(
                            usuario_id=novo_id,
                            email=email_pre,
                            nome=nome_pre if nome_pre.strip() else None,
                            role_padrao=role_pre,
                        )
                        st.success(f"Acesso pré-configurado para '{email_pre}' como {role_pre.capitalize()}!")
                        st.rerun()

    st.markdown("---")
    st.subheader("Lista Geral de Usuários do Sistema")

    if usuarios:
        dados_tabela = []
        for u in usuarios:
            status_txt = "🟢 Ativo" if u.ativo else "🔴 Inativo"
            badge_role = (
                "👑 Admin" if u.role == "admin"
                else ("👤 Cliente" if u.role == "cliente" else "👀 Visitante")
            )
            ultimo_login_fmt = (
                u.ultimo_login.strftime("%d/%m/%Y %H:%M") if u.ultimo_login else "Nunca logou"
            )
            criado_fmt = (
                u.criado_em.strftime("%d/%m/%Y") if u.criado_em else "-"
            )

            dados_tabela.append({
                "Nome": u.nome or "Não informado",
                "E-mail": u.email,
                "Papel (Role)": badge_role,
                "Status": status_txt,
                "Último Acesso": ultimo_login_fmt,
                "Cadastrado em": criado_fmt,
            })

        st.dataframe(dados_tabela, width="stretch", hide_index=True)
    else:
        st.info("Nenhum usuário registrado até o momento.")

# =====================================================================
# TAB 2: PROVEDORES OAUTH & BANCO
# =====================================================================
with tab_integracoes:
    st.subheader("Status das Integrações de Autenticação")
    st.caption("Verificação dos serviços de segurança configurados para o SVVDST.")

    url_supa, key_supa = obter_supabase_config()
    tem_supabase = bool(url_supa and key_supa)

    c_supa, c_google, c_meta = st.columns(3)

    with c_supa:
        with st.container(border=True):
            st.markdown("#### Supabase Auth")
            if tem_supabase:
                st.success("Conectado e Ativo ✅")
                st.code(f"URL: {url_supa[:25]}...", language="text")
            else:
                st.warning("Pendente de Configuração ⚠️")
                st.caption("Adicione `SUPABASE_URL` e `SUPABASE_ANON_KEY` ao seu `.streamlit/secrets.toml`.")

    with c_google:
        with st.container(border=True):
            st.markdown("#### Google OAuth")
            if tem_supabase:
                st.info("Gerenciado pelo Supabase")
                st.caption(
                    "Ative o provedor **Google** em *Authentication > Providers* no painel do Supabase "
                    "fornecendo o Client ID e Secret do Google Cloud Console."
                )
            else:
                st.caption("Requer configuração prévia do Supabase.")

    with c_meta:
        with st.container(border=True):
            st.markdown("#### Meta (Facebook) OAuth")
            if tem_supabase:
                st.info("Gerenciado pelo Supabase")
                st.caption(
                    "Ative o provedor **Facebook** em *Authentication > Providers* no painel do Supabase "
                    "fornecendo o App ID e App Secret do Meta for Developers."
                )
            else:
                st.caption("Requer configuração prévia do Supabase.")

# =====================================================================
# TAB 3: PARÂMETROS DA CONFECÇÃO
# =====================================================================
with tab_geral:
    st.subheader("Parâmetros Gerais do Negócio")
    st.caption("Definições padrão para cálculos de bordado e matrizes.")

    with st.container(border=True):
        p1, p2 = st.columns(2)
        with p1:
            st.text_input("Nome da Confecção", value="SVVDST Bordados Computadorizados", disabled=True, key="cfg_nome_empresa")
            st.number_input("Preço Base Padrão de Matriz Pronta (R$)", value=15.00, step=1.0, format="%.2f", disabled=True, key="cfg_preco_base")
        with p2:
            st.text_input("Formato Padrão de Exportação de Matriz", value=".DST / .PES", disabled=True, key="cfg_formato_padrao")
            st.caption("ℹ️ Configurações avançadas de precificação e custos serão integradas nas próximas versões.")
