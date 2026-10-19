"""Simplificacion de gramaticas y conversion a Forma Normal de Chomsky (CNF).


Orden de las transformaciones (cada una conserva el lenguaje):
  1. Simbolo inicial nuevo  (solo si S es anulable y aparece en un lado derecho)
  2. Eliminacion de producciones epsilon
  3. Eliminacion de producciones unitarias
  4. Eliminacion de simbolos inutiles (primero no generadores, luego inalcanzables)
  5. Sustitucion de terminales en lados derechos de longitud >= 2
  6. Binarizacion de lados derechos de longitud >= 3
  7. Validacion final

Por que en este orden: eliminar epsilon puede crear producciones unitarias
(A -> B C con C anulable produce A -> B), por eso 2 va antes que 3. Eliminar
epsilon y unitarias puede dejar simbolos inutiles, por eso 4 va despues. En
4 hay que calcular generadores ANTES que alcanzables: al reves podria quedar
un simbolo inalcanzable. Los pasos 5 y 6 solo cambian la forma de las
producciones ya limpias y no crean simbolos inutiles, epsilon ni unitarias.
"""

from dataclasses import dataclass, field

from .gramatica import Gramatica, ErrorGramatica

# Nombres legibles para los auxiliares de terminales que no son palabras.
NOMBRES_TERMINALES = {
    "+": "MAS", "-": "MENOS", "*": "POR", "/": "DIV", "(": "PAR_IZQ", ")": "PAR_DER",
    "[": "COR_IZQ", "]": "COR_DER", "{": "LLAVE_IZQ", "}": "LLAVE_DER", ",": "COMA",
    ";": "PUNTO_COMA", ".": "PUNTO", "=": "IGUAL", "<": "MENOR", ">": "MAYOR",
}


@dataclass
class Etapa:
    nombre: str
    descripcion: str
    gramatica: Gramatica
    cambio: bool
    detalles: list = field(default_factory=list)


@dataclass
class ResultadoCNF:
    original: Gramatica
    final: Gramatica
    etapas: list
    ya_estaba_en_cnf: bool


class GeneradorNombres:
    """Crea nombres de auxiliares que no chocan con ningun simbolo existente."""

    def __init__(self, gramatica):
        self.usados = gramatica.no_terminales | gramatica.terminales

    def nuevo(self, base):
        nombre = base
        sufijo = 2
        while nombre in self.usados:
            nombre = f"{base}_{sufijo}"
            sufijo += 1
        self.usados.add(nombre)
        return nombre


# Verificacion de CNF


def problemas_cnf(gramatica):
    """Lista de motivos por los que la gramatica NO esta en CNF (vacia si lo esta)."""
    problemas = []
    no_terminales = gramatica.no_terminales
    inicial_en_derecha = any(gramatica.inicial in c for _, c in gramatica.todas())
    for cabeza, cuerpo in gramatica.todas():
        texto = f"{cabeza} -> {' '.join(cuerpo) if cuerpo else 'ε'}"
        if len(cuerpo) == 0:
            if cabeza != gramatica.inicial:
                problemas.append(f"{texto}: epsilon solo se permite en el simbolo inicial")
            elif inicial_en_derecha:
                problemas.append(
                    f"{texto}: se usa S -> ε pero el inicial aparece en un lado derecho"
                )
        elif len(cuerpo) == 1:
            if cuerpo[0] in no_terminales:
                problemas.append(f"{texto}: produccion unitaria")
        elif len(cuerpo) == 2:
            if any(s not in no_terminales for s in cuerpo):
                problemas.append(f"{texto}: un lado derecho de longitud 2 contiene terminales")
        else:
            problemas.append(f"{texto}: lado derecho de longitud {len(cuerpo)} (> 2)")
    return problemas


def es_cnf(gramatica):
    return not problemas_cnf(gramatica)


# Conjuntos auxiliares (puntos fijos)

def anulables(gramatica):
    """No terminales A tales que A =>* ε. Se itera hasta un punto fijo:
    A es anulable si tiene una produccion cuyos simbolos son todos anulables
    (la produccion vacia cumple esto trivialmente)."""
    resultado = set()
    hubo_cambio = True
    while hubo_cambio:
        hubo_cambio = False
        for cabeza, cuerpo in gramatica.todas():
            if cabeza not in resultado and all(s in resultado for s in cuerpo):
                resultado.add(cabeza)
                hubo_cambio = True
    return resultado


def generadores(gramatica):
    """No terminales que derivan alguna cadena de terminales (punto fijo)."""
    resultado = set()
    hubo_cambio = True
    while hubo_cambio:
        hubo_cambio = False
        for cabeza, cuerpo in gramatica.todas():
            if cabeza not in resultado and all(
                gramatica.es_terminal(s) or s in resultado for s in cuerpo
            ):
                resultado.add(cabeza)
                hubo_cambio = True
    return resultado


