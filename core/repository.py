from datetime import datetime
import json
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from core.database import get_session
from core.models import Bordado, LocalBordado, Lote, Peca, PerfilUsuario, TemplateBordado, TemplatePeca


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
    def listar_todos_os_locais() -> list[str]:
        """Retorna todos os locais de bordado distintos já cadastrados em templates e pedidos."""
        with get_session() as session:
            locais_templates = session.exec(select(LocalBordado.nome).distinct()).all()
            locais_bordados = session.exec(
                select(Bordado.local).where(Bordado.local != None).distinct()
            ).all()
            todos = set(locais_templates + locais_bordados)
            locais_limpos = {l.strip() for l in todos if l and l.strip()}
            return sorted(list(locais_limpos))

    @staticmethod
    def salvar_template_bordado(template: TemplateBordado) -> TemplateBordado:
        """Salva ou atualiza um template de bordado / matriz no catálogo."""
        with get_session() as session:
            session.add(template)
            session.commit()
            session.refresh(template)
            return template

    @staticmethod
    def listar_templates_bordado(role_usuario: str = "admin") -> list[TemplateBordado]:
        """
        Retorna os bordados cadastrados filtrando por permissão de acesso (Role):
        - admin: vê todos os bordados (todos, restrito, admin)
        - cliente / visitante: vê apenas bordados com visibilidade 'todos'
        """
        with get_session() as session:
            statement = select(TemplateBordado)
            if role_usuario in ["cliente", "visitante"]:
                statement = statement.where(TemplateBordado.visibilidade == "todos")
            statement = statement.order_by(TemplateBordado.id.desc())
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
        visibilidade: str | None = None,
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
                if visibilidade is not None:
                    template.visibilidade = visibilidade
                session.add(template)
                session.commit()
                return True
            return False

    @staticmethod
    def listar_categorias_matriz() -> list[str]:
        """Retorna todas as categorias distintas de matrizes de bordado já cadastradas no acervo."""
        with get_session() as session:
            statement = (
                select(TemplateBordado.categoria)
                .where(TemplateBordado.categoria != None)
                .distinct()
            )
            categorias = session.exec(statement).all()
            return sorted(list({c.strip() for c in categorias if c and c.strip()}))

    @staticmethod
    def listar_subcategorias_matriz() -> list[str]:
        """Retorna todas as subcategorias distintas de matrizes já cadastradas no acervo."""
        with get_session() as session:
            statement = (
                select(TemplateBordado.subcategoria)
                .where(TemplateBordado.subcategoria != None)
                .distinct()
            )
            subcategorias = session.exec(statement).all()
            return sorted(list({s.strip() for s in subcategorias if s and s.strip()}))

    @staticmethod
    def listar_tipos_matriz() -> list[str]:
        """Retorna todos os tipos distintos de matrizes já cadastrados no acervo."""
        with get_session() as session:
            statement = (
                select(TemplateBordado.tipo)
                .where(TemplateBordado.tipo != None)
                .distinct()
            )
            tipos = session.exec(statement).all()
            return sorted(list({t.strip() for t in tipos if t and t.strip()}))

    @staticmethod
    def listar_cores_matriz_cadastradas() -> dict[str, str]:
        """
        Retorna um dicionário mapeando {codigo_linha: hex} de todas as cores de linha
        já cadastradas no acervo de matrizes.
        """
        with get_session() as session:
            bordados = session.exec(select(TemplateBordado)).all()
            mapa_cores: dict[str, str] = {}
            for b in bordados:
                if b.cores_detalhes:
                    try:
                        detalhes = json.loads(b.cores_detalhes)
                        for item in detalhes:
                            cod = str(item.get("codigo") or "").strip()
                            hex_c = str(item.get("hex") or "").strip()
                            if cod:
                                if cod not in mapa_cores or (hex_c and hex_c.startswith("#")):
                                    mapa_cores[cod] = hex_c if hex_c.startswith("#") else "#888888"
                    except Exception:
                        pass
                if b.linhas_usadas:
                    for pedaco in b.linhas_usadas.split(","):
                        pedaco = pedaco.strip()
                        if pedaco and not pedaco.endswith("cores") and pedaco not in mapa_cores:
                            mapa_cores[pedaco] = "#888888"
            return mapa_cores

    @staticmethod
    def listar_codigos_cores_matriz() -> list[str]:
        """Retorna uma lista ordenada com todos os códigos de cores de linha cadastrados no acervo."""
        mapa = CatalogoRepository.listar_cores_matriz_cadastradas()
        return sorted(list(mapa.keys()))


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

    @staticmethod
    def listar_fontes_cadastradas() -> list[str]:
        """Retorna todas as fontes já cadastradas em bordados e/ou disponíveis no ecossistema."""
        with get_session() as session:
            statement = (
                select(Bordado.fonte)
                .where(Bordado.fonte != None)
                .distinct()
            )
            fontes_db = session.exec(statement).all()
            fontes_limpas = {f.strip() for f in fontes_db if f and f.strip() and f.strip() != "N/A"}

            try:
                from utils.ecosystem_data import load_ecosystem_data
                fontes_eco, _, _ = load_ecosystem_data()
                for f in fontes_eco:
                    if f and f.strip():
                        fontes_limpas.add(f.strip())
            except Exception:
                pass

            return sorted(list(fontes_limpas))

    @staticmethod
    def listar_cores_linha_cadastradas() -> list[str]:
        """Retorna todas as cores de linha já cadastradas em bordados ou no acervo de matrizes."""
        with get_session() as session:
            statement = (
                select(Bordado.cor)
                .where(Bordado.cor != None)
                .distinct()
            )
            cores_db = session.exec(statement).all()
            cores_limpas = {c.strip() for c in cores_db if c and c.strip() and c.strip() != "N/A"}

            # Puxa também os códigos de cores cadastrados no acervo de matrizes
            codigos_acervo = CatalogoRepository.listar_codigos_cores_matriz()
            for cod in codigos_acervo:
                if cod and cod.strip():
                    cores_limpas.add(cod.strip())

            return sorted(list(cores_limpas))

    @staticmethod
    def listar_especialidades_cadastradas() -> list[str]:
        """Retorna todas as especialidades já extraídas ou utilizadas em bordados."""
        with get_session() as session:
            statement = select(Bordado.informacao).where(Bordado.informacao != None)
            infos = session.exec(statement).all()
            esps = set()
            for info in infos:
                if info and " - " in info:
                    partes = info.split(" - ", 1)
                    if len(partes) > 1 and partes[1].strip():
                        esps.add(partes[1].strip())
            return sorted(list(esps))


