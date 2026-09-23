import freetype
import unicodedata
import os
from pyembroidery import EmbPattern, COLOR_CHANGE, TRIM, JUMP, STITCH, END, NO_COMMAND

# --- CONFIGURAÇÕES E CONSTANTES ---
FONT_PATH = "mtcorsva.ttf"
DST_FOLDER = "dstsfonts/monotype"
OUTPUT_FOLDER = "./lote"
ALTURA_D_DST = 109  # Nossa 'Régua Mestra' baseada na letra 'd' digitalizada
ESPACO_ENTRE_PALAVRAS = 54.4

# Garante que a pasta de saída exista
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_font_engine(font_path, altura_ref_dst=109):
    """
    Inicializa o motor FreeType e calcula a escala global baseada na letra 'd'.
    """
    face = freetype.Face(font_path)
    # FT_LOAD_NO_SCALE extrai os dados brutos de design (FUnits)
    face.load_char('d', freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    
    ttf_height_d = face.glyph.metrics.height
    escala_mestra = altura_ref_dst / ttf_height_d
    
    return face, escala_mestra

def limpar_texto(texto):
    """
    Remove acentos e normaliza o texto para compatibilidade com os nomes de arquivos DST.
    """
    return "".join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c)
    )

def obter_caminho_dst(char):
    """
    Mapeia o caractere para o arquivo DST correspondente.
    """
    if char == ".":
        return os.path.join(DST_FOLDER, "PONTO.DST")
    if char.isupper():
        return os.path.join(DST_FOLDER, f"{char}m.DST")
    return os.path.join(DST_FOLDER, f"{char}.DST")

def gerar_bordado_nome(nome, face, escala):
    """
    Processa uma string e gera o padrão de bordado alinhado.
    """
    bordado = EmbPattern()
    cursor_x = 0.0
    
    # Início do bordado no ponto zero
    bordado.add_stitch_absolute(STITCH, 0, 0)

    for char in nome:
        if char == ' ':
            cursor_x += ESPACO_ENTRE_PALAVRAS
            continue

        # 1. Obter métricas da fonte (âncora teórica)
        face.load_char(char, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
        metrics = face.glyph.metrics
        
        # Conversão de unidades TTF para unidades de Bordado (0.1mm)
        adv_x = metrics.horiAdvance * escala
        lsb   = metrics.horiBearingX * escala
        h_bearing_y = metrics.horiBearingY * escala # Distância Baseline até Topo
        h_ttf = metrics.height * escala              # Altura total da letra no TTF

        # 2. Carregar o desenho físico (DST)
        caminho_dst = obter_caminho_dst(char)
        if not os.path.exists(caminho_dst):
            print(f"Aviso: Arquivo não encontrado: {caminho_dst}")
            cursor_x += adv_x # Pula mas avança o cursor
            continue
            
        letra_dst = EmbPattern()
        letra_dst.read(caminho_dst)
        min_x, _, _, max_y = letra_dst.bounds()

        # 3. Lógica de Alinhamento 'Wilcom' (Neutralização de Origem)
        
        # Alinhamento X: Cursor atual + recuo da fonte (LSB) - início real da costura no arquivo
        ajuste_x = cursor_x + lsb - min_x
        
        # Alinhamento Y (Baseline): 
        # (Altura total - Altura do Topo) = Tamanho do Descendente (perninha que fura o chão)
        # Subtraímos o maxY do DST para garantir que o topo da costura sente na altura correta.
        ajuste_y = (h_ttf - h_bearing_y) - max_y
        
        letra_dst.translate(ajuste_x, ajuste_y)
        bordado.add_pattern(letra_dst)

        # 4. Avanço do Cursor para a próxima origem lógica
        cursor_x += adv_x

    # Remove o comando END automático para evitar paradas bruscas indesejadas
    for stitch in bordado.get_match_commands(END):
        stitch[2] = NO_COMMAND
        
    return bordado

# --- EXECUÇÃO PRINCIPAL ---

face_engine, escala_global = get_font_engine(FONT_PATH, ALTURA_D_DST)

# Exemplo de processamento para um nome
texto_alvo = "Daniel Antonio"
texto_limpo = limpar_texto(texto_alvo)

resultado = gerar_bordado_nome(texto_limpo, face_engine, escala_global)
resultado.write(os.path.join(OUTPUT_FOLDER, f"{texto_limpo.replace(' ', '_')}.dst"))

print(f"Processamento concluído para: {texto_alvo}")