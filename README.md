# AgentesAgno — Exemplos / POCs com agentes Agno

Repositório com vários exemplos e proofs-of-concept (POCs) mostrando como criar e executar agentes usando o framework Agno (versão alvo: 2.2.0). Cada exemplo demonstra padrões diferentes, integrações (Gemini / Vertex AI), ferramentas de busca e backends de vetores (ChromaDB recomendado).

## Estrutura do repositório

- `playground_agent_agno_gemini.py` — playground interativo usando Gemini / Vertex AI.  
- `agent_agno_gemini.py` — exemplo de agente configurado para Gemini.  
- `agent_rag_pdf.py` — exemplo RAG com PDFs.  
- `agent_financeiro_deepseek.py` — exemplo financeiro.  
- `agent_researcher_deepseek.py` — exemplo researcher.  
- `keys/` — local sugerido para chaves/JSON de serviço.  
- `pdfs/` — PDFs de exemplo.  
- `tmp/` — artefatos de execução:
  - `tmp/data.db` — SQLite para histórico.
  - `tmp/chromadb/` — armazenamento ChromaDB (recomendado).
  - `tmp/lancedb/` — (opcional / legado).

## Principais características

- Exemplos demonstrando agentes Agno com ferramentas e histórico.
- Integração com Gemini (via API key) ou Vertex AI (Google).
- Uso recomendado de ChromaDB como vetor local.
- Exemplos RAG sobre PDFs e integração com Tavily para buscas web.

## Requisitos

- Python 3.10+  
- Recomenda-se criar um ambiente virtual.

Exemplo (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
