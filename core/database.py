import os
from sqlmodel import SQLModel, Session, create_engine

# 1. Tenta obter a URL do banco das variáveis de ambiente ou dos secrets do Streamlit
database_url = None

try:
    import streamlit as st
    if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
        database_url = st.secrets["DATABASE_URL"]
except Exception:
    pass

if not database_url:
    database_url = os.environ.get("DATABASE_URL")

# 2. Configuração do Engine
# SQLAlchemy requer URL de conexão PostgreSQL (postgresql://...), não URLs REST HTTP (https://...)
if database_url and (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    try:
        # Conexão remota (PostgreSQL) com verificação automática de conexões ociosas
        engine = create_engine(database_url, echo=False, pool_pre_ping=True)
    except Exception as err:
        print(f"⚠️ Erro ao conectar ao PostgreSQL remoto: {err}. Utilizando SQLite local.")
        sqlite_file_name = "banco.db"
        sqlite_url = f"sqlite:///{sqlite_file_name}"
        connect_args = {"check_same_thread": False}
        engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)
else:
    if database_url and database_url.startswith("http"):
        print(
            "⚠️ A URL fornecida é uma URL HTTP/REST do Supabase. "
            "Para conectar o banco via SQLAlchemy/SQLModel, utilize a Connection String URI do PostgreSQL "
            "(no painel do Supabase: Project Settings -> Database -> Connection String -> URI, começando com 'postgresql://'). "
            "Utilizando SQLite local como fallback."
        )

    # Fallback local (SQLite)
    sqlite_file_name = "banco.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


def init_db():
    """Garante que todas as tabelas estejam criadas no banco (SQLite ou PostgreSQL)."""
    import core.models  # Importa para registrar os modelos no SQLModel
    SQLModel.metadata.create_all(engine)


def get_session():
    """Retorna uma sessão ativa com o banco de dados configurado."""
    return Session(engine, expire_on_commit=False)


# Garante inicialização automática das tabelas
try:
    init_db()
except Exception as e:
    print(f"⚠️ Aviso ao inicializar tabelas: {e}")