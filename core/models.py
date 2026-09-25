from datetime import date, datetime
from typing import List, Optional
import warnings
from sqlalchemy.exc import SAWarning
from sqlmodel import Field, Relationship, SQLModel

# Silencia o aviso inofensivo de recriação de modelos em reloads do Streamlit
warnings.filterwarnings("ignore", category=SAWarning)

# Mantemos a limpeza preventiva para o Streamlit
if hasattr(SQLModel, "registry") and hasattr(SQLModel.registry, "_class_registry"):
    SQLModel.registry._class_registry.clear()

# ==========================================
# CAMADA DE CATÁLOGO (TEMPLATES)
# ==========================================

class TemplatePeca(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str

    # Usando o caminho completo do módulo nas strings
    locais_permitidos: List["core.models.LocalBordado"] = Relationship(
        back_populates="template_peca"
    )
    pecas_pedidas: List["core.models.Peca"] = Relationship(
        back_populates="template"
    )


class LocalBordado(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str

    template_peca_id: Optional[int] = Field(
        default=None, foreign_key="templatepeca.id", index=True
    )
    
    # Usando o caminho completo do módulo aqui também
    template_peca: "core.models.TemplatePeca" = Relationship(
        back_populates="locais_permitidos"
    )


class TemplateBordado(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    tipo: str = Field(default="Logo/Brasão")
    categoria: Optional[str] = Field(default=None)
    subcategoria: Optional[str] = Field(default=None)
    arquivo_dst: Optional[str] = Field(default=None)
    pontos: int = Field(default=0)
    largura_mm: Optional[float] = Field(default=None)
    altura_mm: Optional[float] = Field(default=None)
    trocas_cor: Optional[int] = Field(default=0)
    cores_detalhes: Optional[str] = Field(default=None)
    linhas_usadas: Optional[str] = Field(default=None)
    preco: float = Field(default=0.0)
    matriz_pronta: bool = Field(default=True)
    preco_matriz: Optional[float] = Field(default=0.0)
    codigo_identificacao: Optional[str] = Field(default=None)
    visibilidade: str = Field(default="todos", index=True)
    imagem_digital: Optional[str] = Field(default=None)
    foto_bordado: Optional[str] = Field(default=None)


# ==========================================
# CAMADA DE OPERAÇÃO (DADOS DO PEDIDO)
# ==========================================

class Lote(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente: str
    data_entrada: date
    data_entrega: date
    preco_total: float = Field(default=0.0)

    # Caminho completo
    pecas: List["core.models.Peca"] = Relationship(back_populates="lote")

    @property
    def status(self) -> str:
        if not self.pecas:
            return "Vazio"
        status_pecas = [p.status for p in self.pecas]
        if all(s == "Concluído" for s in status_pecas):
            return "Concluído"
        if any(s == "Em Produção" for s in status_pecas):
            return "Em Produção"
        return "Pendente"


class Peca(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(default="Peça")
    observacao: Optional[str] = Field(default=None)
    quantidade: int = Field(default=1)
    preco_peca_total: float = Field(default=0.0)

    lote_id: Optional[int] = Field(default=None, foreign_key="lote.id", index=True)
    # Caminho completo
    lote: Optional["core.models.Lote"] = Relationship(back_populates="pecas")

    template_peca_id: Optional[int] = Field(
        default=None, foreign_key="templatepeca.id", index=True
    )
    # Caminho completo
    template: Optional["core.models.TemplatePeca"] = Relationship(
        back_populates="pecas_pedidas"
    )

    # Caminho completo
    bordados: List["core.models.Bordado"] = Relationship(back_populates="peca")

    @property
    def status(self) -> str:
        if not self.bordados:
            return "Sem bordados"
        status_bordados = [b.status for b in self.bordados]
        if all(s == "Concluído" for s in status_bordados):
            return "Concluído"
        if any(s == "Em Produção" for s in status_bordados):
            return "Em Produção"
        return "Pendente"


class Bordado(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    local: Optional[str] = Field(default=None)
    tipo: str
    informacao: str
    fonte: Optional[str] = None
    cor: str
    status: str = Field(default="Pendente")

    precisa_matriz: bool = Field(default=False)
    preco_matriz: Optional[float] = Field(default=0.0)
    preco_bordado: float = Field(default=0.0)

    peca_id: Optional[int] = Field(default=None, foreign_key="peca.id", index=True)
    # Caminho completo
    peca: Optional["core.models.Peca"] = Relationship(back_populates="bordados")

    local_bordado_id: Optional[int] = Field(
        default=None, foreign_key="localbordado.id", index=True
    )


# ==========================================
# CAMADA DE AUTENTICAÇÃO E PERFIS
# ==========================================

class PerfilUsuario(SQLModel, table=True):
    __tablename__ = "perfil_usuario"
    __table_args__ = {"extend_existing": True}

    id: str = Field(primary_key=True)  # UUID originário do Supabase Auth
    email: str = Field(index=True, unique=True)
    nome: Optional[str] = Field(default=None)
    foto_url: Optional[str] = Field(default=None)
    role: str = Field(default="cliente", index=True)  # "admin", "operador", "cliente"
    ativo: bool = Field(default=True, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    ultimo_login: Optional[datetime] = Field(default=None)

