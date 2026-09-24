# Template: Métodos de Repositório (CRUD com Eager Loading)

Esqueleto copiável para adicionar novas operações ao `core/repository.py`.

```python
from sqlmodel import select
from sqlalchemy.orm import selectinload, joinedload
from core.database import get_session
from core.models import <ModeloPrincipal>, <ModeloFilho>

class <NomeRepository>:
    """Gerencia as operações de persistência de <Entidade>."""

    @staticmethod
    def salvar_<entidade_minuscula>(entidade: <ModeloPrincipal>) -> <ModeloPrincipal>:
        """Salva ou cria um novo registro com commit e refresh atômicos."""
        with get_session() as session:
            session.add(entidade)
            session.commit()
            session.refresh(entidade)
            return entidade

    @staticmethod
    def listar_<entidade_plural>() -> list[<ModeloPrincipal>]:
        """Retorna todos os registros com relacionamentos carregados via eager loading."""
        with get_session() as session:
            statement = (
                select(<ModeloPrincipal>)
                .options(selectinload(<ModeloPrincipal>.<relacao_filha>))
                .order_by(<ModeloPrincipal>.id.desc())
            )
            return list(session.exec(statement).all())

    @staticmethod
    def buscar_por_id(registro_id: int) -> <ModeloPrincipal> | None:
        """Busca uma entidade específica por ID."""
        with get_session() as session:
            statement = (
                select(<ModeloPrincipal>)
                .where(<ModeloPrincipal>.id == registro_id)
                .options(selectinload(<ModeloPrincipal>.<relacao_filha>))
            )
            return session.exec(statement).first()

    @staticmethod
    def atualizar_<entidade_minuscula>(
        registro_id: int,
        campo_texto: str | None = None,
        campo_numero: float | None = None,
    ) -> bool:
        """Atualiza campos individuais sem sobrescrever valores omitidos."""
        with get_session() as session:
            registro = session.get(<ModeloPrincipal>, registro_id)
            if not registro:
                return False

            if campo_texto is not None:
                registro.campo_texto = campo_texto
            if campo_numero is not None:
                registro.campo_numero = campo_numero

            session.add(registro)
            session.commit()
            return True

    @staticmethod
    def deletar_<entidade_minuscula>(registro_id: int) -> bool:
        """Remove a entidade e gerencia eventuais filhos dependentes."""
        with get_session() as session:
            registro = session.get(<ModeloPrincipal>, registro_id)
            if registro:
                session.delete(registro)
                session.commit()
                return True
            return False
```
