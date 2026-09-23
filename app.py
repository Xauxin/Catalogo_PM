import streamlit as st
from st_pages import get_nav_from_toml

from utils.auth import verificar_autenticacao
from utils.ecosystem_data import load_ecosystem_data

st.set_page_config(layout="wide")

FONTES_DISPONIVEIS, ESPECIALIDADES_PRONTAS, ESPACAMENTO_LOCAL = load_ecosystem_data()

# Bloqueia a aplicação inteira se não autenticado
verificar_autenticacao()

# Navegação entre páginas
nav = get_nav_from_toml("pages_sections.toml")
pg = st.navigation(nav)
st.title(pg.title)
pg.run()
