# Proyecto 2 

## Requisitos e instalación

- Python **3.10 o superior** (probado con Python 3.14.5 en Windows 11).
- No hay dependencias externas: no hace falta `pip install`.

```bash
cd PROYECTO-2-TEORIA
```

## Ejecución

Menú interactivo:

```bash
python main.py
```

Opciones: 1 cargar gramática (pide archivo y símbolo inicial; Enter = primer lado izquierdo),
2 mostrar original, 3 verificar CNF, 4 convertir mostrando etapas, 5 analizar cadena (pregunta si se
muestra la tabla CYK), 6 cambiar símbolo inicial, 7 cambiar modo de tokenización, 0 salir.
Si se analiza sin haber convertido, la conversión se hace automáticamente.

Modo directo (sin menú), útil para demostraciones:

```bash
python main.py --gramatica gramaticas/1.txt --inicial E --etapas --tabla --cadena "(id*id)+id"
```

```bash
python main.py --gramatica gramaticas/ingles.txt --inicial S --tabla --cadena "she eats a cake with a fork" --cadena "the cat drinks beer"
```

## Pruebas

```bash
python -m unittest discover -v
```

31 pruebas (lector, conversión a CNF, CYK). Resultado real de la última ejecución: `Ran 31 tests ... OK`
(ver [docs/ejecuciones/pruebas.txt](docs/ejecuciones/pruebas.txt)).

Medición de tiempos para distintas longitudes de entrada:

```bash
python herramientas/medir_tiempos.py
```



