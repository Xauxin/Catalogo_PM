from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from core.database import get_session
from core.models import Bordado, LocalBordado, Lote, Peca, TemplateBordado, TemplatePeca


# =====================================================================
# 1. REPOSITÓRIO DO CATÁLOGO (Templates)
# =====================================================================
class CatalogoRepository:
    """Gerencia as configurações prévias de peças, locais permitidos e catálogo de bordados."""

    @staticmethod
    def salvar_template_peca(nome_peca: str, nomes_locais: list[str]) -> TemplatePeca:
        """Cria um template de peça (ex: Camisa Polo) e vincula seus locais permitidos."""
        with get_session() as session:
            template = TemplatePeca(nome=nome_peca)
            session.add(template)
            session.commit()  # Salva para gerar o ID da peça

            for nome_local in nomes_locais:
                local = LocalBordado(nome=nome_local, template_peca_id=template.id)
                session.add(local)

            session.commit()
            session.refresh(template)
            return template

    @staticmethod
    def listar_templates() -> list[TemplatePeca]:
        """Retorna todas as peças do catálogo carregando seus locais via Join."""
        with get_session() as session:
            statement = select(TemplatePeca).options(joinedload(TemplatePeca.locais_permitidos))
            return list(session.exec(statement).unique().all())

    @staticmethod
    def deletar_template_peca(template_id: int) -> bool:
        """Remove uma peça do catálogo e seus respectivos locais permitidos."""
        with get_session() as session:
            statement = (
                select(TemplatePeca)
                .where(TemplatePeca.id == template_id)
                .options(joinedload(TemplatePeca.locais_permitidos))
            )
            template = session.exec(statement).first()
            if template:
                for local in template.locais_permitidos:
                    session.delete(local)
                session.delete(template)
                session.commit()
                return True
            return False

    @staticmethod
    def salvar_template_bordado(template: TemplateBordado) -> TemplateBordado:
        """Salva ou atualiza um template de bordado / matriz no catálogo."""
        with get_session() as session:
            session.add(template)
            session.commit()
            session.refresh(template)
            return template

    @staticmethod
    def listar_templates_bordado() -> list[TemplateBordado]:
        """Retorna todos os bordados cadastrados no catálogo ordenados por ID desc."""
        with get_session() as session:
            statement = select(TemplateBordado).order_by(TemplateBordado.id.desc())
            return list(session.exec(statement).all())

    @staticmethod
    def deletar_template_bordado(bordado_id: int) -> bool:
        """Remove um template de bordado do catálogo."""
        with get_session() as session:
            template = session.get(TemplateBordado, bordado_id)
            if template:
                session.delete(template)
                session.commit()
                return True
            return False

    @staticmethod
    def atualizar_imagens_template_bordado(
        bordado_id: int,
        imagem_digital: str | None = None,
        foto_bordado: str | None = None,
    ) -> bool:
        """Atualiza os caminhos das imagens (digital e/ou foto real) de um bordado."""
        with get_session() as session:
            template = session.get(TemplateBordado, bordado_id)
            if template:
                if imagem_digital is not None:
                    template.imagem_digital = imagem_digital
                if foto_bordado is not None:
                    template.foto_bordado = foto_bordado
                session.add(template)
                session.commit()
                return True
            return False

    @staticmethod
    def atualizar_template_bordado(
        bordado_id: int,
        nome: str | None = None,
        tipo: str | None = None,
        pontos: int | None = None,
        preco: float | None = None,
        matriz_pronta: bool | None = None,
        preco_matriz: float | None = None,
        linhas_usadas: str | None = None,
        codigo_identificacao: str | None = None,
        categoria: str | None = None,
        subcategoria: str | None = None,
        largura_mm: float | None = None,
        altura_mm: float | None = None,
        trocas_cor: int | None = None,
        cores_detalhes: str | None = None,
        arquivo_dst: str | None = None,
    ) -> bool:
        """Atualiza os dados cadastrais de um bordado/matriz existente."""
        with get_session() as session:
            template = session.get(TemplateBordado, bordado_id)
            if template:
                if nome is not None:
                    template.nome = nome
                if tipo is not None:
                    template.tipo = tipo
                if pontos is not None:
                    template.pontos = pontos
                if preco is not None:
                    template.preco = preco
                if matriz_pronta is not None:
                    template.matriz_pronta = matriz_pronta
                if preco_matriz is not None:
                    template.preco_matriz = preco_matriz
                if linhas_usadas is not None:
                    template.linhas_usadas = linhas_usadas
                if codigo_identificacao is not None:
                    template.codigo_identificacao = codigo_identificacao
                if categoria is not None:
                    template.categoria = categoria
                if subcategoria is not None:
                    template.subcategoria = subcategoria
                if largura_mm is not None:
                    template.largura_mm = largura_mm
                if altura_mm is not None:
                    template.altura_mm = altura_mm
                if trocas_cor is not None:
                    template.trocas_cor = trocas_cor
                if cores_detalhes is not None:
                    template.cores_detalhes = cores_detalhes
                if arquivo_dst is not None:
                    template.arquivo_dst = arquivo_dst
                session.add(template)
                session.commit()
                return True
            return False


