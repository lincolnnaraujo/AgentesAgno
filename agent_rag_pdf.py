import os

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.google import Gemini
from agno.os import AgentOS
from agno.vectordb.chroma import ChromaDb
from dotenv import load_dotenv, find_dotenv

# 1. Carregar Variáveis de Ambiente
# Load .env from project root
load_dotenv(find_dotenv())

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

# 4. Tools list (empty for now, as we focus on RAG with PDF)
tools_list = []

# Create Knowledge Instance with ChromaDB
knowledge = Knowledge(
    name="Basic SDK Knowledge Base",
    description="Agno 2.0 Knowledge Implementation with ChromaDB",
    vector_db=ChromaDb(
        collection="vectors", path="tmp/chromadb", persistent_client=True
    ),
)

knowledge.add_content(
        name="Ebook Guitarra PDF",
        path="pdfs/ebook-guitarras.pdf"
)

# Create and use the agent
# 5. Instanciar o Agente Agno
agent = Agent(
    model=gemini_instance, # Usa a instância configurada na etapa 3
    knowledge=knowledge,
    markdown=True,          # Habilita respostas em Markdown
    debug_mode=True,         # Habilita o modo de depuração para logs detalhados
    search_knowledge=True # Habilita a busca na base de conhecimento
)

# 6. Instanciar o AgentOS com o agente criado
agent_os = AgentOS(agents = [agent])

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="playground_agent_agno_gemini:app", reload=True) # reload para desenvolvimento