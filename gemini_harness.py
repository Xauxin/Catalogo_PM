import os
import sys
import re
from google import genai
from google.genai import types

# 1. Configuração e Inicialização do Cliente
# O novo SDK puxa automaticamente a variável de ambiente GEMINI_API_KEY
if not os.environ.get("GEMINI_API_KEY"):
    print("Erro: Configure a variável de ambiente GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client()

# 2. Instruções de Sistema (O seu Mentor Sucinto)
INSTRUCOES_MENTOR = """
Você é um mentor de programação experiente, porém muito sucinto e direto ao ponto.
O usuário é um desenvolvedor nível Júnior. Regras obrigatórias:
1. Analise o código do usuário para identificar a linguagem e bibliotecas usadas. Mantenha-se dentro desse ecossistema.
2. Use implementações simples e adequadas para um júnior. Siga os padrões que ele já está usando.
3. ALERTA DE NOVIDADE: Se você precisar introduzir uma função, conceito, biblioteca ou método diferente do código original, DEVE avisar e oferecer explicação.
4. Explique o "porquê" brevemente quando solicitado, focando no aprendizado.
"""

# Nova forma de configurar as instruções do modelo
configuracao_mentor = types.GenerateContentConfig(
    system_instruction=INSTRUCOES_MENTOR,
    temperature=0.7
)

# 3. Dicionário de Atalhos
COMANDOS_ATALHO = {
    "/refatorar": "Refatore o código fornecido, melhorando a legibilidade sem alterar o que ele faz.",
    "/explicar": "Explique passo a passo como o código funciona, de forma simples para um júnior.",
    "/testar": "Crie exemplos de testes unitários ou de execução simples para o código.",
    "/planejar": "Analise o cenário e crie um plano de mudanças em tópicos para aprovação. Não escreva o código final ainda."
}

def extrair_codigo(texto_resposta):
    match = re.search(r'```(?:\w+)?\n(.*?)```', texto_resposta, re.DOTALL)
    return match.group(1) if match else None

def carregar_contexto_inicial(chat):
    print("🔍 Analisando o projeto automaticamente...")
    contexto = "INSTRUÇÃO INTERNA: O usuário acabou de iniciar o harness. Contexto atual do projeto abaixo. Apenas diga 'Entendido'.\n\n"
    
    arquivos_encontrados = []
    
    if os.path.exists("package.json"):
        with open("package.json", "r", encoding='utf-8') as f:
            contexto += f"Dependências (package.json):\n{f.read()[:2000]}\n\n"
        arquivos_encontrados.append("package.json")
            
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding='utf-8') as f:
            contexto += f"Dependências (requirements.txt):\n{f.read()[:2000]}\n\n"
        arquivos_encontrados.append("requirements.txt")
        
    lista_arquivos = [f for f in os.listdir('.') if os.path.isfile(f)]
    contexto += f"Arquivos na raiz: {', '.join(lista_arquivos)}\n"
    
    try:
        # Envia a mensagem inicial
        chat.send_message(contexto)
        if arquivos_encontrados:
            print(f"✅ Contexto carregado: {', '.join(arquivos_encontrados)} detectados.")
        else:
            print("✅ Estrutura de pastas carregada.")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar o contexto inicial ({e})")

def main():
    print("🎓 Harness Mentor Iniciado (Novo SDK Google GenAI)")
    print("Comandos: /ler <arquivo>, /salvar <arquivo>, /refatorar, /explicar, /testar, /planejar")
    print("-" * 65)
    
    # Inicia a sessão de chat com o modelo e a configuração
    chat = client.chats.create(
        model='gemini-3.5-flash',
        config=configuracao_mentor
    )
    
    carregar_contexto_inicial(chat)
    ultima_resposta_ia = ""
    
    while True:
        try:
            user_input = input("\nVocê: ")
            
            if user_input.strip().lower() in ['sair', 'exit']:
                print("Até a próxima! Bom código.")
                break
                
            if not user_input.strip():
                continue

            # Ação de Escrita: Comando /salvar
            if user_input.startswith("/salvar "):
                arquivo_destino = user_input.split(" ", 1)[1].strip()
                codigo_extraido = extrair_codigo(ultima_resposta_ia)
                
                if codigo_extraido:
                    with open(arquivo_destino, 'w', encoding='utf-8') as f:
                        f.write(codigo_extraido)
                    print(f"✅ Código salvo em '{arquivo_destino}'!")
                else:
                    print("❌ Não encontrei nenhum bloco de código na última resposta.")
                continue

            prompt_final = user_input

            # Comando /ler
            if "/ler " in prompt_final:
                match = re.search(r'/ler\s+(\S+)', prompt_final)
                if match:
                    nome_arquivo = match.group(1)
                    try:
                        with open(nome_arquivo, 'r', encoding='utf-8') as f:
                            conteudo = f.read()
                        texto_substituto = f"\n[Conteúdo de {nome_arquivo}]:\n```\n{conteudo}\n```\n"
                        prompt_final = prompt_final.replace(match.group(0), texto_substituto)
                        print(f"📂 Arquivo '{nome_arquivo}' carregado.")
                    except FileNotFoundError:
                        print(f"❌ Erro: Arquivo '{nome_arquivo}' não encontrado.")
                        continue

            # Comandos de atalho
            for atalho, instrucao in COMANDOS_ATALHO.items():
                if atalho in prompt_final:
                    prompt_final = prompt_final.replace(atalho, f"\n{instrucao}\n")
                    print(f"⚡ Comando {atalho} ativado.")

            # Envia via streaming usando o novo método send_message_stream
            response = chat.send_message_stream(prompt_final)
            
            print("\nMentor: ", end="", flush=True)
            resposta_completa = ""
            for chunk in response:
                print(chunk.text, end="", flush=True)
                resposta_completa += chunk.text
            print("\n" + "-"*40)
            
            ultima_resposta_ia = resposta_completa
            
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"\n[Erro na API]: {e}")

if __name__ == "__main__":
    main()