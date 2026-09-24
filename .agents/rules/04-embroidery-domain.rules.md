# Regra de Domínio e Engenharia de Bordados (.DST)

## 1. Declaração da Regra
O manuseio de matrizes de bordado computadorizado (`.dst`, `.pes`, `.exp`, etc.), cálculo de pontos, cores de linha e geração de arquivos técnicos deve seguir rigorosamente as especificações industriais e a precisão dimensional do ecossistema têxtil.

---

## 2. Diretrizes Mandatórias

1. **Manipulação com pyembroidery:**
   * Toda leitura e escrita de arquivos de bordado deve utilizar a biblioteca `pyembroidery`.
   * A contagem de pontos (`stitches`) deve desconsiderar comandos que não sejam de perfuração física de agulha quando aplicável, ou utilizar a contagem retornada por `pattern.count_stitches()`.
   * Dimensões de matrizes devem ser calculadas a partir dos limites espaciais (`pattern.bounds()`), convertendo unidades internas (décimos de milímetro) para milímetros reais (`mm = valor / 10.0`).

2. **Detecção de Trocas de Cor e Paradas de Agulha:**
   * A quantidade de trocas de cor deve ser extraída através dos comandos de parada (`COLOR_CHANGE`, `STOP`).
   * Arquivos acompanhantes de informação de paleta (`.col`, `.inf`, `.edr`) devem ser lidos conjuntamente se existirem no mesmo diretório base da matriz.

3. **Caminhos de Arquivo Relativos e Normalizados:**
   * Ao persistir localizações de matrizes (`arquivo_dst`) ou imagens (`imagem_digital`, `foto_bordado`) no banco de dados, os caminhos **DEVEM** ser relativos à raiz do projeto e com barras inclinadas normais (`/`), por exemplo: `uploads/bordados/arte_123.png`.
   * É estritamente proibido salvar caminhos absolutos do Windows (ex: `C:\Users\...`) no banco, para garantir portabilidade completa no Linux/Docker/Cloud.

4. **Renderização de Pré-visualização com Matplotlib:**
   * A renderização de caminhos de ponto deve sempre inverter o eixo Y (`ax.invert_yaxis()`) para respeitar a convenção tradicional de visualização do bordador na máquina.
   * Os eixos devem ser desativados (`ax.set_axis_off()`) e a proporção de aspecto deve ser travada (`ax.axis("equal")`).
