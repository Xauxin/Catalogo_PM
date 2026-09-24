import uuid
from datetime import date

import pandas as pd
import streamlit as st

from core.models import Bordado, Lote, Peca
from core.repository import CatalogoRepository, LoteRepository
from utils.ecosystem_data import load_ecosystem_data

try:
    st.set_page_config(layout="wide")
except Exception:
    pass

from utils.auth import verificar_autenticacao
verificar_autenticacao()

# CSS compacto para ajuste 16:9 em tela única (elimina margens excessivas)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.35rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 4px 10px;
        font-size: 0.82rem;
    }
    h1, h2, h3, h4, h5 {
        margin-top: 0rem !important;
        margin-bottom: 0.2rem !important;
        padding: 0rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 1. ESTADOS DA SESSÃO
# =====================================================================
if "tabela_lote" not in st.session_state:
    st.session_state.tabela_lote = pd.DataFrame(
        columns=[
            "ID_Grupo",
            "Peça",
            "Qtd",
            "Observação",
            "Local",
            "Tipo",
            "Informação",
            "Cor",
            "Fonte",
            "Matriz Pronta",
            "Preço UN",
            "Preço Total",
            "Preço Matriz",
            "Total + Matriz",
        ]
    )

if "lote_salvo_info" not in st.session_state:
    st.session_state.lote_salvo_info = None

if "form_iteration" not in st.session_state:
    st.session_state.form_iteration = 0


# =====================================================================
# 2. CARREGAMENTO DE OPÇÕES HISTÓRICAS (AUTOCOMPLETE)
# =====================================================================
def carregar_opcoes_historicas():
    fontes = LoteRepository.listar_fontes_cadastradas()
    cores = LoteRepository.listar_cores_linha_cadastradas()

    especialidades = [
        "Cardiologia",
        "Cirurgia Geral",
        "Clínica Geral",
        "Dermatologia",
        "Enfermagem",
        "Farmácia",
        "Fisioterapia",
        "Ginecologia",
        "Medicina",
        "Médica",
        "Médico",
        "Neurologia",
        "Nutrição",
        "Odontologia",
        "Oftalmologia",
        "Ortopedia",
        "Pediatria",
        "Psicologia",
        "Psiquiatria",
        "Radiologia",
        "Urologia",
        "Veterinária",
    ]
    try:
        _, espc_eco, _ = load_ecosystem_data()
        for e in espc_eco:
            limpo = e.replace(".DST", "").replace(".dst", "").strip()
            if limpo and limpo not in especialidades:
                especialidades.append(limpo)
    except Exception:
        pass

    try:
        esps_banco = LoteRepository.listar_especialidades_cadastradas()
        for esp in esps_banco:
            if esp not in especialidades:
                especialidades.append(esp)
    except Exception:
        pass

    return sorted(list(set(fontes))), sorted(list(set(especialidades))), sorted(list(set(cores)))


if (
    "historico_fontes" not in st.session_state
    or "historico_especialidades" not in st.session_state
    or "historico_cores" not in st.session_state
):
    f_ini, e_ini, c_ini = carregar_opcoes_historicas()
    st.session_state.historico_fontes = f_ini
    st.session_state.historico_especialidades = e_ini
    st.session_state.historico_cores = c_ini

# Atualiza os templates de peças e locais cadastrados no banco
try:
    templates_do_banco = CatalogoRepository.listar_templates()
    dicionario_pecas = {}
    for template in templates_do_banco:
        locais = (
            [local.nome for local in template.locais_permitidos]
            if template.locais_permitidos
            else []
        )
        dicionario_pecas[template.nome] = locais
    st.session_state.mock_templates = dicionario_pecas
except Exception:
    if "mock_templates" not in st.session_state:
        st.session_state.mock_templates = {}

if "historico_pecas" not in st.session_state:
    st.session_state.historico_pecas = sorted(list(st.session_state.mock_templates.keys()))
else:
    for p in st.session_state.mock_templates.keys():
        if p not in st.session_state.historico_pecas:
            st.session_state.historico_pecas.append(p)
    st.session_state.historico_pecas.sort()

if "historico_locais" not in st.session_state:
    st.session_state.historico_locais = CatalogoRepository.listar_todos_os_locais()


def atualizar_preco_matriz(local_chave: str, form_iter: int):
    matriz_val = st.session_state.get(f"sel_mat_{local_chave}_{form_iter}")
    if matriz_val == "Não":
        st.session_state[f"mtz_logo_{local_chave}_{form_iter}"] = 40.00
    elif matriz_val == "Sim":
        st.session_state[f"mtz_logo_{local_chave}_{form_iter}"] = 0.00


# =====================================================================
# 3. CABEÇALHO COMPACTO (CLIENTE E DATAS)
# =====================================================================
col_cli, col_ent, col_entreg = st.columns([3.2, 1, 1.2])

with col_cli:
    cliente = st.text_input(
        "Nome do Cliente *",
        placeholder="Ex: Hospital São Lucas",
        key="cliente_input",
    )
with col_ent:
    data_entrada = st.date_input("Entrada", value=date.today(), disabled=True)
with col_entreg:
    data_entrega = st.date_input(
        "Previsão de Entrega *",
        value=date.today(),
        min_value=date.today(),
    )

# =====================================================================
# 4. LAYOUT 16:9 EM DUAS COLUNAS
# =====================================================================
col_esquerda, col_direita = st.columns([1.15, 1.0], gap="medium")

# ---------------------------------------------------------------------
# COLUNA ESQUERDA: CONFIGURADOR DA PEÇA E BORDADOS
# ---------------------------------------------------------------------
with col_esquerda:
    st.markdown("##### Peça e Bordados")

    it = st.session_state.form_iteration

    col_peca, col_qtd, col_obs = st.columns([2.2, 0.9, 2.2])
    with col_peca:
        peca_selecionada = st.selectbox(
            "Peça *",
            options=st.session_state.historico_pecas,
            placeholder="Selecione ou digite uma peça...",
            accept_new_options=True,
            key=f"peca_sel_{it}",
        )

    with col_qtd:
        qtd = st.number_input(
            "Qtd *",
            min_value=1,
            value=1,
            step=1,
            key=f"qtd_peca_{it}",
        )

    with col_obs:
        obs_peca = st.text_input(
            "Observação",
            placeholder="Ex: Tam G, Manga Longa",
            key=f"obs_peca_{it}",
        )

    # Locais associados ao template ou catálogo geral
    locais_do_catalogo = st.session_state.mock_templates.get(peca_selecionada, [])
    is_peca_cadastrada = bool(locais_do_catalogo)

    if is_peca_cadastrada:
        opcoes_locais = list(locais_do_catalogo)
        default_locais = [locais_do_catalogo[0]] if locais_do_catalogo else []
    else:
        # Para peça não cadastrada, lista todos os locais já cadastrados no sistema
        todos_locais = CatalogoRepository.listar_todos_os_locais()
        opcoes_locais = todos_locais
        default_locais = []

    locais_selecionados = st.multiselect(
        "Locais de Bordado * (Selecione ou digite novos)",
        options=opcoes_locais,
        default=default_locais,
        placeholder="Selecione ou digite novos locais...",
        accept_new_options=True,
        key=f"locais_sel_{peca_selecionada}_{it}",
    )

    dados_para_salvar = {}

    if not locais_selecionados:
        st.caption("Selecione um ou mais locais acima para preencher os bordados.")
    else:
        # Abas horizontais compactas para cada local selecionado
        titulos_abas = []
        for loc in locais_selecionados:
            tipo_salvo = st.session_state.get(f"tipo_{loc}_{it}", "Texto")
            if tipo_salvo == "Texto":
                nome_val = st.session_state.get(f"nome_{loc}_{it}")
                fon_val = st.session_state.get(f"sel_fon_{loc}_{it}")
                cor_val = st.session_state.get(f"sel_cor_{loc}_{it}")
                completo = bool(nome_val and fon_val and cor_val)
            else:
                nome_val = st.session_state.get(f"logo_{loc}_{it}")
                mat_val = st.session_state.get(f"sel_mat_{loc}_{it}")
                completo = bool(nome_val and mat_val in ["Sim", "Não"])

            rotulo_aba = f"{loc} (OK)" if completo else loc
            titulos_abas.append(rotulo_aba)

        tabs = st.tabs(titulos_abas)

        for idx, local in enumerate(locais_selecionados):
            with tabs[idx]:
                tipos_matriz = CatalogoRepository.listar_tipos_matriz()
                opcoes_tipo = ["Texto"] + [t for t in tipos_matriz if t != "Texto"]
                tipo_salvo = st.session_state.get(f"tipo_{local}_{it}", "Texto")
                idx_tipo = opcoes_tipo.index(tipo_salvo) if tipo_salvo in opcoes_tipo else 0

                col_tipo, col_nome, col_pun = st.columns([1.3, 2.5, 1.2])

                with col_tipo:
                    tipo = st.selectbox(
                        "Tipo *",
                        options=opcoes_tipo,
                        index=idx_tipo,
                        key=f"tipo_{local}_{it}",
                    )

                if tipo == "Texto":
                    with col_nome:
                        nome_texto = st.text_input(
                            "Nome para Bordado *",
                            placeholder="Ex: Dr. Carlos",
                            key=f"nome_{local}_{it}",
                        )
                    with col_pun:
                        preco_un = st.number_input(
                            "Preço UN (R$)",
                            min_value=0.0,
                            value=10.00,
                            step=0.50,
                            key=f"prc_{local}_{it}",
                        )

                    c_esp, c_fon, c_cor = st.columns([1.8, 1.6, 1.6])
                    with c_esp:
                        especialidade = st.selectbox(
                            "Especialidade",
                            options=st.session_state.historico_especialidades,
                            index=None,
                            placeholder="Selecione ou digite (opcional)...",
                            accept_new_options=True,
                            key=f"sel_esp_{local}_{it}",
                        )
                    with c_fon:
                        fonte = st.selectbox(
                            "Fonte *",
                            options=st.session_state.historico_fontes,
                            index=None,
                            placeholder="Selecione ou digite...",
                            accept_new_options=True,
                            key=f"sel_fon_{local}_{it}",
                        )
                    with c_cor:
                        cor = st.selectbox(
                            "Cor da Linha *",
                            options=st.session_state.historico_cores,
                            index=None,
                            placeholder="Selecione ou digite...",
                            accept_new_options=True,
                            key=f"sel_cor_{local}_{it}",
                        )

                    nome_limpo = str(nome_texto).strip() if nome_texto else ""
                    esp_limpa = str(especialidade).strip() if especialidade else ""
                    fonte_limpa = str(fonte).strip() if fonte else ""
                    cor_limpa = str(cor).strip() if cor else ""
                    info_final = f"{nome_limpo} - {esp_limpa}" if esp_limpa else nome_limpo

                    dados_para_salvar[local] = {
                        "tipo": tipo,
                        "nome_texto": nome_limpo,
                        "especialidade": esp_limpa,
                        "fonte": fonte_limpa,
                        "cor": cor_limpa,
                        "info": info_final,
                        "matriz_pronta": "Sim",
                        "preco_un": preco_un,
                        "preco_matriz": 0.00,
                    }

                else:  # Matrizes de bordado cadastradas filtradas pelo Tipo selecionado
                    try:
                        catalogo_b = CatalogoRepository.listar_templates_bordado()
                        sugestoes_b = {}
                        for b in catalogo_b:
                            if b.tipo and b.tipo.strip().lower() == str(tipo).strip().lower():
                                sugestoes_b[b.nome] = b
                    except Exception:
                        sugestoes_b = {}

                    with col_nome:
                        nome_bordado = st.selectbox(
                            f"Nome do {tipo} *",
                            options=list(sugestoes_b.keys()),
                            index=None,
                            placeholder=f"Selecione {tipo} do catálogo ou digite...",
                            accept_new_options=True,
                            key=f"logo_{local}_{it}",
                        )

                    item_cat = sugestoes_b.get(nome_bordado)
                    preco_sugerido = float(item_cat.preco) if item_cat else 18.00

                    with col_pun:
                        preco_un = st.number_input(
                            "Preço UN (R$)",
                            min_value=0.0,
                            value=preco_sugerido,
                            step=0.50,
                            key=f"prc_logo_{local}_{it}",
                        )

                    c_cor, c_mat, c_pmat = st.columns([2, 1.6, 1.4])
                    with c_cor:
                        cor_default_text = item_cat.linhas_usadas if (item_cat and item_cat.linhas_usadas) else "Ex: Dourado / Verde"
                        cor_logo = st.selectbox(
                            "Cores do Elemento",
                            options=st.session_state.historico_cores,
                            index=None,
                            placeholder=cor_default_text,
                            accept_new_options=True,
                            key=f"sel_cor_logo_{local}_{it}",
                        )
                    with c_mat:
                        matriz_idx = None
                        if item_cat:
                            matriz_idx = 0 if item_cat.matriz_pronta else 1
                        matriz_pronta_sel = st.selectbox(
                            "Matriz Pronta? *",
                            options=["Sim", "Não"],
                            index=matriz_idx,
                            placeholder="Selecione...",
                            key=f"sel_mat_{local}_{it}",
                            on_change=atualizar_preco_matriz,
                            args=(local, it),
                        )
                    with c_pmat:
                        chave_mtz = f"mtz_logo_{local}_{it}"
                        if chave_mtz not in st.session_state:
                            if item_cat and not item_cat.matriz_pronta and item_cat.preco_matriz:
                                st.session_state[chave_mtz] = float(item_cat.preco_matriz)
                            else:
                                st.session_state[chave_mtz] = (
                                    40.00 if matriz_pronta_sel == "Não" else 0.00
                                )

                        preco_matriz = st.number_input(
                            "Preço Matriz (R$)",
                            min_value=0.0,
                            step=5.00,
                            key=chave_mtz,
                        )

                    nome_limpo = str(nome_bordado).strip() if nome_bordado else ""
                    cor_limpa = str(cor_logo).strip() if cor_logo else ""

                    dados_para_salvar[local] = {
                        "tipo": tipo,
                        "nome_bordado": nome_limpo,
                        "info": nome_limpo,
                        "cor": cor_limpa or "Padrão",
                        "fonte": "N/A",
                        "matriz_pronta": matriz_pronta_sel,
                        "preco_un": preco_un,
                        "preco_matriz": preco_matriz,
                    }

    botao_adicionar = st.button(
        "Adicionar Peça ao Lote",
        type="primary",
        use_container_width=True,
    )

    if botao_adicionar:
        if not peca_selecionada or not str(peca_selecionada).strip():
            st.error("Digite ou selecione o nome da Peça antes de adicionar.")
        elif not locais_selecionados:
            st.error("Selecione ou digite ao menos um local antes de adicionar à tabela.")
        else:
            erros_validacao = []
            for local in locais_selecionados:
                dados = dados_para_salvar.get(local, {})
                tipo = dados.get("tipo", "")
                if tipo == "Texto":
                    campos_faltando = []
                    if not dados.get("nome_texto"):
                        campos_faltando.append("Nome")
                    if not dados.get("fonte"):
                        campos_faltando.append("Fonte")
                    if not dados.get("cor"):
                        campos_faltando.append("Cor da Linha")
                    if campos_faltando:
                        erros_validacao.append(
                            f"**{local}** (Texto): preencha **{', '.join(campos_faltando)}**."
                        )
                else:
                    campos_faltando = []
                    if not dados.get("nome_bordado"):
                        campos_faltando.append(f"Nome do {tipo}")
                    if dados.get("matriz_pronta") not in ["Sim", "Não"]:
                        campos_faltando.append("Matriz Pronta ('Sim' ou 'Não')")
                    if campos_faltando:
                        erros_validacao.append(
                            f"**{local}** ({tipo}): preencha **{', '.join(campos_faltando)}**."
                        )

            if erros_validacao:
                st.error(
                    "**Preencha os campos obrigatórios antes de adicionar:**\n\n"
                    + "\n".join(f"- {e}" for e in erros_validacao)
                )
            else:
                peca_nome_limpo = str(peca_selecionada).strip()
                if peca_nome_limpo not in st.session_state.historico_pecas:
                    st.session_state.historico_pecas.append(peca_nome_limpo)
                    st.session_state.historico_pecas.sort()

                for local in locais_selecionados:
                    local_limpo = str(local).strip()
                    if local_limpo and local_limpo not in st.session_state.historico_locais:
                        st.session_state.historico_locais.append(local_limpo)
                        st.session_state.historico_locais.sort()

                for local in locais_selecionados:
                    dados = dados_para_salvar.get(local, {})
                    if dados.get("tipo") == "Texto":
                        esp = dados.get("especialidade", "")
                        fon = dados.get("fonte", "")
                        c = dados.get("cor", "")
                        if esp and esp not in st.session_state.historico_especialidades:
                            st.session_state.historico_especialidades.append(esp)
                            st.session_state.historico_especialidades.sort()
                        if fon and fon not in st.session_state.historico_fontes:
                            st.session_state.historico_fontes.append(fon)
                            st.session_state.historico_fontes.sort()
                        if c and c not in st.session_state.historico_cores:
                            st.session_state.historico_cores.append(c)
                            st.session_state.historico_cores.sort()
                    else:
                        c_logo = dados.get("cor", "")
                        if (
                            c_logo
                            and c_logo != "Padrão"
                            and c_logo not in st.session_state.historico_cores
                        ):
                            st.session_state.historico_cores.append(c_logo)
                            st.session_state.historico_cores.sort()

                novas_linhas = []
                id_grupo = str(uuid.uuid4())

                for local in locais_selecionados:
                    dados = dados_para_salvar[local]
                    p_un = dados["preco_un"]
                    p_total = p_un * qtd
                    p_matriz = dados["preco_matriz"]
                    total_com_matriz = p_total + p_matriz

                    linha = {
                        "ID_Grupo": id_grupo,
                        "Peça": peca_nome_limpo,
                        "Qtd": qtd,
                        "Observação": obs_peca,
                        "Local": local,
                        "Tipo": dados["tipo"],
                        "Informação": dados["info"],
                        "Cor": dados["cor"],
                        "Fonte": dados["fonte"],
                        "Matriz Pronta": dados["matriz_pronta"],
                        "Preço UN": p_un,
                        "Preço Total": p_total,
                        "Preço Matriz": p_matriz,
                        "Total + Matriz": total_com_matriz,
                    }
                    novas_linhas.append(linha)

                df_novas = pd.DataFrame(novas_linhas)
                st.session_state.tabela_lote = pd.concat(
                    [st.session_state.tabela_lote, df_novas], ignore_index=True
                )
                st.session_state.lote_salvo_info = None
                st.session_state.sucesso_adicao = (
                    f"{qtd}x '{peca_nome_limpo}' adicionada(s) ao lote!"
                )
                st.session_state.form_iteration += 1
                st.rerun()

# ---------------------------------------------------------------------
# COLUNA DIREITA: RESUMO DO LOTE, TABELA E SALVAMENTO
# ---------------------------------------------------------------------
with col_direita:
    st.markdown("##### Resumo do Lote")

    if st.session_state.get("sucesso_adicao"):
        st.toast(st.session_state.sucesso_adicao)
        st.session_state.sucesso_adicao = None

    if st.session_state.get("lote_salvo_info"):
        info_salvo = st.session_state.lote_salvo_info
        st.success(
            f"**Lote #{info_salvo['id']} salvo com sucesso!** | "
            f"Cliente: **{info_salvo['cliente']}** | **{info_salvo['total_pecas']}** peças (R$ {info_salvo['preco_total']:,.2f})"
        )
        c_novo, c_link = st.columns([1, 1])
        with c_novo:
            if st.button("Iniciar Novo Lote", type="primary", use_container_width=True):
                st.session_state.tabela_lote = st.session_state.tabela_lote.iloc[0:0]
                st.session_state.lote_salvo_info = None
                if "cliente_input" in st.session_state:
                    st.session_state.cliente_input = ""
                st.rerun()
        with c_link:
            st.page_link(
                "pages/visualizar_lotes.py",
                label="Ir para Gestão de Lotes",
                icon="📑",
                use_container_width=True,
            )

    if st.session_state.tabela_lote.empty:
        st.info("A tabela do lote está vazia. Adicione itens no configurador ao lado.")
    else:
        colunas_visiveis = [
            col for col in st.session_state.tabela_lote.columns if col != "ID_Grupo"
        ]
        st.dataframe(
            st.session_state.tabela_lote[colunas_visiveis],
            height=250,
            width="stretch",
            hide_index=True,
            column_config={
                "Qtd": st.column_config.NumberColumn("Qtd", format="%d un"),
                "Preço UN": st.column_config.NumberColumn("Preço UN", format="R$ %.2f"),
                "Preço Total": st.column_config.NumberColumn("Preço Total", format="R$ %.2f"),
                "Preço Matriz": st.column_config.NumberColumn("Preço Matriz", format="R$ %.2f"),
                "Total + Matriz": st.column_config.NumberColumn("Total + Matriz", format="R$ %.2f"),
            },
        )

        c_acoes_tab, c_tot_pecas, c_financeiro = st.columns([2, 1, 1.2])

        with c_acoes_tab:
            col_btn_rem, col_btn_limp = st.columns([1.2, 1])
            with col_btn_rem:
                grupos_unicos = st.session_state.tabela_lote.drop_duplicates(subset=["ID_Grupo"])
                opcoes_remocao = {}
                for idx, (_, row_g) in enumerate(grupos_unicos.iterrows(), start=1):
                    id_g = row_g["ID_Grupo"]
                    nome_p = row_g["Peça"]
                    qtd_p = row_g["Qtd"]
                    locais_p = ", ".join(
                        st.session_state.tabela_lote[st.session_state.tabela_lote["ID_Grupo"] == id_g]["Local"].tolist()
                    )
                    label_g = f"Item {idx}: {qtd_p}x {nome_p} ({locais_p})"
                    opcoes_remocao[label_g] = id_g

                with st.popover("Remover Peça", use_container_width=True):
                    st.markdown("**Selecione a peça para remover:**")
                    peca_para_remover = st.selectbox(
                        "Peça para remover:",
                        options=list(opcoes_remocao.keys()),
                        label_visibility="collapsed",
                    )
                    if st.button("Confirmar Remoção", type="primary", key="btn_confirm_remover_peca"):
                        id_remover = opcoes_remocao[peca_para_remover]
                        st.session_state.tabela_lote = st.session_state.tabela_lote[
                            st.session_state.tabela_lote["ID_Grupo"] != id_remover
                        ].reset_index(drop=True)
                        st.session_state.lote_salvo_info = None
                        st.toast("Peça removida!")
                        st.rerun()

            with col_btn_limp:
                with st.popover("Limpar Tudo", use_container_width=True):
                    st.warning("Deseja realmente remover todos os itens adicionados ao lote?")
                    if st.button("Confirmar Limpeza Total", type="primary", key="btn_conf_limpar_tudo"):
                        st.session_state.tabela_lote = st.session_state.tabela_lote.iloc[0:0]
                        st.session_state.lote_salvo_info = None
                        if "cliente_input" in st.session_state:
                            st.session_state.cliente_input = ""
                        st.rerun()

        with c_tot_pecas:
            total_pecas_fisicas = int(
                st.session_state.tabela_lote.drop_duplicates(subset=["ID_Grupo"])["Qtd"].sum()
            )
            st.metric("Total Peças", f"{total_pecas_fisicas} un")

        with c_financeiro:
            valor_financeiro_total = st.session_state.tabela_lote["Total + Matriz"].sum()
            st.metric("Valor Total", f"R$ {valor_financeiro_total:,.2f}")

        # Salvar lote no banco
        lote_ja_salvo = st.session_state.get("lote_salvo_info") is not None
        if lote_ja_salvo:
            st.info("Lote já salvo no banco. Clique em 'Iniciar Novo Lote' para cadastrar outro pedido.")
        else:
            if st.button(
                "Salvar Lote de Produção",
                type="primary",
                use_container_width=True,
            ):
                if not cliente or not cliente.strip():
                    st.error("Digite o Nome do Cliente no topo da página antes de salvar.")
                else:
                    try:
                        df = st.session_state.tabela_lote
                        valor_total_lote = float(df["Total + Matriz"].sum())

                        lote_novo = Lote(
                            cliente=cliente.strip(),
                            data_entrada=data_entrada,
                            data_entrega=data_entrega,
                            preco_total=valor_total_lote,
                        )

                        estrutura_pedido = []

                        for id_grupo, grupo_df in df.groupby("ID_Grupo"):
                            primeira_linha = grupo_df.iloc[0]
                            qtd_peca = int(primeira_linha["Qtd"])
                            preco_total_peca = float(grupo_df["Preço Total"].sum())
                            obs_val = primeira_linha["Observação"]
                            obs_str = (
                                str(obs_val).strip()
                                if pd.notna(obs_val) and str(obs_val).strip()
                                else None
                            )

                            peca_obj = Peca(
                                nome=str(primeira_linha["Peça"]),
                                quantidade=qtd_peca,
                                observacao=obs_str,
                                preco_peca_total=preco_total_peca,
                            )

                            bordados_lista = []
                            for _, linha in grupo_df.iterrows():
                                matriz_pronta_str = str(linha["Matriz Pronta"]).strip().lower()
                                precisa_criar_matriz = matriz_pronta_str in ["não", "nao", "false", "0"]

                                fonte_val = str(linha["Fonte"]).strip() if pd.notna(linha["Fonte"]) else None
                                fonte_limpa = fonte_val if fonte_val and fonte_val != "N/A" else None

                                bordado_obj = Bordado(
                                    local=str(linha["Local"]),
                                    tipo=str(linha["Tipo"]),
                                    informacao=str(linha["Informação"]),
                                    cor=str(linha["Cor"]),
                                    fonte=fonte_limpa,
                                    precisa_matriz=precisa_criar_matriz,
                                    preco_bordado=float(linha["Preço UN"]),
                                    preco_matriz=float(linha["Preço Matriz"]),
                                    status="Pendente",
                                )
                                bordados_lista.append(bordado_obj)

                            estrutura_pedido.append(
                                {"peca": peca_obj, "bordados": bordados_lista}
                            )

                        lote_salvo = LoteRepository.criar_lote_completo(lote_novo, estrutura_pedido)

                        data_entrega_formatada = (
                            data_entrega.strftime("%d/%m/%Y") if data_entrega else "-"
                        )
                        st.session_state.lote_salvo_info = {
                            "id": lote_salvo.id,
                            "cliente": lote_salvo.cliente,
                            "preco_total": valor_total_lote,
                            "total_pecas": total_pecas_fisicas,
                            "data_entrega": data_entrega_formatada,
                        }

                        st.toast(f"Lote #{lote_salvo.id} salvo com sucesso!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados: {e}")
