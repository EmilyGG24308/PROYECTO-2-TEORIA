"""Lectura de gramaticas desde archivos de texto.
"""

from .gramatica import Gramatica, ErrorGramatica

FLECHAS = ("->", "→")
MARCAS_EPSILON = {"e", "ε"}


def leer_archivo(ruta, inicial=None):
    """Lee la gramatica de `ruta`. Lanza ErrorGramatica u OSError."""
    with open(ruta, encoding="utf-8-sig") as archivo:
        return leer_texto(archivo.read(), inicial)


def leer_texto(texto, inicial=None):
    """Convierte el texto de una gramatica en un objeto Gramatica.

    Devuelve la gramatica; las producciones duplicadas que se descartaron
    quedan descritas en el atributo `advertencias` del resultado.
    """
    reglas = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        contenido = linea.strip()
        if contenido and not contenido.startswith("#"):
            reglas.append(_analizar_linea(contenido, numero))

    if not reglas:
        raise ErrorGramatica("El archivo no contiene ninguna produccion.")

    # Paso 1: los no terminales son exactamente los lados izquierdos.
    orden_no_terminales = []
    for _, cabeza, _ in reglas:
        if cabeza not in orden_no_terminales:
            orden_no_terminales.append(cabeza)

    if inicial is None:
        inicial = orden_no_terminales[0]
    elif inicial not in orden_no_terminales:
        raise ErrorGramatica(
            f"El simbolo inicial '{inicial}' no es lado izquierdo de ninguna produccion. "
            f"No terminales disponibles: {', '.join(orden_no_terminales)}"
        )

    # Paso 2: construir las producciones (la clasificacion terminal/no terminal
    # queda implicita: Gramatica considera no terminales a las claves).
    gramatica = Gramatica(inicial, {nt: [] for nt in orden_no_terminales})
    advertencias = []
    for numero, cabeza, alternativas in reglas:
        for simbolos in alternativas:
            cuerpo = _cuerpo(simbolos, numero)
            if not gramatica.agregar(cabeza, cuerpo):
                texto_cuerpo = " ".join(cuerpo) if cuerpo else "ε"
                advertencias.append(
                    f"Linea {numero}: produccion duplicada {cabeza} -> {texto_cuerpo} (se ignora)."
                )
    gramatica.advertencias = advertencias
    return gramatica


def _analizar_linea(contenido, numero):
    """Devuelve (numero, cabeza, [lista de alternativas como listas de simbolos])."""
    flechas = sum(contenido.count(f) for f in FLECHAS)
    if flechas != 1:
        raise ErrorGramatica(
            f"Linea {numero}: se esperaba exactamente una flecha '->' y hay {flechas}: {contenido!r}"
        )
    flecha = next(f for f in FLECHAS if f in contenido)
    izquierda, derecha = contenido.split(flecha)

    partes_izquierda = izquierda.split()
    if len(partes_izquierda) != 1:
        raise ErrorGramatica(
            f"Linea {numero}: el lado izquierdo debe ser un unico simbolo: {izquierda.strip()!r}"
        )
    cabeza = partes_izquierda[0]
    if cabeza in MARCAS_EPSILON or cabeza == "|":
        raise ErrorGramatica(f"Linea {numero}: '{cabeza}' no puede usarse como lado izquierdo.")

    alternativas = []
    for alternativa in derecha.split("|"):
        simbolos = alternativa.split()
        if not simbolos:
            raise ErrorGramatica(
                f"Linea {numero}: alternativa vacia en {contenido!r} (use 'e' o 'ε' para epsilon)."
            )
        alternativas.append(simbolos)
    return numero, cabeza, alternativas


def _cuerpo(simbolos, numero):
    if any(s in MARCAS_EPSILON for s in simbolos):
        if len(simbolos) != 1:
            raise ErrorGramatica(
                f"Linea {numero}: epsilon ('e' o 'ε') debe aparecer sola en su alternativa: "
                f"{' '.join(simbolos)!r}"
            )
        return ()
    return tuple(simbolos)
