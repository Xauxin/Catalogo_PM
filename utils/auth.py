import os
from typing import Any, Dict, Optional, Tuple
import streamlit as st

from core.repository import UsuarioRepository

# Hierarquia de permissões (quanto maior o número, mais privilégios)
HIERARQUIA_ROLES = {
    "admin": 3,
    "cliente": 2,
    "visitante": 1,
}


def obter_senha_mestra() -> Optional[str]:
    """Retorna a senha mestra configurada em st.secrets ou variáveis de ambiente."""
    try:
        if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
            return st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    return os.environ.get("APP_PASSWORD")


def obter_supabase_config() -> Tuple[Optional[str], Optional[str]]:
    """Obtém SUPABASE_URL e SUPABASE_ANON_KEY dos secrets ou ambiente, normalizando o formato."""
    url = None
    key = None
    try:
        if hasattr(st, "secrets"):
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        pass

    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_ANON_KEY")

    if url:
        url = url.strip()
        # Normaliza caso tenha sido colada a URL de REST (/rest/v1) ou barras finais
        url = url.split("/rest/v1")[0].split("/auth/v1")[0].rstrip("/")

    if key:
        key = key.strip()

    return url, key


def obter_app_url() -> str:
    """Retorna a URL base configurada para retorno do fluxo OAuth."""
    try:
        if hasattr(st, "secrets") and "APP_URL" in st.secrets:
            return st.secrets["APP_URL"].strip().rstrip("/")
    except Exception:
        pass
    # Porta padrão atual da aplicação (8502)
    return "http://localhost:8502"


def obter_supabase_client():
    """Cria e reutiliza uma instância do cliente oficial Supabase."""
    url, key = obter_supabase_config()
    if not url or not key:
        return None

    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        print(f"⚠️ Erro ao inicializar cliente Supabase: {e}")
        return None


def tem_permissao(role_usuario: str, role_minima: str) -> bool:
    """Verifica se a role do usuário atende ao nível mínimo exigido."""
    peso_usuario = HIERARQUIA_ROLES.get((role_usuario or "").lower(), 0)
    peso_minimo = HIERARQUIA_ROLES.get((role_minima or "").lower(), 0)
    return peso_usuario >= peso_minimo


def obter_usuario_atual() -> Optional[Dict[str, Any]]:
    """Retorna o dicionário de dados do usuário autenticado na sessão."""
    return st.session_state.get("usuario")


def obter_role_usuario() -> str:
    """Retorna a role do usuário logado ('admin', 'cliente') ou 'visitante'."""
    usuario = obter_usuario_atual()
    if usuario and usuario.get("role"):
        return usuario["role"]
    # Se autenticado sem usuário definido (modo senha mestra)
    if st.session_state.get("auth_ok", False):
        return "admin"
    return "visitante"


def login_com_senha_mestra(senha: str) -> bool:
    """Autentica o usuário local com perfil de administrador via senha mestra."""
    senha_mestra = obter_senha_mestra()
    if senha_mestra and senha == senha_mestra:
        st.session_state["auth_ok"] = True
        st.session_state["usuario"] = {
            "id": "admin-local",
            "email": "admin@svvdst.local",
            "nome": "Administrador Local",
            "role": "admin",
            "foto_url": None,
            "ativo": True,
        }
        return True
    return False


from collections import deque
from pathlib import Path

_HISTORICO_CODE_VERIFIERS = deque(maxlen=20)
_PKCE_FILE = Path(__file__).resolve().parent.parent / ".agents" / ".pkce_verifier.tmp"


def _registrar_verifier(verifier: str):
    """Armazena o code_verifier do PKCE em memória, sessão e arquivo temporário."""
    if not verifier:
        return
    if verifier not in _HISTORICO_CODE_VERIFIERS:
        _HISTORICO_CODE_VERIFIERS.append(verifier)
    try:
        st.session_state["supabase_code_verifier"] = verifier
    except Exception:
        pass
    try:
        _PKCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PKCE_FILE.write_text(verifier, encoding="utf-8")
    except Exception:
        pass


def _obter_verifiers() -> list[str]:
    """Retorna os verifiers válidos conhecidos em ordem de prioridade."""
    candidatos = []
    try:
        s_verifier = st.session_state.get("supabase_code_verifier")
        if s_verifier:
            candidatos.append(s_verifier)
    except Exception:
        pass
    try:
        if _PKCE_FILE.exists():
            f_val = _PKCE_FILE.read_text(encoding="utf-8").strip()
            if f_val and f_val not in candidatos:
                candidatos.append(f_val)
    except Exception:
        pass
    for v in reversed(_HISTORICO_CODE_VERIFIERS):
        if v not in candidatos:
            candidatos.append(v)
    return candidatos


