# Regra de Camadas Arquiteturais e Persistência

## 1. Declaração da Regra
O sistema adota uma **Arquitetura em Camadas (Layered Architecture)** com implementação estrita do **Repository Pattern**. A camada de apresentação (`pages/`) nunca deve interagir diretamente com o banco de dados via SQL ou queries desacopladas.

---

## 2. Diretrizes Mandatórias

1. **Proibição Absoluta de SQL Raw nas Páginas:**
   Nenhum arquivo em `pages/` deve conter chamadas do tipo `session.execute(text("..."))`, `cursor.execute(...)` ou instanciar sessões de banco ad-hoc.
   * ✅ **Correto:** `lotes = LoteRepository.listar_todos_os_lotes()`
   * ❌ **Proibido:** `with Session(engine) as session: session.exec(select(Lote)).all()` diretamente na UI.

2. **Isolamento de Persistência no Repositório:**
   Todas as operações de criação, leitura, atualização e exclusão (CRUD) devem residir em classes estáticas em `core/repository.py` ([`CatalogoRepository`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py) ou [`LoteRepository`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py)).

3. **Gerenciamento de Sessão por Context Manager:**
   Todo método de repositório deve abrir e fechar a sessão através da função utilitária `get_session()` utilizando a cláusula `with`:
   ```python
   with get_session() as session:
       # operações de consulta / mutação
       session.commit()
   ```

4. **Prevenção de N+1 Queries e Detached Instances:**
   Ao retornar entidades que possuem relacionamentos (`Lote.pecas`, `Peca.bordados`, `TemplatePeca.locais_permitidos`), o repositório **DEVE** utilizar `selectinload` ou `joinedload` para carregar as relações antes do encerramento da sessão:
   ```python
   statement = (
       select(Lote)
       .options(selectinload(Lote.pecas).selectinload(Peca.bordados))
       .order_by(Lote.id.desc())
   )
   ```

5. **Entidades Anêmicas vs. Propriedades Calculadas:**
   Regras de agregação de estado (como o status geral de um Lote derivado das peças filhas) devem ser implementadas como `@property` nas entidades em `core/models.py`, e não recalculadas repetidamente na interface.
