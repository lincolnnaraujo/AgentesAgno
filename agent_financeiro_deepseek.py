# python

from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv, find_dotenv

# Load .env from project root
load_dotenv(find_dotenv())

agent = Agent(
    model=DeepSeek(id="deepseek-chat"),
    tools=[YFinanceTools()],
    instructions="Use tabela para formatar dados financeiros. Nao inclua nenhum outro texto.",
    debug_mode=True,
    markdown=True
)

agent.print_response("Qual a cotacao atual do Itau?", stream=True) # com stream de resposta
