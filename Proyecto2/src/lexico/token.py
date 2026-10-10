# -*- coding: utf-8 -*-
"""
token.py
Clase Token y catalogo de tipos de token de MarkdownCheck.

Los tipos son cadenas constantes. Se declaran aqui una sola vez para que el
lexico, el parser y la interfaz usen exactamente el mismo nombre: si alguien
escribe 'VINETA' en vez de VINETA, Python avisa que la variable no existe en
lugar de fallar en silencio.
"""

# ----------------------------------------------------------------------
# Tipos de la tabla del enunciado (seccion 4.5)
# ----------------------------------------------------------------------
NUMERAL = 'NUMERAL'
VINETA = 'VIÑETA'
INDENT = 'INDENT'
DEDENT = 'DEDENT'
CITA = 'CITA'
CERCA_CODIGO = 'CERCA_CODIGO'
REGLA_HORIZONTAL = 'REGLA_HORIZONTAL'
NEGRITA = 'NEGRITA'
CURSIVA = 'CURSIVA'
CODIGO_INLINE = 'CODIGO_INLINE'
TEXTO = 'TEXTO'
SALTO_PARRAFO = 'SALTO_PARRAFO'

# ----------------------------------------------------------------------
# Tipos agregados (seccion 2.2 del documento de diseno, D-01 y D-12)
# ----------------------------------------------------------------------
SALTO_LINEA = 'SALTO_LINEA'
TEXTO_LITERAL = 'TEXTO_LITERAL'
LENGUAJE_CODIGO = 'LENGUAJE_CODIGO'
FIN = 'FIN'


class Token:
    """
    Un token reconocido por el AFD.

    numero   posicion del token en el orden en que se reconocio (1, 2, 3...)
    lexema   texto exacto del archivo; '' en los tokens virtuales
    tipo     una de las constantes de arriba
    linea    linea donde empieza el lexema (la primera es 1)
    columna  columna donde empieza el lexema (la primera es 1)
    """

    def __init__(self, numero, lexema, tipo, linea, columna):
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna

    def es(self, tipo):
        """True si el token es del tipo indicado. Lo usa mucho el parser."""
        return self.tipo == tipo

    def es_virtual(self):
        """
        Los tokens virtuales no tienen texto en el archivo: INDENT, DEDENT,
        FIN y el SALTO_LINEA que se agrega cuando la ultima linea no termina
        en '\\n' (D-01).
        """
        if self.tipo == INDENT or self.tipo == DEDENT or self.tipo == FIN:
            return True
        if self.lexema == '':
            if self.tipo == SALTO_LINEA or self.tipo == SALTO_PARRAFO:
                return True
        return False

    def lexema_visible(self):
        """
        Lexema listo para mostrarse en una tabla. Un salto de linea o un
        texto vacio no se ven en pantalla, asi que se reemplazan por una
        descripcion.
        """
        if self.es_virtual():
            return '(virtual)'
        if self.lexema == '\n':
            return '\\n'
        if self.lexema == '':
            return '(vacío)'
        return self.lexema

    def descripcion(self):
        """Texto legible del token, para imprimir en consola."""
        return ('[' + str(self.numero) + '] ' + self.tipo +
                ' -> ' + self.lexema_visible() +
                '  (linea ' + str(self.linea) +
                ', columna ' + str(self.columna) + ')')
