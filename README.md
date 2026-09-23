# 🪡 SVVDST — Sistema de Gestão de Produção & Bordados Computadorizados

Sistema completo desenvolvido em Python e Streamlit para gestão operacional de confecções e ateliês de bordado computadorizado. Integra o cadastro de clientes e lotes, catálogo técnico de peças e matrizes, cálculo automático de custos e produção, e geração de arquivos de bordado `.dst`.

---

## 🌟 Principais Funcionalidades

### 1. 📦 Gerador de Lotes de Produção (`pages/gerar_lote.py`)
- **Interface Otimizada (16:9):** Dashboard compacto em tela única, dividindo o configurador de pedidos e o resumo do lote lado a lado.
- **Suporte Multipeças & Multilocais:** Adicione diferentes tipos de peças (ex: Jalecos, Camisas, Bonés) e configure bordados específicos para cada local permitido (Peito, Mangas, Costas, etc.).
- **Autocomplete Inteligente:** Sugestões dinâmicas para peças cadastradas, fontes tipográficas, especialidades médicas/profissionais e cores de linhas (com permissão para inclusão imediata de novos termos via `accept_new_options`).
- **Conexão com o Catálogo:** Ao escolher logos ou brasões, o sistema sugere as matrizes do acervo e preenche automaticamente o preço, cores e status da matriz.
- **Cálculo Financeiro em Tempo Real:** Totalização de peças, bordados unitários e taxas de confecção de matrizes.

### 2. 🏷️ Catálogo Geral (`pages/pecas.py`)
- **👕 Catálogo de Peças:** Cadastro de modelos têxteis da confecção e definição das áreas físicas permitidas para aplicação de bordados.
- **🪡 Catálogo de Bordados & Matrizes:**
  - Cadastro técnico: Nome, Tipo (Logo, Brasão, Desenho, Texto, etc.), Contagem de Pontos, Preço Unitário, Código de Identificação e Cores de Linha.
  - Gestão de Matriz: Indicação se a matriz já está pronta ou se exige taxa de programação/digitalização.
  - **Suporte Multimídia:** Upload e exibição de **Arte Digital / Mockup** e **Foto Real da Peça Bordada**.
  - **Visualização Dupla:** Alterne entre **Tabela Técnica** (com formatação de moeda e dados) e **Galeria Visual** (comparativo lado a lado da arte digital vs. foto real).
  - **Edição & Gestão:** Popovers rápidos para editar dados, anexar novas fotos ou excluir registros.

### 3. 📑 Acompanhamento & Produção (`pages/visualizar_lotes.py`)
- Visualização do histórico de lotes e pedidos.
- Acompanhamento do status de execução (Pendente, Em Produção, Concluído).

### 4. 🖊️ Motor de Geração de Bordados DST
- Integração com `pyembroidery` e `freetype-py` para montagem automatizada de matrizes de texto e nomes a partir de alfabetos digitalizados e fontes tipográficas.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Frontend / Aplicação:** [Streamlit](https://streamlit.io/) (com navegação multipágina nativa)
- **Banco de Dados & ORM:** [SQLModel](https://sqlmodel.tiangolo.com/) & [SQLAlchemy](https://www.sqlalchemy.org/)
  - *Desenvolvimento Local:* SQLite (`banco.db`)
  - *Produção em Nuvem:* PostgreSQL ([Supabase](https://supabase.com/) ou [Neon](https://neon.tech/))
- **Manipulação de Bordado:** [pyembroidery](https://github.com/EmbroidePy/pyembroidery)
- **Tipografia & Vetorização:** [FreeType-py](https://github.com/rougier/freetype-py)
- **Processamento de Dados:** [Pandas](https://pandas.pydata.org/) & [Matplotlib](https://matplotlib.org/)

---

## 🚀 Instalação e Execução Local

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/svvdst.git
cd svvdst
```

### 2. Criar e Ativar o Ambiente Virtual
No Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
No Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação
```bash
streamlit run app.py
```
Acesse no seu navegador: `http://localhost:8501` ou `http://localhost:8502`.

---

## 📁 Estrutura de Diretórios

```text
svvdst/
├── core/
│   ├── database.py         # Configuração híbrida do Engine (PostgreSQL / SQLite)
│   ├── models.py           # Modelos SQLModel (Lote, Peca, Bordado, Templates)
│   └── repository.py       # Camada de persistência e operações de CRUD
├── pages/
│   ├── home.py             # Painel inicial
│   ├── gerar_lote.py       # Configurador de lotes e pedidos (16:9)
│   ├── pecas.py            # Gestão do Catálogo (Peças e Bordados)
│   └── visualizar_lotes.py # Acompanhamento dos lotes de produção
├── utils/
│   └── ecosystem_data.py   # Carregamento compartilhado de fontes e matrizes
├── fontsfiles/             # Arquivos de fontes tipográficas para bordado
├── ESPECIALIDADES_PRONTAS/ # Matrizes prontas (.dst) para bordado
├── uploads/                # Armazenamento local de imagens de bordado
├── .streamlit/
│   └── secrets.toml.example# Modelo de configuração de secrets
├── app.py                  # Ponto de entrada da aplicação e controle de acesso
├── pages_sections.toml     # Estrutura do menu e ícones de navegação
├── requirements.txt        # Dependências do projeto
├── .gitignore              # Filtros de arquivos para o Git
└── README.md               # Documentação do projeto
```

---

## 📄 Licença
Uso interno e comercial para confecções e ateliês de bordado.
