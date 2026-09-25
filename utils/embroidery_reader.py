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


def extrair_preview_wilcom(caminho_arquivo: Union[str, Path], tamanho: int = 256) -> Optional[Any]:
    """
    Extrai o thumbnail nativo de alta fidelidade gerado pelo Wilcom Shell Extension via Windows Shell API (IShellItemImageFactory).
    Retorna uma instância de PIL.Image.Image em formato RGBA (fundo transparente) ou None se indisponível.
    """
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes, Structure, POINTER, byref, c_void_p
        from PIL import Image

        class GUID(Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8)
            ]
            def __init__(self, l, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8):
                self.Data1 = l
                self.Data2 = w1
                self.Data3 = w2
                self.Data4 = (wintypes.BYTE * 8)(b1, b2, b3, b4, b5, b6, b7, b8)

        IID_IShellItemImageFactory = GUID(
            0xbcc18b79, 0xba16, 0x442f, 0x80, 0xc4, 0x8a, 0x59, 0xc3, 0x0c, 0x46, 0x3b
        )

        class SIZE(Structure):
            _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]

        class BITMAP(Structure):
            _fields_ = [
                ("bmType", wintypes.LONG),
                ("bmWidth", wintypes.LONG),
                ("bmHeight", wintypes.LONG),
                ("bmWidthBytes", wintypes.LONG),
                ("bmPlanes", wintypes.WORD),
                ("bmBitsPixel", wintypes.WORD),
                ("bmBits", c_void_p)
            ]

        class BITMAPINFOHEADER(Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)
            ]

        ole32 = ctypes.windll.ole32
        shell32 = ctypes.windll.shell32
        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32

        ole32.CoInitialize(None)

        SHCreateItemFromParsingName = shell32.SHCreateItemFromParsingName
        SHCreateItemFromParsingName.argtypes = [wintypes.LPCWSTR, c_void_p, POINTER(GUID), POINTER(c_void_p)]
        SHCreateItemFromParsingName.restype = wintypes.HRESULT

        p_factory = c_void_p()
        caminho_abs = str(Path(caminho_arquivo).resolve())
        hr = SHCreateItemFromParsingName(caminho_abs, None, byref(IID_IShellItemImageFactory), byref(p_factory))
        if hr != 0 or not p_factory.value:
            return None

        vtable = ctypes.cast(p_factory, POINTER(POINTER(c_void_p))).contents
        GetImage = ctypes.WINFUNCTYPE(
            wintypes.HRESULT, c_void_p, SIZE, wintypes.DWORD, POINTER(wintypes.HBITMAP)
        )(vtable[3])

        hbitmap = wintypes.HBITMAP()
        hr2 = GetImage(p_factory, SIZE(tamanho, tamanho), 0x0, byref(hbitmap))
        if hr2 != 0 or not hbitmap.value:
            return None

        bmp = BITMAP()
        gdi32.GetObjectW(hbitmap, ctypes.sizeof(BITMAP), byref(bmp))

        hdc = user32.GetDC(None)
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = bmp.bmWidth
        bmi.biHeight = -bmp.bmHeight  # top-down DIB
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0  # BI_RGB

        buf_size = bmp.bmWidth * bmp.bmHeight * 4
        buffer = (ctypes.c_char * buf_size)()

        gdi32.GetDIBits(hdc, hbitmap, 0, bmp.bmHeight, buffer, byref(bmi), 0)
        user32.ReleaseDC(None, hdc)
        gdi32.DeleteObject(hbitmap)

        return Image.frombuffer("RGBA", (bmp.bmWidth, bmp.bmHeight), buffer, "raw", "BGRA", 0, 1)
    except Exception:
        return None


def gerar_preview_matriz(
    caminho_matriz: Union[str, Path],
    caminho_saida: Optional[Union[str, Path]] = None,
    tamanho: int = 256,
    sobrescrever: bool = False
) -> Optional[str]:
    """
    Gera um arquivo PNG de preview para uma matriz de bordado (.pes, .dst, etc.).
    1º Tenta via Wilcom Shell Extension (renderização nativa de altíssima fidelidade e fundo transparente).
    2º Fallback: utiliza o pyembroidery para renderizar os pontos diretamente em PNG.

    Retorna o caminho normalizado (com barras normais '/') do PNG gerado ou None se falhar.
    """
    caminho_matriz = Path(caminho_matriz)
    if not caminho_matriz.exists():
        return None

    if caminho_saida is None:
        caminho_saida = caminho_matriz.with_suffix(".png")
    else:
        caminho_saida = Path(caminho_saida)

    # Se já existir e não for para sobrescrever, apenas retorna o caminho
    if caminho_saida.exists() and not sobrescrever and caminho_saida.stat().st_size > 0:
        return str(caminho_saida.as_posix())

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    # 1. Tenta extrair via Wilcom Shell Extension
    img = extrair_preview_wilcom(caminho_matriz, tamanho=tamanho)
    if img:
        try:
            img.save(str(caminho_saida), format="PNG")
            if caminho_saida.exists() and caminho_saida.stat().st_size > 0:
                return str(caminho_saida.as_posix())
        except Exception:
            pass

    # 2. Fallback: renderização direta dos pontos via pyembroidery
    try:
        pattern = pyembroidery.read(str(caminho_matriz))
        if pattern:
            pyembroidery.write_png(pattern, str(caminho_saida))
            if caminho_saida.exists() and caminho_saida.stat().st_size > 0:
                return str(caminho_saida.as_posix())
    except Exception:
        pass

    return None

