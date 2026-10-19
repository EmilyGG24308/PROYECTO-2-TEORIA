"""Division de la cadena de entrada en tokens (terminales).

Modos:
* "palabras": para frases en ingles. Se pasa todo a minusculas y se separa
  por palabras (secuencias de letras, digitos o _). Cualquier otro caracter
  que no sea espacio (por ejemplo "." o ",") se convierte en un token propio:
  NO se elimina en silencio, asi CYK lo rechaza y explica que es desconocido.
* "simbolos": para expresiones como (id*id)+id. No se cambian mayusculas.
  Las secuencias de letras/digitos/_ forman un token ("id", "idx"); el resto
  se corta con "coincidencia mas larga" contra los terminales de la gramatica
  que no son palabras ("(", "+", ...); un caracter que no coincide con
  ninguno queda como token propio de un caracter. Los espacios solo separan.
* "auto": elige "palabras" si todos los terminales de la gramatica estan
  formados solo por letras, y "simbolos" en caso contrario.
"""

import re

MODO_AUTO = "auto"
MODO_PALABRAS = "palabras"
MODO_SIMBOLOS = "simbolos"
MODOS = (MODO_AUTO, MODO_PALABRAS, MODO_SIMBOLOS)

_PALABRA = re.compile(r"\w+")


def resolver_modo(modo, terminales):
    if modo not in MODOS:
        raise ValueError(f"Modo de tokenizacion desconocido: {modo}")
    if modo != MODO_AUTO:
        return modo
    if terminales and all(t.isalpha() for t in terminales):
        return MODO_PALABRAS
    return MODO_SIMBOLOS


def tokenizar(texto, modo, terminales):
    """Devuelve la lista de tokens de `texto` segun el modo (ya resuelto o 'auto')."""
    modo = resolver_modo(modo, terminales)
    if modo == MODO_PALABRAS:
        return re.findall(r"\w+|[^\w\s]", texto.lower())
    return _tokenizar_simbolos(texto, terminales)


def _tokenizar_simbolos(texto, terminales):
    no_palabras = sorted((t for t in terminales if not _PALABRA.fullmatch(t)), key=len, reverse=True)
    tokens = []
    i = 0
    while i < len(texto):
        if texto[i].isspace():
            i += 1
            continue
        palabra = _PALABRA.match(texto, i)
        if palabra:
            tokens.append(palabra.group())
            i = palabra.end()
            continue
        coincidencia = next((t for t in no_palabras if texto.startswith(t, i)), texto[i])
        tokens.append(coincidencia)
        i += len(coincidencia)
    return tokens
