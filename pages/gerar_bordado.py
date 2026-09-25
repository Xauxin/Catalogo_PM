import os
import tempfile

import matplotlib.pyplot as plt
import streamlit as st

from name_maker import MotorBordado
from utils.ecosystem_data import load_ecosystem_data

FONTES_DISPONIVEIS, ESPECIALIDADES_PRONTAS, ESPACAMENTO_LOCAL = load_ecosystem_data()

from utils.auth import verificar_autenticacao
verificar_autenticacao(role_minima="cliente")


def renderizar_preview_bordado(bordado):

    fig, ax = plt.subplots(figsize=(8, 2))

    try:
        stitches = bordado.stitches
        x = [s[0] for s in stitches]
        y = [s[1] for s in stitches]

        ax.plot(x, y)
        ax.invert_yaxis()  # Inverte o eixo Y para simular a visualização tradicional de bordado

    except Exception as e:
        ax.text(
            0.5,
            0.5,
            f"Erro ao renderizar preview:\n{e}",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.set_axis_off()

    ax.set_title("Preview do Bordado")
    ax.axis("equal")
    ax.grid(False)
    ax.set_axis_off()  # Esconde os eixos para uma visualização mais limpa

    return fig


# --- INTERFACE ---

colFont1, colFont2, colFont3 = st.columns(3, vertical_alignment="center")
fonte_nome = colFont1.selectbox("Fonte Nome", FONTES_DISPONIVEIS)
nome = st.text_input("Nome")

# Layout das colunas para especialidade
colEspc1, colEspc2, colEspc3, colEspc4 = st.columns(
    [1, 1.5, 2, 1.5], vertical_alignment="center"
)

com_especialidade = colEspc1.checkbox("Especialidade")

# Variáveis de controle para sabermos o que passar para o motor
tipo_especialidade = "pronta"  # Pode ser 'pronta' ou 'customizada'
especialidade_final = ""
fonte_espc_final = None

if com_especialidade:
    # Em vez de ifs aninhados perigosos, usamos o checkbox de controle logo no início da linha
    customizada = colEspc2.checkbox("Customizar?")

    if not customizada:
        tipo_especialidade = "pronta"
        # O usuário escolhe o arquivo .dst pronto
        arquivo_escolhido = colEspc3.selectbox(
            "Escolha a Especialidade Pronta", ESPECIALIDADES_PRONTAS
        )
        # Caminho completo do arquivo pronto para o seu motor abrir
        especialidade_final = os.path.join(
            "./ESPECIALIDADES_PRONTAS", arquivo_escolhido
        )
    else:
        tipo_especialidade = "customizada"
        # O usuário digita o texto e escolhe a fonte
        especialidade_final = colEspc3.text_input(
            "Texto da Especialidade", placeholder="ex: MÉDICA"
        )
        fonte_espc_final = colEspc4.selectbox(
            "Fonte da Espc.", FONTES_DISPONIVEIS, key="fonte_espc"
        )

colLoc1, colLoc2, colLoc3 = st.columns(3, vertical_alignment="center")
local = colLoc1.selectbox("Local do Bordado", ESPACAMENTO_LOCAL.keys())
tamanho_maximo = colLoc2.text_input(
    "Largura Máxima (dmm)",
    help="Deixe vazio para ignorar limite de largura",
    value="1100",
)

# --- PROCESSAMENTO ---

colFinal1, colFinal2, colFinal3 = st.columns(3, vertical_alignment="center")

if colFinal1.button("Gerar Bordado", width="stretch", type="primary"):
    if not nome:
        st.warning("Por favor, digite um nome.")
    else:
        status = st.empty()
        texto = f"Gerando bordado para **{nome}**..."
        if com_especialidade:
            if tipo_especialidade == "pronta":
                texto += f" com especialidade pronta '{arquivo_escolhido}'"
            else:
                texto += f" com especialidade customizada '{especialidade_final}' usando fonte '{fonte_espc_final}'"
        status.write(texto)

        motor = MotorBordado(fonte_nome)
        bordado = motor.gerar_nome(
            nome, float(tamanho_maximo) if tamanho_maximo else None
        )

        if com_especialidade:
            if tipo_especialidade == "pronta":
                # AQUI: Seu motor precisa saber que está recebendo o CAMINHO de um arquivo .dst pronto
                # Exemplo ideal: motor.incluir_especialidade_pronta(bordado, caminho_arquivo=especialidade_final)
                # Vou manter a sua função, mas lembre-se de tratar o fato de que 'especialidade_final' é um caminho de arquivo aqui.
                bordado = motor.incluir_especialidade_pronta(
                    bordado,
                    especialidade=especialidade_final,
                    espaco_vertical=ESPACAMENTO_LOCAL[local],
                )
            else:
                # AQUI: Passamos o texto digitado e a fonte escolhida para gerar do zero
                # Seu motor deve aceitar a fonte customizada se necessário
                bordado = motor.gera_especialidade(
                    bordado,
                    especialidade=especialidade_final,
                    fonte_especialidade=fonte_espc_final,
                    espaco_extra=-5,
                    espaco_vertical=ESPACAMENTO_LOCAL[local],
                )

        # Guardamos o resultado final na sessão do Streamlit para o botão de download não sumir
        st.session_state["bordado_pronto"] = bordado
        st.session_state["nome_arquivo"] = nome
        texto_sucesso = f"Bordado para **{nome}** gerado com sucesso!"
        if com_especialidade:
            if tipo_especialidade == "pronta":
                texto_sucesso += f" (com especialidade pronta '{arquivo_escolhido}')"
            else:
                texto_sucesso += (
                    f" (com especialidade customizada '{especialidade_final}')"
                )

        status.write(f"{texto_sucesso}! Largura final: {bordado.bounds()[2]:.2f}mm")


# --- BOTÃO DE DOWNLOAD (Fora do bloco de geração para evitar bugs de recarregamento) ---
if "bordado_pronto" in st.session_state:
    bordadao_gerado = st.session_state["bordado_pronto"]
    nome_salvar = st.session_state["nome_arquivo"]

    figura_preview = renderizar_preview_bordado(bordadao_gerado)

    st.pyplot(figura_preview)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dst") as tmp_file:
        caminho_temporario = tmp_file.name

    bordadao_gerado.write(caminho_temporario)

    with open(caminho_temporario, "rb") as f:
        dados_dst = f.read()

    # Remove o arquivo temporário do servidor após ler os bytes (boa prática)
    try:
        os.unlink(caminho_temporario)
    except Exception as e:
        print(f"Erro ao remover arquivo temporário: {e}")

    colFinal2.download_button(
        "Baixar DST",
        data=dados_dst,
        file_name=f"{nome_salvar}.dst",
        mime="application/octet-stream",
        width="stretch",
        icon=":material/download:",
        type="secondary",
    )
