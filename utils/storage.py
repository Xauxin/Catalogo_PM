import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from utils.auth import obter_supabase_client

BUCKET_NAME = "bordados"
UPLOAD_LOCAL_DIR = Path("uploads/bordados")
UPLOAD_LOCAL_DIR.mkdir(parents=True, exist_ok=True)

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def upload_arquivo_imagem(
    arquivo_ou_bytes: Union[any, bytes, str, Path],
    prefixo: str = "img",
    nome_original: Optional[str] = None,
) -> Optional[str]:
    """
    Realiza o upload de imagem para o Supabase Storage (bucket 'bordados')
    e retorna sua URL pública acessível em qualquer lugar.
    Mantém uma cópia de contingência local em uploads/bordados.
    """
    if arquivo_ou_bytes is None:
        return None

    # 1. Determina nome e extensão
    if hasattr(arquivo_ou_bytes, "name"):
        nome_base = arquivo_ou_bytes.name
    elif nome_original:
        nome_base = nome_original
    elif isinstance(arquivo_ou_bytes, (str, Path)):
        nome_base = Path(arquivo_ou_bytes).name
    else:
        nome_base = "imagem.png"

    ext = Path(nome_base).suffix.lower()
    if ext not in MIME_TYPES:
        ext = ".png"

    content_type = MIME_TYPES.get(ext, "image/png")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    limpo = re.sub(r"[^a-zA-Z0-9_-]", "_", prefixo).strip("_") or "arquivo"
    nome_arquivo = f"{limpo}_{timestamp}{ext}"

    # 2. Extrai os bytes
    if hasattr(arquivo_ou_bytes, "getvalue"):
        bytes_data = arquivo_ou_bytes.getvalue()
    elif hasattr(arquivo_ou_bytes, "read"):
        bytes_data = arquivo_ou_bytes.read()
    elif isinstance(arquivo_ou_bytes, (str, Path)):
        p = Path(arquivo_ou_bytes)
        if not p.exists():
            return None
        with open(p, "rb") as f:
            bytes_data = f.read()
    elif isinstance(arquivo_ou_bytes, bytes):
        bytes_data = arquivo_ou_bytes
    else:
        return None

    if not bytes_data:
        return None

    # 3. Salva cópia local como backup e contingência
    destino_local = UPLOAD_LOCAL_DIR / nome_arquivo
    try:
        with open(destino_local, "wb") as f:
            f.write(bytes_data)
    except Exception as e:
        print(f"⚠️ Aviso ao salvar cópia local: {e}")

    # 4. Upload no Supabase Storage
    client = obter_supabase_client()
    if client:
        try:
            client.storage.from_(BUCKET_NAME).upload(
                path=nome_arquivo,
                file=bytes_data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            url_publica = client.storage.from_(BUCKET_NAME).get_public_url(nome_arquivo)
            return url_publica
        except Exception as err:
            print(f"⚠️ Erro ao enviar imagem ao Supabase Storage: {err}")
            # Em caso de erro na nuvem, retorna o caminho local
            return str(destino_local).replace("\\", "/")

    return str(destino_local).replace("\\", "/")


def migrar_imagens_locais_para_supabase(limite: Optional[int] = None) -> dict:
    """
    Percorre os bordados no banco de dados e faz o upload de imagens locais
    para o Supabase Storage, substituindo os caminhos locais por URLs públicas.
    """
    from core.repository import CatalogoRepository

    client = obter_supabase_client()
    if not client:
        return {"status": "erro", "mensagem": "Supabase client não configurado."}

    bordados = CatalogoRepository.listar_templates_bordado(role_usuario="admin")
    total_migrados = 0
    total_erros = 0

    itens_processar = bordados[:limite] if limite else bordados

    for b in itens_processar:
        alterou = False
        nova_dig = b.imagem_digital
        nova_foto = b.foto_bordado

        # Migra arte digital se for caminho local existente
        if b.imagem_digital and not b.imagem_digital.startswith("http"):
            caminho_local = Path(b.imagem_digital)
            if caminho_local.exists():
                url_up = upload_arquivo_imagem(
                    caminho_local,
                    prefixo=f"digital_{b.codigo_identificacao or b.id}",
                    nome_original=caminho_local.name,
                )
                if url_up and url_up.startswith("http"):
                    nova_dig = url_up
                    alterou = True

        # Migra foto real se for caminho local existente
        if b.foto_bordado and not b.foto_bordado.startswith("http"):
            caminho_local = Path(b.foto_bordado)
            if caminho_local.exists():
                url_up = upload_arquivo_imagem(
                    caminho_local,
                    prefixo=f"foto_{b.codigo_identificacao or b.id}",
                    nome_original=caminho_local.name,
                )
                if url_up and url_up.startswith("http"):
                    nova_foto = url_up
                    alterou = True

        if alterou:
            try:
                CatalogoRepository.atualizar_imagens_template_bordado(
                    b.id, imagem_digital=nova_dig, foto_bordado=nova_foto
                )
                total_migrados += 1
            except Exception as e:
                print(f"⚠️ Erro ao atualizar bordado #{b.id}: {e}")
                total_erros += 1

    return {
        "status": "sucesso",
        "migrados": total_migrados,
        "erros": total_erros,
        "total_analisados": len(itens_processar),
    }
