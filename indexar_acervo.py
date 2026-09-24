#!/usr/bin/env python3
"""
Script de Indexação Automática do Acervo de Matrizes e Brasões.
Lê os arquivos de bordado (.dst, .pes, .exp, .jef, etc.) na pasta organizada,
extrai pontos, dimensões, trocas de cor, códigos de linha com pyembroidery
e grava/atualiza no banco de dados (Supabase PostgreSQL ou SQLite local).
"""

import os
import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
raiz_projeto = Path(__file__).resolve().parent
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlmodel import select
from core.database import get_session
from core.models import TemplateBordado
from utils.embroidery_reader import extrair_dados_matriz

# Pastas padrão onde o acervo pode ser colocado
PASTAS_ACERVO = [
    Path("matrizes"),
    Path("matrizes/logos_e_brasoes"),
    Path("logos_e_brasoes"),
    Path("ESPECIALIDADES_PRONTAS"),
]

EXTENSOES_BORDADO = {".dst", ".pes", ".exp", ".jef", ".vp3", ".xxx"}
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}


def normalizar_tipo(pasta_tipo: str) -> str:
    """Normaliza o nome da pasta de tipo para um padrão consistente."""
    limpo = pasta_tipo.replace("_", " ").strip()
    low = limpo.lower()
    if low in ["brasao", "brasão", "brasoes", "brasões"]:
        return "Brasão"
    if low in ["logo", "logos"]:
        return "Logo"
    if low in ["logo fixo", "logofixo"]:
        return "Logo Fixo"
    if low in ["logos e brasoes", "logos e brasões", "logo/brasao", "logo/brasão"]:
        return "Logo/Brasão"
    if low in ["desenho", "desenhos"]:
        return "Desenho"
    if low in ["escudo", "escudos"]:
        return "Escudo"
    if low in ["aplique", "apliques"]:
        return "Aplique"
    return limpo.title() if limpo.islower() else limpo


def localizar_pasta_acervo(caminho_especifico: str = None) -> Path:
    if caminho_especifico:
        p = Path(caminho_especifico)
        if p.exists() and p.is_dir():
            return p
        print(f"⚠️ Pasta informada '{caminho_especifico}' não foi encontrada.")

    for p in PASTAS_ACERVO:
        if p.exists() and p.is_dir():
            return p

    # Se nenhuma existir, cria a pasta padrão sugerida
    padrao = Path("matrizes")
    padrao.mkdir(parents=True, exist_ok=True)
    return padrao


