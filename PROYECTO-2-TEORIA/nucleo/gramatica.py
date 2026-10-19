"""Representacion de una gramatica libre de contexto (CFG).

Una produccion A -> X1 X2 ... Xk se guarda como el par (A, (X1, X2, ..., Xk)):
el lado derecho es una TUPLA de simbolos, nunca una cadena que se recorra
caracter por caracter. Asi "id" es un solo simbolo y "Det" tambien.
La produccion epsilon A -> ε se representa con la tupla vacia ().

Un simbolo es no terminal si y solo si aparece como lado izquierdo de alguna
produccion (es una clave del diccionario). Todo lo demas es terminal.
"""

EPSILON = "ε"


class ErrorGramatica(Exception):
    """Error de formato o de consistencia en una gramatica."""


class Gramatica:
    def __init__(self, inicial, producciones):
        """
        inicial: nombre del simbolo inicial.
        producciones: dict {no_terminal: iterable de tuplas de simbolos}.
        El orden de insercion se conserva para mostrar la gramatica igual
        que en el archivo. Las producciones duplicadas se descartan.
        """
        self.inicial = inicial
        self.advertencias = []
        self.producciones = {}
        for cabeza, cuerpos in producciones.items():
            self.producciones.setdefault(cabeza, [])
            for cuerpo in cuerpos:
                self.agregar(cabeza, cuerpo)
        self.producciones.setdefault(inicial, [])

    def agregar(self, cabeza, cuerpo):
        """Agrega cabeza -> cuerpo. Devuelve False si ya existia (duplicado)."""
        cuerpo = tuple(cuerpo)
        lista = self.producciones.setdefault(cabeza, [])
        if cuerpo in lista:
            return False
        lista.append(cuerpo)
        return True

    @property
    def no_terminales(self):
        return set(self.producciones)

    @property
    def terminales(self):
        no_terminales = self.no_terminales
        return {s for _, cuerpo in self.todas() for s in cuerpo if s not in no_terminales}

    def es_terminal(self, simbolo):
        return simbolo not in self.producciones

    def todas(self):
        """Itera todas las producciones como pares (cabeza, cuerpo)."""
        for cabeza, cuerpos in self.producciones.items():
            for cuerpo in cuerpos:
                yield cabeza, cuerpo

    def cantidad(self):
        return sum(len(cuerpos) for cuerpos in self.producciones.values())

    def copiar(self):
        return Gramatica(self.inicial, self.producciones)

    def conjunto(self):
        """Conjunto de producciones; util para comparar gramaticas."""
        return {(cabeza, cuerpo) for cabeza, cuerpo in self.todas()}

    def __eq__(self, otra):
        return (
            isinstance(otra, Gramatica)
            and self.inicial == otra.inicial
            and self.conjunto() == otra.conjunto()
        )

    def __repr__(self):
        return f"Gramatica(inicial={self.inicial!r}, producciones={self.cantidad()})"
