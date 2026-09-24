# Instrução: Indexar Novo Lote de Matrizes de Bordado

Este roteiro descreve como realizar a leitura em lote de novos arquivos de bordado (`.dst`, `.pes`, `.exp`) e salvá-los no catálogo técnico com extração automática de pontos, dimensões e cores.

---

## Roteiro Passo a Passo

### 1. Organizar os Arquivos Físicos
Copie as matrizes para a pasta padrão do acervo:
- Pasta principal recomendada: `matrizes/logos_e_brasoes/` (ou `matrizes/` ou `ESPECIALIDADES_PRONTAS/`).
- **Arquivos acompanhantes de cor:** Se possuir arquivos `.col`, `.inf` ou `.edr`, certifique-se de mantê-los com exatamente o mesmo nome base do arquivo de bordado (ex: `logo_medicina.dst` e `logo_medicina.col`).

### 2. Executar a Varredura via Script CLI
Abra o terminal do projeto e execute o indexador:
```bash
python indexar_acervo.py
```
Se desejar indexar uma pasta personalizada fora do padrão:
```bash
python indexar_acervo.py --pasta "caminho/para/pasta_matrizes"
```

### 3. Verificar o Processamento no Terminal
O script exibirá:
1. Conexão ativa com o banco (PostgreSQL ou SQLite local).
2. Arquivos de bordado encontrados.
3. Extração técnica de cada matriz: pontos totais, dimensões milimétricas, quantidade de trocas de cor e nomes/códigos de cores identificadas.
4. Confirmação de gravação ou atualização em `TemplateBordado`.

### 4. Validar na Interface
1. Abra a aplicação Streamlit: `streamlit run app.py`
2. Navegue até o menu **Catálogo** (`pages/pecas.py`) -> Aba **🪡 Catálogo de Bordados**.
3. Verifique se as matrizes indexadas aparecem na tabela técnica e na galeria visual.
