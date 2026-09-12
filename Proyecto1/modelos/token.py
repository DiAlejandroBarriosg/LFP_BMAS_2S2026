# -*- coding: utf-8 -*-
"""
token.py
Representa una unidad lexica reconocida por el AFD.
"""


class Token:

    def __init__(self, numero, lexema, tipo, linea, columna):
        self.numero = numero      # correlativo dentro del analisis
        self.lexema = lexema      # texto exacto tal como aparece en el archivo
        self.tipo = tipo          # categoria (ver palabras_reservadas.py)
        self.linea = linea        # linea donde INICIA el lexema (base 1)
        self.columna = columna    # columna donde INICIA el lexema (base 1)

    def a_fila(self):
        """Devuelve una tupla lista para insertarse en un Treeview de Tkinter."""
        return (self.numero, self.lexema, self.tipo, self.linea, self.columna)

    def __str__(self):
        return ('[' + str(self.numero) + '] ' + self.tipo +
                ' -> ' + self.lexema +
                '  (linea ' + str(self.linea) +
                ', columna ' + str(self.columna) + ')')

    def __repr__(self):
        return self.__str__()