def alcanzables(gramatica):
    """No terminales alcanzables desde el simbolo inicial (recorrido en anchura)."""
    visitados = {gramatica.inicial}
    pendientes = [gramatica.inicial]
    while pendientes:
        actual = pendientes.pop()
        for cuerpo in gramatica.producciones.get(actual, []):
            for simbolo in cuerpo:
                if not gramatica.es_terminal(simbolo) and simbolo not in visitados:
                    visitados.add(simbolo)
                    pendientes.append(simbolo)
    return visitados


def cierre_unitario(gramatica):
    """Para cada A, el conjunto de B tales que A =>* B usando solo producciones
    unitarias (incluye A mismo). Los ciclos A -> B -> A no causan problemas
    porque cada no terminal se visita una sola vez."""
    cierre = {}
    for a in gramatica.producciones:
        visitados = {a}
        pendientes = [a]
        while pendientes:
            actual = pendientes.pop()
            for cuerpo in gramatica.producciones[actual]:
                if _es_unitaria(gramatica, cuerpo) and cuerpo[0] not in visitados:
                    visitados.add(cuerpo[0])
                    pendientes.append(cuerpo[0])
        cierre[a] = visitados
    return cierre


def _es_unitaria(gramatica, cuerpo):
    return len(cuerpo) == 1 and not gramatica.es_terminal(cuerpo[0])


def _texto(cabeza, cuerpo):
    return f"{cabeza} -> {' '.join(cuerpo) if cuerpo else 'ε'}"


# ---------------------------------------------------------------------------
# Etapas de la conversion
# ---------------------------------------------------------------------------

def _paso_inicial(g, nombres):
    nul = anulables(g)
    en_derecha = any(g.inicial in cuerpo for _, cuerpo in g.todas())
    if g.inicial in nul and en_derecha:
        nuevo = nombres.nuevo(g.inicial + "0")
        producciones = {nuevo: [(g.inicial,)]}
        producciones.update(g.producciones)
        return Gramatica(nuevo, producciones), [
            f"{g.inicial} es anulable y aparece en un lado derecho: "
            f"se agrega {nuevo} -> {g.inicial} y {nuevo} pasa a ser el inicial."
        ]
    motivo = "no es anulable" if g.inicial not in nul else "no aparece en ningun lado derecho"
    return g.copiar(), [f"No hace falta un inicial nuevo: {g.inicial} {motivo}."]


def _paso_epsilon(g):
    nul = anulables(g)
    if not nul:
        return g.copiar(), ["No hay no terminales anulables."]
    nueva = Gramatica(g.inicial, {nt: [] for nt in g.producciones})
    for cabeza, cuerpo in g.todas():
        posiciones = [i for i, s in enumerate(cuerpo) if s in nul]
        # Cada mascara de bits decide que ocurrencias anulables se omiten:
        # con m anulables hay 2^m combinaciones.
        for mascara in range(2 ** len(posiciones)):
            omitidas = {posiciones[j] for j in range(len(posiciones)) if mascara >> j & 1}
            combinacion = tuple(s for i, s in enumerate(cuerpo) if i not in omitidas)
            if combinacion:
                nueva.agregar(cabeza, combinacion)
    detalles = [f"Anulables: {{{', '.join(sorted(nul))}}}"]
    if g.inicial in nul:
        nueva.agregar(g.inicial, ())
        detalles.append(f"La cadena vacia pertenece al lenguaje: se conserva {g.inicial} -> ε.")
    else:
        detalles.append("La cadena vacia no pertenece al lenguaje.")
    return nueva, detalles


def _paso_unitarias(g):
    cierre = cierre_unitario(g)
    nueva = Gramatica(g.inicial, {nt: [] for nt in g.producciones})
    pares = []
    for a in g.producciones:
        for b in sorted(cierre[a] - {a}):
            pares.append(f"({a}, {b})")
        for b in [a] + sorted(cierre[a] - {a}):
            for cuerpo in g.producciones[b]:
                if not _es_unitaria(g, cuerpo):
                    nueva.agregar(a, cuerpo)
    if not pares:
        return nueva, ["No hay producciones unitarias."]
    return nueva, ["Pares unitarios (A, B) con A =>* B: " + ", ".join(pares)]


def _paso_inutiles(g):
    gen = generadores(g)
    no_generadores = [nt for nt in g.producciones if nt not in gen]
    if g.inicial not in gen:
        return Gramatica(g.inicial, {}), [
            f"El inicial {g.inicial} no genera ninguna cadena: el lenguaje es vacio."
        ]
    filtrada = Gramatica(g.inicial, {nt: [] for nt in g.producciones if nt in gen})
    for cabeza, cuerpo in g.todas():
        if cabeza in gen and all(g.es_terminal(s) or s in gen for s in cuerpo):
            filtrada.agregar(cabeza, cuerpo)

    alc = alcanzables(filtrada)
    inalcanzables = [nt for nt in filtrada.producciones if nt not in alc]
    nueva = Gramatica(g.inicial, {nt: filtrada.producciones[nt] for nt in filtrada.producciones if nt in alc})

    detalles = [
        "No generadores: " + (", ".join(no_generadores) if no_generadores else "ninguno"),
        "Inalcanzables (calculados despues): " + (", ".join(inalcanzables) if inalcanzables else "ninguno"),
    ]
    return nueva, detalles