# =====================================================================
# 2. REPOSITÓRIO DA OPERAÇÃO (Lotes e Pedidos)
# =====================================================================
class LoteRepository:
    """Gerencia toda a criação, leitura e atualização dos lotes de produção."""

    @staticmethod
    def criar_lote_completo(lote: Lote, estrutura_pedido: list[dict]) -> Lote:
        """
        Salva toda a estrutura hierárquica de um novo pedido no banco de dados.
        O argumento 'estrutura_pedido' deve ser uma lista de dicionários contendo a peça
        e seus respectivos bordados associados.
        """
        with get_session() as session:
            # 1. Salva o Lote Principal (Cliente, datas, etc.)
            session.add(lote)
            session.commit()  # Gera o ID do Lote

            # 2. Processa as Peças enviadas na estrutura
            for item in estrutura_pedido:
                peca_dados: Peca = item["peca"]
                bordados_dados: list[Bordado] = item["bordados"]

                # Vincula a peça física ao lote pai
                peca_dados.lote_id = lote.id
                session.add(peca_dados)
                session.commit()  # Gera o ID da Peça

                # 3. Processa e vincula os bordados à peça criada
                for bordado in bordados_dados:
                    bordado.peca_id = peca_dados.id
                    session.add(bordado)

            session.commit()
            session.refresh(lote)
            return lote

    @staticmethod
    def listar_todos_os_lotes() -> list[Lote]:
        """Puxa o histórico de todos os lotes, trazendo as peças e bordados associados."""
        with get_session() as session:
            # Ordenado pelo ID mais recente com peças e bordados carregados antecipadamente
            statement = (
                select(Lote)
                .options(selectinload(Lote.pecas).selectinload(Peca.bordados))
                .order_by(Lote.id.desc())
            )
            return list(session.exec(statement).all())

    @staticmethod
    def buscar_por_id(lote_id: int) -> Lote | None:
        """Busca um lote específico pelo ID com suas peças e bordados carregados."""
        with get_session() as session:
            statement = (
                select(Lote)
                .where(Lote.id == lote_id)
                .options(selectinload(Lote.pecas).selectinload(Peca.bordados))
            )
            return session.exec(statement).first()

    @staticmethod
    def atualizar_status_bordado(bordado_id: int, novo_status: str) -> bool:
        """
        Atualiza o status de um bordado específico.
        As propriedades dinâmicas das peças e lotes vão refletir essa mudança automaticamente.
        """
        with get_session() as session:
            bordado = session.get(Bordado, bordado_id)
            if bordado:
                bordado.status = novo_status
                session.add(bordado)
                session.commit()
                return True
            return False

    @staticmethod
    def deletar_lote(lote_id: int) -> bool:
        """Remove um lote do banco. O SQLite se encarrega de limpar os filhos se configurado, ou fazemos manualmente."""
        with get_session() as session:
            lote = session.get(Lote, lote_id)
            if lote:
                # Remove os filhos manualmente para evitar quebras de chaves estrangeiras
                for peca in lote.pecas:
                    for bordado in peca.bordados:
                        session.delete(bordado)
                    session.delete(peca)
                session.delete(lote)
                session.commit()
                return True
            return False
