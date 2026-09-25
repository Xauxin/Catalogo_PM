# Regra de Padrões de Interface e Estilo Streamlit

## 1. Declaração da Regra
As páginas desenvolvidas em Streamlit devem priorizar **ergonomia operacional**, carregamento rápido, responsividade limpa e integridade de estado de sessão (`st.session_state`), sem quebras de layout ou loops de re-execução.

---

## 2. Diretrizes Mandatórias

1. **Barreira de Autenticação Mandatória:**
   Toda subpágina em `pages/` deve obrigatoriamente invocar `verificar_autenticacao()` do módulo `utils/auth.py` imediatamente após `st.set_page_config()`. Sem isso, a página não deve renderizar nenhum componente.

2. **Chaves Únicas para Widgets (`key=...`):**
   Todos os campos de entrada (`st.text_input`, `st.selectbox`, `st.button`, `st.data_editor`, etc.) gerados dinamicamente em loops ou listas **DEVEM** receber uma chave (`key`) única contendo o ID ou identificador de linha (ex: `key=f"btn_edit_{item.id}_{idx}"`), prevenindo o erro clássico de `DuplicateWidgetID`.

3. **Ergonomia Visual e Layout 16:9:**
   * Utilizar `st.set_page_config(layout="wide")` com `padding-top: 3.8rem !important` no `.block-container` para assegurar que os títulos não fiquem cortados sob o cabeçalho fixo nativo do Streamlit (`stHeader`).
   * Telas operacionais e configuradores (como `pages/gerar_lote.py`) devem usar layouts lado a lado (`st.columns`), containers compactos e bordas limpas (`st.container(border=True)`) para permitir visualização de ponta a ponta em monitores 16:9 sem scroll vertical excessivo.
   * Utilizar `width="stretch"` em botões, popovers, link_buttons, tabelas (`st.dataframe`/`st.data_editor`) e imagens (`st.image`) para preenchimento harmonioso do grid, evitando a diretiva legada `use_container_width=True`.

4. **Operações Rápidas via Popovers e Expanders:**
   Ações de edição rápida, anexação de fotos ou exclusões devem ser implementadas através de `st.popover` ou caixas retráteis para manter a tela limpa e não forçar navegações fragmentadas.

5. **Tratamento de Estado (`st.session_state`):**
   * Inicializar variáveis de sessão sempre com checagem prévia (`if "chave" not in st.session_state:`).
   * Modificações no banco que exigem atualização imediata da tela devem utilizar `st.rerun()` de forma controlada após a confirmação da operação.

6. **Primeira Dobra Funcional (Single-Screen First Fold):**
   * A área superior da tela (primeira dobra) deve concentrar as métricas operacionais principais, cabeçalhos compactos e controles de filtro/busca essenciais, viabilizando visão imediata e ação rápida sem necessidade de rolagem.
   * Tabelas extensas, históricos completos ou coleções densas de cards devem se posicionar ordenadamente abaixo do ponto de rolagem (scroll fold).

7. **Tipografia Limpa e Uso Restrito de Emojis:**
   * É proibido o uso excessivo de emojis decorativos em títulos, rótulos de botões, métricas, abas e mensagens de alerta do sistema.
   * Emojis e ícones visuais são reservados **estritamente** para links e itens de navegação (como `pages_sections.toml` e atalhos `st.page_link`), preservando a sobriedade, legibilidade e profissionalismo da aplicação.

8. **Paginação Mandatória para Coleções de Cards e Proteção de WebSocket:**
   * O servidor Streamlit impõe um limite máximo rígido na fila de saída assíncrona (`WEBSOCKET_MAX_SEND_QUEUE_SIZE = 500`).
   * **Proibição de Loops Não-Paginados:** É estritamente proibido iterar sobre coleções extensas (> 24 itens) desenhando múltiplos componentes pesados (cards com colunas, expanders, imagens e popovers) de uma só vez. Fazer isso dispara milhares de `ForwardMsg`s instantaneamente, causando estouro de fila (`asyncio.QueueFull`), queda do WebSocket e travamento da página ("running" infinito).
   * **Paginação com Session State:** Telas com visualização em cards (ex: Catálogo de Bordados) devem paginar os resultados (máximo recomendado de 12 a 24 itens por página), disponibilizando botões `◀ Anterior` e `Próxima ▶` com persistência em `st.session_state`.

