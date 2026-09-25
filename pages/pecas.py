import json
import os
import re
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

from core.models import TemplateBordado
from core.repository import CatalogoRepository
from utils.auth import obter_role_usuario, verificar_autenticacao
from utils.embroidery_reader import extrair_dados_matriz, renderizar_chips_cores_html
from utils.storage import upload_arquivo_imagem, migrar_imagens_locais_para_supabase
from indexar_acervo import localizar_pasta_acervo, indexar_arquivos

st.set_page_config(page_title="Catálogo de Bordados", page_icon="🏷️", layout="wide")

# Permissão pública de visualização básica para visitantes
verificar_autenticacao(role_minima="visitante")

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
    """Faz o upload para o Supabase Storage (com contingência local) e retorna a URL pública."""
    if not uploaded_file:
        return None
    return upload_arquivo_imagem(uploaded_file, prefixo=prefixo)


def renderizar_catalogo_pecas():
    """Renderiza a gestão de modelos de peças físicas (exclusivo para Admin)."""
    with st.expander("Cadastrar Novo Modelo de Peça", expanded=False):
        with st.form("form_novo_template", clear_on_submit=True):
            col_nome, col_locais = st.columns([1, 2])

            with col_nome:
                nome_peca = st.text_input(
                    "Nome do Modelo", placeholder="Ex: Jaqueta Corta Vento"
                )

            with col_locais:
                locais_cadastrados = CatalogoRepository.listar_todos_os_locais()
                locais_selecionados = st.multiselect(
                    "Locais de Bordado *",
                    options=locais_cadastrados,
                    placeholder="Selecione ou digite novos locais...",
                    accept_new_options=True,
                    help="Selecione locais já cadastrados ou digite novos e pressione Enter para adicionar",
                )

            st.markdown(" ")
            botao_salvar = st.form_submit_button("Salvar Modelo", type="primary")

            if botao_salvar:
                if not nome_peca.strip():
                    st.error("O nome da peça é obrigatório.")
                elif not locais_selecionados:
                    st.error("Selecione ou adicione pelo menos um local de bordado.")
                else:
                    lista_locais = [
                        local.strip() for local in locais_selecionados if local.strip()
                    ]

                    try:
                        CatalogoRepository.salvar_template_peca(nome_peca.strip(), lista_locais)
                        st.success(
                            f"Peça '{nome_peca}' cadastrada com sucesso com {len(lista_locais)} local(is)!"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")

    st.subheader("Modelos Cadastrados")

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
                with st.popover("Excluir Modelo", width="stretch"):
                    st.markdown("**Remover modelo cadastrado**")
                    opcoes_pecas = {f"{t.nome} (ID: {t.id})": t.id for t in templates}
                    peca_selecionada = st.selectbox(
                        "Selecione o modelo para remover",
                        options=list(opcoes_pecas.keys()),
                        key="sel_peca_del",
                    )
                    if st.button("Confirmar Exclusão", type="primary", width="stretch", key="btn_del_peca"):
                        id_del = opcoes_pecas[peca_selecionada]
                        if CatalogoRepository.deletar_template_peca(id_del):
                            st.success("Peça removida com sucesso!")
                            st.rerun()
                        else:
                            st.error("Não foi possível excluir a peça.")

    except Exception as e:
        st.error(f"Erro ao buscar os dados do catálogo: {e}")


def renderizar_acervo_bordados(role_usuario: str, is_admin: bool):
    """Renderiza a vitrine/gestão do acervo de matrizes de bordados com base na role."""
    is_visitante = (role_usuario == "visitante")
    is_cliente = (role_usuario == "cliente")

    # ---------------------------------------------------------------------
    # 1. FERRAMENTAS EXCLUSIVAS DE ADMINISTRADOR (SINCRONIZAÇÃO E CADASTRO)
    # ---------------------------------------------------------------------
    if is_admin:
        with st.expander("Sincronizar Pasta do Acervo (Logos, Brasões e Matrizes)", expanded=False):
            st.markdown(
                "Esta ferramenta analisa sua pasta local de matrizes organizada por **Tipo, Categoria e Subcategoria** "
                "(ex: `matrizes/Brasão/Faculdades/Unicesumar/Medicina.dst`), lê os arquivos com o **pyembroidery**, "
                "extrai pontos, dimensões e cores, e cadastra direto no banco de dados."
            )
            c_sync1, c_sync2 = st.columns([3, 1])
            with c_sync1:
                pasta_sugestao = str(localizar_pasta_acervo())
                caminho_dir = st.text_input(
                    "Caminho da Pasta do Acervo",
                    value=pasta_sugestao,
                    help="Pasta onde você organizou os arquivos .dst / .pes por pastas de cursos, faculdades ou empresas",
                    key="input_pasta_acervo",
                )
            with c_sync2:
                st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                btn_sync_pasta = st.button("Sincronizar Acervo", type="primary", width="stretch", key="btn_sync_acervo")

            if btn_sync_pasta:
                with st.spinner("Processando arquivos de bordado e extraindo dados com pyembroidery..."):
                    try:
                        p_obj = Path(caminho_dir)
                        if not p_obj.exists():
                            st.error(f"A pasta informada '{caminho_dir}' não existe.")
                        else:
                            indexar_arquivos(p_obj)
                            st.success("Acervo sincronizado com sucesso!")
                            st.rerun()
                    except Exception as err:
                        st.error(f"Erro na sincronização: {err}")

            st.markdown("---")
            c_sync_cloud1, c_sync_cloud2 = st.columns([3, 1])
            with c_sync_cloud1:
                st.caption("☁️ **Supabase Storage CDN:** Se você tiver imagens locais vinculadas anteriormente, envie-as para a nuvem pública do Supabase com um clique:")
            with c_sync_cloud2:
                if st.button("Enviar Imagens ao Supabase", width="stretch", key="btn_sync_cloud_storage"):
                    with st.spinner("Enviando imagens para o Supabase Storage..."):
                        res_mig = migrar_imagens_locais_para_supabase()
                        st.success(f"Migração concluída! {res_mig.get('migrados', 0)} imagem(ns) enviada(s) para o Supabase Storage.")
                        st.rerun()

        with st.expander("Cadastrar Novo Bordado Manualmente", expanded=False):
            st.caption("Você pode subir um arquivo de bordado (.dst, .pes, etc.) para extrair pontos, dimensões e cores automaticamente:")
            
            up_matriz_auto = st.file_uploader(
                "Arquivo da Matriz (.dst, .pes, .exp, .jef) [Opcional para Leitura]",
                type=["dst", "pes", "exp", "jef", "vp3"],
                key="up_matriz_auto",
                help="Ao selecionar o arquivo, os pontos, dimensões e paradas de agulha são lidos na hora pelo pyembroidery"
            )

            dados_auto = {}
            if up_matriz_auto:
                try:
                    dados_auto = extrair_dados_matriz(up_matriz_auto, up_matriz_auto.name) or {}
                    if dados_auto:
                        st.info(
                            f"**Dados extraídos do arquivo:** `{dados_auto.get('pontos', 0):,}` pontos | "
                            f"Dimensões: `{dados_auto.get('largura_mm', 0)} x {dados_auto.get('altura_mm', 0)} mm` | "
                            f"Trocas de Cor: `{dados_auto.get('trocas_cor', 0)}` | Linhas: `{dados_auto.get('linhas_usadas')}`"
                        )
                except Exception as e:
                    st.warning(f"Não foi possível ler os detalhes técnicos do arquivo: {e}")

            with st.form("form_novo_bordado", clear_on_submit=True):
                col_b1, col_b2, col_b3 = st.columns([2.2, 1.4, 1.4])
                with col_b1:
                    nome_sug = ""
                    if up_matriz_auto:
                        nome_raw = Path(up_matriz_auto.name).stem.replace("_", " ").strip()
                        for pref in ["brasão", "brasao", "logo fixo", "logo"]:
                            if nome_raw.lower().startswith(pref + " "):
                                nome_raw = nome_raw[len(pref) + 1:].strip()
                                break
                        nome_sug = nome_raw

                    nome_bordado = st.text_input(
                        "Nome do Bordado / Matriz *",
                        value=nome_sug,
                        placeholder="Ex: Medicina Unicesumar",
                        help="Nome de identificação do bordado (sem precisar repetir o tipo)",
                    )
                with col_b2:
                    categorias_existentes = CatalogoRepository.listar_categorias_matriz()
                    categoria_sug = st.selectbox(
                        "Categoria *",
                        options=categorias_existentes,
                        index=None,
                        placeholder="Selecione ou digite...",
                        accept_new_options=True,
                        help="Assunto principal ou grupo (apenas cadastradas ou nova)",
                    )
                with col_b3:
                    subcategorias_existentes = CatalogoRepository.listar_subcategorias_matriz()
                    subcategoria_sug = st.selectbox(
                        "Subcategoria / Instituição",
                        options=subcategorias_existentes,
                        index=None,
                        placeholder="Selecione ou digite...",
                        accept_new_options=True,
                        help="Instituição, faculdade, especialidade ou cliente específico (apenas cadastradas ou nova)",
                    )

                col_t1, col_t2, col_t3 = st.columns([1.5, 1.5, 1.5])
                with col_t1:
                    tipos_existentes = CatalogoRepository.listar_tipos_matriz()
                    tipo_bordado = st.selectbox(
                        "Tipo *",
                        options=tipos_existentes,
                        index=0 if tipos_existentes else None,
                        placeholder="Selecione ou digite...",
                        accept_new_options=True,
                        help="Tipo ou categoria do bordado (apenas cadastrados ou novo)",
                    )
                with col_t2:
                    codigo_identificacao = st.text_input(
                        "Código de Identificação",
                        placeholder="Ex: BRAS-01 / MAT-2024",
                        help="Código interno ou referência de arquivo",
                    )
                with col_t3:
                    pontos_val = dados_auto.get("pontos", 5000)
                    pontos = st.number_input(
                        "Contagem de Pontos *",
                        min_value=0,
                        value=int(pontos_val),
                        step=500,
                        help="Quantidade de pontos estimada ou exata da matriz",
                    )

                col_dim1, col_dim2, col_dim3, col_dim4 = st.columns([1.2, 1.2, 1.2, 1.4])
                with col_dim1:
                    larg_val = float(dados_auto.get("largura_mm", 0.0))
                    largura_input = st.number_input("Largura (mm)", min_value=0.0, value=larg_val, step=1.0, format="%.1f")
                with col_dim2:
                    alt_val = float(dados_auto.get("altura_mm", 0.0))
                    altura_input = st.number_input("Altura (mm)", min_value=0.0, value=alt_val, step=1.0, format="%.1f")
                with col_dim3:
                    matriz_pronta_opt = st.selectbox(
                        "Matriz Pronta?",
                        options=["Sim", "Não"],
                        index=0,
                        help="Indica se a matriz computadorizada já está digitalizada e pronta",
                    )
                with col_dim4:
                    visibilidade_opt = st.selectbox(
                        "Visibilidade por Papel (Role) *",
                        options=["todos", "cliente", "admin"],
                        format_func=lambda v: (
                            "🌐 Todos (Visitantes & Clientes)" if v in ["todos", "visitante"]
                            else ("👤 Apenas Clientes & Admin" if v == "cliente"
                            else "👑 Apenas Administradores (Privado)")
                        ),
                        index=0,
                        help="Define quais perfis de usuário podem ver este bordado no catálogo",
                        key="sel_visibilidade_pecas",
                    )

                mapa_cores_cadastradas = CatalogoRepository.listar_cores_matriz_cadastradas()
                opcoes_cores = sorted(list(mapa_cores_cadastradas.keys()))

                cores_do_arquivo = []
                if dados_auto and dados_auto.get("linhas_usadas"):
                    for c in dados_auto["linhas_usadas"].split(","):
                        c_limpo = c.strip()
                        if c_limpo and not c_limpo.endswith("cores"):
                            cores_do_arquivo.append(c_limpo)
                            if c_limpo not in opcoes_cores:
                                opcoes_cores.append(c_limpo)
                    opcoes_cores = sorted(list(set(opcoes_cores)))

                cores_selecionadas = st.multiselect(
                    "Códigos das Cores da Linha",
                    options=opcoes_cores,
                    default=cores_do_arquivo,
                    accept_new_options=False,
                    placeholder="Selecione os códigos de cores já cadastrados no catálogo...",
                    help="Apenas códigos de cores já cadastrados com referência visual (sem novos cadastros sem hex associado)",
                )

                col_img_d, col_img_f = st.columns(2)
                with col_img_d:
                    upload_digital = st.file_uploader(
                        "Imagem Digital (Mockup / Arte) [Upload Direto Supabase]",
                        type=["png", "jpg", "jpeg", "webp"],
                        help="Arte digital enviada automaticamente para o Supabase Storage",
                        key="up_digital",
                    )
                with col_img_f:
                    upload_foto = st.file_uploader(
                        "Foto do Bordado Real [Upload Direto Supabase]",
                        type=["png", "jpg", "jpeg", "webp"],
                        help="Fotografia real da peça enviada automaticamente para o Supabase Storage",
                        key="up_foto",
                    )

                st.markdown(" ")
                btn_salvar_bordado = st.form_submit_button(
                    "Salvar Bordado", type="primary"
                )

                if btn_salvar_bordado:
                    if not nome_bordado.strip():
                        st.error("O Nome do bordado é obrigatório.")
                    elif not tipo_bordado or not str(tipo_bordado).strip():
                        st.error("O Tipo do bordado é obrigatório.")
                    elif pontos <= 0:
                        st.error("A contagem de pontos deve ser maior que zero.")
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

                            linhas_usadas_salvar = ", ".join(cores_selecionadas) if cores_selecionadas else None

                            if dados_auto and dados_auto.get("cores_detalhes") and cores_selecionadas == cores_do_arquivo:
                                detalhes_salvar = dados_auto["cores_detalhes"]
                            elif cores_selecionadas:
                                detalhes_lista = []
                                for idx, cod in enumerate(cores_selecionadas):
                                    hex_c = mapa_cores_cadastradas.get(cod) or "#888888"
                                    detalhes_lista.append({
                                        "posicao": idx + 1,
                                        "codigo": cod,
                                        "descricao": None,
                                        "marca": None,
                                        "hex": hex_c
                                    })
                                detalhes_salvar = json.dumps(detalhes_lista, ensure_ascii=False)
                            else:
                                detalhes_salvar = None

                            novo_bordado = TemplateBordado(
                                nome=nome_bordado.strip(),
                                categoria=str(categoria_sug).strip() if categoria_sug and str(categoria_sug).strip() else None,
                                subcategoria=str(subcategoria_sug).strip() if subcategoria_sug and str(subcategoria_sug).strip() else None,
                                tipo=str(tipo_bordado).strip(),
                                pontos=int(pontos),
                                largura_mm=float(largura_input) if largura_input > 0 else None,
                                altura_mm=float(altura_input) if altura_input > 0 else None,
                                trocas_cor=int(dados_auto.get("trocas_cor", 0)) if dados_auto else max(0, len(cores_selecionadas) - 1),
                                preco=0.0,
                                matriz_pronta=(matriz_pronta_opt == "Sim"),
                                preco_matriz=0.0,
                                linhas_usadas=linhas_usadas_salvar,
                                cores_detalhes=detalhes_salvar,
                                codigo_identificacao=codigo_identificacao.strip() if codigo_identificacao and codigo_identificacao.strip() else None,
                                visibilidade=visibilidade_opt,
                                imagem_digital=caminho_digital,
                                foto_bordado=caminho_foto,
                            )
                            CatalogoRepository.salvar_template_bordado(novo_bordado)
                            st.success(f"Bordado '{nome_bordado}' cadastrado com sucesso no catálogo!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar bordado no banco: {e}")

    # ---------------------------------------------------------------------
    # 2. CARREGAMENTO DOS BORDADOS DO BANCO
    # ---------------------------------------------------------------------
    try:
        bordados = CatalogoRepository.listar_templates_bordado(role_usuario=role_usuario)

        if not bordados:
            st.info("O catálogo de bordados ainda está vazio.")
            return

        # Prepara listas de categorias/tipos existentes
        categorias_existentes = sorted(list(set(b.categoria for b in bordados if b.categoria)))
        subcategorias_existentes = sorted(list(set(b.subcategoria for b in bordados if b.subcategoria)))
        tipos_existentes = sorted(list(set(b.tipo for b in bordados if b.tipo)))

        # ---------------------------------------------------------------------
        # 3. MODO VISITANTE (SEM FILTROS, COM BANNER DE CADASTRO)
        # ---------------------------------------------------------------------
        if is_visitante:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(42,157,143,0.18), rgba(29,53,87,0.25)); border: 1px solid rgba(42,157,143,0.4); border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;">
                    <h4 style="margin:0 0 6px 0; color:#2a9d8f;">🔓 Visualizando como Visitante</h4>
                    <p style="margin:0 0 8px 0; font-size:13.5px; color:#ddd;">
                        Você está explorando uma amostra do acervo aberto de matrizes e bordados da confecção.
                        <strong>Crie sua conta gratuita ou entre</strong> para desbloquear a busca por termos, filtros por faculdade, instituição, especialidade e a ferramenta de simulação e geração de bordados!
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_cta1, col_cta2 = st.columns([1.6, 2.4])
            with col_cta1:
                if st.button("🚀 Criar Conta / Entrar para Liberar Filtros", type="primary", width="stretch", key="btn_cta_visitante_topo"):
                    st.switch_page("pages/login.py")
            st.markdown(" ")

            # Visitante vê a lista diretamente sem barra de filtros
            bordados_filtrados = bordados
            modo_exibicao = "Cards Detalhados"
            st.caption(f"Mostrando **{len(bordados_filtrados)}** matrizes do acervo aberto:")

        # ---------------------------------------------------------------------
        # 4. MODO CLIENTE E ADMIN (COM KPIs E BARRA DE FILTROS COMPLETA)
        # ---------------------------------------------------------------------
        else:
            # 1. Métricas / KPIs Resumidas
            total_itens = len(bordados)
            prontas_count = sum(1 for b in bordados if b.matriz_pronta)
            com_imagem_count = sum(1 for b in bordados if b.imagem_digital or b.foto_bordado)
            media_pontos = sum(b.pontos for b in bordados) / total_itens if total_itens else 0

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total no Acervo", f"{total_itens} matrizes")
            kpi2.metric("Matrizes Prontas", f"{prontas_count} ({int(prontas_count / total_itens * 100)}%)")
            kpi3.metric("Com Imagens / Fotos", f"{com_imagem_count} itens")
            kpi4.metric("Média de Pontos", f"{int(media_pontos):,} pts".replace(",", "."))

            st.markdown(" ")

            # 2. Barra de Filtros e Modo de Visualização (Admin tem filtro extra de visibilidade por role)
            if is_admin:
                f_col1, f_col2, f_col3, f_col4, f_col_vis, f_col5 = st.columns([1.8, 1.1, 1.1, 1.0, 1.2, 1.0])
                with f_col_vis:
                    filtro_vis = st.selectbox(
                        "Visibilidade Role",
                        options=["Todas", "🌐 Todos (Público)", "👤 Clientes & Admin", "👑 Admin (Privado)"],
                        key="filtro_visibilidade_admin",
                    )
            else:
                f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([2.0, 1.2, 1.2, 1.1, 1.1])
                filtro_vis = "Todas"

            with f_col1:
                busca_texto = st.text_input(
                    "Buscar bordado",
                    placeholder="Filtrar por nome, código, instituição ou cores...",
                    key="busca_bordado",
                )
            with f_col2:
                filtro_categoria = st.selectbox(
                    "Categoria",
                    options=["Todas"] + categorias_existentes,
                    key="filtro_categoria_bordado",
                )
            with f_col3:
                filtro_subcategoria = st.selectbox(
                    "Subcategoria / Instituição",
                    options=["Todas"] + subcategorias_existentes,
                    key="filtro_subcategoria_bordado",
                )
            with f_col4:
                filtro_tipo = st.selectbox(
                    "Tipo",
                    options=["Todos"] + tipos_existentes,
                    key="filtro_tipo_bordado",
                )
            with f_col5:
                modo_exibicao = st.selectbox(
                    "Visualização",
                    options=["Cards Detalhados", "Tabela Técnica"],
                    key="modo_exibicao_bordado",
                )

            # Aplicação dos filtros selecionados
            bordados_filtrados = bordados
            if busca_texto.strip():
                termo = busca_texto.strip().lower()
                bordados_filtrados = [
                    b
                    for b in bordados_filtrados
                    if termo in b.nome.lower()
                    or (b.categoria and termo in b.categoria.lower())
                    or (b.subcategoria and termo in b.subcategoria.lower())
                    or (b.codigo_identificacao and termo in b.codigo_identificacao.lower())
                    or (b.linhas_usadas and termo in b.linhas_usadas.lower())
                ]

            if filtro_categoria != "Todas":
                bordados_filtrados = [
                    b for b in bordados_filtrados if b.categoria == filtro_categoria
                ]

            if filtro_subcategoria != "Todas":
                bordados_filtrados = [
                    b for b in bordados_filtrados if b.subcategoria == filtro_subcategoria
                ]

            if filtro_tipo != "Todos":
                bordados_filtrados = [
                    b for b in bordados_filtrados if b.tipo == filtro_tipo
                ]

            if is_admin and filtro_vis != "Todas":
                if filtro_vis == "🌐 Todos (Público)":
                    bordados_filtrados = [b for b in bordados_filtrados if b.visibilidade in ["todos", "visitante"]]
                elif filtro_vis == "👤 Clientes & Admin":
                    bordados_filtrados = [b for b in bordados_filtrados if b.visibilidade == "cliente"]
                elif filtro_vis == "👑 Admin (Privado)":
                    bordados_filtrados = [b for b in bordados_filtrados if b.visibilidade in ["admin", "restrito"]]

            st.caption(f"Mostrando **{len(bordados_filtrados)}** de **{len(bordados)}** matrizes do acervo:")

        # ---------------------------------------------------------------------
        # 5. RENDERIZAÇÃO DOS RESULTADOS (CARDS OU TABELA)
        # ---------------------------------------------------------------------
        if not bordados_filtrados:
            st.warning("Nenhum bordado encontrado com os filtros selecionados.")
            return

        # MODO 1: CARDS DETALHADOS
        if modo_exibicao == "Cards Detalhados":
            st.markdown(
                """
                <style>
                div[data-testid="stColumn"] div[data-testid="stPopover"] > button {
                    padding: 0.2rem 0.4rem !important;
                    font-size: 0.82rem !important;
                    min-height: 38px !important;
                    height: 38px !important;
                    border-radius: 6px !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            for b in bordados_filtrados:
                qtd_cores = 1
                if b.cores_detalhes:
                    try:
                        th = json.loads(b.cores_detalhes)
                        vistas = set(str(t.get("codigo") or t.get("hex") or "").strip() for t in th if (t.get("codigo") or t.get("hex")))
                        qtd_cores = len(vistas) if vistas else len(th)
                    except Exception:
                        qtd_cores = 1
                elif b.linhas_usadas:
                    qtd_cores = len([c for c in b.linhas_usadas.split(",") if c.strip()])

                texto_cores = f"{qtd_cores} cor" if qtd_cores == 1 else f"{qtd_cores} cores"
                pontos_formatado = f"{b.pontos:,}".replace(",", ".")
                titulo_card = f"[{b.tipo}] **{b.nome}** — {texto_cores} | {pontos_formatado} pts"

                # Layout de colunas adaptativo conforme a role
                if is_admin:
                    col_card, col_edit, col_del = st.columns([12, 1.5, 1.5], vertical_alignment="top")
                else:
                    col_card, col_acao = st.columns([11.8, 3.2], vertical_alignment="top")

                with col_card:
                    with st.expander(titulo_card, expanded=False):
                        c_det, c_img1, c_img2 = st.columns([1.8, 1.1, 1.1])
                        with c_det:
                            hierarquia = [x for x in [b.categoria, b.subcategoria] if x]
                            if hierarquia:
                                st.markdown(f"**Grupo:** `{' > '.join(hierarquia)}`")
                            st.markdown(f"**Código:** `{b.codigo_identificacao or 'N/A'}` | **Tipo:** `{b.tipo}`")
                            if b.largura_mm and b.altura_mm:
                                st.markdown(f"**Dimensões:** `{b.largura_mm:.1f} x {b.altura_mm:.1f} mm`")
                            status_mat = "Matriz Pronta" if b.matriz_pronta else "Matriz Pendente"
                            st.markdown(f"**Status:** {status_mat}")

                            # Badge de visibilidade por role (informativo para Admin)
                            if is_admin:
                                badge_vis = (
                                    "🌐 Visível para Todos" if b.visibilidade in ["todos", "visitante"]
                                    else ("👤 Apenas Clientes & Admin" if b.visibilidade == "cliente"
                                    else "👑 Apenas Administradores (Privado)")
                                )
                                cor_vis = (
                                    "#2a9d8f" if b.visibilidade in ["todos", "visitante"]
                                    else ("#457b9d" if b.visibilidade == "cliente"
                                    else "#e63946")
                                )
                                st.markdown(
                                    f"**Visibilidade:** <span style='background:{cor_vis}; color:#fff; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;'>{badge_vis}</span>",
                                    unsafe_allow_html=True,
                                )

                            palette_html = renderizar_chips_cores_html(b.cores_detalhes, b.linhas_usadas)
                            if palette_html:
                                st.markdown("**Cores da Matriz:**", unsafe_allow_html=True)
                                st.markdown(palette_html, unsafe_allow_html=True)
                            elif b.linhas_usadas:
                                st.markdown(f"**Cores:** `{b.linhas_usadas}`")

                        with c_img1:
                            st.markdown("**Arte Digital**")
                            tem_dig = b.imagem_digital and (b.imagem_digital.startswith("http") or os.path.exists(b.imagem_digital))
                            if tem_dig:
                                st.image(b.imagem_digital, width="stretch")
                            else:
                                st.caption("Sem imagem digital")

                        with c_img2:
                            st.markdown("**Foto Real**")
                            tem_fot = b.foto_bordado and (b.foto_bordado.startswith("http") or os.path.exists(b.foto_bordado))
                            if tem_fot:
                                st.image(b.foto_bordado, width="stretch")
                            else:
                                st.caption("Sem foto real")

                            if is_admin:
                                with st.popover("Fotos", key=f"pop_fot_{b.id}", width="stretch"):
                                    st.markdown(f"**Atualizar Fotos (Supabase Storage):** [{b.tipo}] {b.nome}")
                                    nova_dig = st.file_uploader("Arte Digital", type=["png", "jpg", "jpeg", "webp"], key=f"alt_dig_{b.id}")
                                    nova_foto = st.file_uploader("Foto Real", type=["png", "jpg", "jpeg", "webp"], key=f"alt_foto_{b.id}")
                                    if st.button("Salvar Fotos no Supabase", key=f"btn_salv_fotos_{b.id}", type="primary", width="stretch"):
                                        c_dig = salvar_arquivo_upload(nova_dig, f"digital_{b.codigo_identificacao or b.id}") if nova_dig else None
                                        c_fot = salvar_arquivo_upload(nova_foto, f"foto_{b.codigo_identificacao or b.id}") if nova_foto else None
                                        if c_dig or c_fot:
                                            CatalogoRepository.atualizar_imagens_template_bordado(b.id, imagem_digital=c_dig, foto_bordado=c_fot)
                                            st.success("Fotos enviadas para o Supabase com sucesso!")
                                            st.rerun()

                # Ações de administração
                if is_admin:
                    with col_edit:
                        with st.popover("Editar", help=f"Editar {b.nome}", width="stretch"):
                            st.markdown(f"**Editar Matriz #{b.id}**")
                            ed_nome = st.text_input("Nome *", value=b.nome, key=f"ed_nom_{b.id}")
                            ed_cat = st.selectbox(
                                "Categoria",
                                options=categorias_existentes,
                                index=categorias_existentes.index(b.categoria) if b.categoria in categorias_existentes else None,
                                placeholder="Selecione ou digite...",
                                accept_new_options=True,
                                key=f"ed_cat_{b.id}",
                            )
                            ed_sub = st.selectbox(
                                "Subcategoria / Instituição",
                                options=subcategorias_existentes,
                                index=subcategorias_existentes.index(b.subcategoria) if b.subcategoria in subcategorias_existentes else None,
                                placeholder="Selecione ou digite...",
                                accept_new_options=True,
                                key=f"ed_sub_{b.id}",
                            )
                            ed_tipo = st.selectbox(
                                "Tipo *",
                                options=tipos_existentes,
                                index=tipos_existentes.index(b.tipo) if b.tipo in tipos_existentes else None,
                                placeholder="Selecione ou digite...",
                                accept_new_options=True,
                                key=f"ed_tip_{b.id}",
                            )

                            opcoes_vis = ["todos", "cliente", "admin"]
                            vis_val = b.visibilidade if b.visibilidade in opcoes_vis else "todos"
                            ed_vis = st.selectbox(
                                "Visibilidade por Papel (Role) *",
                                options=opcoes_vis,
                                index=opcoes_vis.index(vis_val),
                                format_func=lambda v: (
                                    "🌐 Todos (Visitantes & Clientes)" if v in ["todos", "visitante"]
                                    else ("👤 Apenas Clientes & Admin" if v == "cliente"
                                    else "👑 Apenas Administradores (Privado)")
                                ),
                                key=f"ed_vis_{b.id}",
                                help="Controla quem pode ver esta matriz no catálogo",
                            )

                            ed_cod = st.text_input("Código", value=b.codigo_identificacao or "", key=f"ed_cod_{b.id}")
                            ed_pts = st.number_input("Pontos *", min_value=0, value=int(b.pontos), step=500, key=f"ed_pts_{b.id}")
                            ed_larg = st.number_input("Largura (mm)", min_value=0.0, value=float(b.largura_mm or 0.0), step=1.0, format="%.1f", key=f"ed_larg_{b.id}")
                            ed_alt = st.number_input("Altura (mm)", min_value=0.0, value=float(b.altura_mm or 0.0), step=1.0, format="%.1f", key=f"ed_alt_{b.id}")
                            ed_mat = st.selectbox("Matriz Pronta?", options=["Sim", "Não"], index=0 if b.matriz_pronta else 1, key=f"ed_mat_{b.id}")
                            ed_linhas = st.text_input("Códigos das Cores", value=b.linhas_usadas or "", key=f"ed_lin_{b.id}")

                            if st.button("Salvar Alterações", key=f"btn_salv_ed_{b.id}", type="primary", width="stretch"):
                                if not ed_nome.strip():
                                    st.error("Nome é obrigatório.")
                                else:
                                    CatalogoRepository.atualizar_template_bordado(
                                        bordado_id=b.id,
                                        nome=ed_nome.strip(),
                                        tipo=str(ed_tipo).strip(),
                                        categoria=ed_cat.strip() if ed_cat.strip() else None,
                                        subcategoria=ed_sub.strip() if ed_sub.strip() else None,
                                        pontos=int(ed_pts),
                                        largura_mm=float(ed_larg) if ed_larg > 0 else None,
                                        altura_mm=float(ed_alt) if ed_alt > 0 else None,
                                        matriz_pronta=(ed_mat == "Sim"),
                                        linhas_usadas=ed_linhas.strip() if ed_linhas.strip() else None,
                                        codigo_identificacao=ed_cod.strip() if ed_cod.strip() else None,
                                        visibilidade=ed_vis,
                                    )
                                    st.success("Atualizado com sucesso!")
                                    st.rerun()

                    with col_del:
                        with st.popover("Excluir", help=f"Excluir {b.nome}", width="stretch"):
                            st.markdown(f"Excluir **[{b.tipo}] {b.nome}**?")
                            st.caption("Esta ação não poderá ser desfeita.")
                            if st.button("Confirmar Exclusão", key=f"btn_card_del_{b.id}", type="primary", width="stretch"):
                                if CatalogoRepository.deletar_template_bordado(b.id):
                                    st.success("Bordado removido!")
                                    st.rerun()
                                else:
                                    st.error("Não foi possível excluir o bordado.")

                # Ações de Cliente (Simulação direta)
                elif is_cliente:
                    with col_acao:
                        if st.button("Simular Bordado ➔", key=f"btn_sim_{b.id}", type="primary", width="stretch"):
                            st.switch_page("pages/gerar_bordado.py")

                # Ações de Visitante (Incentivo ao Cadastro)
                elif is_visitante:
                    with col_acao:
                        if st.button("Cadastrar-se ➔", key=f"btn_cad_card_{b.id}", width="stretch"):
                            st.switch_page("pages/login.py")

        # MODO 2: TABELA TÉCNICA (Disponível para Cliente e Admin)
        else:
            dados_bordados = []
            for b in bordados_filtrados:
                tem_digital = "Sim" if b.imagem_digital and (b.imagem_digital.startswith("http") or os.path.exists(b.imagem_digital)) else "-"
                tem_foto = "Sim" if b.foto_bordado and (b.foto_bordado.startswith("http") or os.path.exists(b.foto_bordado)) else "-"
                dim_str = f"{b.largura_mm:.1f} x {b.altura_mm:.1f} mm" if (b.largura_mm and b.altura_mm) else "-"

                item_tab = {
                    "ID": b.id,
                    "Código": b.codigo_identificacao or "-",
                    "Nome": b.nome,
                    "Categoria": b.categoria or "-",
                    "Subcategoria": b.subcategoria or "-",
                    "Tipo": b.tipo,
                    "Pontos": b.pontos,
                    "Dimensões": dim_str,
                    "Matriz Pronta": b.matriz_pronta,
                    "Cores (Códigos)": b.linhas_usadas or "-",
                    "Arte Digital": tem_digital,
                    "Foto Real": tem_foto,
                }
                if is_admin:
                    item_tab["Visibilidade"] = b.visibilidade.capitalize()

                dados_bordados.append(item_tab)

            df_bordados = pd.DataFrame(dados_bordados)

            cfg_colunas = {
                "ID": st.column_config.NumberColumn("ID", format="%d", width="small"),
                "Código": st.column_config.TextColumn("Código", width="small"),
                "Nome": st.column_config.TextColumn("Nome", width="medium"),
                "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                "Subcategoria": st.column_config.TextColumn("Subcategoria", width="small"),
                "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                "Pontos": st.column_config.NumberColumn("Pontos", format="%d pts", width="small"),
                "Dimensões": st.column_config.TextColumn("Dimensões", width="small"),
                "Matriz Pronta": st.column_config.CheckboxColumn("Matriz Pronta", width="small"),
                "Cores (Códigos)": st.column_config.TextColumn("Cores (Códigos)", width="medium"),
                "Arte Digital": st.column_config.TextColumn("Arte Digital", width="small"),
                "Foto Real": st.column_config.TextColumn("Foto Real", width="small"),
            }
            if is_admin:
                cfg_colunas["Visibilidade"] = st.column_config.TextColumn("Visibilidade", width="small")

            st.dataframe(
                df_bordados,
                hide_index=True,
                width="stretch",
                column_config=cfg_colunas,
            )

            c_tot, c_acao = st.columns([3, 1])
            with c_tot:
                st.caption(f"Mostrando **{len(bordados_filtrados)}** de **{len(bordados)}** matrizes cadastradas.")

            if is_admin:
                with c_acao:
                    with st.popover("Excluir Bordado", width="stretch"):
                        st.markdown("**Remover bordado**")
                        opcoes_b = {
                            f"[{b.tipo}] {b.nome} ({b.codigo_identificacao or f'ID: {b.id}'})": b.id
                            for b in bordados
                        }
                        bordado_sel = st.selectbox(
                            "Selecione o bordado para remover",
                            options=list(opcoes_b.keys()),
                            key="sel_bordado_del",
                        )
                        if st.button("Confirmar Exclusão", type="primary", width="stretch", key="btn_del_bordado"):
                            id_del = opcoes_b[bordado_sel]
                            if CatalogoRepository.deletar_template_bordado(id_del):
                                st.success("Bordado removido com sucesso!")
                                st.rerun()
                            else:
                                st.error("Não foi possível excluir o bordado.")

    except Exception as e:
        st.error(f"Erro ao buscar os dados do catálogo de bordados: {e}")


# =====================================================================
# FLUXO PRINCIPAL DA PÁGINA COM BASE NO PAPEL DO USUÁRIO
# =====================================================================
role_atual = obter_role_usuario()
is_admin = (role_atual == "admin")
is_cliente = (role_atual == "cliente")
is_visitante = (role_atual == "visitante")

if is_admin:
    st.title("Gestão do Catálogo")
    st.caption("Gerencie o catálogo de peças confeccionadas e o acervo completo de bordados, matrizes e imagens com Supabase Storage.")
    tab_pecas, tab_bordados = st.tabs(["Modelos de Peças", "Acervo de Bordados"])
    with tab_pecas:
        renderizar_catalogo_pecas()
    with tab_bordados:
        renderizar_acervo_bordados(role_atual, is_admin=True)
else:
    st.title("Catálogo de Bordados & Matrizes")
    if is_cliente:
        st.caption("Explore nosso acervo completo com filtros avançados e personalize bordados computadorizados.")
    else:
        st.caption("Conheça uma amostra do nosso acervo de bordados computadorizados.")
    renderizar_acervo_bordados(role_atual, is_admin=False)
