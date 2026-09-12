# -*- coding: utf-8 -*-
"""
error_lexico.py
Representa un error detectado durante el analisis lexico.
"""


class ErrorLexico:

    def __init__(self, numero, lexema, tipo, descripcion, linea, columna):
        self.numero = numero            # correlativo del error
        self.lexema = lexema            # texto invalido encontrado
        self.tipo = tipo                # categoria del error
        self.descripcion = descripcion  # mensaje legible para el usuario
        self.linea = linea
        self.columna = columna

    def a_fila(self):
        return (self.numero, self.lexema, self.tipo,
                self.descripcion, self.linea, self.columna)

    def __str__(self):
        return ('[E' + str(self.numero) + '] ' + self.tipo +
                ' -> ' + self.descripcion)

    def __repr__(self):
        return self.__str__()
