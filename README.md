# AgentesAgno — POCs com o Framework Agno

Repositório de exemplos e proofs-of-concept demonstrando padrões de criação de agentes de IA com o **[Agno](https://github.com/agno-agi/agno)** (versão alvo: 2.2.0). Cada script é autocontido — não há entrypoint compartilhado.

---

## Sumário

- [Instalação](#instalação)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Agentes Simples (CLI)](#agentes-simples-cli)
  - [agent\_agno\_gemini.py](#agent_agno_geminipy)
  - [agent\_financeiro\_deepseek.py](#agent_financeiro_deepseekpy)
  - [agent\_researcher\_deepseek.py](#agent_researcher_deepseekpy)
- [Bots de Mensageria](#bots-de-mensageria)
  - [agent\_agno\_telegram.py](#agent_agno_telegrampy)
  - [agent\_slackblt\_agno.py](#agent_slackblt_agnopy)
- [Automação Git / DevOps](#automação-git--devops)
  - [agent\_git\_developer.py](#agent_git_developerpy)
- [RAG / Base de Conhecimento](#rag--base-de-conhecimento)
  - [agent\_rag\_pdf.py](#agent_rag_pdfpy)
- [Playground (Web UI)](#playground-web-ui)
  - [playground\_agent\_agno\_gemini.py](#playground_agent_agno_geminipy)
- [Módulos de Suporte](#módulos-de-suporte)
- [Artefatos de Execução](#artefatos-de-execução)

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/lincolnnaraujo/AgentesAgno.git
cd AgentesAgno

# Crie e ative o ambiente virtual (Python 3.10+)
python -m venv .venv

# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Instale as dependências
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz com as chaves necessárias (veja a seção abaixo).

---

## Variáveis de Ambiente

Todos os scripts carregam o `.env` via `python-dotenv`. As chaves variam por script:

| Variável | Obrigatória em |
|---|---|
| `GEMINI_API_KEY` | Todos os agentes Gemini (alternativa ao Vertex AI) |
| `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` | Gemini via Vertex AI |
| `TAVILY_API_KEY` | Agentes com busca web |
| `DEEPSEEK_API_KEY` | `agent_financeiro_deepseek.py`, `agent_researcher_deepseek.py` |
| `TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` | `agent_agno_telegram.py` |
| `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` | `agent_slackblt_agno.py` |
| `GITHUB_TOKEN` | `agent_git_developer.py` |

> Para Gemini, use **ou** `GEMINI_API_KEY` **ou** o par `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` (Vertex AI).

---

## Agentes Simples (CLI)

Scripts executados uma vez no terminal — recebem um prompt fixo, imprimem a resposta e encerram.

### `agent_agno_gemini.py`

Agente de busca web com Gemini e Tavily. Ponto de entrada ideal para entender o padrão básico do Agno.

| Atributo | Valor |
|---|---|
| Modelo | `gemini-2.5-flash` (API Key ou Vertex AI) |
| Ferramentas | `TavilyTools` (busca web) |
| Chaves necessárias | `GEMINI_API_KEY` ou Vertex AI, `TAVILY_API_KEY` |

```bash
python agent_agno_gemini.py
```

---

### `agent_financeiro_deepseek.py`

Agente financeiro usando DeepSeek e YFinance. Responde perguntas sobre cotações de ações formatando os dados em tabela.

| Atributo | Valor |
|---|---|
| Modelo | `deepseek-chat` |
| Ferramentas | `YFinanceTools` (cotações de mercado) |
| Chaves necessárias | `DEEPSEEK_API_KEY` |

```bash
python agent_financeiro_deepseek.py
```

---

### `agent_researcher_deepseek.py`

Agente de pesquisa usando DeepSeek com busca avançada via Tavily (`search_depth="advanced"`). Inclui tratamento explícito de erros de saldo/quota do provider.

| Atributo | Valor |
|---|---|
| Modelo | `deepseek-chat` |
| Ferramentas | `TavilyTools` (busca avançada, até 8000 tokens, saída Markdown) |
| Chaves necessárias | `DEEPSEEK_API_KEY`, `TAVILY_API_KEY` |

```bash
python agent_researcher_deepseek.py
```

---

## Bots de Mensageria

Processos long-running que ficam ouvindo mensagens de plataformas externas.

### `agent_agno_telegram.py`

Bot do Telegram com múltiplas ferramentas: busca web, dados financeiros, API Pokémon personalizada e envio proativo de mensagens.

| Atributo | Valor |
|---|---|
| Modelo | `gemini-2.5-flash` |
| Ferramentas | `TavilyTools`, `YFinanceTools`, `TelegramTools`, `PokemonApiTools` (custom) |
| Modo de execução | Long-running (polling) |
| Chaves necessárias | `GEMINI_API_KEY` ou Vertex AI, `TAVILY_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` |

O bot responde a qualquer mensagem de texto, escolhendo automaticamente a ferramenta adequada com base no contexto (pesquisa web, finanças ou Pokémon).

```bash
python agent_agno_telegram.py
```

---

### `agent_slackblt_agno.py`

Bot do Slack com **persona dinâmica carregada via XML**. A descrição e as instruções do agente são definidas em `personas/pm-po-persona.xml` em tempo de execução, sem alterar o código.

| Atributo | Valor |
|---|---|
| Modelo | `gemini-2.5-flash` |
| Ferramentas | `TavilyTools` (busca web) |
| Modo de execução | Long-running (Socket Mode) |
| Personas | `personas/pm-po-persona.xml`, `personas/java-developer-persona.xml` |
| Chaves necessárias | `GEMINI_API_KEY` ou Vertex AI, `TAVILY_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` |

O bot pode ser restrito a um canal específico configurado no XML. Reações (`👀` e `✅`) sinalizam o status do processamento no Slack.

```bash
python agent_slackblt_agno.py
```

---

## Automação Git / DevOps

### `agent_git_developer.py`

Agente de automação completa de repositórios GitHub. Implementa 10 ferramentas customizadas cobrindo o ciclo completo de Git.

| Atributo | Valor |
|---|---|
| Modelo | `gemini-2.5-flash` |
| Ferramentas | 10 tools customizadas (GitHub API + subprocess Git) |
| Chaves necessárias | `GEMINI_API_KEY` ou Vertex AI, `GITHUB_TOKEN`, `TAVILY_API_KEY` |

**Ferramentas disponíveis:**

| Ferramenta | Descrição |
|---|---|
| `get_github_repos` | Lista repositórios públicos de um usuário |
| `clone_github_repo` | Clona um repositório em diretório temporário |
| `list_repo_files` | Lista arquivos no repositório clonado |
| `read_repo_file` | Lê conteúdo de um arquivo |
| `write_repo_file` | Cria ou modifica um arquivo |
| `checkout_branch` | Faz checkout ou cria uma branch local |
| `commit_changes` | Adiciona todos os arquivos e faz commit |
| `push_to_remote` | Envia mudanças para o GitHub |
| `create_pull_request` | Cria um Pull Request via API GitHub |
| `cleanup_repo` | Remove o repositório temporário local |

**Fluxo demonstrado no script:** lista repos → clona → lista arquivos → lê README → cria branch → modifica arquivo → commit → push → abre PR → cleanup.

```bash
python agent_git_developer.py
```

---

## RAG / Base de Conhecimento

### `agent_rag_pdf.py`

Agente RAG (Retrieval-Augmented Generation) sobre PDFs locais usando **ChromaDB** como vector store persistente. Sobe uma interface web via `AgentOS`.

| Atributo | Valor |
|---|---|
| Modelo | `gemini-2.5-flash` |
| Knowledge | `agno.knowledge.Knowledge` + `ChromaDb` (persistente em `tmp/chromadb/`) |
| PDF indexado | `pdfs/ebook-guitarras.pdf` |
| Interface | Web UI (uvicorn via `AgentOS.serve()`) |
| Chaves necessárias | `GEMINI_API_KEY` ou Vertex AI |

O PDF é vetorizado e armazenado em `tmp/chromadb/`. Na segunda execução, o ChromaDB reutiliza os dados persistidos sem re-indexar.

```bash
python agent_rag_pdf.py
# Acesse: http://localhost:7777
```

---

## Playground (Web UI)

### `playground_agent_agno_gemini.py`

Interface web interativa com **histórico de conversas persistido em SQLite**. Ideal para experimentação sem precisar editar código.

| Atributo | Valor |
|---|---|
| Modelo | `gemini-2.5-flash` |
| Ferramentas | `TavilyTools` (busca web) |
| Histórico | `SqliteDb` (arquivo `tmp/data.db`, últimas 3 interações no contexto) |
| Interface | Web UI (uvicorn via `AgentOS.serve()`, com hot-reload) |
| Chaves necessárias | `GEMINI_API_KEY` ou Vertex AI, `TAVILY_API_KEY` |

```bash
python playground_agent_agno_gemini.py
# Acesse: http://localhost:7777
```

---

## Módulos de Suporte

### `customTools/PokemonApiTools.py`

Toolkit customizado que estende `agno.tools.Toolkit`. Consulta a PokéAPI para dados de Pokémon. Serve como referência para criar ferramentas customizadas no Agno.

### `functions/SanitizarStringContent.py`

Utilitário de sanitização de strings para log — usado pelo bot do Telegram para limpar conteúdo antes de registrar.

### `personas/`

Arquivos XML que definem `description` e `instructions` de agentes em runtime. Utilizados por `agent_slackblt_agno.py`:

- `pm-po-persona.xml` — persona de Product Manager / Product Owner
- `java-developer-persona.xml` — persona de desenvolvedor Java

---

## Artefatos de Execução

O diretório `tmp/` é ignorado pelo Git e armazena dados efêmeros:

| Caminho | Gerado por | Conteúdo |
|---|---|---|
| `tmp/data.db` | `playground_agent_agno_gemini.py` | Histórico de conversas (SQLite) |
| `tmp/chromadb/` | `agent_rag_pdf.py` | Vetores dos PDFs indexados (ChromaDB) |
