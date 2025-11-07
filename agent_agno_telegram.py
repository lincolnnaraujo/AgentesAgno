#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agente de Pesquisa com IA para Telegram (Agno + Gemini + Tavily)

Este script implementa um bot do Telegram que utiliza a biblioteca 'agno'
para criar um agente de IA. O agente usa o Google Gemini como cérebro (LLM)
e pode ser equipado com ferramentas como Tavily (busca na web), YFinance (dados
financeiros) e Telegram (para enviar mensagens proativamente).

O bot responde a mensagens de texto pesquisando na web (via Tavily) e
formatando a resposta em Markdown V2.
"""

# === 1. IMPORTS E CONFIGURAÇÃO INICIAL ===

import os
import logging
from dotenv import load_dotenv, find_dotenv

# --- Bibliotecas Agno (O Framework do Agente) ---
from agno.models.google import Gemini
from agno.agent import Agent
from agno.tools.tavily import TavilyTools
from agno.tools.telegram import TelegramTools
from agno.tools.yfinance import YFinanceTools

# --- Bibliotecas Telegram (A Interface do Bot) ---
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode, ChatAction

# === 2. CONFIGURAÇÃO DE LOGGING ===

# Ativa o logging para acompanhar o que o bot está fazendo
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === 3. CARREGAMENTO DE VARIÁVEIS DE AMBIENTE ===

# Carrega o arquivo .env do diretório raiz do projeto.
# find_dotenv() é útil para garantir que ele encontre o .env
# mesmo se o script for executado de um subdiretório.
load_dotenv(find_dotenv())

# --- Chaves de API ---

# Chave para busca na web (Obrigatória para a instrução do agente)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Chave para o bot do Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Chave para o modelo Gemini (Modo API Key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Credenciais para o modelo Gemini (Modo Vertex AI)
GOOGLE_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

# ID do Chat para a *ferramenta* Telegram (para o agente enviar msgs)
# Nota: Isso é usado pela *ferramenta* (Agno), não pelo bot em si.
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Validação das Variáveis Críticas ---

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN não encontrado em .env. O bot não pode iniciar.")

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


# === 5. CONFIGURAÇÃO DAS FERRAMENTAS (TOOLS) ===

tools_list = []

# 1. Ferramenta de Busca (Tavily)
if TAVILY_API_KEY:
    tavily_tool = TavilyTools(api_key=TAVILY_API_KEY)
    tools_list.append(tavily_tool)
    logger.info("Ferramenta Tavily (Busca Web) adicionada.")
else:
    logger.warning("Tavily não será usado. O agente terá conhecimento limitado.")

# 2. Ferramenta do Telegram (Para o agente enviar mensagens)
telegram_tools = TelegramTools(
    token=TELEGRAM_TOKEN,
    chat_id=TELEGRAM_CHAT_ID,
    enable_send_message=True
)
tools_list.append(telegram_tools)
logger.info("Ferramenta Telegram (Enviar Mensagem) adicionada.")

# 3. Ferramenta de Finanças (YFinance)
tools_list.append(YFinanceTools())
logger.info("Ferramenta YFinance (Cotações) adicionada.")


# === 6. CONFIGURAÇÃO DO AGENTE (AGNO) ===

# O "Agente" é o cérebro que orquestra o Modelo (LLM) e as Ferramentas.
agent = Agent(
    model=gemini_instance,      # O cérebro (Gemini)
    name="AgenteDePesquisa",
    tools=tools_list,           # As ferramentas que ele pode usar

    # Instruções são o "Prompt de Sistema"
    instructions=[
        "Você é um assistente de pesquisa.",
        "Você DEVE usar a ferramenta TavilySearch para pesquisar na internet a mensagem do usuário.",
        "Após obter os resultados da busca, sintetize uma resposta clara e útil.",
        "Você DEVE formatar sua resposta final inteiramente na sintaxe Markdown V2.",
    ],

    # Habilita o processamento de Markdown na saída do Agno
    markdown=True,

    # Modo Debug (Verbosidade)
    debug_mode=True
)


# === 7. HANDLERS DO BOT TELEGRAM ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Envia uma mensagem de boas-vindas quando o comando /start é emitido.
    """
    await update.message.reply_text(
        "Olá! Sou um agente de pesquisa com IA. Pergunte-me qualquer coisa!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa mensagens de texto do usuário.
    1. Envia a mensagem para o Agente Agno.
    2. O Agente (com Gemini) decide usar ferramentas (Tavily).
    3. O Agente formula uma resposta em Markdown V2.
    4. Envia a resposta de volta ao usuário.
    """
    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Recebida mensagem de {chat_id}: {user_text}")

    response_text = "" # Inicializa para o bloco 'except'

    try:
        # Mostra "Digitando..." no Telegram para feedback do usuário
        await context.bot.send_chat_action(
            chat_id=chat_id,
            action=ChatAction.TYPING
        )

        # 1. Executa o agente com o texto do usuário
        #    'agent.run()' retorna um objeto RunOutput
        run_output = agent.run(user_text)

        # 2. Extrai a string de texto final da propriedade .content
        response_text = run_output.content

        # 3. Envia a resposta formatada em Markdown V2
        await update.message.reply_text(
            text=str(response_text),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

        # Tratamento de erro específico para falhas de parsing do Markdown
        if "can't parse entities" in str(e) and response_text:
            logger.error("Erro de parsing do Markdown V2. Enviando como texto puro.")
            await update.message.reply_text(
                "Encontrei uma resposta, mas tive problemas para formatá-la "
                "(erro de Markdown V2). Aqui está o texto puro:\n\n" + response_text
            )
        else:
            # Resposta genérica de erro
            await update.message.reply_text(f"Desculpe, encontrei um erro: {e}")


# === 8. INICIALIZAÇÃO DO BOT ===

def main() -> None:
    """
    Função principal que configura e inicia o bot do Telegram.
    """
    logger.info("Iniciando o bot...")

    # Cria a Aplicação do Bot usando o Token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Registra os handlers (comandos e mensagens)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Inicia o Bot (modo "polling" - fica perguntando ao Telegram por atualizações)
    application.run_polling()


if __name__ == "__main__":
    main()