from datetime import date
import pandas as pd
import streamlit as st

from core.repository import CatalogoRepository, LoteRepository
from utils.auth import verificar_autenticacao

verificar_autenticacao(role_minima="admin")

st.title("Painel de Controle")
st.caption("Visão geral em tempo real de pedidos, lotes de produção e acervo técnico da confecção.")

# =====================================================================
# 1. CARREGAMENTO DOS DADOS (CONSULTAS OTIMIZADAS)
# =====================================================================
try:
    lotes = LoteRepository.listar_todos_os_lotes()
except Exception:
    lotes = []

try:
    bordados = CatalogoRepository.listar_templates_bordado()
except Exception:
    bordados = []

try:
    templates_pecas = CatalogoRepository.listar_templates()
except Exception:
    templates_pecas = []

# =====================================================================
# 2. MÉTRICAS PRINCIPAIS (PRIMEIRA DOBRA)
# =====================================================================
total_lotes = len(lotes)
lotes_em_producao = sum(1 for l in lotes if l.status == "Em Produção")
lotes_pendentes = sum(1 for l in lotes if l.status == "Pendente")
lotes_concluidos = sum(1 for l in lotes if l.status == "Concluído")
faturamento_total = sum(l.preco_total for l in lotes)
total_matrizes = len(bordados)

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total de Lotes", total_lotes)
m2.metric("Em Produção", lotes_em_producao)
m3.metric("Pendentes", lotes_pendentes)
m4.metric("Concluídos", lotes_concluidos)
m5.metric("Faturamento", f"R$ {faturamento_total:,.2f}")
m6.metric("Matrizes no Acervo", total_matrizes)

st.markdown("---")

# =====================================================================
# 3. ATALHOS DE ACESSO RÁPIDO (NAVEGAÇÃO)
# =====================================================================
st.markdown("##### Acesso Rápido")
a1, a2, a3, a4 = st.columns(4)

with a1:
    with st.container(border=True):
        st.page_link(
            "pages/gerar_lote.py",
            label="Novo Pedido / Lote",
            icon="📦",
            width="stretch",
        )
        st.caption("Configurar pedido multipeças e calcular orçamento.")

with a2:
    with st.container(border=True):
        st.page_link(
            "pages/visualizar_lotes.py",
            label="Acompanhar Produção",
            icon="📑",
            width="stretch",
        )
        st.caption("Consultar histórico, detalhes e alterar status.")

with a3:
    with st.container(border=True):
        st.page_link(
            "pages/pecas.py",
            label="Catálogo Geral",
            icon="🏷️",
            width="stretch",
        )
        st.caption("Gerenciar modelos de peças e matrizes cadastradas.")

with a4:
    with st.container(border=True):
        st.page_link(
            "pages/gerar_bordado_em_lote.py",
            label="Gerar Bordados DST",
            icon="📋",
            width="stretch",
        )
        st.caption("Criar matrizes de nomes em lote com motor DST.")

st.markdown("---")

# =====================================================================
# 4. PAINEL INFORMATIVO LADO A LADO
# =====================================================================
col_pedidos, col_acervo = st.columns([1.6, 1.0], gap="medium")

with col_pedidos:
    st.markdown("##### Pedidos Recentes")
    if not lotes:
        st.info("Nenhum pedido cadastrado no momento. Inicie um novo lote pelo atalho acima.")
    else:
        # Prepara resumo tabular dos lotes mais recentes
        dados_recentes = []
        for l in lotes[:8]:
            dt_ent = l.data_entrada.strftime("%d/%m/%Y") if l.data_entrada else "-"
            dt_entreg = l.data_entrega.strftime("%d/%m/%Y") if l.data_entrega else "-"
            total_pecas = sum(p.quantidade for p in l.pecas) if l.pecas else 0
            dados_recentes.append(
                {
                    "Lote": f"#{l.id}",
                    "Cliente": l.cliente,
                    "Entrada": dt_ent,
                    "Entrega": dt_entreg,
                    "Peças": f"{total_pecas} un",
                    "Valor": l.preco_total,
                    "Status": l.status,
                }
            )

        df_recentes = pd.DataFrame(dados_recentes)
        st.dataframe(
            df_recentes,
            width="stretch",
            hide_index=True,
            column_config={
                "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Status": st.column_config.TextColumn("Status"),
            },
        )

with col_acervo:
    st.markdown("##### Resumo do Acervo")
    with st.container(border=True):
        c_mod, c_prt = st.columns(2)
        c_mod.metric("Modelos de Peças", len(templates_pecas))
        matrizes_prontas = sum(1 for b in bordados if b.matriz_pronta)
        c_prt.metric("Matrizes Prontas", matrizes_prontas)

        st.markdown(" ")
        st.markdown("**Últimas Matrizes Adicionadas**")
        if not bordados:
            st.caption("Nenhuma matriz cadastrada ainda.")
        else:
            for b in bordados[:4]:
                cat_info = f"[{b.categoria}] " if b.categoria else ""
                dim = f"{b.largura_mm:.0f}x{b.altura_mm:.0f} mm" if (b.largura_mm and b.altura_mm) else "Dim. N/A"
                st.markdown(
                    f"- **{cat_info}{b.nome}** — `{b.pontos:,} pts` | {dim}".replace(",", ".")
                )