def indexar_arquivos(pasta_base: Path):
    print(f"\n========================================================")
    print(f"🚀 INICIANDO INDEXAÇÃO DE MATRIZES EM: {pasta_base.resolve()}")
    print(f"========================================================\n")

    arquivos_encontrados = []
    for root, _, files in os.walk(pasta_base):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in EXTENSOES_BORDADO:
                arquivos_encontrados.append(Path(root) / f)

    if not arquivos_encontrados:
        print(f"ℹ️ Nenhum arquivo de bordado ({', '.join(EXTENSOES_BORDADO)}) encontrado na pasta.")
        print(f"👉 Dica: Coloque seus arquivos organizados dentro de: {pasta_base.resolve()}")
        print(f"   Exemplo de estrutura (Tipo / Categoria / Subcategoria / Arquivo):")
        print(f"   {pasta_base}/Brasão/Faculdades/Unicesumar/Medicina.dst")
        print(f"   {pasta_base}/Logo/Faculdades/Unicesumar/Logo_Unicesumar.dst")
        print(f"   {pasta_base}/Brasão/Cursos/Direito.dst")
        print(f"   {pasta_base}/Logo/Empresas/Logo_Empresa.dst")
        return

    print(f"🔍 Encontrados {len(arquivos_encontrados)} arquivos de matrizes. Processando com pyembroidery...\n")

    novos = 0
    atualizados = 0
    erros = 0

    with get_session() as session:
        for arq in arquivos_encontrados:
            try:
                # 1. Determina hierarquia de pastas (Tipo / Categoria / Subcategoria / Nome)
                rel_path = arq.relative_to(pasta_base)
                partes = rel_path.parts

                nome_matriz = arq.stem.replace("_", " ").strip()
                tipo = "Logo Fixo"
                categoria = "Geral"
                subcategoria = None

                # A primeira pasta determina o TIPO (ex: Brasão, Logo, etc.)
                # As pastas seguintes determinam Categoria e Subcategoria
                if len(partes) >= 4:
                    tipo = normalizar_tipo(partes[0])
                    categoria = partes[1].replace("_", " ").strip()
                    subcategoria = " > ".join(p.replace("_", " ").strip() for p in partes[2:-1])
                elif len(partes) == 3:
                    tipo = normalizar_tipo(partes[0])
                    categoria = partes[1].replace("_", " ").strip()
                    subcategoria = None
                elif len(partes) == 2:
                    tipo = normalizar_tipo(partes[0])
                    categoria = "Geral"
                    subcategoria = None
                else:
                    tipo = "Logo Fixo"
                    categoria = "Geral"
                    subcategoria = None

                # Remove prefixo redundante do tipo no nome do arquivo (ex: "Brasão Medicina..." -> "Medicina...")
                prefixos_remover = [tipo.lower(), "brasão", "brasao", "logo fixo", "logo"]
                for pref in prefixos_remover:
                    if nome_matriz.lower().startswith(pref + " "):
                        nome_matriz = nome_matriz[len(pref) + 1:].strip()
                        break

                # 2. Busca imagem de preview com o mesmo nome na mesma pasta
                imagem_digital = None
                for ext_img in EXTENSOES_IMAGEM:
                    img_candidata = arq.with_suffix(ext_img)
                    if img_candidata.exists():
                        # Armazena caminho relativo para uso web
                        imagem_digital = str(img_candidata.as_posix())
                        break

                # 3. Extrai dados técnicos com pyembroidery
                dados = extrair_dados_matriz(arq)
                if not dados:
                    print(f"⚠️ Não foi possível ler os pontos de: {rel_path}")
                    erros += 1
                    continue

                caminho_rel_salvo = str(rel_path.as_posix())

                # 4. Verifica se já existe no banco
                stmt = select(TemplateBordado).where(
                    (TemplateBordado.arquivo_dst == caminho_rel_salvo)
                    | (
                        (TemplateBordado.nome == nome_matriz)
                        & (TemplateBordado.tipo == tipo)
                        & (TemplateBordado.categoria == categoria)
                        & (TemplateBordado.subcategoria == subcategoria)
                    )
                )
                existente = session.exec(stmt).first()

                if existente:
                    # Atualiza dados técnicos
                    existente.tipo = tipo
                    existente.categoria = categoria
                    existente.subcategoria = subcategoria
                    existente.pontos = dados["pontos"]
                    existente.largura_mm = dados["largura_mm"]
                    existente.altura_mm = dados["altura_mm"]
                    existente.trocas_cor = dados["trocas_cor"]
                    existente.linhas_usadas = dados["linhas_usadas"]
                    existente.cores_detalhes = dados["cores_detalhes"]
                    existente.arquivo_dst = caminho_rel_salvo
                    if imagem_digital and not existente.imagem_digital:
                        existente.imagem_digital = imagem_digital

                    session.add(existente)
                    atualizados += 1
                    print(f"🔄 Atualizado: ({tipo}) [{categoria} > {subcategoria or '-'}] {nome_matriz} ({dados['pontos']} pts, {dados['linhas_usadas']})")
                else:
                    novo = TemplateBordado(
                        nome=nome_matriz,
                        tipo=tipo,
                        categoria=categoria,
                        subcategoria=subcategoria,
                        arquivo_dst=caminho_rel_salvo,
                        pontos=dados["pontos"],
                        largura_mm=dados["largura_mm"],
                        altura_mm=dados["altura_mm"],
                        trocas_cor=dados["trocas_cor"],
                        cores_detalhes=dados["cores_detalhes"],
                        linhas_usadas=dados["linhas_usadas"],
                        preco=15.00,
                        matriz_pronta=True,
                        preco_matriz=0.00,
                        imagem_digital=imagem_digital,
                    )
                    session.add(novo)
                    novos += 1
                    print(f"✨ Cadastrado: ({tipo}) [{categoria} > {subcategoria or '-'}] {nome_matriz} ({dados['pontos']} pts, {dados['linhas_usadas']})")

            except Exception as e:
                print(f"❌ Erro ao processar {arq}: {type(e).__name__} - {e}")
                erros += 1

        session.commit()

    print(f"\n========================================================")
    print(f"✅ INDEXAÇÃO CONCLUÍDA:")
    print(f"   - Novos cadastrados: {novos}")
    print(f"   - Atualizados:       {atualizados}")
    print(f"   - Falhas/Erros:      {erros}")
    print(f"   - Total no acervo:   {novos + atualizados}")
    print(f"========================================================\n")


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else None
    pasta = localizar_pasta_acervo(caminho)
    indexar_arquivos(pasta)
