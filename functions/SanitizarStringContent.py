import re
import string


def sanitizar_string_para_log(texto: str) -> str:
    """
        Limpa e escapa uma string para ser segura em sistemas de log.

        1. Remove caracteres não imprimíveis (ex: \x00).
        2. PRESERVA whitespace (espaços, \n, \t).
        3. Escapa SOMENTE caracteres reservados ((), :, *, \) para evitar erros de parse.
        """

    # Etapa 1: Remover não-imprimíveis. (Sem alteração)
    caracteres_validos = set(string.printable)
    texto_limpo = ''.join(filter(lambda char: char in caracteres_validos, texto))

    # Etapa 2: Escapar seletivamente '(', ')', ':', '*' e '\'
    #
    # --- ÚNICA LINHA MODIFICADA ---
    # Adicionamos '*' e '\' (escrito como '\\') à classe de caracteres.
    # O '*' dentro de [] é literal.
    # O '\\' dentro de [] significa um '\' literal.
    padrao_reservado = r'([():*\\])'
    # -------------------------------
    #
    # A substituição (r'\\\1') continua a mesma.
    # Ela pega o caractere encontrado (\1) e coloca uma barra (\) antes dele.
    texto_seguro = re.sub(padrao_reservado, r'\\\1', texto_limpo)

    return texto_seguro

# # --- Teste ---
# string_suja = "Erro \x07grave\x00 na query:(funcao_xpto(123))"
#
# print(f"ORIGINAL: {repr(string_suja)}")
# print(f"SEGURA:   {sanitizar_string_para_log(string_suja)}")