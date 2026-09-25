from datetime import datetime
import pandas as pd
import streamlit as st

from core.repository import LoteRepository
from utils.auth import verificar_autenticacao

st.set_page_config(page_title="Gestão de Lotes", layout="wide")

verificar_autenticacao(role_minima="admin")

st.title("Gestão e Acompanhamento de Lotes")
st.caption("Consulte pedidos cadastrados, acompanhe as peças/bordados e gerencie o status de produção.")

# =====================================================================
# 1. CARREGAMENTO DOS DADOS
# =====================================================================
try:
    lotes = LoteRepository.listar_todos_os_lotes()
except Exception as e:
    st.error(f"Erro ao consultar lotes no banco de dados: {e}")
    lotes = []

# =====================================================================
# 2. MÉTRICAS GERAIS (PRIMEIRA DOBRA)
# =====================================================================
total_lotes = len(lotes)
lotes_pendentes = sum(1 for l in lotes if l.status == "Pendente")
lotes_em_producao = sum(1 for l in lotes if l.status == "Em Produção")
lotes_concluidos = sum(1 for l in lotes if l.status == "Concluído")
faturamento_total = sum(l.preco_total for l in lotes)

c_metric1, c_metric2, c_metric3, c_metric4, c_metric5 = st.columns(5)
c_metric1.metric("Total de Lotes", total_lotes)
c_metric2.metric("Pendentes", lotes_pendentes)
c_metric3.metric("Em Produção", lotes_em_producao)
c_metric4.metric("Concluídos", lotes_concluidos)
c_metric5.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")

st.markdown("---")

# =====================================================================
# 3. FILTROS E BUSCA COMPACTOS
# =====================================================================
col_busca, col_filtro_status, col_ordem = st.columns([2, 1, 1])

with col_busca:
    termo_busca = st.text_input(
        "Buscar por Cliente",
        placeholder="Digite o nome do cliente...",
        key="input_busca_cliente",
    ).strip().lower()

with col_filtro_status:
    filtro_status = st.selectbox(
        "Filtrar por Status",
        options=["Todos", "Pendente", "Em Produção", "Concluído"],
        key="sel_filtro_status",
    )

with col_ordem:
    ordenacao = st.selectbox(
        "Ordenar por",
        options=["Mais Recentes", "Mais Antigos", "Data de Entrega", "Maior Valor"],
        key="sel_ordenacao_lotes",
    )

# Aplica filtros
lotes_filtrados = lotes

if termo_busca:
    lotes_filtrados = [l for l in lotes_filtrados if termo_busca in l.cliente.lower()]

if filtro_status != "Todos":
    lotes_filtrados = [l for l in lotes_filtrados if l.status == filtro_status]

if ordenacao == "Mais Recentes":
    lotes_filtrados.sort(key=lambda x: x.id or 0, reverse=True)
elif ordenacao == "Mais Antigos":
    lotes_filtrados.sort(key=lambda x: x.id or 0)
elif ordenacao == "Data de Entrega":
    lotes_filtrados.sort(key=lambda x: x.data_entrega)
elif ordenacao == "Maior Valor":
    lotes_filtrados.sort(key=lambda x: x.preco_total, reverse=True)

# =====================================================================
# 4. LISTAGEM DETALHADA DOS LOTES (FLUXO ABAIXO DO SCROLL)
# =====================================================================
st.subheader(f"Pedidos Cadastrados ({len(lotes_filtrados)})")

if not lotes_filtrados:
    st.info("Nenhum lote corresponde aos filtros selecionados.")
