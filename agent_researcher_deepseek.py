# python
import sys

from agno.agent import Agent
from agno.tools.tavily import TavilyTools
from dotenv import load_dotenv, find_dotenv
from agno.models.deepseek import DeepSeek
import os

# Load .env from project root
load_dotenv(find_dotenv())

# Required: Tavily API key
tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    raise RuntimeError("TAVILY_API_KEY not found in .env")

agent = Agent(
    model=DeepSeek(id="deepseek-chat"),
    tools=[TavilyTools(
        api_key=tavily_key,
        max_tokens=8000,
        search_depth="advanced",
        format="markdown"
    )]
)

try:
    agent.print_response("Qual o canal do youtube mais famoso no brasil ?")
except Exception as e:
    msg = str(e).lower()
    if "insufficient balance" in msg or "insufficient funds" in msg or "quota" in msg:
        sys.stderr.write(
            "ModelProviderError: insufficient balance or quota detected.\n"
            "Actions:\n"
            "- Verify billing is enabled and the project has funds (Google Cloud / provider account).\n"
            "- If using a provider-specific key (e.g. GEMINI_API_KEY or Tavily account), top up or contact support.\n"
            "- Consider switching to a different model or provider if urgent.\n"
        )
        raise RuntimeError("Model provider account has insufficient balance or quota.") from e
    raise