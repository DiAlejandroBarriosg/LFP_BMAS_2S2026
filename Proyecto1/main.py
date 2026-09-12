# -*- coding: utf-8 -*-
"""
main.py
Punto de entrada de HorarioScript.

Uso:
    python main.py                        abre la ventana vacia
    python main.py entradas/archivo.hor   abre la ventana con el archivo cargado
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        import tkinter as tk
    except ImportError:
        print('Falta Tkinter.')
        print('En Windows y macOS viene con el instalador oficial de Python.')
        print('En Debian o Ubuntu: sudo apt install python3-tk')
        return 1

    from gui.interfaz import InterfazHorarioScript

    raiz = tk.Tk()
    aplicacion = InterfazHorarioScript(raiz)

    # Si se paso un archivo por linea de comandos, se carga y se analiza
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        if os.path.isfile(ruta):
            archivo = open(ruta, 'r', encoding='utf-8', newline='')
            contenido = archivo.read()
            archivo.close()
            aplicacion.cargar_texto(contenido, os.path.abspath(ruta))
            aplicacion.analizar()
        else:
            print('No existe el archivo: ' + ruta)

    raiz.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
