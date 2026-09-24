# Instrução: Adicionar Novo Método no Repositório

Este roteiro descreve como implementar uma nova operação de consulta, atualização ou exclusão dentro do `core/repository.py`, respeitando o padrão de sessões e eager loading.

---

## Roteiro Passo a Passo

### 1. Identificar o Domínio da Operação
- **Catálogo / Cadastros prévios:** Adicionar em [`CatalogoRepository`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py#L11) (`TemplatePeca`, `LocalBordado`, `TemplateBordado`).
- **Operação de Produção / Lotes:** Adicionar em [`LoteRepository`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py#L163) (`Lote`, `Peca`, `Bordado`).

### 2. Implementar o Método com Context Manager
Todos os métodos devem ser `@staticmethod` e abrir a sessão através de `with get_session() as session:`.

#### Exemplo A: Consulta com Relacionamentos (Eager Loading)
```python
@staticmethod
def buscar_<entidade>_por_<criterio>(parametro: <Tipo>) -> list[<Modelo>]:
    """Busca registros por critério carregando relacionamentos associados."""
    with get_session() as session:
        statement = (
            select(<Modelo>)
            .where(<Modelo>.<campo> == parametro)
            .options(selectinload(<Modelo>.<relacao_filha>))
            .order_by(<Modelo>.id.desc())
        )
        return list(session.exec(statement).all())
```

#### Exemplo B: Atualização Parcial Atômica
```python
@staticmethod
def atualizar_<entidade>(
    registro_id: int,
    <campo_1>: <Tipo> | None = None,
    <campo_2>: <Tipo> | None = None,
) -> bool:
    """Atualiza campos específicos de uma entidade existente."""
    with get_session() as session:
        registro = session.get(<Modelo>, registro_id)
        if not registro:
            return False

        if <campo_1> is not None:
            registro.<campo_1> = <campo_1>
        if <campo_2> is not None:
            registro.<campo_2> = <campo_2>

        session.add(registro)
        session.commit()
        return True
```

### 3. Validação
- Testar a chamada a partir de um script ou diretamente na tela de destino.
- Confirmar que não ocorre `DetachedInstanceError` ao acessar `registro.[relacao_filha]` na interface.
