import unittest
from pathlib import Path

from nucleo.gramatica import ErrorGramatica
from nucleo.lector import leer_archivo, leer_texto

GRAMATICAS = Path(__file__).resolve().parent.parent / "gramaticas"


class PruebasLector(unittest.TestCase):
    def test_lee_1_txt_con_epsilon_e_id_como_un_terminal(self):
        g = leer_archivo(GRAMATICAS / "1.txt")
        self.assertEqual(g.inicial, "E")
        self.assertEqual(g.no_terminales, {"E", "X", "T", "Y", "F"})
        self.assertEqual(g.terminales, {"+", "*", "(", ")", "id"})
        self.assertIn((), g.producciones["X"])           # X -> e
        self.assertIn(("id",), g.producciones["F"])      # id es UN simbolo
        self.assertIn(("(", "E", ")"), g.producciones["F"])

    def test_no_terminales_de_varios_caracteres(self):
        g = leer_archivo(GRAMATICAS / "ingles.txt")
        self.assertEqual(g.inicial, "S")
        self.assertIn("Det", g.no_terminales)
        self.assertIn(("Det", "N"), g.producciones["NP"])
        self.assertNotIn("D", g.no_terminales)

    def test_simbolo_inicial_explicito(self):
        g = leer_archivo(GRAMATICAS / "1.txt", inicial="T")
        self.assertEqual(g.inicial, "T")

    def test_inicial_inexistente(self):
        with self.assertRaises(ErrorGramatica):
            leer_archivo(GRAMATICAS / "1.txt", inicial="Q")

    def test_varias_lineas_mismo_lado_izquierdo_y_duplicados(self):
        g = leer_texto("A -> a | b\nA -> b | c\nA → a\n")
        self.assertEqual(g.producciones["A"], [("a",), ("b",), ("c",)])
        self.assertEqual(len(g.advertencias), 2)

    def test_epsilon_unicode(self):
        g = leer_texto("S -> a S | ε")
        self.assertIn((), g.producciones["S"])

    def test_clasificacion_usa_todos_los_lados_izquierdos(self):
        # B aparece a la derecha antes de definirse: igual debe ser no terminal.
        g = leer_texto("S -> B c\nB -> b")
        self.assertFalse(g.es_terminal("B"))
        self.assertEqual(g.terminales, {"b", "c"})

    def test_lineas_mal_formadas_informan_numero(self):
        casos = {
            "S -> a\nS a b\n": "Linea 2",                 # falta flecha
            "S -> a\n\nA B -> c\n": "Linea 3",            # lado izquierdo con dos simbolos
            "S -> a e\n": "Linea 1",                      # epsilon mezclado
            "S -> a |\n": "Linea 1",                      # alternativa vacia
            "S -> a -> b\n": "Linea 1",                   # dos flechas
            "e -> a\n": "Linea 1",                        # epsilon como lado izquierdo
            " -> a\n": "Linea 1",                         # sin lado izquierdo
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorGramatica) as contexto:
                    leer_texto(texto)
                self.assertIn(esperado, str(contexto.exception))

    def test_archivo_vacio_o_solo_comentarios(self):
        with self.assertRaises(ErrorGramatica):
            leer_texto("# nada\n\n")


if __name__ == "__main__":
    unittest.main()
