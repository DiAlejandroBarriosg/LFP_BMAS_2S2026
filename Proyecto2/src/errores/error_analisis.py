# -*- coding: utf-8 -*-
"""
error_analisis.py
Un registro de la tabla de errores, y el catalogo de tipos de error.

Los tipos son los de la seccion 4.9 del enunciado, mas TOKEN_INESPERADO
para cualquier token que la gramatica no admita en su posicion (seccion 5
del documento de diseno).
"""

# Fases
FASE_LEXICA = 'Léxico'
FASE_SINTACTICA = 'Sintáctico'

# Tipos de error (seccion 4.9 del enunciado)
NEGRITA_SIN_CERRAR = 'NEGRITA_SIN_CERRAR'
CURSIVA_SIN_CERRAR = 'CURSIVA_SIN_CERRAR'
CODIGO_INLINE_SIN_CERRAR = 'CODIGO_INLINE_SIN_CERRAR'
BLOQUE_CODIGO_SIN_CERRAR = 'BLOQUE_CODIGO_SIN_CERRAR'
ENCABEZADO_INVALIDO = 'ENCABEZADO_INVALIDO'
INDENTACION_INVALIDA = 'INDENTACION_INVALIDA'
CITA_MAL_FORMADA = 'CITA_MAL_FORMADA'

# Tipo agregado (seccion 5 del documento de diseno)
TOKEN_INESPERADO = 'TOKEN_INESPERADO'

# Tipos del alcance opcional (D-31 y D-33)
TACHADO_SIN_CERRAR = 'TACHADO_SIN_CERRAR'
TABLA_MAL_FORMADA = 'TABLA_MAL_FORMADA'


class ErrorAnalisis:
    """
    numero       posicion en la tabla (la asigna el GestorErrores)
    lexema       texto que provoco el error
    tipo         una de las constantes de arriba
    descripcion  mensaje para el usuario, con linea y columna
    linea        linea donde empieza el problema
    columna      columna donde empieza el problema
    fase         FASE_LEXICA o FASE_SINTACTICA
    """

    def __init__(self, numero, lexema, tipo, descripcion, linea, columna,
                 fase):
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna
        self.fase = fase

    def esta_despues_de(self, otro):
        """
        True si este error aparece en el archivo DESPUES que 'otro'.
        Compara primero la linea y, si es la misma, la columna.
        """
        if self.linea > otro.linea:
            return True
        if self.linea == otro.linea:
            if self.columna > otro.columna:
                return True
        return False

    def como_texto(self):
        """
        Texto legible del error, para imprimir en consola.

        Se llama 'como_texto' y no 'descripcion' porque el atributo
        self.descripcion ya existe y guarda el mensaje del error.
        """
        return ('[E' + str(self.numero) + '] ' + self.fase + ' - ' +
                self.tipo + ': ' + self.descripcion)
