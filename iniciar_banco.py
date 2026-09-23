from sqlmodel import SQLModel

from core.database import engine

# É CRUCIAL importar os modelos aqui, mesmo que não os use diretamente no script.
# Isso garante que o SQLModel os leia e saiba quais tabelas criar.
from core.models import Bordado, LocalBordado, Lote, Peca, TemplateBordado, TemplatePeca
from core.repository import CatalogoRepository


def criar_tabelas():
    print("⏳ Criando tabelas no banco de dados...")
    # Este comando lê todos os modelos importados e cria as tabelas correspondentes
    SQLModel.metadata.create_all(engine)
    print("✅ Tabelas criadas com sucesso!")


def popular_catalogo_inicial():
    print("⏳ Povoando catálogo inicial de peças...")
    templates_existentes = CatalogoRepository.listar_templates()

    if not templates_existentes:
        # Se o banco estiver vazio, insere os dados padrão
        CatalogoRepository.salvar_template_peca(
            "Camisa Polo", ["Peito Esquerdo", "Manga Direita", "Costas"]
        )
        CatalogoRepository.salvar_template_peca(
            "Jaleco Hospitalar", ["Peito Esquerdo", "Manga Esquerda"]
        )
        CatalogoRepository.salvar_template_peca(
            "Boné Tactel", ["Frente", "Lateral Esquerda"]
        )
        print("✅ Catálogo inicial inserido com sucesso!")
    else:
        print("⚡ O catálogo já possui peças cadastradas. Pulando esta etapa.")


if __name__ == "__main__":
    criar_tabelas()

    print("🚀 Banco de dados pronto para uso!")
