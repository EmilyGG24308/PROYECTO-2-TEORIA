"""

Uso interactivo:
    python main.py

Uso directo (sin menu), util para demostraciones:
    python main.py --gramatica gramaticas/1.txt --inicial E --etapas --tabla --cadena "(id*id)+id"
    python main.py --gramatica gramaticas/ingles.txt --cadena "she eats a cake with a fork"

La clase Principal concentra TODA la interaccion con el usuario (entrada y
mensajes). Los modulos de `nucleo/` solo devuelven resultados o lanzan
excepciones.
"""

import argparse
import sys
from pathlib import Path

from nucleo.cnf import convertir_a_cnf, problemas_cnf
from nucleo.cyk import AnalizadorCYK
from nucleo.gramatica import ErrorGramatica
from nucleo.lector import leer_archivo
from nucleo.presentacion import (
    formatear_arbol,
    formatear_corchetes,
    formatear_gramatica,
    formatear_tabla,
)
from nucleo.tokenizador import MODOS, MODO_AUTO, resolver_modo, tokenizar

CARPETA_GRAMATICAS = Path(__file__).resolve().parent / "gramaticas"

MENU = """
================ PROYECTO 2: CFG -> CNF -> CYK ================
 1. Cargar gramatica desde archivo
 2. Mostrar gramatica original
 3. Verificar si esta en CNF
 4. Simplificar y convertir a CNF (mostrar etapas)
 5. Analizar una cadena con CYK
 6. Cambiar simbolo inicial
 7. Cambiar modo de tokenizacion (actual: {modo})
 0. Salir
Gramatica cargada: {ruta}"""


