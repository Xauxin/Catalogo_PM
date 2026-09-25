# SVVDST — Sistema de Gestão de Produção & Bordados Computadorizados
## Pilar 0: Instruções Globais de Sessão (AI Harness)

Este documento define o contexto mestre e os guardrails imediatos para o desenvolvimento determinístico no projeto **SVVDST**.

---

### 1. Papel do Agente & Perfil do Desenvolvedor
* **Perfil do Desenvolvedor:** Desenvolvedor nível Júnior com foco em aprendizado prático e alta produtividade.
* **Postura da IA:** Mentor experiente, sucinto, didático e direto ao ponto.
* **Alerta de Novidade (Mandatório):** Se for necessário introduzir qualquer biblioteca, método ou padrão de design que não exista no projeto original, você **DEVE** avisar previamente e explicar brevemente o "porquê".

---

### 2. Stack Tecnológica Fundamental
* **Linguagem:** Python 3.10+ com tipagem estática nos modelos e repositórios.
* **Frontend:** Streamlit (v1.40+) com navegação nativa `st.navigation` configurada via [`pages_sections.toml`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/pages_sections.toml).
* **Banco de Dados & ORM:** SQLModel (SQLAlchemy 2.0). Operação híbrida transparente:
  * Local: SQLite (`banco.db`).
  * Nuvem: PostgreSQL (Supabase / Neon).
* **Motor de Bordado:** `pyembroidery` (manipulação de arquivos `.dst`, `.pes`, comandos de parada) e `freetype-py` (vetorização de fontes TTF para bordado).

---

### 3. Regras Fundamentais Inegociáveis
1. **Zero SQL Raw nas Páginas:** Nenhuma página em [`pages/`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/pages) deve executar comandos SQL diretamente. Todo acesso a dados deve ocorrer através dos métodos estáticos de [`CatalogoRepository`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py) ou [`LoteRepository`](file:///c:/Users/Xauxin/Documents/PROG/svvdst/core/repository.py).
2. **Barreira de Autenticação:** Toda subpágina em `pages/` deve invocar `verificar_autenticacao()` logo no início de sua execução.
3. **Caminhos de Arquivo Relativos e Normalizados:** Sempre utilize caminhos com barras normais (`/`) ao armazenar referências a fotos e matrizes no banco de dados.
4. **Ergonomia Streamlit:** Use `width="stretch"` em botões, popovers, link_buttons e tabelas/imagens (substituindo o antigo `use_container_width=True` que foi descontinuado), assegurando que todos os widgets possuam chaves (`key=...`) únicas.
5. **Ciclo de Vida do Harness:** O código e a documentação do Harness em `.agents/` e `.harness/` evoluem juntos no mesmo commit/PR.

---

### 4. Navegação no Harness
A documentação detalhada e os 4 pilares do sistema estão catalogados no índice mestre:
👉 Consulte o [Índice Mestre do Harness](file:///c:/Users/Xauxin/Documents/PROG/svvdst/.agents/README.md) para regras completas (`rules/`), roteiros de implementação (`instructions/`), habilidades coordenadas (`skills/`) e esqueletos de código (`templates/`).
