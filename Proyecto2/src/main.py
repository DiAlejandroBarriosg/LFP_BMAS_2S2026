# -*- coding: utf-8 -*-
"""
main.py
Punto de entrada de MarkdownCheck.

Uso, desde la carpeta Proyecto2:
    python src/main.py
    python src/main.py examples/ejemplo_valido.md   (abre ese archivo)

Los reportes se guardan en Proyecto2/salida/<nombre del archivo>/.
"""

import os
import sys
import tkinter as tk

CARPETA_SRC = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_SRC)
# Asi los paquetes lexico, sintactico, errores, reportes y gui se encuentran
# aunque el programa se ejecute desde otra carpeta.
sys.path.insert(0, CARPETA_SRC)

from gui.ventana_principal import VentanaPrincipal


def main():
    ventana = tk.Tk()
    aplicacion = VentanaPrincipal(ventana,
                                  os.path.join(CARPETA_PROYECTO, 'salida'))
    if len(sys.argv) > 1:
        aplicacion.cargar_archivo(sys.argv[1])
    ventana.mainloop()


if __name__ == '__main__':
    main()