def gerar_url_oauth(provider: str, redirect_to: str) -> Optional[str]:
    """
    Gera a URL de login do provedor OAuth (ex: 'google', 'facebook' para Meta)
    através do Supabase Auth garantindo o parâmetro apikey para acesso via navegador
    e persistindo o code_verifier para o fluxo PKCE.
    """
    client = obter_supabase_client()
    url_base, key = obter_supabase_config()
    if not client or not key:
        return None

    try:
        # provider aceita 'google', 'facebook' (Meta), etc.
        res = client.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": redirect_to,
            }
        })

        # Salva o code_verifier gerado pelo cliente Supabase para validação no retorno
        verifier = client.auth._storage.get_item(f"{client.auth._storage_key}-code-verifier")
        if verifier:
            _registrar_verifier(verifier)

        url_gerada = getattr(res, "url", None)
        if url_gerada:
            import urllib.parse
            parsed = urllib.parse.urlparse(url_gerada)
            qs = urllib.parse.parse_qs(parsed.query)
            if "apikey" not in qs:
                sep = "&" if "?" in url_gerada else "?"
                url_gerada = f"{url_gerada}{sep}apikey={key}"
        return url_gerada
    except Exception as e:
        print(f"⚠️ Erro ao gerar URL OAuth para {provider}: {e}")
        return None


def processar_codigo_oauth(auth_code: str) -> Optional[Dict[str, Any]]:
    """
    Troca o authorization code retornado pelo provedor OAuth por uma sessão válida
    no Supabase Auth usando o code_verifier do PKCE e sincroniza o perfil no banco.
    """
    client = obter_supabase_client()
    if not client:
        return None

    verifiers = _obter_verifiers()
    res = None
    ultimo_erro = None

    for v in verifiers:
        try:
            res = client.auth.exchange_code_for_session({
                "auth_code": auth_code,
                "code_verifier": v,
            })
            if res and res.user:
                break
        except Exception as e:
            ultimo_erro = e
            continue

    if not res or not res.user:
        if ultimo_erro:
            print(f"⚠️ Erro ao processar retorno OAuth com verifiers ({len(verifiers)} testados): {ultimo_erro}")
        return None

    try:
        # Limpa arquivo temporário após uso bem-sucedido
        _PKCE_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    try:
        user = res.user
        metadata = getattr(user, "user_metadata", {}) or {}

        user_id = str(user.id)
        email = str(user.email or metadata.get("email") or f"{user_id}@auth.supabase")
        nome = metadata.get("full_name") or metadata.get("name") or metadata.get("user_name")
        foto_url = metadata.get("avatar_url") or metadata.get("picture")

        # Registra ou atualiza no banco via repositório
        perfil = UsuarioRepository.salvar_ou_atualizar(
            usuario_id=user_id,
            email=email,
            nome=nome,
            foto_url=foto_url,
            role_padrao="cliente",
        )

        if not perfil.ativo:
            return None

        dados_sessao = {
            "id": perfil.id,
            "email": perfil.email,
            "nome": perfil.nome or email.split("@")[0].title(),
            "role": perfil.role,
            "foto_url": perfil.foto_url,
            "ativo": perfil.ativo,
        }

        st.session_state["auth_ok"] = True
        st.session_state["usuario"] = dados_sessao
        return dados_sessao
    except Exception as e:
        print(f"⚠️ Erro ao gravar perfil do usuário: {e}")
        return None


def verificar_autenticacao(role_minima: Optional[str] = None) -> bool:
    """
    Barreira de autenticação mandatória para subpáginas do Streamlit.
    - Se role_minima for None ou 'visitante': acesso público liberado.
    - Se role_minima for 'cliente': exige cadastro/login.
    - Se role_minima for 'admin': exige privilégios de administrador.
    """
    if role_minima in [None, "visitante"]:
        return True

    autenticado = st.session_state.get("auth_ok", False)
    senha_mestra = obter_senha_mestra()
    url, key = obter_supabase_config()

    # Caso em desenvolvimento sem senhas ou chaves configuradas
    if not autenticado and not senha_mestra and not (url and key):
        return True

    if not autenticado:
        st.error("🔒 Acesso restrito. Faça login ou cadastre-se para acessar este módulo.")
        st.stop()
        return False

    usuario = obter_usuario_atual()
    if usuario and not usuario.get("ativo", True):
        st.error("⛔ Sua conta foi desativada temporariamente pelo administrador.")
        st.stop()
        return False

    role_atual = obter_role_usuario()
    if not tem_permissao(role_atual, role_minima):
        st.error(
            f"⛔ Acesso negado. Este módulo exige permissão de **{role_minima.capitalize()}** "
            f"(seu perfil atual é **{role_atual.capitalize()}**)."
        )
        st.stop()
        return False

    return True


def fazer_logout():
    """Encerra a sessão atual e recarrega a aplicação."""
    client = obter_supabase_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