else:
    for lote in lotes_filtrados:
        data_ent_formatada = lote.data_entrada.strftime("%d/%m/%Y") if lote.data_entrada else "-"
        data_entrega_formatada = lote.data_entrega.strftime("%d/%m/%Y") if lote.data_entrega else "-"
        
        titulo_expander = (
            f"Lote #{lote.id} — {lote.cliente} | "
            f"Entrega: {data_entrega_formatada} | "
            f"R$ {lote.preco_total:,.2f} | "
            f"Status: {lote.status}"
        )

        with st.expander(titulo_expander, expanded=False):
            # Cabeçalho do Card
            c_info1, c_info2, c_info3, c_acoes = st.columns([1.5, 1.5, 1.5, 1])

            with c_info1:
                st.write(f"**Cliente:** {lote.cliente}")
                st.write(f"**Data de Entrada:** {data_ent_formatada}")

            with c_info2:
                st.write(f"**Previsão de Entrega:** {data_entrega_formatada}")
                st.write(f"**Total do Lote:** R$ {lote.preco_total:,.2f}")

            with c_info3:
                st.write(f"**Status Geral:** **{lote.status}**")
                qtd_total_pecas = sum(p.quantidade for p in lote.pecas) if lote.pecas else 0
                st.write(f"**Total de Peças Físicas:** {qtd_total_pecas} un")

            with c_acoes:
                st.write("**Ações:**")
                with st.popover("Excluir", width="stretch"):
                    st.warning(f"Deseja realmente excluir o Lote #{lote.id}?")
                    if st.button("Confirmar Exclusão", key=f"del_lote_{lote.id}", type="primary"):
                        if LoteRepository.deletar_lote(lote.id):
                            st.success(f"Lote #{lote.id} excluído com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir lote.")

            st.markdown("---")

            # Estrutura de Peças e Bordados
            if not lote.pecas:
                st.info("Este lote não possui peças vinculadas.")
            else:
                st.markdown("#### Peças e Bordados deste Pedido:")
                
                for idx_peca, peca in enumerate(lote.pecas, start=1):
                    obs_texto = f" *(Obs: {peca.observacao})*" if peca.observacao else ""
                    st.markdown(
                        f"##### Peça {idx_peca}: **{peca.quantidade}x {peca.nome}**{obs_texto} "
                        f"— Subtotal Peça: R$ {peca.preco_peca_total:,.2f} | Status Peça: **{peca.status}**"
                    )

                    if not peca.bordados:
                        st.caption("Nenhum bordado cadastrado nesta peça.")
                    else:
                        for b in peca.bordados:
                            c_local, c_tipo, c_info, c_cor, c_mtz, c_prc, c_status = st.columns(
                                [1.5, 1.2, 2.5, 1.2, 1.2, 1.2, 1.5],
                                vertical_alignment="center",
                            )

                            with c_local:
                                st.write(f"**{b.local or 'Local N/A'}**")
                            with c_tipo:
                                st.caption(f"Tipo: {b.tipo}")
                            with c_info:
                                fonte_info = f" *(Fonte: {b.fonte})*" if b.fonte else ""
                                st.write(f"**{b.informacao}**{fonte_info}")
                            with c_cor:
                                st.caption(f"Linha: {b.cor}")
                            with c_mtz:
                                mtz_texto = "Criar Nova" if b.precisa_matriz else "Pronta"
                                st.caption(f"Matriz: {mtz_texto}")
                            with c_prc:
                                total_item = (b.preco_bordado * peca.quantidade) + (b.preco_matriz or 0.0)
                                st.caption(f"R$ {total_item:,.2f}")
                            with c_status:
                                opcoes_status = ["Pendente", "Em Produção", "Concluído"]
                                status_atual_idx = (
                                    opcoes_status.index(b.status)
                                    if b.status in opcoes_status
                                    else 0
                                )
                                novo_status = st.selectbox(
                                    "Status",
                                    opcoes_status,
                                    index=status_atual_idx,
                                    key=f"status_b_{b.id}",
                                    label_visibility="collapsed",
                                )
                                if novo_status != b.status:
                                    LoteRepository.atualizar_status_bordado(b.id, novo_status)
                                    st.rerun()

                    st.markdown(" ")
