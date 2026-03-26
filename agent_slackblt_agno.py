import logging
import os
import xml.etree.ElementTree as ET

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.tavily import TavilyTools
from dotenv import load_dotenv, find_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Ativa o logging para acompanhar o que o bot está fazendo
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carrega o arquivo .env do diretório raiz do projeto.
# find_dotenv() é útil para garantir que ele encontre o .env
# mesmo se o script for executado de um subdiretório.
load_dotenv(find_dotenv())

TARGET_CHANNEL_ID = None

# Chave para o modelo Gemini (Modo API Key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

# Chave para busca na web (Obrigatória para a instrução do agente)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Chave do Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# Personas
PERSONA_PMPO_XML_PATH = "personas/pm-po-persona.xml"
PERSONA_DEVELOPER_XML_PATH = "personas/java-developer-persona.xml"

# Diretório global para o repositório clonado
REPO_LOCAL_DIR = None

if not GEMINI_API_KEY and not (GOOGLE_PROJECT and GOOGLE_LOCATION):
    raise RuntimeError(
        "Defina `GEMINI_API_KEY` (para API) ou ambos `GOOGLE_CLOUD_PROJECT` e "
        "`GOOGLE_CLOUD_LOCATION` (para Vertex AI) em .env"
    )

if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY não encontrada. O agente não poderá fazer buscas na web.")

# === 4. CONFIGURAÇÃO DO MODELO (LLM) ===

# Define o ID do modelo Gemini.
MODEL_ID = "gemini-2.5-flash"

# Se o projeto/local do Google Cloud forem fornecidos, exporta-os
# para que o cliente Vertex AI os utilize automaticamente.
if GOOGLE_PROJECT:
    os.environ["GOOGLE_CLOUD_PROJECT"] = GOOGLE_PROJECT
if GOOGLE_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_LOCATION

# Instancia o modelo Gemini (Apenas uma vez)
if GEMINI_API_KEY:
    logger.info("Usando Gemini via API Key.")
    gemini_instance = Gemini(id=MODEL_ID, api_key=GEMINI_API_KEY)
else:
    logger.info(f"Usando Gemini via Vertex AI (Projeto: {GOOGLE_PROJECT}).")
    # Para Vertex AI, Agno só precisa saber que é Vertex.
    # As variáveis de ambiente (GOOGLE_PROJECT) são lidas internamente.
    gemini_instance = Gemini(id=MODEL_ID, vertexai=True)

    # --- Função Auxiliar: Ler XML ---


# --- Função 1: Ler XML (Atualizada para ler <channel>) ---
def load_config_from_xml(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        description = root.find('description').text.strip() if root.find('description') is not None else "Assistente."

        target_channel_name = root.find('channel').text.strip() if root.find('channel') is not None else None

        instructions = []
        if root.find('instructions') is not None:
            for item in root.find('instructions').findall('item'):
                if item.text: instructions.append(item.text.strip())

        return description, instructions, target_channel_name

    except Exception as e:
        logger.error(f"Erro ao ler XML: {e}")
        return "Assistente", [], None


#### Personas
def load_persona_from_xml(filepath):
    """Lê a descrição e instruções de um arquivo XML."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Extrai a descrição (texto simples)
        description_node = root.find('description')
        description = description_node.text.strip() if description_node is not None else "Você é um assistente útil."

        # Extrai a lista de instruções
        instructions_node = root.find('instructions')
        instructions = []
        if instructions_node is not None:
            for item in instructions_node.findall('item'):
                if item.text:
                    instructions.append(item.text.strip())

        logger.info(f"Persona carregada com sucesso de {filepath}")
        return description, instructions

    except FileNotFoundError:
        logger.warning(f"Arquivo {filepath} não encontrado. Usando persona padrão.")
        return "Você é um assistente útil.", ["Responda de forma concisa."]
    except ET.ParseError:
        logger.error(f"Erro de sintaxe no XML {filepath}.")
        return "Erro na config.", []


# --- Função 2: Descobrir o ID do Canal pelo Nome ---
def get_channel_id_by_name(app, channel_name):
    """Busca na lista de canais públicos do Slack o ID correspondente ao nome."""
    try:
        # Lista canais (pode precisar de paginação se tiver milhares, aqui simplificado)
        result = app.client.conversations_list(types="public_channel,private_channel")
        channels = result["channels"]

        for channel in channels:
            if channel["name"] == channel_name:
                return channel["id"]

        logger.warning(f"Canal '{channel_name}' não encontrado na lista do bot.")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar canais: {e}")
        return None

# --- 1. Configuração do Agente Agno (Phidata) ---
def get_agno_agent():
    # Carrega a configuração do XML
    xml_description, xml_instructions = load_persona_from_xml(PERSONA_PMPO_XML_PATH)

    return Agent(
        model=gemini_instance,
        tools=[TavilyTools()],
        markdown=True,
        # Configurações injetadas via XML
        description=xml_description,
        instructions=xml_instructions,
        show_tool_calls=True
    )


# Instancia o agente (agora com a persona do XML)
agent = get_agno_agent()

# --- 2. Configuração do Slack App ---
app = App(token=SLACK_BOT_TOKEN)


# --- Handler de Mensagem ---
@app.message()
def handle_message(message, say):
    global TARGET_CHANNEL_ID

    # 1. Filtro de Canal: Se definimos um canal alvo, verificamos se a msg veio dele
    if TARGET_CHANNEL_ID and message["channel"] != TARGET_CHANNEL_ID:
        # Se a mensagem veio de "desenvolvimento", o bot ignora silenciosamente
        return

    # Filtros padrão (ignora outros bots)
    if message.get("bot_id") or message.get("subtype") == "bot_message":
        return

    user_question = message.get("text")
    logger.info(f"Processando mensagem no canal {target_channel_name}: {user_question}")

    try:
        app.client.reactions_add(channel=message["channel"], name="eyes", timestamp=message["ts"])

        response = agent.run(user_question, stream=False)
        final_response = f"*Resposta para a pergunta: {user_question}*\n\n{response.content}"

        say(text=final_response, mrkdwn=True)

        app.client.reactions_remove(channel=message["channel"], name="eyes", timestamp=message["ts"])
        app.client.reactions_add(channel=message["channel"], name="white_check_mark", timestamp=message["ts"])

    except Exception as e:
        logger.error(f"Erro: {e}")


# --- Inicialização ---
if __name__ == "__main__":
    logger.info("⚡️ Iniciando Listener...")

    # Antes de começar a ouvir, resolvemos o nome do canal para ID
    if target_channel_name:
        TARGET_CHANNEL_ID = get_channel_id_by_name(app, target_channel_name)
        if TARGET_CHANNEL_ID:
            logger.info(f"Bot restrito ao canal: {target_channel_name} (ID: {TARGET_CHANNEL_ID})")
        else:
            logger.error(
                f"ATENÇÃO: Não foi possível encontrar o ID para '{target_channel_name}'. O bot pode não responder.")

    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()