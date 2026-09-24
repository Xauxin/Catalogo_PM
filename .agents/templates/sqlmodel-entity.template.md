# Template: Entidade SQLModel com Relacionamento e Status Dinâmico

Esqueleto copiável para adicionar novas classes de tabela em `core/models.py`.

```python
from datetime import date
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class <EntidadePai>(SQLModel, table=True):
    """Modelo representativo de <DescricaoPai>."""
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)
    observacao: Optional[str] = Field(default=None)
    ativo: bool = Field(default=True)
    criado_em: date = Field(default_factory=date.today)

    # Relacionamento 1:N com modelo filho
    itens: List["<EntidadeFilho>"] = Relationship(back_populates="pai")

    @property
    def status_calculado(self) -> str:
        """Derivação dinâmica de status a partir do estado dos itens filhos."""
        if not self.itens:
            return "Vazio"
        status_lista = [i.status for i in self.itens]
        if all(s == "Concluído" for s in status_lista):
            return "Concluído"
        if any(s == "Em Produção" for s in status_lista):
            return "Em Produção"
        return "Pendente"


class <EntidadeFilho>(SQLModel, table=True):
    """Modelo filho associado a <EntidadePai>."""
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    descricao: str
    status: str = Field(default="Pendente")
    valor: float = Field(default=0.0)

    # Chave estrangeira e vínculo bidirecional
    pai_id: Optional[int] = Field(default=None, foreign_key="<tabela_pai_em_minusculo>.id")
    pai: Optional["<EntidadePai>"] = Relationship(back_populates="itens")
```
