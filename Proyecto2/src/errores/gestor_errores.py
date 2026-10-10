# -*- coding: utf-8 -*-
"""
gestor_errores.py
GestorErrores: acumula los errores lexicos y sintacticos de un analisis.

Lo comparten el AnalizadorLexico y el AnalizadorSintactico. Ninguno de los
dos se detiene al encontrar un error (modo panico): lo registran aqui y
siguen analizando, de modo que al final se reportan todos en una sola
pasada.
"""

from errores.error_analisis import ErrorAnalisis


class GestorErrores:

    def __init__(self):
        self.errores = []

    def agregar(self, lexema, tipo, descripcion, linea, columna, fase):
        """
        Registra un error y lo deja en su lugar segun su posicion.

        El parser pide tokens al lexico sobre la marcha, asi que los errores
        no siempre llegan en el orden del archivo (por ejemplo, una negrita
        sin cerrar solo se detecta al terminar su linea). Por eso se inserta
        de forma ordenada: se empieza al final de la lista y se retrocede
        mientras el error anterior este despues del nuevo. Es el paso
        interno del ordenamiento por insercion.
        """
        nuevo = ErrorAnalisis(0, lexema, tipo, descripcion, linea, columna,
                              fase)
        posicion = len(self.errores)
        buscando = True
        while buscando and posicion > 0:
            anterior = self.errores[posicion - 1]
            if anterior.esta_despues_de(nuevo):
                posicion = posicion - 1
            else:
                buscando = False
        self.errores.insert(posicion, nuevo)
        self._renumerar()
        return nuevo

    def _renumerar(self):
        """El numero de cada error es su posicion en la tabla."""
        i = 0
        while i < len(self.errores):
            self.errores[i].numero = i + 1
            i = i + 1

    def existe(self, tipo, linea, fase):
        """
        True si ya hay un error de ese tipo, en esa linea y de esa fase.
        El parser lo usa para no reportar dos veces el mismo problema
        mientras se recupera de el (D-22).
        """
        i = 0
        while i < len(self.errores):
            e = self.errores[i]
            if e.tipo == tipo and e.linea == linea and e.fase == fase:
                return True
            i = i + 1
        return False

    def hay_errores(self):
        return len(self.errores) > 0

    def cantidad(self):
        return len(self.errores)

    def contar_tipo(self, tipo):
        """Cuantos errores de un tipo hay. Util en las pruebas."""
        total = 0
        i = 0
        while i < len(self.errores):
            if self.errores[i].tipo == tipo:
                total = total + 1
            i = i + 1
        return total

    def limpiar(self):
        self.errores = []
