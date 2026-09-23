import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional, Union
import pyembroidery


def extrair_dados_matriz(
    origem: Union[str, Path, Any],
    nome_arquivo: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Lê um arquivo de bordado (.dst, .pes, .exp, .jef, etc.) e extrai:
    - Contagem exata de pontos
    - Dimensões em milímetros (largura x altura)
    - Quantidade de trocas de cor (paradas de agulha)
    - Lista de cores/linhas com códigos de catálogo, marcas, descrições e hexadecimais
    - Arquivo de cores acompanhante (.col, .inf, .edr) se existir
    """
    caminho_temporario = None
    caminho_final = None

    try:
        # Se for UploadedFile do Streamlit ou BytesIO
        if hasattr(origem, "getvalue") or hasattr(origem, "read"):
            ext = ".dst"
            if nome_arquivo:
                ext = Path(nome_arquivo).suffix or ".dst"
            elif hasattr(origem, "name"):
                ext = Path(origem.name).suffix or ".dst"

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                if hasattr(origem, "seek"):
                    origem.seek(0)
                tmp.write(origem.getvalue() if hasattr(origem, "getvalue") else origem.read())
                caminho_temporario = tmp.name
                caminho_final = caminho_temporario
        else:
            caminho_final = str(origem)

        if not os.path.exists(caminho_final):
            return None

        # Lê com pyembroidery
        pattern = pyembroidery.read(caminho_final)
        if not pattern:
            return None

        # Se foi lido a partir de um arquivo em disco, verifica arquivos acompanhantes de cor (.col, .inf, .edr)
        if not caminho_temporario:
            base, _ = os.path.splitext(caminho_final)
            for ext_cor in [".col", ".inf", ".edr"]:
                col_path = base + ext_cor
                if os.path.exists(col_path):
                    try:
                        pyembroidery.read(col_path, pattern=pattern)
                    except Exception:
                        pass

        pontos = int(pattern.count_stitches())
        trocas_cor = int(pattern.count_color_changes())
        total_agulhas = trocas_cor + 1

        bounds = pattern.bounds()
        # pyembroidery armazena coordenadas em décimos de milímetro (0.1 mm)
        if bounds and bounds != (0, 0, 0, 0):
            largura_mm = round((bounds[2] - bounds[0]) / 10.0, 1)
            altura_mm = round((bounds[3] - bounds[1]) / 10.0, 1)
        else:
            largura_mm = 0.0
            altura_mm = 0.0

        threads_info = []
        linhas_resumo = []

        for idx, t in enumerate(pattern.threadlist):
            hex_val = None
            if hasattr(t, "hex_color"):
                try:
                    hex_val = t.hex_color()
                except Exception:
                    hex_val = None

            cod = getattr(t, "catalog_number", None)
            desc = getattr(t, "description", None)
            marca = getattr(t, "brand", None)

            # Limpa strings vazias
            cod = cod.strip() if isinstance(cod, str) and cod.strip() else None
            desc = desc.strip() if isinstance(desc, str) and desc.strip() else None
            marca = marca.strip() if isinstance(marca, str) and marca.strip() else None

            thread_dict = {
                "posicao": idx + 1,
                "codigo": cod,
                "descricao": desc,
                "marca": marca,
                "hex": hex_val
            }
            threads_info.append(thread_dict)

            # Formata resumo da cor para exibição: apenas o código ou hex (sem marcas de linha)
            if cod:
                linhas_resumo.append(str(cod))
            elif hex_val:
                linhas_resumo.append(str(hex_val))
            elif desc:
                linhas_resumo.append(str(desc))
            else:
                linhas_resumo.append(f"Cor {idx+1}")

        if linhas_resumo:
            linhas_usadas = ", ".join(linhas_resumo)
        else:
            linhas_usadas = f"{total_agulhas} cores"

        cores_detalhes_json = json.dumps(threads_info, ensure_ascii=False) if threads_info else None

        return {
            "pontos": pontos,
            "trocas_cor": trocas_cor,
            "total_agulhas": total_agulhas,
            "largura_mm": largura_mm,
            "altura_mm": altura_mm,
            "threads": threads_info,
            "cores_detalhes": cores_detalhes_json,
            "linhas_usadas": linhas_usadas
        }

    finally:
        if caminho_temporario and os.path.exists(caminho_temporario):
            try:
                os.remove(caminho_temporario)
            except Exception:
                pass


def renderizar_chips_cores_html(
    cores_detalhes: Optional[str] = None,
    linhas_usadas: Optional[str] = None
) -> str:
    """
    Gera HTML com quadradinhos de visualização da cor (estilo IDE / editor de código)
    ao lado do código da linha e do #hex.
    """
    chips = []

    if cores_detalhes:
        try:
            threads = json.loads(cores_detalhes) if isinstance(cores_detalhes, str) else cores_detalhes
            # Mantém cores únicas preservando a ordem de aparição no bordado
            vistas = set()
            for t in threads:
                cod = str(t.get("codigo") or "").strip()
                hex_c = str(t.get("hex") or "").strip()
                if not hex_c or not hex_c.startswith("#"):
                    hex_c = "#888888"
                chave = (cod, hex_c)
                if chave not in vistas:
                    vistas.add(chave)
                    chips.append({"codigo": cod if cod else None, "hex": hex_c})
        except Exception:
            pass

    if not chips and linhas_usadas:
        for item in linhas_usadas.split(","):
            item = item.strip()
            if not item:
                continue
            if item.startswith("#"):
                chips.append({"codigo": None, "hex": item})
            else:
                # Pega apenas o código (remove marcas se houver)
                partes = item.split()
                cod = partes[-1] if partes else item
                chips.append({"codigo": cod, "hex": "#888888"})

    if not chips:
        return ""

    html_parts = [
        '<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; margin-bottom:6px;">'
    ]

    for c in chips:
        hex_c = c["hex"]
        cod = c["codigo"]
        texto = f"<b>{cod}</b>" if cod else f"<code>{hex_c}</code>"

        chip_html = (
            f'<span title="{hex_c}" style="display:inline-flex; align-items:center; gap:6px; '
            f'background:rgba(128,128,128,0.12); border:1px solid rgba(128,128,128,0.28); '
            f'border-radius:4px; padding:2px 7px; font-size:12px; font-family:monospace;">'
            f'<span style="display:inline-block; width:12px; height:12px; background-color:{hex_c}; '
            f'border-radius:2px; border:1px solid rgba(0,0,0,0.35); box-shadow:0 0 2px rgba(0,0,0,0.2);"></span>'
            f'{texto}'
            f'</span>'
        )
        html_parts.append(chip_html)

    html_parts.append("</div>")
    return "".join(html_parts)
