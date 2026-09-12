# -*- coding: utf-8 -*-
"""
gestor_errores.py

Acumula los errores lexicos sin detener el analisis (modo panico / recuperacion
de errores). El analizador reporta el error, descarta el lexema problematico y
continua desde el siguiente caracter valido, de modo que un solo recorrido del
archivo revela TODOS los problemas.
"""

from modelos.error_lexico import ErrorLexico


class GestorErrores:

    def __init__(self):
        self.errores = []
        self.contador = 0

    def agregar(self, lexema, tipo, descripcion, linea, columna):
        self.contador = self.contador + 1
        error = ErrorLexico(self.contador, lexema, tipo,
                            descripcion, linea, columna)
        self.errores.append(error)
        return error

    def hay_errores(self):
        return len(self.errores) > 0

    def total(self):
        return len(self.errores)

    def contar_por_tipo(self):
        """Devuelve un diccionario {tipo_de_error: cantidad}."""
        conteo = {}
        i = 0
        while i < len(self.errores):
            tipo = self.errores[i].tipo
            if tipo in conteo:
                conteo[tipo] = conteo[tipo] + 1
            else:
                conteo[tipo] = 1
            i = i + 1
        return conteo

    def limpiar(self):
        self.errores = []
        self.contador = 0
