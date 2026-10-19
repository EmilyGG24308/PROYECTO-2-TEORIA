"""Algoritmo CYK (Cocke-Younger-Kasami) con programacion dinamica.
"""

from dataclasses import dataclass, field
from time import perf_counter

from .cnf import es_cnf, problemas_cnf
from .gramatica import ErrorGramatica, EPSILON


@dataclass(frozen=True)
class Referencia:
    produccion: tuple
    division: int | None


@dataclass
class Nodo:
    simbolo: str
    hijos: list = field(default_factory=list)

    def hojas(self):
        """Tokens en las hojas, de izquierda a derecha (ε no cuenta)."""
        if not self.hijos:
            return [] if self.simbolo == EPSILON else [self.simbolo]
        return [token for hijo in self.hijos for token in hijo.hojas()]


@dataclass
class ResultadoCYK:
    tokens: list
    aceptada: bool
    tabla: list
    tiempo_cyk: float           # segundos: llenado de la tabla + decision
    arbol: Nodo | None
    tiempo_arbol: float         # segundos: reconstruccion del arbol (aparte)
    desconocidos: list
    motivo: str


class AnalizadorCYK:
    def __init__(self, gramatica):
        if not es_cnf(gramatica):
            raise ErrorGramatica("CYK requiere una gramatica en CNF: " + "; ".join(problemas_cnf(gramatica)))
        self.gramatica = gramatica
        # Indices construidos una sola vez (fuera de la medicion de tiempo):
        #   por_terminal[a]      = [A, ...] con A -> a
        #   por_par[(B, C)]      = [A, ...] con A -> B C
        self.por_terminal = {}
        self.por_par = {}
        for cabeza, cuerpo in gramatica.todas():
            if len(cuerpo) == 1:
                self.por_terminal.setdefault(cuerpo[0], []).append(cabeza)
            elif len(cuerpo) == 2:
                self.por_par.setdefault(cuerpo, []).append(cabeza)
        self.acepta_vacia = () in gramatica.producciones.get(gramatica.inicial, [])

    def analizar(self, tokens):
        tokens = list(tokens)
        inicial = self.gramatica.inicial
        desconocidos = [t for t in dict.fromkeys(tokens) if t not in self.por_terminal]

        if not tokens:
            return self._analizar_vacia()

        inicio = perf_counter()
        tabla = self._llenar_tabla(tokens)
        aceptada = inicial in tabla[len(tokens) - 1][0]
        tiempo_cyk = perf_counter() - inicio

        arbol = None
        tiempo_arbol = 0.0
        if aceptada:
            inicio = perf_counter()
            arbol = self._construir(tabla, inicial, 0, len(tokens))
            tiempo_arbol = perf_counter() - inicio

        motivo = self._motivo(tokens, tabla, aceptada, desconocidos)
        return ResultadoCYK(tokens, aceptada, tabla, tiempo_cyk, arbol, tiempo_arbol, desconocidos, motivo)

    def _llenar_tabla(self, tokens):
        n = len(tokens)
        tabla = [[{} for _ in range(n - largo + 1)] for largo in range(1, n + 1)]

        # Longitud 1: producciones A -> a.
        for i, token in enumerate(tokens):
            for a in self.por_terminal.get(token, ()):
                tabla[0][i].setdefault(a, Referencia((token,), None))

        # Longitudes 2..n: para cada inicio i y cada punto de division k,
        # si B esta en [i, k] y C en [i+k, largo-k] y existe A -> B C, A entra.
        for largo in range(2, n + 1):
            for i in range(n - largo + 1):
                celda = tabla[largo - 1][i]
                for k in range(1, largo):
                    izquierda = tabla[k - 1][i]
                    derecha = tabla[largo - k - 1][i + k]
                    for b in izquierda:
                        for c in derecha:
                            for a in self.por_par.get((b, c), ()):
                                if a not in celda:
                                    celda[a] = Referencia((b, c), k)
        return tabla

    def _construir(self, tabla, simbolo, i, largo):
        referencia = tabla[largo - 1][i][simbolo]
        if referencia.division is None:
            return Nodo(simbolo, [Nodo(referencia.produccion[0])])
        b, c = referencia.produccion
        k = referencia.division
        return Nodo(simbolo, [
            self._construir(tabla, b, i, k),
            self._construir(tabla, c, i + k, largo - k),
        ])

    def _analizar_vacia(self):
        inicial = self.gramatica.inicial
        inicio = perf_counter()
        aceptada = self.acepta_vacia
        tiempo = perf_counter() - inicio
        if aceptada:
            arbol = Nodo(inicial, [Nodo(EPSILON)])
            motivo = f"Entrada vacia: la gramatica CNF contiene {inicial} -> ε."
        else:
            arbol = None
            motivo = f"Entrada vacia: la gramatica CNF no contiene {inicial} -> ε."
        return ResultadoCYK([], aceptada, [], tiempo, arbol, 0.0, [], motivo)

    def _motivo(self, tokens, tabla, aceptada, desconocidos):
        inicial = self.gramatica.inicial
        n = len(tokens)
        if aceptada:
            return f"{inicial} esta en la celda que cubre toda la entrada (longitud {n}, posicion 1)."
        if desconocidos:
            return ("Tokens desconocidos: " + ", ".join(repr(t) for t in desconocidos)
                    + ". Ninguna produccion A -> a los genera, asi que su celda queda vacia"
                    " y ninguna celda superior puede cubrir toda la entrada.")
        superior = tabla[n - 1][0]
        contenido = "{" + ", ".join(superior) + "}" if superior else "vacia"
        return f"{inicial} no esta en la celda que cubre toda la entrada (esa celda esta {contenido})."
