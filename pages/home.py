import streamlit as st
from utils.auth import verificar_autenticacao

verificar_autenticacao()

st.title("Home")
