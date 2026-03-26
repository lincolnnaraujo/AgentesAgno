import logging
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
import requests
import json
from agno.models.google import Gemini
from agno.tools.tavily import TavilyTools
from agno.agent import Agent


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

# Chave para o modelo Gemini (Modo API Key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

# Chave para busca na web (Obrigatória para a instrução do agente)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- Configuração de Autenticação ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Diretório global para o repositório clonado
REPO_LOCAL_DIR = None

if not GITHUB_TOKEN:
    print("ERRO: A variável de ambiente GITHUB_TOKEN não foi encontrada.")
    exit(1)

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

# --- Tool 1: Listar Repositórios (Leitura) ---
def get_github_repos(username: str) -> str:
    """
    Busca a lista de repositórios públicos de um usuário do GitHub.
    """
    url = f"https://api.github.com/users/{username}/repos"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            repos = response.json()
            # Retorna apenas nome e branch padrão para economizar tokens
            repo_list = [{"name": r['name'], "default_branch": r['default_branch']} for r in repos]
            return json.dumps(repo_list[:10])
        return f"Erro: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Erro de execução: {e}"


# --- Tool 2: Criar Branch (Escrita) ---
def create_github_branch(owner: str, repo: str, new_branch_name: str, base_branch: str = "main") -> str:
    """
    Cria uma nova branch em um repositório do GitHub.

    Args:
        owner (str): O dono do repositório (usuário ou organização).
        repo (str): O nome do repositório.
        new_branch_name (str): O nome da nova branch a ser criada (ex: 'feature/nova-func').
        base_branch (str): A branch de origem (padrão 'main').
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        # Passo 1: Pegar o SHA do último commit da branch base
        ref_url = f"{base_url}/git/ref/heads/{base_branch}"
        resp_sha = requests.get(ref_url, headers=HEADERS)

        if resp_sha.status_code != 200:
            return f"Erro ao buscar branch base '{base_branch}': {resp_sha.text}"

        sha_ultimo_commit = resp_sha.json()['object']['sha']

        # Passo 2: Criar a nova referência (branch)
        create_url = f"{base_url}/git/refs"
        payload = {
            "ref": f"refs/heads/{new_branch_name}",
            "sha": sha_ultimo_commit
        }

        resp_create = requests.post(create_url, headers=HEADERS, json=payload)

        if resp_create.status_code == 201:
            return f"Sucesso! Branch '{new_branch_name}' criada no repositório '{repo}' a partir de '{base_branch}'."
        else:
            return f"Erro ao criar branch: {resp_create.status_code} - {resp_create.text}"

    except Exception as e:
        return f"Exceção ocorrida: {e}"


# --- Tool 3: Clonar Repositório Localmente ---
def clone_github_repo(owner: str, repo: str, branch: str = "master") -> str:
    """
    Clona um repositório do GitHub localmente para permitir modificações.

    Args:
        owner (str): O dono do repositório.
        repo (str): O nome do repositório.
        branch (str): A branch a ser clonada (padrão 'master').
    """
    global REPO_LOCAL_DIR

    try:
        # Cria um diretório temporário
        temp_dir = tempfile.mkdtemp(prefix="github_repo_")
        REPO_LOCAL_DIR = temp_dir

        # Monta a URL com token para autenticação
        repo_url = f"https://{GITHUB_TOKEN}@github.com/{owner}/{repo}.git"

        # Clona o repositório
        result = subprocess.run(
            ["git", "clone", "-b", branch, repo_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return f"Sucesso! Repositório '{owner}/{repo}' clonado em '{temp_dir}' (branch: {branch})."
        else:
            REPO_LOCAL_DIR = None
            return f"Erro ao clonar: {result.stderr}"

    except subprocess.TimeoutExpired:
        REPO_LOCAL_DIR = None
        return "Erro: Timeout ao clonar o repositório."
    except FileNotFoundError:
        REPO_LOCAL_DIR = None
        return "Erro: Git não está instalado ou não está no PATH."
    except Exception as e:
        REPO_LOCAL_DIR = None
        return f"Exceção ocorrida: {e}"


# --- Tool 4: Listar Arquivos do Repositório Local ---
def list_repo_files(path: str = ".") -> str:
    """
    Lista os arquivos no repositório clonado localmente.

    Args:
        path (str): Caminho relativo dentro do repositório (padrão: raiz).
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Erro: Nenhum repositório foi clonado ainda. Use 'clone_github_repo' primeiro."

    try:
        full_path = Path(REPO_LOCAL_DIR) / path
        if not full_path.exists():
            return f"Erro: Caminho '{path}' não existe no repositório."

        if full_path.is_file():
            return f"'{path}' é um arquivo."

        files = []
        for item in full_path.iterdir():
            if item.name.startswith('.git'):
                continue
            tipo = "📁 DIR" if item.is_dir() else "📄 FILE"
            files.append(f"{tipo}: {item.name}")

        return f"Conteúdo de '{path}':\n" + "\n".join(files) if files else f"Diretório '{path}' está vazio."

    except Exception as e:
        return f"Erro ao listar arquivos: {e}"


