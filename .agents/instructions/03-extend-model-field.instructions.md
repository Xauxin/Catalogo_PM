# Instrução: Estender Campos de um Modelo SQLModel

Este roteiro descreve como adicionar um novo campo a uma entidade existente em `core/models.py`, assegurando que a alteração seja refletida no banco de dados e na interface do usuário.

---

## Roteiro Passo a Passo

### 1. Adicionar o Campo no Modelo (`core/models.py`)
Abra [`core/models.py`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/models.py) e localize a classe alvo (ex: `TemplateBordado`, `Lote` ou `Bordado`).
Adicione o novo campo utilizando tipagem explícita e valor padrão quando aplicável:

```python
class TemplateBordado(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    # ... campos existentes ...
    [novo_campo]: Optional[[tipo]] = Field(default=[valor_padrao])
```

> **Atenção:** Mantenha compatibilidade com SQLite definindo `default=None` ou um valor primitivo padrão caso tabelas já existam com dados preenchidos.

### 2. Atualizar o Repositório (`core/repository.py`)
Se o novo campo for editável via formulário, adicione o parâmetro no método de atualização correspondente em [`core/repository.py`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py):

```python
@staticmethod
def atualizar_template_bordado(
    bordado_id: int,
    # ... parametros existentes ...
    [novo_campo]: [tipo] | None = None,
) -> bool:
    with get_session() as session:
        template = session.get(TemplateBordado, bordado_id)
        if template:
            # ... atribuicoes existentes ...
            if [novo_campo] is not None:
                template.[novo_campo] = [novo_campo]
            session.add(template)
            session.commit()
            return True
        return False
```

### 3. Expor o Campo no Formulário da Interface Streamlit
Abra a página correspondente (ex: `pages/pecas.py` ou `pages/gerar_lote.py`) e insira o widget visual apropriado dentro do formulário:

```python
[novo_campo_input] = st.text_input(
    "[Rótulo do Campo]",
    value=[valor_atual],
    key=f"input_[novo_campo]_{id_unico}"
)
```

### 4. Recriação do Esquema Local (quando necessário)
Em desenvolvimento local com SQLite, caso a tabela não reconheça a nova coluna automaticamente, utilize o utilitário de inicialização:
```bash
python iniciar_banco.py
```
*(Se necessário em bancos com dados existentes, execute o comando de `ALTER TABLE [tabela] ADD COLUMN [novo_campo] [TIPO];` via script).*
