import os

# Importar as classes necessárias do Agno
from agno.agent import Agent
from agno.models.google import Gemini
from agno.os import AgentOS
from agno.tools.tavily import TavilyTools  # Importação necessária para a ferramenta de busca
from dotenv import load_dotenv, find_dotenv
from agno.db.sqlite import SqliteDb

# 1. Carregar Variáveis de Ambiente
# Load .env from project root
load_dotenv(find_dotenv())

# Required: Tavily API key
tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    # Se o Tavily for usado, a chave deve existir
    print("Aviso: TAVILY_API_KEY não encontrada. O agente não poderá fazer buscas na web.")
    # Se você quiser que o script pare sem a chave Tavily, descomente a linha abaixo:
    # raise RuntimeError("TAVILY_API_KEY not found in .env")

# Gemini: either provide a GEMINI_API_KEY or both GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
gemini_api_key = os.getenv("GEMINI_API_KEY")
google_project = os.getenv("GOOGLE_CLOUD_PROJECT")
google_location = os.getenv("GOOGLE_CLOUD_LOCATION")

if not gemini_api_key and not (google_project and google_location):
    raise RuntimeError(
        "Defina `GEMINI_API_KEY` ou ambos `GOOGLE_CLOUD_PROJECT` e `GOOGLE_CLOUD_LOCATION` em `.env`"
    )

# 2. Configurar Variáveis de Ambiente para Vertex AI (se aplicável)
# Se project/location provided, export them for the Vertex AI client
if google_project:
    os.environ["GOOGLE_CLOUD_PROJECT"] = google_project
if google_location:
    os.environ["GOOGLE_CLOUD_LOCATION"] = google_location


# --- CONSOLIDAÇÃO DO MODELO ---

# Definir o ID do modelo (usando um modelo padrão robusto)
MODEL_ID = "gemini-2.5-flash" # Use um modelo que suporte ferramentas

# 3. Instanciar o modelo Gemini (Apenas uma vez)
if gemini_api_key:
    print("Usando Gemini via API Key.")
    gemini_instance = Gemini(id=MODEL_ID, api_key=gemini_api_key)
else:
    print(f"Usando Gemini via Vertex AI (Projeto: {google_project}, Local: {google_location}).")
    # Quando usamos Vertex AI, precisamos apenas definir vertexai=True
    gemini_instance = Gemini(id=MODEL_ID, vertexai=True)

# 4. Instanciar a Ferramenta de Busca (Tavily)
tools_list = []
if tavily_key:
    tavily_tool = TavilyTools(api_key=tavily_key)
    tools_list.append(tavily_tool)
    print("Ferramenta Tavily adicionada para busca na web.")

# 6. Instanciar o banco de dados SQLite para histórico de conversas
db = SqliteDb(db_file="tmp/data.db")

# 5. Instanciar o Agente Agno
agent = Agent(
    model=gemini_instance, # Usa a instância configurada na etapa 3
    db=db,                  # Adiciona o banco de dados para histórico
    tools=tools_list,      # Adiciona a ferramenta de busca (essencial para a pergunta)
    markdown=True,          # Habilita respostas em Markdown
    add_history_to_context=True, # Habilita o histórico de conversas
    num_history_runs=3,     # Default 3 - 3 ultimas interações
    debug_mode=True         # Habilita o modo de depuração para logs detalhados
)

# 6. Instanciar o AgentOS com o agente criado
agent_os = AgentOS(agents = [agent])

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="playground_agent_agno_gemini:app", reload=True) # reload para desenvolvimento