# Regra Primária: Ciclo de Vida e Manutenção do Harness

## 1. Declaração da Regra
O modelo de **Harness Development** é a **fonte única da verdade** para o desenvolvimento determinístico no projeto **SVVDST**. Código e documentação evoluem juntos no mesmo commit/PR. Nenhuma decisão arquitetural, restrição de negócio ou convenção técnica deve permanecer apenas na memória dos desenvolvedores.

---

## 2. Diretrizes Mandatórias

1. **Sincronia Estrita (Código + Harness no mesmo Commit):**
   Toda nova decisão de projeto não-óbvia, restrição arquitetural ou convenção acordada **DEVE** ser registrada imediatamente em um arquivo correspondente dentro de `rules/`.

2. **Atualização Reativa de Regras:**
   Toda alteração no código que modifique, relaxe ou restrinja o comportamento de uma regra existente **OBRIGA** a atualização imediata do arquivo de `rules/` correspondente.

3. **Padronização de Tarefas Recorrentes:**
   Toda implementação de tarefa recorrente ou multi-etapas que possa ser repetida por desenvolvedores ou agentes de IA (ex: adicionar uma nova página, criar métodos de repositório, estender modelos) **DEVE** ser documentada em `instructions/` no formato de roteiro sequencial numerado com placeholders claros.

4. **Encapsulamento de Tarefas Coordenadas:**
   Toda tarefa complexa que envolva geração coordenada de múltiplos arquivos ou lógica de scaffold deve ser encapsulada ou atualizada dentro de `skills/`.

5. **Modelos de Código Atualizados:**
   Qualquer alteração na estrutura padrão de páginas Streamlit, entidades SQLModel ou métodos de repositório deve ser refletida nos esqueletos em `templates/`.

6. **Manutenção do Índice Mestre:**
   Qualquer adição, renomeação ou remoção de arquivo nos 4 pilares (`rules/`, `instructions/`, `skills/`, `templates/`) **EXIGE** a atualização imediata do índice mestre em `.agents/README.md`.

7. **Proibição de Conhecimento Tácito:**
   É estritamente proibido manter regras implícitas, convenções não documentadas ou "conhecimento tácito" fora do harness sempre que isso impactar a arquitetura, persistência, regras de bordado ou o determinismo do sistema.

8. **Captura Ativa de Gotchas e Aprendizados da Stack (Mandatório):**
   Toda resolução de bugs não-triviais, armadilhas técnicas de bibliotecas (Streamlit, SQLModel/SQLAlchemy, Uvicorn, Pyembroidery, etc.), limitações de rede (buffers de WebSocket, proxies Cloudflare, headers, túneis) ou gargalos de performance **DEVE ser imediatamente sintetizada e adicionada à regra temática em `rules/` ou criada como nova regra/instrução no mesmo turno de trabalho**. O Harness deve funcionar como uma memória de longo prazo evolutiva para qualquer IA ou programador humano que atue no projeto.

---

## 3. Checklist de Validação da Regra
- [ ] A nova feature introduziu uma restrição técnica? Está documentada em `rules/`?
- [ ] O erro não-óbvio, gotcha de biblioteca ou gargalo resolvido foi registrado nas regras do Harness?
- [ ] A tarefa será repetida no futuro? Há um roteiro em `instructions/`?
- [ ] O modelo ou template de código foi alterado? O arquivo em `templates/` foi sincronizado?
- [ ] O arquivo novo foi catalogado no índice mestre (`.agents/README.md`)?
