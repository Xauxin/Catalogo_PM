import os

import pandas as pd
import streamlit as st

from name_maker import MotorBordado
from utils.ecosystem_data import load_ecosystem_data

FONTES_DISPONIVEIS, ESPECIALIDADES_PRONTAS, ESPACAMENTO_LOCAL = load_ecosystem_data()


def limpar_lista_colunas(colunas, valores_a_remover=[]):
    if not valores_a_remover:
        return colunas
    return [col for col in colunas if col not in valores_a_remover]


def renderizar_input_dinamico(coluna_selecionada, chave_prefixo):
    config = config_colunas.get(coluna_selecionada)
    type_config = config["type_config"]  # Acessa o dicionário interno do tipo de coluna
    print(type_config)
    if type_config["type"] == "selectbox":
        return st.selectbox(
            "Valor",
            options=type_config["options"],
            key=f"{chave_prefixo}_valor",
            label_visibility="collapsed",
        )
    elif type_config["type"] == "number":
        return st.number_input(
            "Valor",
            min_value=type_config["min_value"],
            max_value=type_config["max_value"],
            step=type_config["step"],
            key=f"{chave_prefixo}_valor",
            label_visibility="collapsed",
        )
    else:
        return st.text_input(
            "Valor", key=f"{chave_prefixo}_valor", label_visibility="collapsed"
        )


# --- ESTADOS DO STREAMLIT ---
if "lote_processado" not in st.session_state:
    st.session_state.lote_processado = False
if "df_lote" not in st.session_state:
    st.session_state.df_lote = None

st.markdown("## 📦 Gerador de Bordados em Lote")

# --- PASSO 1: ENTRADA DOS NOMES ---
if not st.session_state.lote_processado:
    st.markdown("### 1. Cole a lista de nomes (um por linha):")
    texto_lotes = st.text_area(
        "Lista de Nomes",
        placeholder="João Silva\nMaria Santos\nPedro Oliveira",
        height=200,
        label_visibility="collapsed",
    )

    if st.button("Criar Tabela de Lote", type="primary"):
        if not texto_lotes.strip():
            st.warning("Insira pelo menos um nome.")
        else:
            # Transforma as linhas de texto em uma lista limpa
            nomes = [nome.strip() for nome in texto_lotes.splitlines() if nome.strip()]

            # Criamos a estrutura inicial da tabela
            dados_iniciais = {
                "Prefixo": [
                    "" for _ in nomes
                ],  # Coluna de prefixo vazia para o usuário preencher
                "Nome": nomes,
                "Fonte Nome": "",
                "Especialidade": "Nenhuma",
                "Local": "Peito",
                "Largura Max (dmm)": 1100,
                "Select": [False for _ in nomes],
            }

            # Salva o DataFrame no session_state
            st.session_state.df_lote = pd.DataFrame(dados_iniciais)
            st.session_state.lote_processado = True
            st.rerun()

