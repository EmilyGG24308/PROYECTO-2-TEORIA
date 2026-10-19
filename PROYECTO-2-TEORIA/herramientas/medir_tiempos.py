"""Mide el tiempo de CYK para entradas de distinta longitud (datos del reporte).

Cada medicion es la mediana de varias repeticiones de AnalizadorCYK.analizar,
que solo cronometra el llenado de la tabla y la decision
"""

import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo.cnf import convertir_a_cnf  # noqa: E402
from nucleo.cyk import AnalizadorCYK  # noqa: E402
from nucleo.lector import leer_archivo  # noqa: E402

REPETICIONES = 25


def mediana_ms(analizador, tokens):
    tiempos = [analizador.analizar(tokens).tiempo_cyk for _ in range(REPETICIONES)]
    return statistics.median(tiempos) * 1000


def main():
    ingles = AnalizadorCYK(convertir_a_cnf(leer_archivo(RAIZ / "gramaticas" / "ingles.txt")).final)
    expresiones = AnalizadorCYK(convertir_a_cnf(leer_archivo(RAIZ / "gramaticas" / "1.txt")).final)

    print("Gramatica de ingles: 'she eats a cake' + k veces 'with a fork'")
    print(f"{'n tokens':>9} {'acepta':>7} {'mediana ms':>11}")
    for k in (0, 1, 2, 4, 8, 16):
        tokens = "she eats a cake".split() + "with a fork".split() * k
        print(f"{len(tokens):>9} {str(ingles.analizar(tokens).aceptada):>7} {mediana_ms(ingles, tokens):>11.4f}")

    print("\nGramatica 1.txt en CNF: 'id' + k veces '+ id'")
    print(f"{'n tokens':>9} {'acepta':>7} {'mediana ms':>11}")
    for k in (1, 3, 7, 15, 31):
        tokens = ["id"] + ["+", "id"] * k
        print(f"{len(tokens):>9} {str(expresiones.analizar(tokens).aceptada):>7} {mediana_ms(expresiones, tokens):>11.4f}")


if __name__ == "__main__":
    main()