# --- Tool 5: Ler Conteúdo de Arquivo ---
def read_repo_file(file_path: str) -> str:
    """
    Lê o conteúdo de um arquivo no repositório clonado.

    Args:
        file_path (str): Caminho relativo do arquivo dentro do repositório.
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Erro: Nenhum repositório foi clonado ainda. Use 'clone_github_repo' primeiro."

    try:
        full_path = Path(REPO_LOCAL_DIR) / file_path
        if not full_path.exists():
            return f"Erro: Arquivo '{file_path}' não existe."

        if not full_path.is_file():
            return f"Erro: '{file_path}' não é um arquivo."

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return f"Conteúdo de '{file_path}':\n```\n{content}\n```"

    except UnicodeDecodeError:
        return f"Erro: '{file_path}' parece ser um arquivo binário e não pode ser lido como texto."
    except Exception as e:
        return f"Erro ao ler arquivo: {e}"


# --- Tool 6: Modificar/Criar Arquivo ---
def write_repo_file(file_path: str, content: str) -> str:
    """
    Cria ou modifica um arquivo no repositório clonado.

    Args:
        file_path (str): Caminho relativo do arquivo dentro do repositório.
        content (str): Novo conteúdo do arquivo.
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Erro: Nenhum repositório foi clonado ainda. Use 'clone_github_repo' primeiro."

    try:
        full_path = Path(REPO_LOCAL_DIR) / file_path

        # Cria diretórios intermediários se necessário
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Escreve o conteúdo
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Sucesso! Arquivo '{file_path}' foi {'modificado' if full_path.exists() else 'criado'}."

    except Exception as e:
        return f"Erro ao escrever arquivo: {e}"


