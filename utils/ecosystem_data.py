# utils.py
from pathlib import Path
import json
import streamlit as st

FONTES_DIR = Path("./fontsfiles")
ESPC_DIR = Path("./ESPECIALIDADES_PRONTAS")
CONFIG_ESPACAMENTO = Path("espacamento_local.JSON")

@st.cache_data
def load_ecosystem_data():
    """Carrega os dados do ecossistema uma única vez e compartilha entre todas as páginas."""
    fontes = [f.name for f in FONTES_DIR.iterdir() if f.is_dir()] if FONTES_DIR.exists() else []
    espc = [f.name for f in ESPC_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".dst"] if ESPC_DIR.exists() else []
    
    espacamento = {}
    if CONFIG_ESPACAMENTO.exists():
        with open(CONFIG_ESPACAMENTO, "r", encoding="utf-8") as f:
            espacamento = json.load(f)
            
    return fontes, espc, espacamento