import unittest
from pathlib import Path

from nucleo.cnf import anulables, convertir_a_cnf, es_cnf, problemas_cnf
from nucleo.cyk import AnalizadorCYK
from nucleo.lector import leer_archivo, leer_texto
from tests.utilidades import diferencias_de_lenguaje, reconoce_earley

GRAMATICAS = Path(__file__).resolve().parent.parent / "gramaticas"


def convertir(texto, inicial=None):
    original = leer_texto(texto, inicial)
    return original, convertir_a_cnf(original, forzar=True)


class PruebasConversion(unittest.TestCase):
    def assertMismoLenguaje(self, original, alfabeto, longitud, cnf=None):
        self.assertEqual(diferencias_de_lenguaje(original, alfabeto, longitud, cnf), [])

    def test_1_txt_queda_en_cnf_y_conserva_el_lenguaje(self):
        original = leer_archivo(GRAMATICAS / "1.txt", "E")
        self.assertFalse(es_cnf(original))
        resultado = convertir_a_cnf(original)
        self.assertTrue(es_cnf(resultado.final))
        self.assertEqual(resultado.final.inicial, "E")
        self.assertMismoLenguaje(original, {"id", "+", "*", "(", ")"}, 6, resultado.final)

    def test_etapas_sin_cambios_se_marcan(self):
        resultado = convertir_a_cnf(leer_archivo(GRAMATICAS / "1.txt", "E"))
        cambios = {e.nombre[:2]: e.cambio for e in resultado.etapas}
        self.assertFalse(cambios["1."])    # E no es anulable: no hace falta inicial nuevo
        self.assertTrue(cambios["2."])
        self.assertTrue(cambios["3."])
        self.assertFalse(cambios["4."])    # no hay simbolos inutiles
        self.assertTrue(cambios["5."])
        self.assertTrue(cambios["6."])

    def test_anulabilidad_indirecta_y_varios_anulables(self):
        original, resultado = convertir(
            "S -> A B C d | A B\n"
            "A -> B C\n"
            "B -> b | e\n"
            "C -> c | e\n"
        )
        self.assertEqual(anulables(original), {"A", "B", "C", "S"})   # A y S indirectamente
        # A B C d tiene 3 anulables -> 2^3 combinaciones, entre ellas "d" sola.
        cnf = resultado.final
        self.assertTrue(AnalizadorCYK(cnf).analizar(["d"]).aceptada)
        self.assertTrue(AnalizadorCYK(cnf).analizar([]).aceptada)
        self.assertMismoLenguaje(original, {"b", "c", "d"}, 5, cnf)

    def test_cadena_vacia_aceptada_con_inicial_nuevo(self):
        original, resultado = convertir("S -> a S b | e")
        cnf = resultado.final
        self.assertNotEqual(cnf.inicial, "S")          # S es anulable y aparece a la derecha
        self.assertIn((), cnf.producciones[cnf.inicial])
        self.assertFalse(any(cnf.inicial in c for _, c in cnf.todas()))
        self.assertTrue(es_cnf(cnf))
        analizador = AnalizadorCYK(cnf)
        self.assertTrue(analizador.analizar([]).aceptada)
        self.assertTrue(analizador.analizar(["a", "a", "b", "b"]).aceptada)
        self.assertFalse(analizador.analizar(["a", "b", "b"]).aceptada)
        self.assertMismoLenguaje(original, {"a", "b"}, 8, cnf)

    def test_cadena_vacia_rechazada(self):
        original, resultado = convertir("S -> a S b | a b")
        self.assertEqual(resultado.final.inicial, "S")
        self.assertFalse(AnalizadorCYK(resultado.final).analizar([]).aceptada)
        self.assertMismoLenguaje(original, {"a", "b"}, 8, resultado.final)

    def test_cadenas_y_ciclos_de_unitarias(self):
        original, resultado = convertir(
            "S -> A | a S\n"
            "A -> B\n"
            "B -> C | b\n"
            "C -> A | c\n"          # ciclo A -> B -> C -> A
        )
        cnf = resultado.final
        self.assertFalse(any(len(c) == 1 and c[0] in cnf.no_terminales for _, c in cnf.todas()))
        self.assertMismoLenguaje(original, {"a", "b", "c"}, 6, cnf)

    def test_simbolos_no_generadores_e_inalcanzables(self):
        original, resultado = convertir(
            "S -> A B | a\n"
            "A -> a A\n"           # A nunca termina: no generador
            "B -> b\n"             # B solo se alcanzaba por S -> A B: queda inalcanzable
            "C -> c\n"             # C inalcanzable desde el principio
        )
        cnf = resultado.final
        self.assertEqual(cnf.conjunto(), {("S", ("a",))})
        detalles = " ".join(next(e for e in resultado.etapas if e.nombre.startswith("4.")).detalles)
        self.assertIn("No generadores: A", detalles)
        self.assertIn("B", detalles)
        self.assertIn("C", detalles)

    def test_lenguaje_vacio(self):
        original, resultado = convertir("S -> a S")
        self.assertEqual(resultado.final.cantidad(), 0)
        self.assertFalse(AnalizadorCYK(resultado.final).analizar(["a"]).aceptada)

    def test_producciones_largas_con_terminales_mezclados(self):
        original, resultado = convertir("S -> x B y D z | x x\nB -> b\nD -> d | x")
        cnf = resultado.final
        self.assertTrue(es_cnf(cnf))
        self.assertTrue(AnalizadorCYK(cnf).analizar("x b y x z".split()).aceptada)
        # El auxiliar de "x" se reutiliza: solo debe existir una produccion A -> x
        # que no sea de un no terminal original.
        auxiliares_x = [a for a, c in cnf.todas() if c == ("x",) and a.startswith("TERM_")]
        self.assertEqual(len(auxiliares_x), 1)
        self.assertMismoLenguaje(original, {"x", "b", "y", "d", "z"}, 5, cnf)

    def test_nombres_auxiliares_no_colisionan(self):
        texto = (
            "S -> BIN1 + S S0 | e\n"
            "BIN1 -> TERM_MAS | n\n"
            "TERM_MAS -> m\n"
            "S0 -> o\n"
        )
        original, resultado = convertir(texto)
        cnf = resultado.final
        nuevos = cnf.no_terminales - original.no_terminales
        self.assertTrue(nuevos)
        self.assertFalse(nuevos & (original.no_terminales | original.terminales))
        self.assertNotIn(cnf.inicial, {"S", "S0"})
        # Si un auxiliar hubiera reutilizado BIN1, TERM_MAS o S0, el lenguaje cambiaria.
        self.assertMismoLenguaje(original, {"+", "n", "m", "o"}, 8, cnf)

    def test_gramatica_ya_en_cnf(self):
        original = leer_archivo(GRAMATICAS / "1-cnf.txt", "E")
        self.assertEqual(problemas_cnf(original), [])
        resultado = convertir_a_cnf(original)
        self.assertTrue(resultado.ya_estaba_en_cnf)
        self.assertEqual(resultado.etapas, [])
        self.assertEqual(resultado.final, original)
        forzado = convertir_a_cnf(original, forzar=True)
        self.assertTrue(es_cnf(forzado.final))
        self.assertMismoLenguaje(original, {"id", "+", "*", "(", ")"}, 5, forzado.final)

    def test_ingles_convertido_conserva_lenguaje(self):
        original = leer_archivo(GRAMATICAS / "ingles.txt")
        cnf = convertir_a_cnf(original).final
        self.assertTrue(es_cnf(cnf))
        analizador = AnalizadorCYK(cnf)
        frases = ["she eats", "he cuts the cake", "she drinks the juice in the oven",
                  "the dog eats a meat with a spoon in the oven", "a cat", "he he"]
        for frase in frases:
            with self.subTest(frase=frase):
                tokens = frase.split()
                self.assertEqual(analizador.analizar(tokens).aceptada, reconoce_earley(original, tokens))


if __name__ == "__main__":
    unittest.main()