# --- Tool 7: Checkout para Branch ---
def checkout_branch(branch_name: str) -> str:
    """
    Faz checkout para uma branch específica no repositório local.

    Args:
        branch_name (str): Nome da branch.
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Erro: Nenhum repositório foi clonado ainda."

    try:
        result = subprocess.run(
            ["git", "checkout", branch_name],
            cwd=REPO_LOCAL_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return f"Sucesso! Agora você está na branch '{branch_name}'."
        else:
            # Tenta criar a branch se não existir
            result_create = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=REPO_LOCAL_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result_create.returncode == 0:
                return f"Sucesso! Branch '{branch_name}' criada e selecionada."
            return f"Erro ao fazer checkout: {result.stderr}"

    except Exception as e:
        return f"Exceção ocorrida: {e}"


# --- Tool 8: Commit das Mudanças ---
def commit_changes(commit_message: str) -> str:
    """
    Adiciona todos os arquivos modificados e faz commit no repositório local.

    Args:
        commit_message (str): Mensagem do commit.
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Erro: Nenhum repositório foi clonado ainda."

    try:
        # Configura usuário se necessário
        subprocess.run(
            ["git", "config", "user.email", "agent@agno.bot"],
            cwd=REPO_LOCAL_DIR,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Agno Agent"],
            cwd=REPO_LOCAL_DIR,
            capture_output=True
        )

        # Adiciona todos os arquivos
        result_add = subprocess.run(
            ["git", "add", "-A"],
            cwd=REPO_LOCAL_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result_add.returncode != 0:
            return f"Erro ao adicionar arquivos: {result_add.stderr}"

        # Faz o commit
        result_commit = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=REPO_LOCAL_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result_commit.returncode == 0:
            return f"Sucesso! Commit realizado: '{commit_message}'"
        else:
            # Verifica se não há mudanças
            if "nothing to commit" in result_commit.stdout:
                return "Nenhuma mudança para commitar."
            return f"Erro ao fazer commit: {result_commit.stderr}"

    except Exception as e:
        return f"Exceção ocorrida: {e}"


# --- Tool 9: Push para Branch Remota ---
def push_to_remote(branch_name: str) -> str:
    """
    Faz push das mudanças locais para a branch remota no GitHub.

    Args:
        branch_name (str): Nome da branch para fazer push.
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Erro: Nenhum repositório foi clonado ainda."

    try:
        result = subprocess.run(
            ["git", "push", "origin", branch_name],
            cwd=REPO_LOCAL_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return f"Sucesso! Push realizado para 'origin/{branch_name}'."
        else:
            return f"Erro ao fazer push: {result.stderr}"

    except Exception as e:
        return f"Exceção ocorrida: {e}"


# --- Tool 10: Criar Pull Request ---
def create_pull_request(owner: str, repo: str, head_branch: str, base_branch: str, title: str, body: str = "") -> str:
    """
    Cria um Pull Request no GitHub.

    Args:
        owner (str): O dono do repositório.
        repo (str): O nome do repositório.
        head_branch (str): A branch de origem (com as mudanças).
        base_branch (str): A branch de destino (ex: 'main' ou 'master').
        title (str): Título do Pull Request.
        body (str): Descrição do Pull Request (opcional).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    payload = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 201:
            pr_data = response.json()
            pr_url = pr_data.get('html_url', '')
            pr_number = pr_data.get('number', '')
            return f"Sucesso! Pull Request #{pr_number} criado: {pr_url}"
        else:
            return f"Erro ao criar PR: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Exceção ocorrida: {e}"


# --- Tool 11: Limpar Repositório Local ---
def cleanup_repo() -> str:
    """
    Remove o repositório clonado localmente (limpeza).
    """
    global REPO_LOCAL_DIR

    if not REPO_LOCAL_DIR:
        return "Nenhum repositório para limpar."

    try:
        shutil.rmtree(REPO_LOCAL_DIR)
        temp_dir = REPO_LOCAL_DIR
        REPO_LOCAL_DIR = None
        return f"Repositório local '{temp_dir}' removido com sucesso."
    except Exception as e:
        return f"Erro ao limpar repositório: {e}"


# --- Configuração do Agente ---
agent = Agent(
    model=gemini_instance,
    description="Você é um engenheiro de DevOps capaz de gerenciar repositórios GitHub com operações completas de Git.",
    instructions=[
        "Use 'get_github_repos' para listar repositórios de um usuário.",
        "Use 'clone_github_repo' para clonar um repositório localmente.",
        "Use 'list_repo_files' para ver os arquivos no repositório clonado.",
        "Use 'read_repo_file' para ler o conteúdo de um arquivo.",
        "Use 'write_repo_file' para criar ou modificar arquivos.",
        "Use 'checkout_branch' para mudar de branch ou criar uma nova.",
        "Use 'commit_changes' para commitar as mudanças.",
        "Use 'push_to_remote' para enviar as mudanças ao GitHub.",
        "Use 'create_pull_request' para criar um PR.",
        "Use 'cleanup_repo' ao final para limpar o repositório temporário.",
        "Sempre verifique se cada operação foi bem sucedida antes de prosseguir.",
        "Se o usuário não especificar a branch base, assuma que é 'master'.",
        "Siga sempre este fluxo: clone -> checkout branch -> modificar arquivos -> commit -> push -> criar PR.",
    ],
    tools=[
        get_github_repos,
        clone_github_repo,
        list_repo_files,
        read_repo_file,
        write_repo_file,
        checkout_branch,
        commit_changes,
        push_to_remote,
        create_pull_request,
        cleanup_repo
    ],
    markdown=True
)

# --- Execução ---
if __name__ == "__main__":
    # Substitua pelos seus dados reais para testar
    dono = "lincolnnaraujo"
    repositorio = "AgentesAgno"
    nova_branch = "feature/teste-agent-agno"

    print("--- Iniciando Agente GitHub Developer ---")

    # Exemplo de prompt complexo para fluxo completo
    prompt = (
        f"Execute as seguintes tarefas em ordem:\n"
        f"1. Verifique se o repositório '{repositorio}' existe para o usuário '{dono}'.\n"
        f"2. Clone o repositório a partir da branch 'master'.\n"
        f"3. Liste os arquivos na raiz do repositório.\n"
        f"4. Leia o conteúdo do arquivo 'README.md'.\n"
        f"5. Crie uma nova branch local chamada '{nova_branch}'.\n"
        f"6. Adicione uma nova linha ao final do README.md: '\\n\\n## Modificação via Agent\\nBranch criada e modificada pelo agente Agno em {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'.\n"
        f"7. Faça commit das mudanças com a mensagem 'feat: Adicionar seção de modificação via Agent'.\n"
        f"8. Faça push da branch '{nova_branch}' para o GitHub.\n"
        f"9. Crie um Pull Request da branch '{nova_branch}' para 'master' com o título 'Modificação via Agente Agno' e descrição 'PR criado automaticamente pelo agente para demonstrar capacidades de automação Git'.\n"
        f"10. Limpe o repositório local.\n"
        f"Informe-me o resultado de cada etapa."
    )

    agent.print_response(prompt)