class Principal:
    def __init__(self):
        self.ruta = None
        self.gramatica = None
        self.resultado_cnf = None
        self.analizador = None
        self.modo = MODO_AUTO

    # ------------------------------------------------------------------ menu

    def ejecutar_menu(self):
        acciones = {
            "1": self.opcion_cargar,
            "2": self.mostrar_original,
            "3": self.verificar_cnf,
            "4": self.convertir,
            "5": self.opcion_analizar,
            "6": self.opcion_cambiar_inicial,
            "7": self.opcion_cambiar_modo,
        }
        activo = True
        while activo:
            print(MENU.format(modo=self.modo, ruta=self.ruta or "(ninguna)"))
            opcion = self._leer("Opcion: ")
            if opcion is None or opcion == "0":
                activo = False
                print("Hasta luego.")
            elif opcion in acciones:
                acciones[opcion]()
            else:
                print("Opcion no valida.")

    def opcion_cargar(self):
        disponibles = sorted(p.name for p in CARPETA_GRAMATICAS.glob("*.txt"))
        print("Archivos en gramaticas/: " + ", ".join(disponibles))
        ruta = self._leer("Ruta del archivo (o nombre dentro de gramaticas/): ")
        if not ruta:
            print("No se cargo ninguna gramatica.")
            return
        if self.cargar(ruta):
            inicial = self._leer(
                f"Simbolo inicial [Enter = {self.gramatica.inicial}]: "
            )
            if inicial:
                self.cambiar_inicial(inicial)

    def opcion_cambiar_inicial(self):
        if self._requiere_gramatica():
            print("No terminales: " + ", ".join(self.gramatica.producciones))
            inicial = self._leer("Nuevo simbolo inicial: ")
            if inicial:
                self.cambiar_inicial(inicial)

    def opcion_cambiar_modo(self):
        print("Modos: auto (segun los terminales), palabras (frases en ingles), simbolos (expresiones)")
        modo = self._leer("Modo: ")
        if modo in MODOS:
            self.modo = modo
            print(f"Modo de tokenizacion: {modo}")
        else:
            print("Modo no valido; se mantiene " + self.modo)

    def opcion_analizar(self):
        if not self._requiere_gramatica():
            return
        texto = self._leer("Cadena a analizar (Enter = cadena vacia): ")
        if texto is None:
            return
        detalle = self._leer("Mostrar la tabla CYK? (s/N): ")
        self.analizar(texto, mostrar_tabla=(detalle or "").lower().startswith("s"))

    # ------------------------------------------------------------- acciones

    def cargar(self, ruta, inicial=None):
        archivo = Path(ruta)
        if not archivo.exists() and (CARPETA_GRAMATICAS / ruta).exists():
            archivo = CARPETA_GRAMATICAS / ruta
        try:
            gramatica = leer_archivo(archivo, inicial)
        except (OSError, ErrorGramatica) as error:
            print(f"No se pudo cargar la gramatica: {error}")
            return False
        self.ruta = str(archivo)
        self._usar_gramatica(gramatica)
        print(f"Gramatica cargada de {archivo} con simbolo inicial {gramatica.inicial}.")
        for advertencia in gramatica.advertencias:
            print("  Aviso: " + advertencia)
        return True

    def cambiar_inicial(self, inicial):
        try:
            gramatica = leer_archivo(self.ruta, inicial)
        except (OSError, ErrorGramatica) as error:
            print(f"No se pudo cambiar el simbolo inicial: {error}")
            return
        self._usar_gramatica(gramatica)
        print(f"Simbolo inicial: {inicial}")

    def mostrar_original(self):
        if self._requiere_gramatica():
            g = self.gramatica
            print(f"\n--- Gramatica original (inicial: {g.inicial}) ---")
            print(formatear_gramatica(g))
            print(f"No terminales: {', '.join(g.producciones)}")
            print(f"Terminales: {', '.join(sorted(g.terminales))}")

    def verificar_cnf(self):
        if self._requiere_gramatica():
            problemas = problemas_cnf(self.gramatica)
            if problemas:
                print("\nLa gramatica NO esta en CNF:")
                for problema in problemas:
                    print("  - " + problema)
            else:
                print("\nLa gramatica SI esta en CNF.")

    def convertir(self, mostrar_etapas=True, forzar=False):
        if not self._requiere_gramatica():
            return False
        try:
            resultado = convertir_a_cnf(self.gramatica, forzar)
            analizador = AnalizadorCYK(resultado.final)
        except ErrorGramatica as error:
            print(f"Error en la conversion: {error}")
            return False
        self.resultado_cnf = resultado
        self.analizador = analizador

        if resultado.ya_estaba_en_cnf:
            print("\nLa gramatica ya esta en CNF: se usa sin transformaciones.")
        elif mostrar_etapas:
            print("\n=========== Conversion a CNF por etapas ===========")
            for etapa in resultado.etapas:
                print(f"\n>>> {etapa.nombre}: {etapa.descripcion}")
                for detalle in etapa.detalles:
                    print("    " + detalle)
                if etapa.nombre.startswith("7."):
                    continue
                if etapa.cambio:
                    print(formatear_gramatica(etapa.gramatica))
                else:
                    print("    (Esta etapa no cambio la gramatica.)")
        else:
            print("\nGramatica convertida a CNF.")
        print(f"\n--- Gramatica en CNF usada por CYK (inicial: {resultado.final.inicial}) ---")
        print(formatear_gramatica(resultado.final))
        return True

    def analizar(self, texto, mostrar_tabla=False):
        if not self._requiere_gramatica():
            return
        if self.analizador is None:
            print("La gramatica aun no se ha preparado para CYK; se convierte primero.")
            if not self.convertir(mostrar_etapas=False):
                return
        terminales = self.analizador.gramatica.terminales
        modo = resolver_modo(self.modo, terminales)
        tokens = tokenizar(texto, modo, terminales)
        resultado = self.analizador.analizar(tokens)

        print(f"\nEntrada: {texto!r}")
        print(f"Tokens (modo {modo}, {len(tokens)}): {' '.join(tokens) if tokens else '(ninguno)'}")
        if mostrar_tabla:
            print("\nTabla CYK (fila l = longitud de la subcadena, columna i = token inicial):")
            print(formatear_tabla(resultado))
        print("\nResultado: " + ("SÍ" if resultado.aceptada else "NO")
              + (", la cadena pertenece al lenguaje." if resultado.aceptada
                 else ", la cadena NO pertenece al lenguaje."))
        print("Motivo: " + resultado.motivo)
        print(f"Tiempo de validacion CYK: {resultado.tiempo_cyk * 1000:.4f} ms "
              "(llenado de la tabla y decision; excluye lectura, conversion, tokenizacion, "
              "impresion y el arbol)")
        if resultado.arbol is not None:
            print(f"Tiempo de reconstruccion del arbol (medido aparte): {resultado.tiempo_arbol * 1000:.4f} ms")
            print("\nArbol de analisis (de la gramatica CNF; puede contener auxiliares TERM_* / BIN*):")
            print(formatear_arbol(resultado.arbol))
            print("Notacion con corchetes: " + formatear_corchetes(resultado.arbol))

    # ------------------------------------------------------------- utilidades

    def _usar_gramatica(self, gramatica):
        self.gramatica = gramatica
        self.resultado_cnf = None
        self.analizador = None

    def _requiere_gramatica(self):
        if self.gramatica is None:
            print("Primero cargue una gramatica (opcion 1).")
            return False
        return True

    @staticmethod
    def _leer(mensaje):
        """Lee una linea; devuelve None si la entrada termino (EOF)."""
        try:
            return input(mensaje).strip()
        except EOFError:
            return None


def argumentos():
    parser = argparse.ArgumentParser(description="CFG -> CNF -> CYK")
    parser.add_argument("--gramatica", help="archivo de la gramatica (sin esto se abre el menu)")
    parser.add_argument("--inicial", help="simbolo inicial (por defecto el primer lado izquierdo)")
    parser.add_argument("--cadena", action="append", default=[], help="cadena a analizar (repetible)")
    parser.add_argument("--modo", choices=MODOS, default=MODO_AUTO, help="modo de tokenizacion")
    parser.add_argument("--etapas", action="store_true", help="mostrar original, verificacion y etapas")
    parser.add_argument("--tabla", action="store_true", help="mostrar la tabla CYK")
    parser.add_argument("--forzar", action="store_true",
                        help="aplicar las etapas aunque la gramatica ya este en CNF")
    return parser.parse_args()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = argumentos()
    principal = Principal()
    principal.modo = args.modo
    if args.gramatica is None:
        principal.ejecutar_menu()
        return 0
    if not principal.cargar(args.gramatica, args.inicial):
        return 1
    if args.etapas:
        principal.mostrar_original()
        principal.verificar_cnf()
    if not principal.convertir(mostrar_etapas=args.etapas, forzar=args.forzar):
        return 1
    for cadena in args.cadena:
        print("\n" + "=" * 60)
        principal.analizar(cadena, mostrar_tabla=args.tabla)
    return 0


if __name__ == "__main__":
    sys.exit(main())
