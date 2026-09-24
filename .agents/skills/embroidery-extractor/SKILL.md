---
name: embroidery-extractor
description: Extração técnica e tratamento de dados de matrizes de bordado (.dst, .pes, .exp) usando pyembroidery, calculando pontos, bounds milimétricos, trocas de cor e arquivos de paleta.
---

# Skill: Extrator Técnico de Bordados

Esta habilidade orienta a leitura, inspeção e conversão de arquivos de bordado computadorizado no ecossistema do **SVVDST**.

## Capacidades Técnicas

1. **Leitura e Extração com `pyembroidery`:**
   - Carregar arquivo via `pyembroidery.read(caminho)`.
   - Extrair contagem exata de pontos com `pattern.count_stitches()`.
   - Extrair caixa delimitadora com `pattern.bounds()`:
     - `largura_mm = (bounds[2] - bounds[0]) / 10.0`
     - `altura_mm = (bounds[3] - bounds[1]) / 10.0`

2. **Identificação de Cores e Paradas:**
   - Detectar comandos de troca de linha (`COLOR_CHANGE`, `STOP`).
   - Carregar arquivos acompanhantes de paleta (`.col`, `.inf`, `.edr`) se disponíveis no mesmo diretório.
   - Extrair nomes de linha de fabricantes conhecidos (ex: Madeira, Isacord, Lumina).

3. **Geração de Pré-visualização Gráfica:**
   - Coletar coordenadas cartesianas `(x, y)` da lista `pattern.stitches`.
   - Gerar gráfico Matplotlib com inversão de eixo vertical (`ax.invert_yaxis()`) e sem linhas de grade.

4. **Tratamento de Exceções:**
   - Garantir que arquivos corrompidos ou com cabeçalho inválido sejam capturados sem interromper a execução em lote da aplicação.
