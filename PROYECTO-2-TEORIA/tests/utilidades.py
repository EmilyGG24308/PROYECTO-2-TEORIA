"""Herramientas para las pruebas.

`reconoce_earley` es un reconocedor INDEPENDIENTE de CYK (algoritmo de Earley
con la correccion de Aycock y Horspool para producciones epsilon). Trabaja
sobre la gramatica ORIGINAL, sin convertirla, y sirve como oraculo: si la
gramatica CNF y la original aceptan exactamente las mismas cadenas hasta
cierta longitud, tenemos evidencia (no una demostracion) de que la conversion
conservo el lenguaje.
"""

from itertools import product

from nucleo.cnf import convertir_a_cnf
from nucleo.cyk import AnalizadorCYK

INICIO_AUMENTADO = "<<inicio>>"


def reconoce_earley(gramatica, tokens):
    tokens = list(tokens)
    n = len(tokens)
    nul = _anulables(gramatica)
    conjuntos = [set() for _ in range(n + 1)]
    conjuntos[0].add((INICIO_AUMENTADO, (gramatica.inicial,), 0, 0))
    for i in range(n + 1):
        agenda = list(conjuntos[i])
        while agenda:
            cabeza, cuerpo, punto, origen = agenda.pop()
            nuevos = []
            if punto < len(cuerpo):
                simbolo = cuerpo[punto]
                if simbolo in gramatica.producciones:            # prediccion
                    nuevos += [((simbolo, c, 0, i), i) for c in gramatica.producciones[simbolo]]
                    if simbolo in nul:
                        nuevos.append(((cabeza, cuerpo, punto + 1, origen), i))
                elif i < n and tokens[i] == simbolo:             # lectura
                    nuevos.append(((cabeza, cuerpo, punto + 1, origen), i + 1))
            else:                                                # complecion
                for b, d, q, o in list(conjuntos[origen]):
                    if q < len(d) and d[q] == cabeza:
                        nuevos.append(((b, d, q + 1, o), i))
            for item, destino in nuevos:
                if item not in conjuntos[destino]:
                    conjuntos[destino].add(item)
                    if destino == i:
                        agenda.append(item)
    return (INICIO_AUMENTADO, (gramatica.inicial,), 1, 0) in conjuntos[n]


def _anulables(gramatica):
    nul = set()
    tamano = -1
    while tamano != len(nul):
        tamano = len(nul)
        nul |= {a for a, c in gramatica.todas() if all(s in nul for s in c)}
    return nul


def cadenas_hasta(alfabeto, longitud_maxima):
    for largo in range(longitud_maxima + 1):
        yield from product(sorted(alfabeto), repeat=largo)


def diferencias_de_lenguaje(original, alfabeto, longitud_maxima, cnf=None):
    """Cadenas (hasta la longitud dada) en las que la gramatica CNF y el
    oraculo sobre la original no coinciden. Lista vacia = coinciden."""
    cnf = cnf or convertir_a_cnf(original, forzar=True).final
    analizador = AnalizadorCYK(cnf)
    return [
        cadena for cadena in cadenas_hasta(alfabeto, longitud_maxima)
        if analizador.analizar(cadena).aceptada != reconoce_earley(original, cadena)
    ]


def arbol_valido(nodo, gramatica):
    """True si cada nodo interno usa una produccion existente de la gramatica."""
    if not nodo.hijos:
        return True
    cuerpo = tuple(h.simbolo for h in nodo.hijos)
    if cuerpo == ("ε",):
        cuerpo = ()
    if cuerpo not in gramatica.producciones.get(nodo.simbolo, []):
        return False
    return all(arbol_valido(h, gramatica) for h in nodo.hijos if h.hijos)
