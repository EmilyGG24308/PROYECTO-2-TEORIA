import unittest
from pathlib import Path

from nucleo.cnf import convertir_a_cnf
from nucleo.cyk import AnalizadorCYK
from nucleo.gramatica import ErrorGramatica
from nucleo.lector import leer_archivo, leer_texto
from nucleo.presentacion import formatear_arbol, formatear_tabla
from nucleo.tokenizador import MODO_AUTO, MODO_PALABRAS, MODO_SIMBOLOS, resolver_modo, tokenizar
from tests.utilidades import arbol_valido

GRAMATICAS = Path(__file__).resolve().parent.parent / "gramaticas"

INGLES_ACEPTADAS = [
    "she eats a cake with a fork",
    "the cat drinks the beer",
    "he cooks",
    "she eats a fork",
]
INGLES_RECHAZADAS = [
    "she a cake",
    "the cat drinks beer",
    "eats she a cake",
    "she eats a pizza",
]
EXPRESIONES_ACEPTADAS = ["id", "id + id", "id * id", "( id * id ) + id", "(id*id)+id"]
EXPRESIONES_RECHAZADAS = ["id +", "* id", "( id + id", "id id"]


def preparar(ruta, inicial=None):
    cnf = convertir_a_cnf(leer_archivo(ruta, inicial)).final
    return AnalizadorCYK(cnf)


class PruebasCYK(unittest.TestCase):
    def analizar(self, analizador, texto):
        terminales = analizador.gramatica.terminales
        tokens = tokenizar(texto, MODO_AUTO, terminales)
        resultado = analizador.analizar(tokens)
        if resultado.aceptada:
            # El arbol debe producir exactamente los tokens y usar producciones reales.
            self.assertEqual(resultado.arbol.hojas(), tokens)
            self.assertTrue(arbol_valido(resultado.arbol, analizador.gramatica))
        else:
            self.assertIsNone(resultado.arbol)
        self.assertGreaterEqual(resultado.tiempo_cyk, 0.0)
        return resultado

    def test_ingles(self):
        analizador = preparar(GRAMATICAS / "ingles.txt", "S")
        for frase in INGLES_ACEPTADAS:
            with self.subTest(frase=frase):
                self.assertTrue(self.analizar(analizador, frase).aceptada)
        for frase in INGLES_RECHAZADAS:
            with self.subTest(frase=frase):
                self.assertFalse(self.analizar(analizador, frase).aceptada)

    def test_ingles_mayusculas_se_normalizan(self):
        analizador = preparar(GRAMATICAS / "ingles.txt")
        self.assertTrue(self.analizar(analizador, "She eats a cake with a fork").aceptada)
        self.assertTrue(self.analizar(analizador, "The cat drinks the beer").aceptada)

    def test_token_desconocido_explica_rechazo(self):
        analizador = preparar(GRAMATICAS / "ingles.txt")
        resultado = self.analizar(analizador, "she eats a pizza")
        self.assertEqual(resultado.desconocidos, ["pizza"])
        self.assertIn("pizza", resultado.motivo)
        # La puntuacion no se borra en silencio: queda como token desconocido.
        resultado = self.analizar(analizador, "he cooks.")
        self.assertFalse(resultado.aceptada)
        self.assertEqual(resultado.desconocidos, ["."])

    def test_expresiones_con_1_txt_y_con_1_cnf_txt(self):
        for archivo in ("1.txt", "1-cnf.txt"):
            analizador = preparar(GRAMATICAS / archivo, "E")
            for expresion in EXPRESIONES_ACEPTADAS:
                with self.subTest(archivo=archivo, expresion=expresion):
                    self.assertTrue(self.analizar(analizador, expresion).aceptada)
            for expresion in EXPRESIONES_RECHAZADAS + [""]:
                with self.subTest(archivo=archivo, expresion=expresion):
                    self.assertFalse(self.analizar(analizador, expresion).aceptada)

    def test_tokenizacion_de_expresiones(self):
        terminales = {"id", "+", "*", "(", ")"}
        self.assertEqual(resolver_modo(MODO_AUTO, terminales), MODO_SIMBOLOS)
        self.assertEqual(tokenizar("(id*id)+id", MODO_AUTO, terminales),
                         ["(", "id", "*", "id", ")", "+", "id"])
        self.assertEqual(tokenizar("idid - id", MODO_SIMBOLOS, terminales), ["idid", "-", "id"])

    def test_tokenizacion_de_palabras(self):
        self.assertEqual(resolver_modo(MODO_AUTO, {"she", "eats"}), MODO_PALABRAS)
        self.assertEqual(tokenizar("  She  EATS, a cake ", MODO_PALABRAS, set()),
                         ["she", "eats", ",", "a", "cake"])

    def test_cadena_vacia(self):
        acepta = AnalizadorCYK(convertir_a_cnf(leer_texto("S -> a S b | e")).final)
        resultado = acepta.analizar([])
        self.assertTrue(resultado.aceptada)
        self.assertEqual(resultado.arbol.hojas(), [])
        rechaza = AnalizadorCYK(convertir_a_cnf(leer_texto("S -> a S b | a b")).final)
        self.assertFalse(rechaza.analizar([]).aceptada)

    def test_gramatica_ambigua_reconstruye_arbol_valido(self):
        cnf = convertir_a_cnf(leer_texto("E -> E + E | E * E | ( E ) | id")).final
        analizador = AnalizadorCYK(cnf)
        tokens = "id + id * id + id".split()
        resultado = analizador.analizar(tokens)
        self.assertTrue(resultado.aceptada)
        self.assertEqual(resultado.arbol.hojas(), tokens)
        self.assertTrue(arbol_valido(resultado.arbol, cnf))
        # La celda de toda la entrada se alcanza por varias divisiones (ambiguedad),
        # pero se guarda una sola referencia por no terminal.
        self.assertIn("E", resultado.tabla[len(tokens) - 1][0])

    def test_tabla_cyk_contenido(self):
        analizador = preparar(GRAMATICAS / "ingles.txt")
        resultado = analizador.analizar("the cat drinks the beer".split())
        self.assertEqual(set(resultado.tabla[0][0]), {"Det"})          # the
        self.assertIn("NP", resultado.tabla[1][0])                    # the cat
        self.assertIn("VP", resultado.tabla[2][2])                    # drinks the beer
        self.assertIn("S", resultado.tabla[4][0])                     # toda la frase
        texto = formatear_tabla(resultado)
        self.assertIn("l=5", texto)
        self.assertIn("beer", texto)
        self.assertTrue(formatear_arbol(resultado.arbol).startswith("S"))

    def test_cyk_exige_cnf(self):
        with self.assertRaises(ErrorGramatica):
            AnalizadorCYK(leer_archivo(GRAMATICAS / "1.txt"))


if __name__ == "__main__":
    unittest.main()
