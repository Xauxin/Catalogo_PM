# Regra de Compatibilidade de Banco de Dados Híbrido

## 1. Declaração da Regra
O sistema deve operar de maneira 100% intercambiável e transparente entre **SQLite local** (`banco.db` para desenvolvimento) e **PostgreSQL gerenciado** (Supabase / Neon para ambiente de homologação/produção).

---

## 2. Diretrizes Mandatórias

1. **Zero Tipos Proprietários Incompatíveis:**
   * É proibido o uso de tipos de coluna exclusivos do PostgreSQL (como `JSONB`, `ARRAY` nativo do Postgres, tipos de rede ou enumerações nativas de dialeto) que não possuam fallback automático para strings ou JSON plano no SQLite.
   * Coleções ou listas de dados devem ser serializadas em texto (ex: strings delimitadas por vírgula ou JSON stringificado em campos `str`), ou estruturadas como tabelas filhas relacionais via foreign key.

2. **Prevenção de Locks e Concorrência:**
   * No SQLite local, o engine é inicializado com `connect_args={"check_same_thread": False}` para suportar o modelo de threads do Streamlit.
   * No PostgreSQL remoto, conexões inativas são recicladas preventivamente através de `pool_pre_ping=True`.

3. **Fallback Automático Resiliente:**
   * Se a variável de ambiente `DATABASE_URL` ou o secret do Streamlit falhar ou estiver inacessível, o módulo `core/database.py` **deve** realizar fallback silencioso para o banco SQLite local (`banco.db`), emitindo log de aviso informativo sem derrubar a aplicação.

4. **Tratamento de Reloads do Streamlit:**
   * Todos os modelos declarados em `core/models.py` devem definir explicitamente `__table_args__ = {"extend_existing": True}` para evitar colisões no registro de metadados do SQLAlchemy durante os reloads dinâmicos de página do Streamlit.
