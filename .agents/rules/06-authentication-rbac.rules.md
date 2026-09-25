# Regra de Autenticação e Controle de Acesso Baseado em Funções (RBAC)

## 1. Declaração da Regra
O sistema **SVVDST** adota autenticação centralizada gerenciada pelo **Supabase Auth** (com suporte a provedores OAuth como Google e Meta, além de senha mestra de contingência/administração local) e **Controle de Acesso Baseado em Funções (RBAC - Role-Based Access Control)**. 
O acesso a páginas e a visibilidade de matrizes de bordado são estritamente governados pelo papel do usuário autenticado.

---

## 2. Hierarquia de Papéis (Roles)

| Papel | Nível | Escopo de Acesso | Visibilidade de Bordados |
| :--- | :---: | :--- | :--- |
| **`admin`** | 3 | Acesso irrestrito a todas as telas, configurações do sistema, gestão de lotes, catálogo de peças e acervo. | Todas as matrizes (`todos`, `restrito`, `admin`). |
| **`cliente`** | 2 | Catálogo de Bordados como Home (com busca e filtros completos) e ferramenta de Gerar Bordado. Sem acesso a catálogo de peças ou configurações. | Apenas matrizes públicas (`todos`). |
| **`visitante`** | 1 | Acesso público ao Catálogo de Bordados **sem filtros** de busca/categorias (para incentivar o cadastro/login na plataforma). | Apenas matrizes públicas (`todos`). |

---

## 3. Diretrizes Mandatórias

1. **Barreira Obrigatória em Subpáginas:**
   Toda subpágina em `pages/` deve invocar `verificar_autenticacao()` logo após `st.set_page_config()`. Caso a página seja restrita a um papel específico, o nível mínimo deve ser explicitado:
   ```python
   from utils.auth import verificar_autenticacao
   verificar_autenticacao(role_minima="admin")  # Bloqueia operadores e clientes
   ```

2. **Defesa em Duas Camadas (Interface + Repositório):**
   * **Camada 1 (UI):** O `app.py` filtra as rotas do `pages_sections.toml` no `st.navigation` antes de desenhar a barra lateral, impedindo que usuários vejam links de telas para as quais não possuem permissão.
   * **Camada 2 (Banco de Dados):** O `CatalogoRepository.listar_templates_bordado(role_usuario)` filtra no nível SQL a cláusula `where(TemplateBordado.visibilidade == ...)` para que dados restritos nunca trafeguem para clientes.

3. **Repositório de Usuários (`UsuarioRepository`):**
   Todas as consultas e atualizações de usuários (criação, alteração de role, ativação/desativação) devem residir em `core/repository.py` sob a classe `UsuarioRepository`. Proibido o uso de SQL direto nas páginas.

4. **Isolamento de Segredos e Chaves de API:**
   * Nenhuma chave de API ou credencial deve constar diretamente no código-fonte.
   * As variáveis `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `APP_PASSWORD` e `APP_URL` devem residir exclusivamente em `.streamlit/secrets.toml` ou variáveis de ambiente.

5. **Encerramento Seguro de Sessão:**
   O logout deve sempre invocar `fazer_logout()` de `utils.auth`, garantindo a limpeza completa do `st.session_state` e dos parâmetros de URL (`st.query_params`).
