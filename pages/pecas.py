import os
import re
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

from core.models import TemplateBordado
from core.repository import CatalogoRepository

UPLOAD_DIR = Path("uploads/bordados")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CORES_PADRAO = [
    "Branco",
    "Preto",
    "Dourado",
    "Prata",
    "Azul Marinho",
    "Azul Royal",
    "Vermelho",
    "Verde Bandeira",
    "Verde Militar",
    "Amarelo Ouro",
    "Cinza",
    "Bordô",
    "Rosa",
    "Laranja",
    "Marrom",
]


def salvar_arquivo_upload(uploaded_file, prefixo: str) -> str | None:
    """Salva o arquivo de upload no disco e retorna o caminho relativo formatado."""
    if not uploaded_file:
        return None
    ext = Path(uploaded_file.name).suffix.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    limpo = re.sub(r"[^a-zA-Z0-9_-]", "_", prefixo).strip("_") or "arquivo"
    nome_arquivo = f"{limpo}_{timestamp}{ext}"
    destino = UPLOAD_DIR / nome_arquivo
    with open(destino, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(destino).replace("\\", "/")


st.set_page_config(page_title="Gestão do Catálogo", page_icon="🏷️", layout="wide")

st.title("🏷️ Gestão do Catálogo")
st.caption(
    "Gerencie o catálogo de peças confeccionadas e o acervo completo de bordados, matrizes e imagens."
)

tab_pecas, tab_bordados = st.tabs(["👕 Catálogo de Peças", "🪡 Catálogo de Bordados"])


# =====================================================================
# ABA 1: CATÁLOGO DE PEÇAS
# =====================================================================
with tab_pecas:
    with st.expander("➕ Cadastrar Nova Peça no Catálogo", expanded=False):
        with st.form("form_novo_template", clear_on_submit=True):
            col_nome, col_locais = st.columns([1, 2])

            with col_nome:
                nome_peca = st.text_input(
                    "Nome do Modelo", placeholder="Ex: Jaqueta Corta Vento"
                )

            with col_locais:
                locais_input = st.text_input(
                    "Locais de Bordado (separe por vírgula)",
                    placeholder="Ex: Peito Esquerdo, Costas, Manga Direita, Gola",
                )

            st.markdown(" ")
            botao_salvar = st.form_submit_button("💾 Salvar Peça no Catálogo", type="primary")

            if botao_salvar:
                if not nome_peca.strip():
                    st.error("⚠️ O nome da peça é obrigatório.")
                elif not locais_input.strip():
                    st.error("⚠️ Digite pelo menos um local de bordado.")
                else:
                    lista_locais = [
                        local.strip() for local in locais_input.split(",") if local.strip()
                    ]

                    try:
                        CatalogoRepository.salvar_template_peca(nome_peca.strip(), lista_locais)
                        st.success(
                            f"🎉 Peça '{nome_peca}' cadastrada com sucesso com {len(lista_locais)} local(is)!"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")

    st.subheader("📚 Modelos de Peças Cadastrados")

    try:
        templates = CatalogoRepository.listar_templates()

        if not templates:
            st.info(
                "O catálogo de peças ainda está vazio. Abra o formulário acima para cadastrar sua primeira peça."
            )
        else:
            dados_tabela = []
            for t in templates:
                nomes_dos_locais = (
                    [local.nome for local in t.locais_permitidos]
                    if t.locais_permitidos
                    else []
                )
                locais_formatados = ", ".join(nomes_dos_locais)

                dados_tabela.append(
                    {
                        "ID": t.id,
                        "Peça": t.nome,
                        "Quantidade de Locais": len(nomes_dos_locais),
                        "Locais Permitidos": locais_formatados,
                    }
                )

            df_catalogo = pd.DataFrame(dados_tabela)

            st.dataframe(
                df_catalogo,
                hide_index=True,
                width="stretch",
                column_config={"ID": st.column_config.NumberColumn("ID", format="%d")},
            )

            c_info, c_del = st.columns([3, 1])
            with c_info:
                st.caption(f"**Total de modelos cadastrados:** {len(templates)}")

            with c_del:
                with st.popover("🗑️ Excluir Peça do Catálogo"):
                    st.markdown("**Remover peça cadastrada**")
                    opcoes_pecas = {f"{t.nome} (ID: {t.id})": t.id for t in templates}
                    peca_selecionada = st.selectbox(
                        "Selecione a peça para remover",
                        options=list(opcoes_pecas.keys()),
                        key="sel_peca_del",
                    )
                    if st.button("Confirmar Exclusão da Peça", type="primary", key="btn_del_peca"):
                        id_del = opcoes_pecas[peca_selecionada]
                        if CatalogoRepository.deletar_template_peca(id_del):
                            st.success("Peça removida com sucesso!")
                            st.rerun()
                        else:
                            st.error("Não foi possível excluir a peça.")

    except Exception as e:
        st.error(f"Erro ao buscar os dados do catálogo: {e}")


# =====================================================================
# ABA 2: CATÁLOGO DE BORDADOS E MATRIZES
# =====================================================================
with tab_bordados:
    with st.expander("➕ Cadastrar Novo Bordado / Matriz no Catálogo", expanded=False):
        with st.form("form_novo_bordado", clear_on_submit=True):
            col_b1, col_b2, col_b3 = st.columns([2.5, 1.5, 1.5])
            with col_b1:
                nome_bordado = st.text_input(
                    "Nome do Bordado / Matriz *",
                    placeholder="Ex: Brasão Colégio Santo Anjo",
                    help="Nome de identificação do bordado",
                )
            with col_b2:
                tipo_bordado = st.selectbox(
                    "Tipo *",
                    options=["Logo Fixo", "Brasão", "Desenho", "Texto", "Aplique", "Escudo", "Outro"],
                    accept_new_options=True,
                    help="Tipo ou categoria do bordado (permite digitar novos tipos)",
                )
            with col_b3:
                codigo_identificacao = st.text_input(
                    "Código de Identificação",
                    placeholder="Ex: BRAS-01 / MAT-2024",
                    help="Código interno ou referência de arquivo",
                )

            col_b4, col_b5, col_b6, col_b7 = st.columns([1.5, 1.5, 1.2, 1.5])
            with col_b4:
                pontos = st.number_input(
                    "Contagem de Pontos *",
                    min_value=0,
                    value=5000,
                    step=500,
                    help="Quantidade de pontos estimada ou exata da matriz",
                )
            with col_b5:
                preco_bordado = st.number_input(
                    "Preço do Bordado (R$) *",
                    min_value=0.0,
                    value=15.00,
                    step=0.50,
                    format="%.2f",
                    help="Preço cobrado pela aplicação deste bordado",
                )
            with col_b6:
                matriz_pronta_opt = st.selectbox(
                    "Matriz Pronta?",
                    options=["Sim", "Não"],
                    index=0,
                    help="Indica se a matriz computadorizada já está digitalizada e pronta",
                )
            with col_b7:
                preco_matriz = st.number_input(
                    "Preço da Matriz (R$)",
                    min_value=0.0,
                    value=0.00,
                    step=5.00,
                    format="%.2f",
                    help="Custo da criação/digitalização da matriz, se aplicável",
                )

            linhas_selecionadas = st.multiselect(
                "Linhas Usadas (Cores)",
                options=CORES_PADRAO,
                accept_new_options=True,
                help="Selecione as cores ou digite uma nova cor/código de linha",
            )

            col_img_d, col_img_f = st.columns(2)
            with col_img_d:
                upload_digital = st.file_uploader(
                    "🖼️ Imagem Digital (Mockup / Arte)",
                    type=["png", "jpg", "jpeg", "webp"],
                    help="Opcional. Arte digital ou prévia do bordado",
                    key="up_digital",
                )
            with col_img_f:
                upload_foto = st.file_uploader(
                    "📸 Foto do Bordado Real",
                    type=["png", "jpg", "jpeg", "webp"],
                    help="Opcional. Fotografia real da peça já bordada",
                    key="up_foto",
                )

            st.markdown(" ")
            btn_salvar_bordado = st.form_submit_button(
                "💾 Salvar Bordado no Catálogo", type="primary"
            )

            if btn_salvar_bordado:
                if not nome_bordado.strip():
                    st.error("⚠️ O Nome do bordado é obrigatório.")
                elif not tipo_bordado or not str(tipo_bordado).strip():
                    st.error("⚠️ O Tipo do bordado é obrigatório.")
                elif pontos <= 0:
                    st.error("⚠️ A contagem de pontos deve ser maior que zero.")
                elif preco_bordado < 0:
                    st.error("⚠️ O preço do bordado não pode ser negativo.")
                else:
                    try:
                        caminho_digital = (
                            salvar_arquivo_upload(
                                upload_digital,
                                f"digital_{codigo_identificacao or nome_bordado}",
                            )
                            if upload_digital
                            else None
                        )
                        caminho_foto = (
                            salvar_arquivo_upload(
                                upload_foto,
                                f"foto_{codigo_identificacao or nome_bordado}",
                            )
                            if upload_foto
                            else None
                        )

                        str_linhas = (
                            ", ".join([c.strip() for c in linhas_selecionadas if c.strip()])
                            if linhas_selecionadas
                            else None
                        )

                        novo_bordado = TemplateBordado(
                            nome=nome_bordado.strip(),
                            tipo=str(tipo_bordado).strip(),
                            pontos=int(pontos),
                            preco=float(preco_bordado),
                            matriz_pronta=(matriz_pronta_opt == "Sim"),
                            preco_matriz=float(preco_matriz),
                            linhas_usadas=str_linhas,
                            codigo_identificacao=codigo_identificacao.strip() if codigo_identificacao.strip() else None,
                            imagem_digital=caminho_digital,
                            foto_bordado=caminho_foto,
                        )
                        CatalogoRepository.salvar_template_bordado(novo_bordado)
                        st.success(f"🎉 Bordado '{nome_bordado}' cadastrado com sucesso no catálogo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar bordado no banco: {e}")

    # =====================================================================
    # VISUALIZAÇÃO DO CATÁLOGO DE BORDADOS
    # =====================================================================
    st.subheader("🗂️ Acervo de Matrizes e Bordados")

    try:
        bordados = CatalogoRepository.listar_templates_bordado()

        if not bordados:
            st.info(
                "O catálogo de bordados ainda está vazio. Abra o formulário acima para cadastrar seu primeiro bordado ou matriz."
            )
        else:
            # 1. Métricas / KPIs Resumidas
            total_itens = len(bordados)
            prontas_count = sum(1 for b in bordados if b.matriz_pronta)
            com_imagem_count = sum(
                1 for b in bordados if b.imagem_digital or b.foto_bordado
            )
            media_pontos = sum(b.pontos for b in bordados) / total_itens if total_itens else 0
            media_preco = sum(b.preco for b in bordados) / total_itens if total_itens else 0

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total Cadastrado", f"{total_itens} itens")
            kpi2.metric("Matrizes Prontas", f"{prontas_count} ({int(prontas_count / total_itens * 100)}%)")
            kpi3.metric("Com Imagens / Fotos", f"{com_imagem_count} itens")
            kpi4.metric("Preço Médio", f"R$ {media_preco:.2f}")

            st.markdown(" ")

            # 2. Barra de Filtros e Modo de Visualização
            f_col1, f_col2, f_col3, f_col4 = st.columns([2.2, 1.3, 1.3, 1.2])
            with f_col1:
                busca_texto = st.text_input(
                    "🔍 Buscar bordado",
                    placeholder="Filtrar por nome, código ou cores de linha...",
                    key="busca_bordado",
                )
            with f_col2:
                tipos_existentes = sorted(list(set(b.tipo for b in bordados if b.tipo)))
                filtro_tipo = st.selectbox(
                    "Filtrar por Tipo",
                    options=["Todos"] + tipos_existentes,
                    key="filtro_tipo_bordado",
                )
            with f_col3:
                filtro_status_matriz = st.selectbox(
                    "Status da Matriz",
                    options=["Todos", "Matriz Pronta (Sim)", "Matriz Pendente (Não)"],
                    key="filtro_status_matriz",
                )
            with f_col4:
                modo_exibicao = st.selectbox(
                    "Visualização",
                    options=["🖼️ Galeria de Fotos", "📋 Tabela Geral"],
                    key="modo_exibicao_bordado",
                )

            # Aplicar filtros
            bordados_filtrados = bordados
            if busca_texto.strip():
                termo = busca_texto.strip().lower()
                bordados_filtrados = [
                    b
                    for b in bordados_filtrados
                    if termo in b.nome.lower()
                    or (b.codigo_identificacao and termo in b.codigo_identificacao.lower())
                    or (b.linhas_usadas and termo in b.linhas_usadas.lower())
                ]

            if filtro_tipo != "Todos":
                bordados_filtrados = [
                    b for b in bordados_filtrados if b.tipo == filtro_tipo
                ]

            if filtro_status_matriz == "Matriz Pronta (Sim)":
                bordados_filtrados = [
                    b for b in bordados_filtrados if b.matriz_pronta
                ]
            elif filtro_status_matriz == "Matriz Pendente (Não)":
                bordados_filtrados = [
                    b for b in bordados_filtrados if not b.matriz_pronta
                ]

            if not bordados_filtrados:
                st.warning("Nenhum bordado encontrado com os filtros selecionados.")
            else:
                # MODO 1: GALERIA DE FOTOS
                if modo_exibicao == "🖼️ Galeria de Fotos":
                    st.caption(f"Mostrando **{len(bordados_filtrados)}** de **{len(bordados)}** bordados cadastrados:")
                    for b in bordados_filtrados:
                        with st.container(border=True):
                            col_info, col_img1, col_img2 = st.columns([1.5, 1.25, 1.25])

                            with col_info:
                                st.markdown(f"### {b.nome}")
                                st.markdown(
                                    f"**Código:** `{b.codigo_identificacao or 'N/A'}` | **Tipo:** `{b.tipo}`"
                                )
                                st.markdown(
                                    f"**Pontos:** `{b.pontos:,} pts` | **Preço Bordado:** `R$ {b.preco:.2f}`".replace(",", ".")
                                )
                                status_mat = "✅ Sim" if b.matriz_pronta else "⏳ Pendente"
                                st.markdown(f"**Matriz Pronta:** {status_mat}")
                                if not b.matriz_pronta or (b.preco_matriz and b.preco_matriz > 0):
                                    st.markdown(f"**Preço Matriz:** `R$ {b.preco_matriz:.2f}`")
                                if b.linhas_usadas:
                                    st.markdown(f"**Linhas / Cores:** {b.linhas_usadas}")

                                st.markdown(" ")
                                # Botões de Ação Direta no Card
                                c_act1, c_act2, c_act3 = st.columns(3)

                                # 1. EDITAR DADOS
                                with c_act1:
                                    with st.popover("✏️ Editar", key=f"pop_edt_{b.id}"):
                                        st.markdown(f"**Editar Bordado #{b.id}**")
                                        ed_nome = st.text_input("Nome *", value=b.nome, key=f"ed_nom_{b.id}")
                                        ed_tipo = st.selectbox(
                                            "Tipo *",
                                            options=["Logo Fixo", "Brasão", "Desenho", "Texto", "Aplique", "Escudo", "Outro"],
                                            index=(
                                                ["Logo Fixo", "Brasão", "Desenho", "Texto", "Aplique", "Escudo", "Outro"].index(b.tipo)
                                                if b.tipo in ["Logo Fixo", "Brasão", "Desenho", "Texto", "Aplique", "Escudo", "Outro"]
                                                else 0
                                            ),
                                            accept_new_options=True,
                                            key=f"ed_tip_{b.id}",
                                        )
                                        ed_cod = st.text_input("Código", value=b.codigo_identificacao or "", key=f"ed_cod_{b.id}")
                                        ed_pts = st.number_input("Pontos *", min_value=0, value=int(b.pontos), step=500, key=f"ed_pts_{b.id}")
                                        ed_prc = st.number_input("Preço Bordado (R$) *", min_value=0.0, value=float(b.preco), step=0.50, format="%.2f", key=f"ed_prc_{b.id}")
                                        ed_mat = st.selectbox("Matriz Pronta?", options=["Sim", "Não"], index=0 if b.matriz_pronta else 1, key=f"ed_mat_{b.id}")
                                        ed_prc_mat = st.number_input("Preço Matriz (R$)", min_value=0.0, value=float(b.preco_matriz or 0.0), step=5.00, format="%.2f", key=f"ed_pmat_{b.id}")

                                        cores_atuais = [c.strip() for c in b.linhas_usadas.split(",")] if b.linhas_usadas else []
                                        ed_cores = st.multiselect(
                                            "Linhas Usadas",
                                            options=list(set(CORES_PADRAO + cores_atuais)),
                                            default=cores_atuais,
                                            accept_new_options=True,
                                            key=f"ed_cor_{b.id}",
                                        )

                                        if st.button("💾 Salvar Alterações", key=f"btn_salv_ed_{b.id}", type="primary"):
                                            if not ed_nome.strip():
                                                st.error("Nome é obrigatório.")
                                            else:
                                                CatalogoRepository.atualizar_template_bordado(
                                                    bordado_id=b.id,
                                                    nome=ed_nome.strip(),
                                                    tipo=str(ed_tipo).strip(),
                                                    pontos=int(ed_pts),
                                                    preco=float(ed_prc),
                                                    matriz_pronta=(ed_mat == "Sim"),
                                                    preco_matriz=float(ed_prc_mat),
                                                    linhas_usadas=", ".join(ed_cores) if ed_cores else None,
                                                    codigo_identificacao=ed_cod.strip() if ed_cod.strip() else None,
                                                )
                                                st.success("Dados atualizados com sucesso!")
                                                st.rerun()

                                # 2. GERENCIAR FOTOS
                                with c_act2:
                                    with st.popover("📷 Fotos", key=f"pop_fot_{b.id}"):
                                        st.markdown(f"**Atualizar Fotos de:** {b.nome}")
                                        nova_dig = st.file_uploader(
                                            "Nova Imagem Digital",
                                            type=["png", "jpg", "jpeg", "webp"],
                                            key=f"alt_dig_{b.id}",
                                        )
                                        nova_foto = st.file_uploader(
                                            "Nova Foto Real",
                                            type=["png", "jpg", "jpeg", "webp"],
                                            key=f"alt_foto_{b.id}",
                                        )
                                        if st.button("Salvar Fotos", key=f"btn_salv_fotos_{b.id}", type="primary"):
                                            c_dig = (
                                                salvar_arquivo_upload(
                                                    nova_dig, f"digital_{b.codigo_identificacao or b.id}"
                                                )
                                                if nova_dig
                                                else None
                                            )
                                            c_fot = (
                                                salvar_arquivo_upload(
                                                    nova_foto, f"foto_{b.codigo_identificacao or b.id}"
                                                )
                                                if nova_foto
                                                else None
                                            )
                                            if c_dig or c_fot:
                                                CatalogoRepository.atualizar_imagens_template_bordado(
                                                    b.id,
                                                    imagem_digital=c_dig,
                                                    foto_bordado=c_fot,
                                                )
                                                st.success("Fotos atualizadas!")
                                                st.rerun()

                                # 3. EXCLUIR DIRETO NO CARD
                                with c_act3:
                                    with st.popover("🗑️ Excluir", key=f"pop_del_{b.id}"):
                                        st.markdown(f"Excluir **{b.nome}**?")
                                        st.caption("Esta ação não poderá ser desfeita.")
                                        if st.button("Sim, Excluir", key=f"btn_card_del_{b.id}", type="primary"):
                                            if CatalogoRepository.deletar_template_bordado(b.id):
                                                st.success("Bordado removido!")
                                                st.rerun()
                                            else:
                                                st.error("Erro ao remover.")

                            with col_img1:
                                st.markdown("**🖼️ Arte Digital / Mockup**")
                                if b.imagem_digital and os.path.exists(b.imagem_digital):
                                    st.image(b.imagem_digital, use_container_width=True)
                                else:
                                    st.info("Nenhuma imagem digital anexada.")

                            with col_img2:
                                st.markdown("**📸 Foto Real do Bordado**")
                                if b.foto_bordado and os.path.exists(b.foto_bordado):
                                    st.image(b.foto_bordado, use_container_width=True)
                                else:
                                    st.info("Nenhuma foto real anexada.")

                # MODO 2: TABELA GERAL
                else:
                    dados_bordados = []
                    for b in bordados_filtrados:
                        tem_digital = "🖼️ Sim" if b.imagem_digital and os.path.exists(b.imagem_digital) else "-"
                        tem_foto = "📸 Sim" if b.foto_bordado and os.path.exists(b.foto_bordado) else "-"

                        dados_bordados.append(
                            {
                                "ID": b.id,
                                "Código": b.codigo_identificacao or "-",
                                "Nome": b.nome,
                                "Tipo": b.tipo,
                                "Pontos": b.pontos,
                                "Preço Bordado": b.preco,
                                "Matriz Pronta": b.matriz_pronta,
                                "Preço Matriz": b.preco_matriz or 0.0,
                                "Linhas / Cores": b.linhas_usadas or "-",
                                "Arte Digital": tem_digital,
                                "Foto Real": tem_foto,
                            }
                        )

                    df_bordados = pd.DataFrame(dados_bordados)

                    st.dataframe(
                        df_bordados,
                        hide_index=True,
                        width="stretch",
                        column_config={
                            "ID": st.column_config.NumberColumn("ID", format="%d", width="small"),
                            "Código": st.column_config.TextColumn("Código", width="small"),
                            "Nome": st.column_config.TextColumn("Nome", width="medium"),
                            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                            "Pontos": st.column_config.NumberColumn("Pontos", format="%d pts", width="small"),
                            "Preço Bordado": st.column_config.NumberColumn("Preço Bordado", format="R$ %.2f", width="small"),
                            "Matriz Pronta": st.column_config.CheckboxColumn("Matriz Pronta", width="small"),
                            "Preço Matriz": st.column_config.NumberColumn("Preço Matriz", format="R$ %.2f", width="small"),
                            "Linhas / Cores": st.column_config.TextColumn("Linhas / Cores", width="medium"),
                            "Arte Digital": st.column_config.TextColumn("Arte Digital", width="small"),
                            "Foto Real": st.column_config.TextColumn("Foto Real", width="small"),
                        },
                    )

                    c_tot, c_acao = st.columns([3, 1])
                    with c_tot:
                        st.caption(f"Mostrando **{len(bordados_filtrados)}** de **{len(bordados)}** bordados cadastrados.")

                    with c_acao:
                        with st.popover("🗑️ Excluir Bordado do Acervo"):
                            st.markdown("**Remover bordado**")
                            opcoes_b = {
                                f"{b.nome} ({b.codigo_identificacao or f'ID: {b.id}'})": b.id
                                for b in bordados
                            }
                            bordado_sel = st.selectbox(
                                "Selecione o bordado para remover",
                                options=list(opcoes_b.keys()),
                                key="sel_bordado_del",
                            )
                            if st.button("Confirmar Exclusão", type="primary", key="btn_del_bordado"):
                                id_del = opcoes_b[bordado_sel]
                                if CatalogoRepository.deletar_template_bordado(id_del):
                                    st.success("Bordado removido com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Não foi possível excluir o bordado.")

    except Exception as e:
        st.error(f"Erro ao buscar os dados do catálogo de bordados: {e}")