def _paso_terminales(g, nombres):
    auxiliar_de = {}
    nueva = Gramatica(g.inicial, {nt: [] for nt in g.producciones})
    for cabeza, cuerpo in g.todas():
        if len(cuerpo) >= 2:
            cuerpo = tuple(
                _auxiliar_terminal(s, auxiliar_de, nombres) if g.es_terminal(s) else s
                for s in cuerpo
            )
        nueva.agregar(cabeza, cuerpo)
    for terminal, auxiliar in auxiliar_de.items():
        nueva.agregar(auxiliar, (terminal,))
    if not auxiliar_de:
        return nueva, ["Ningun lado derecho de longitud >= 2 contiene terminales."]
    return nueva, ["Auxiliares (reutilizados en todas las producciones): "
                   + ", ".join(f"{a} -> {t}" for t, a in auxiliar_de.items())]


def _auxiliar_terminal(terminal, auxiliar_de, nombres):
    if terminal not in auxiliar_de:
        base = NOMBRES_TERMINALES.get(terminal)
        if base is None:
            base = terminal.upper() if terminal.isidentifier() else "SIMBOLO"
        auxiliar_de[terminal] = nombres.nuevo("TERM_" + base)
    return auxiliar_de[terminal]


def _paso_binarizar(g, nombres):
    auxiliar_de = {}
    nueva = Gramatica(g.inicial, {nt: [] for nt in g.producciones})
    for cabeza, cuerpo in g.todas():
        if len(cuerpo) <= 2:
            nueva.agregar(cabeza, cuerpo)
        else:
            nueva.agregar(cabeza, (cuerpo[0], _auxiliar_cola(cuerpo[1:], auxiliar_de, nombres)))
    for cola, auxiliar in auxiliar_de.items():
        if len(cola) == 2:
            nueva.agregar(auxiliar, cola)
        else:
            nueva.agregar(auxiliar, (cola[0], auxiliar_de[cola[1:]]))
    if not auxiliar_de:
        return nueva, ["No hay lados derechos de longitud >= 3."]
    return nueva, ["Auxiliares de binarizacion: "
                   + ", ".join(f"{a} =>* {' '.join(c)}" for c, a in auxiliar_de.items())]


def _auxiliar_cola(cola, auxiliar_de, nombres):
    """Auxiliar que deriva exactamente la secuencia `cola` (longitud >= 2).
    Colas iguales comparten el mismo auxiliar, lo que conserva el lenguaje."""
    if cola not in auxiliar_de:
        if len(cola) > 2:
            _auxiliar_cola(cola[1:], auxiliar_de, nombres)
        auxiliar_de[cola] = nombres.nuevo(f"BIN{len(auxiliar_de) + 1}")
    return auxiliar_de[cola]


# Conversion completa

def convertir_a_cnf(gramatica, forzar=False):
    """Convierte la gramatica a CNF mostrando cada etapa.

    Si ya esta en CNF y forzar es False, no se transforma (se usa tal cual).
    Lanza ErrorGramatica si el resultado no cumpliera CNF (error interno).
    """
    if es_cnf(gramatica) and not forzar:
        return ResultadoCNF(gramatica, gramatica.copiar(), [], True)

    nombres = GeneradorNombres(gramatica)
    etapas = []
    actual = gramatica

    pasos = [
        ("1. Simbolo inicial", "Nuevo inicial si S es anulable y aparece a la derecha.",
         lambda g: _paso_inicial(g, nombres)),
        ("2. Eliminar producciones epsilon", "Anulables por punto fijo y combinaciones.",
         _paso_epsilon),
        ("3. Eliminar producciones unitarias", "Cierre transitivo de A -> B.",
         _paso_unitarias),
        ("4. Eliminar simbolos inutiles", "Primero no generadores, despues inalcanzables.",
         _paso_inutiles),
        ("5. Sustituir terminales", "Terminales en lados derechos de longitud >= 2.",
         lambda g: _paso_terminales(g, nombres)),
        ("6. Binarizar", "Lados derechos de longitud >= 3 en cadenas de binarias.",
         lambda g: _paso_binarizar(g, nombres)),
    ]
    for nombre, descripcion, paso in pasos:
        siguiente, detalles = paso(actual)
        etapas.append(Etapa(nombre, descripcion, siguiente, siguiente != actual, detalles))
        actual = siguiente

    problemas = problemas_cnf(actual)
    if problemas:
        raise ErrorGramatica("La conversion no produjo CNF: " + "; ".join(problemas))
    etapas.append(Etapa(
        "7. Validacion final", "Solo A -> B C, A -> a y, si aplica, inicial -> ε.",
        actual, False,
        [f"Cumple CNF: {actual.cantidad()} producciones, {len(actual.no_terminales)} no terminales."],
    ))
    return ResultadoCNF(gramatica, actual, etapas, False)