# --- PASSO 2: A TABELA EDITÁVEL (st.data_editor) ---
else:
    config_colunas = {
        "Prefixo": st.column_config.TextColumn("Prefixo", width=50),
        "Nome": st.column_config.TextColumn(
            "Nome*", required=True, width="large", alignment="center"
        ),
        "Fonte Nome": st.column_config.SelectboxColumn(
            "Fonte*", options=FONTES_DISPONIVEIS, required=True, width="small"
        ),
        "Especialidade": st.column_config.SelectboxColumn(
            "Espc. Pronta",
            options=["Nenhuma"] + ESPECIALIDADES_PRONTAS,
            width="small",
        ),  # Habilita só se "Com Especialidade" for True
        "Local": st.column_config.SelectboxColumn(
            "Local*", options=ESPACAMENTO_LOCAL, required=True, width="small"
        ),
        "Largura Max (dmm)": st.column_config.NumberColumn(
            "Largura (dmm)",
            min_value=100,
            max_value=3000,
            step=10,
            width="small",
            default=1100,
        ),
        "Select": st.column_config.CheckboxColumn("Select", width=50),
    }

    st.markdown("### 🛠️ 2. Ajuste as configurações na tabela abaixo:")
    collabel1, collabel2 = st.columns(2)
    collabel2.markdown("### Editar Todos os Campos", text_alignment="center")
    collabel1.markdown("### Editar Marcados", text_alignment="center")

    colInputs1, colInputs2, colInputs3, colInputs4, colInputs5, colInputs6 = st.columns(
        6, vertical_alignment="center"
    )
    marcado_colunas_a_editar = colInputs1.selectbox(
        "Coluna", limpar_lista_colunas(config_colunas.keys(), ["Select", "Nome"])
    )
    with colInputs2:
        marcado_valor_a_editar = renderizar_input_dinamico(
            marcado_colunas_a_editar, "marcado"
        )

    if colInputs3.button("Aplicar", width="stretch"):
        df_editado = st.session_state.get("df_editado")
        df_lote = st.session_state.get("df_lote")
        if df_lote is None or df_editado is None:
            st.warning("Os dados do lote não estão disponíveis para atualização.")
        elif "Select" in df_editado.columns and df_editado["Select"].any():
            selected_mask = df_editado["Select"]
            df_lote.loc[selected_mask, marcado_colunas_a_editar] = (
                marcado_valor_a_editar
            )
            st.session_state.df_lote = df_lote
            st.rerun()
        else:
            st.warning("Nenhuma linha selecionada na coluna 'Select'.")

    todos_colunas_a_editar = colInputs4.selectbox(
        "Colunaa", limpar_lista_colunas(config_colunas.keys(), ["Select", "Nome"])
    )

    with colInputs5:
        todos_valor_a_editar = renderizar_input_dinamico(
            todos_colunas_a_editar, "todos"
        )

    if colInputs6.button("Aplicar a Todos", width="stretch"):
        df_lote = st.session_state.get("df_lote")
        if df_lote is None:
            st.warning("Os dados do lote não estão disponíveis para atualização.")
        else:
            df_lote[todos_colunas_a_editar] = todos_valor_a_editar
            st.session_state.df_lote = df_lote
            st.rerun()
    st.info(
        "💡 Você pode dar dois cliques nas células para editar, alterar as fontes e locais diretamente!"
    )

    # Configuração das colunas para colocar menus de seleção dentro das células (Drop-downs)

    # Exibe o editor de dados. O resultado editado é salvo de volta na variável df_editado
    st.session_state.df_editado = st.data_editor(
        st.session_state.df_lote,
        column_config=config_colunas,
        hide_index=True,
        width="stretch",
        num_rows="dynamic",  # Permite que o usuário adicione ou delete linhas direto na tabela!
        key="tabela_lotes",
    )

    # Botões de Ação
    c_voltar, caminho_final_dst, c_gerar = st.columns(3, vertical_alignment="center")

    if c_voltar.button("⬅️ Cancelar e Voltar", width="stretch"):
        st.session_state.lote_processado = False
        st.session_state.df_lote = None
        st.rerun()

    final_dst = caminho_final_dst.text_input(
        "Caminho do Arquivo Final (.DST):", value="./lotes/"
    )

    if c_gerar.button("🚀 Gerar Lote Completo (.DST)", width="stretch", type="primary"):
        # Atualiza o estado com as alterações que o usuário fez na tela
        st.session_state.df_lote = st.session_state.df_editado

        st.markdown("---")
        st.markdown("### ⏳ Processando Arquivos...")

        # Criamos um container para mostrar o progresso
        barra_progresso = st.progress(0)
        total_itens = len(st.session_state.df_editado)

        for index, (_, linha) in enumerate(st.session_state.df_editado.iterrows()):
            print(linha)
            motor = MotorBordado(linha["Fonte Nome"])
            if linha["Prefixo"]:
                nome_completo = f"{linha['Prefixo']} {linha['Nome']}"
            else:
                nome_completo = linha["Nome"]
            bordado = motor.gerar_nome(nome_completo, linha["Largura Max (dmm)"])
            if linha["Especialidade"] != "Nenhuma":
                especialidade_path = os.path.join(
                    "./ESPECIALIDADES_PRONTAS", linha["Especialidade"]
                )
                bordado = motor.incluir_especialidade_pronta(
                    bordado,
                    especialidade=especialidade_path,
                    espaco_vertical=ESPACAMENTO_LOCAL[linha["Local"]],
                )
            bordado.write(os.path.join(final_dst, f"{nome_completo}.dst"))
            # Atualiza a barra de progresso proporcionalmente
            barra_progresso.progress((index + 1) / total_itens)

        st.success("🎉 Todos os bordados do lote foram gerados com sucesso!")
