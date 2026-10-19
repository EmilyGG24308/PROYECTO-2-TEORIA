"""Conversion de gramaticas, tablas y arboles a texto.

Estas funciones solo DEVUELVEN cadenas; quien decide imprimirlas es la
clase Principal (main.py).
"""

from .gramatica import EPSILON


def formatear_gramatica(gramatica):
    if gramatica.cantidad() == 0:
        return f"(sin producciones: el lenguaje de {gramatica.inicial} es vacio)"
    orden = [gramatica.inicial] + [nt for nt in gramatica.producciones if nt != gramatica.inicial]
    ancho = max(len(nt) for nt in orden)
    lineas = []
    for nt in orden:
        cuerpos = gramatica.producciones[nt]
        if cuerpos:
            alternativas = " | ".join(" ".join(c) if c else EPSILON for c in cuerpos)
            lineas.append(f"{nt.ljust(ancho)} -> {alternativas}")
    return "\n".join(lineas)


def formatear_tabla(resultado):
    """Tabla triangular CYK: la fila superior es la celda de toda la entrada
    y la inferior corresponde a cada token. Celda (l, i): subcadena de
    longitud l que empieza en el token i (ambos desde 1)."""
    tokens = resultado.tokens
    n = len(tokens)
    if n == 0:
        return "(entrada vacia: no hay tabla)"

    def texto_celda(celda):
        return ",".join(celda) if celda else "∅"

    filas = [[texto_celda(c) for c in resultado.tabla[largo - 1]] for largo in range(n, 0, -1)]
    ancho = max([len(t) for t in tokens] + [len(c) for fila in filas for c in fila] + [3])
    etiqueta = len(f"l={n}") + 1

    lineas = []
    encabezado = " " * etiqueta + " ".join(f"i={i + 1}".center(ancho) for i in range(n))
    lineas.append(encabezado)
    separador = " " * etiqueta + "-" * (n * (ancho + 1) - 1)
    lineas.append(separador)
    for indice, fila in enumerate(filas):
        largo = n - indice
        lineas.append(f"l={largo}".ljust(etiqueta) + " ".join(c.center(ancho) for c in fila))
    lineas.append(separador)
    lineas.append("tok".ljust(etiqueta) + " ".join(t.center(ancho) for t in tokens))
    return "\n".join(lineas)


def formatear_arbol(nodo):
    """Arbol con ramas tipo ├── / └──."""
    lineas = [nodo.simbolo]
    _ramas(nodo, "", lineas)
    return "\n".join(lineas)


def _ramas(nodo, prefijo, lineas):
    for indice, hijo in enumerate(nodo.hijos):
        ultimo = indice == len(nodo.hijos) - 1
        lineas.append(prefijo + ("└── " if ultimo else "├── ") + hijo.simbolo)
        _ramas(hijo, prefijo + ("    " if ultimo else "│   "), lineas)


def formatear_corchetes(nodo):
    """Arbol en una linea: [S [NP she] [VP ...]]."""
    if not nodo.hijos:
        return nodo.simbolo
    return "[" + nodo.simbolo + " " + " ".join(formatear_corchetes(h) for h in nodo.hijos) + "]"
