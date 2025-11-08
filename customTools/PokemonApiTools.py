from agno.tools import Toolkit
from agno.utils.log import log_debug
from typing import Any, List

import requests
import json
from pprint import pprint  # Para imprimir o JSON de forma mais legível


def get_pokemon_data(pokemon_id_str: str) -> dict[str, str | int] | dict[str, str] | Any:
    """
    Busca dados de um Pokémon na PokeAPI usando um ID em formato string.

    Argumentos:
        pokemon_id_str (str): O ID do Pokémon (ex: "25").

    Retorna:
        dict: O JSON completo da resposta da API ou um dicionário de erro.
    """

    # 1. Tenta converter a string de entrada para um número inteiro
    try:
        pokemon_id = int(pokemon_id_str)
    except ValueError:
        print(f"Erro: O ID '{pokemon_id_str}' não é um número inteiro válido.")
        return {"error": f"ID inválido: '{pokemon_id_str}' não é um inteiro."}

    # 2. Constrói a URL final usando uma f-string
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/"

    print(f"Buscando dados em: {url}")

    # 3. Realiza a requisição GET e trata possíveis erros
    try:
        response = requests.get(url)

        # 4. Verifica se a requisição foi bem-sucedida (status 200)
        # Se for um erro (404, 500, etc.), levanta uma exceção HTTPError
        response.raise_for_status()

        # 5. Retorna o conteúdo da resposta já convertido de JSON para dict
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        # Erro específico se o Pokémon não for encontrado (404)
        print(f"Erro HTTP: {http_err}")
        return {"error": f"Pokemon com ID {pokemon_id} não encontrado.", "status_code": response.status_code}
    except requests.exceptions.RequestException as err:
        # Erro geral de rede (ex: sem conexão, DNS falhou)
        print(f"Erro na requisição: {err}")
        return {"error": f"Erro de conexão: {err}"}


class PokemonApiTools(Toolkit):
    def __init__(
        self,
        **kwargs,
    ):
        tools: List[Any] = [
            get_pokemon_data
        ]

        super().__init__(name="pokemonapi_tools", tools=tools, **kwargs)

# --- Exemplo de Uso ---

# # 1. Teste com o ID "35" (Clefairy), como no seu exemplo
# print("--- Testando com ID '35' (Clefairy) ---")
# clefairy_data = get_pokemon_data("35")
#
# # Se não houver erro, imprime o JSON formatado
# if "error" not in clefairy_data:
#     pprint(clefairy_data)
#     # Se quiser ver apenas o nome:
#     # print(f"\nNome do Pokémon: {clefairy_data.get('name')}")
#
# print("\n" + "=" * 40 + "\n")
#
# # 2. Teste com um ID inválido (não numérico)
# print("--- Testando com ID 'pikachu' ---")
# invalid_data = get_pokemon_data("pikachu")
# pprint(invalid_data)
#
# print("\n" + "=" * 40 + "\n")
#
# # 3. Teste com um ID que não existe (retornará 404)
# print("--- Testando com ID '99999' ---")
# not_found_data = get_pokemon_data("99999")
# pprint(not_found_data)