# =====================================================================
# 3. REPOSITÓRIO DE USUÁRIOS E PERMISSÕES (RBAC)
# =====================================================================
class UsuarioRepository:
    """Gerencia usuários, perfis e controle de acesso baseado em papéis (RBAC)."""

    @staticmethod
    def obter_por_id(usuario_id: str) -> PerfilUsuario | None:
        """Busca perfil de usuário pelo ID do Supabase."""
        with get_session() as session:
            return session.get(PerfilUsuario, usuario_id)

    @staticmethod
    def obter_por_email(email: str) -> PerfilUsuario | None:
        """Busca perfil de usuário pelo e-mail."""
        with get_session() as session:
            stmt = select(PerfilUsuario).where(PerfilUsuario.email == email.lower().strip())
            return session.exec(stmt).first()

    @staticmethod
    def salvar_ou_atualizar(
        usuario_id: str,
        email: str,
        nome: str | None = None,
        foto_url: str | None = None,
        role_padrao: str = "cliente",
    ) -> PerfilUsuario:
        """
        Garante que o usuário autenticado via OAuth tenha registro no banco.
        Se for o primeiríssimo usuário cadastrado no sistema, atribui 'admin' automaticamente!
        """
        with get_session() as session:
            usuario = session.get(PerfilUsuario, usuario_id)
            if not usuario:
                usuario = session.exec(
                    select(PerfilUsuario).where(PerfilUsuario.email == email.lower().strip())
                ).first()

            if not usuario:
                total_existentes = len(session.exec(select(PerfilUsuario.id)).all())
                role_atribuida = "admin" if total_existentes == 0 else role_padrao

                usuario = PerfilUsuario(
                    id=usuario_id,
                    email=email.lower().strip(),
                    nome=nome,
                    foto_url=foto_url,
                    role=role_atribuida,
                    ativo=True,
                    ultimo_login=datetime.utcnow(),
                )
                session.add(usuario)
            else:
                usuario.id = usuario_id
                if nome and not usuario.nome:
                    usuario.nome = nome
                if foto_url:
                    usuario.foto_url = foto_url
                usuario.ultimo_login = datetime.utcnow()
                session.add(usuario)

            session.commit()
            session.refresh(usuario)
            return usuario

    @staticmethod
    def listar_usuarios() -> list[PerfilUsuario]:
        """Lista todos os perfis de usuários cadastrados ordenados por data de criação desc."""
        with get_session() as session:
            stmt = select(PerfilUsuario).order_by(PerfilUsuario.criado_em.desc())
            return list(session.exec(stmt).all())

    @staticmethod
    def atualizar_role(usuario_id: str, nova_role: str) -> bool:
        """Atualiza a role de um usuário ('admin', 'cliente', 'visitante')."""
        if nova_role not in ["admin", "cliente", "visitante"]:
            return False
        with get_session() as session:
            usuario = session.get(PerfilUsuario, usuario_id)
            if usuario:
                usuario.role = nova_role
                session.add(usuario)
                session.commit()
                return True
            return False

    @staticmethod
    def atualizar_status_ativo(usuario_id: str, ativo: bool) -> bool:
        """Ativa ou desativa o acesso de um usuário."""
        with get_session() as session:
            usuario = session.get(PerfilUsuario, usuario_id)
            if usuario:
                usuario.ativo = ativo
                session.add(usuario)
                session.commit()
                return True
            return False

