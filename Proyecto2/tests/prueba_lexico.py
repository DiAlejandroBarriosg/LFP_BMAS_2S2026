# -*- coding: utf-8 -*-
"""
prueba_lexico.py
Pruebas del AnalizadorLexico desde consola (Fase 2).

Uso, desde la carpeta Proyecto2:
    python tests/prueba_lexico.py

Cada verificacion imprime [OK] o [FALLO]. Al final se muestra el total y,
si algo fallo, el programa termina con codigo 1.

Notacion de las firmas: 'TIPO "lexema" linea:columna'. Por ejemplo
    'NEGRITA "**" 3:20'
es un token NEGRITA con lexema ** que empieza en la linea 3, columna 20.
"""

import os
import sys

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

from lexico.analizador_lexico import AnalizadorLexico
from lexico.token import NUMERAL, VINETA, INDENT, DEDENT, CITA
from lexico.token import CERCA_CODIGO, LENGUAJE_CODIGO, TEXTO_LITERAL
from lexico.token import REGLA_HORIZONTAL, NEGRITA, CURSIVA, CODIGO_INLINE
from lexico.token import TEXTO, SALTO_LINEA, SALTO_PARRAFO, FIN
from lexico.token import NUMERO_LISTA, CASILLA, TACHADO, CORCHETE_ABRE
from lexico.token import IMAGEN_ABRE, CORCHETE_CIERRA, PARENTESIS_ABRE, URL
from lexico.token import PARENTESIS_CIERRA, BARRA, SEPARADOR_TABLA
from errores.gestor_errores import GestorErrores
from errores import error_analisis as err


# ======================================================================
# Utilidades
# ======================================================================

class Verificador:
    """Cuenta las verificaciones correctas y fallidas, e imprime cada una."""

    def __init__(self):
        self.correctas = 0
        self.fallidas = 0

    def verificar(self, descripcion, obtenido, esperado):
        if obtenido == esperado:
            self.correctas = self.correctas + 1
            print('  [OK]    ' + descripcion)
        else:
            self.fallidas = self.fallidas + 1
            print('  [FALLO] ' + descripcion)
            print('          esperado: ' + str(esperado))
            print('          obtenido: ' + str(obtenido))


def analizar(texto):
    """Corre el lexico completo sobre un texto y devuelve el analizador."""
    gestor = GestorErrores()
    lexico = AnalizadorLexico(texto, gestor)
    lexico.analizar_todo()
    return lexico


def leer_ejemplo(nombre):
    ruta = os.path.join(CARPETA_PROYECTO, 'examples', nombre)
    archivo = open(ruta, 'r', encoding='utf-8-sig')
    texto = archivo.read()
    archivo.close()
    return texto


def firma(token):
    return (token.tipo + ' "' + token.lexema_visible() + '" ' +
            str(token.linea) + ':' + str(token.columna))


def firmas_de_linea(tokens, linea):
    """Firmas de los tokens que empiezan en una linea."""
    resultado = []
    i = 0
    while i < len(tokens):
        if tokens[i].linea == linea:
            resultado.append(firma(tokens[i]))
        i = i + 1
    return resultado


def tipos(tokens):
    resultado = []
    i = 0
    while i < len(tokens):
        resultado.append(tokens[i].tipo)
        i = i + 1
    return resultado


def tipos_entre_lineas(tokens, desde, hasta):
    resultado = []
    i = 0
    while i < len(tokens):
        if tokens[i].linea >= desde and tokens[i].linea <= hasta:
            resultado.append(tokens[i].tipo)
        i = i + 1
    return resultado


def contar(tokens, tipo):
    total = 0
    i = 0
    while i < len(tokens):
        if tokens[i].tipo == tipo:
            total = total + 1
        i = i + 1
    return total


def resumen_errores(gestor):
    """Cada error como 'TIPO linea:columna', en el orden de la tabla."""
    resultado = []
    i = 0
    while i < len(gestor.errores):
        e = gestor.errores[i]
        resultado.append(e.tipo + ' ' + str(e.linea) + ':' + str(e.columna))
        i = i + 1
    return resultado


def titulo(texto):
    print('')
    print(texto)
    print('-' * len(texto))


# ======================================================================
# A. Archivo valido del enunciado (seccion 4.7)
# ======================================================================

def prueba_ejemplo_valido(v):
    titulo('A. ejemplo_valido.md (archivo de la seccion 4.7 del enunciado)')
    lexico = analizar(leer_ejemplo('ejemplo_valido.md'))
    tokens = lexico.tokens

    v.verificar('sin errores lexicos', lexico.gestor.cantidad(), 0)
    v.verificar('77 tokens en total', len(tokens), 77)

    consecutivos = True
    i = 0
    while i < len(tokens):
        if tokens[i].numero != i + 1:
            consecutivos = False
        i = i + 1
    v.verificar('numeracion consecutiva 1..77', consecutivos, True)

    v.verificar('linea 1: encabezado H1', firmas_de_linea(tokens, 1), [
        'NUMERAL "#" 1:1',
        'TEXTO "Proyecto de Lenguajes Formales" 1:3',
        'SALTO_LINEA "\\n" 1:33',
    ])

    v.verificar('linea 2: linea vacia', firmas_de_linea(tokens, 2), [
        'SALTO_PARRAFO "\\n" 2:1',
    ])

    v.verificar('linea 3: negrita, cursiva y codigo en linea, columna exacta',
                firmas_de_linea(tokens, 3), [
                    'TEXTO "Este curso combina " 3:1',
                    'NEGRITA "**" 3:20',
                    'TEXTO "teoría sólida" 3:22',
                    'NEGRITA "**" 3:35',
                    'TEXTO " y " 3:37',
                    'CURSIVA "*" 3:40',
                    'TEXTO "práctica de código" 3:41',
                    'CURSIVA "*" 3:59',
                    'TEXTO ", con ejemplos en " 3:60',
                    'CODIGO_INLINE "`" 3:78',
                    'TEXTO_LITERAL "Python" 3:79',
                    'CODIGO_INLINE "`" 3:85',
                    'TEXTO " ." 3:86',
                    'SALTO_LINEA "\\n" 3:88',
                ])

    v.verificar('lineas 7 a 14: lista de 3 niveles con INDENT/DEDENT',
                tipos_entre_lineas(tokens, 7, 14), [
                    VINETA, TEXTO, SALTO_LINEA,
                    INDENT, VINETA, TEXTO, SALTO_LINEA,
                    VINETA, TEXTO, SALTO_LINEA,
                    DEDENT, VINETA, TEXTO, SALTO_LINEA,
                    INDENT, VINETA, TEXTO, SALTO_LINEA,
                    INDENT, VINETA, TEXTO, SALTO_LINEA,
                    VINETA, TEXTO, SALTO_LINEA,
                    DEDENT, DEDENT, VINETA, TEXTO, SALTO_LINEA,
                ])

    v.verificar('linea 12: INDENT del tercer nivel en la columna 3',
                firmas_de_linea(tokens, 12)[0], 'INDENT "(virtual)" 12:3')
    v.verificar('8 viñetas', contar(tokens, VINETA), 8)
    v.verificar('INDENT y DEDENT balanceados (3 y 3)',
                [contar(tokens, INDENT), contar(tokens, DEDENT)], [3, 3])

    v.verificar('lineas 16 y 17: cita de nivel 1 y de nivel 2',
                [firmas_de_linea(tokens, 16)[0],
                 firmas_de_linea(tokens, 17)[0]],
                ['CITA ">" 16:1', 'CITA ">>" 17:1'])

    v.verificar('lineas 19 a 22: bloque de codigo en modo literal',
                firmas_de_linea(tokens, 19) + firmas_de_linea(tokens, 20) +
                firmas_de_linea(tokens, 21) + firmas_de_linea(tokens, 22), [
                    'CERCA_CODIGO "```" 19:1',
                    'LENGUAJE_CODIGO "python" 19:4',
                    'SALTO_LINEA "\\n" 19:10',
                    'TEXTO_LITERAL "def hola():" 20:1',
                    'SALTO_LINEA "\\n" 20:12',
                    'TEXTO_LITERAL "    print("Hola LFP")" 21:1',
                    'SALTO_LINEA "\\n" 21:22',
                    'CERCA_CODIGO "```" 22:1',
                    'SALTO_LINEA "\\n" 22:4',
                ])

    v.verificar('linea 24: regla horizontal', firmas_de_linea(tokens, 24), [
        'REGLA_HORIZONTAL "---" 24:1',
        'SALTO_LINEA "\\n" 24:4',
    ])
    v.verificar('el ultimo token es FIN', tokens[len(tokens) - 1].tipo, FIN)


# ======================================================================
# B. Reglas de prioridad (seccion 4.5 del enunciado)
# ======================================================================

def prueba_prioridades(v):
    titulo('B. Reglas de prioridad y ambiguedades')

    v.verificar('"#sinespacio" es TEXTO, no NUMERAL',
                tipos(analizar('#sinespacio\n').tokens),
                [TEXTO, SALTO_LINEA, FIN])
    v.verificar('"## Titulo" es NUMERAL de nivel 2',
                firma(analizar('## Titulo\n').tokens[0]), 'NUMERAL "##" 1:1')

    v.verificar('"* item" al inicio de linea es VIÑETA',
                tipos(analizar('* item\n').tokens),
                [VINETA, TEXTO, SALTO_LINEA, FIN])
    v.verificar('"*cursiva*" al inicio de linea es CURSIVA',
                tipos(analizar('*cursiva*\n').tokens),
                [CURSIVA, TEXTO, CURSIVA, SALTO_LINEA, FIN])
    v.verificar('"+ item" es VIÑETA', analizar('+ item\n').tokens[0].tipo,
                VINETA)

    v.verificar('maximal munch: "**" es NEGRITA, no dos CURSIVA',
                tipos(analizar('**negrita**\n').tokens),
                [NEGRITA, TEXTO, NEGRITA, SALTO_LINEA, FIN])

    v.verificar('"---" es REGLA_HORIZONTAL',
                tipos(analizar('---\n').tokens),
                [REGLA_HORIZONTAL, SALTO_LINEA, FIN])
    v.verificar('"- - -" es VIÑETA seguida de texto',
                tipos(analizar('- - -\n').tokens),
                [VINETA, TEXTO, SALTO_LINEA, FIN])
    v.verificar('"--" es TEXTO', tipos(analizar('--\n').tokens),
                [TEXTO, SALTO_LINEA, FIN])
    v.verificar('"---texto" es TEXTO', tipos(analizar('---texto\n').tokens),
                [TEXTO, SALTO_LINEA, FIN])

    lexico = analizar('***ambas***\n')
    v.verificar('"***ambas***" abre negrita+cursiva y las cierra en orden',
                tipos(lexico.tokens),
                [NEGRITA, CURSIVA, TEXTO, CURSIVA, NEGRITA, SALTO_LINEA, FIN])
    v.verificar('"***ambas***" no produce errores', lexico.gestor.cantidad(),
                0)

    v.verificar('cursiva dentro de negrita',
                tipos(analizar('**a *b* c**\n').tokens),
                [NEGRITA, TEXTO, CURSIVA, TEXTO, CURSIVA, TEXTO, NEGRITA,
                 SALTO_LINEA, FIN])
    v.verificar('"***" final con cursiva en la cima: primero cierra la '
                'cursiva',
                tipos(analizar('**negrita *y cursiva***\n').tokens),
                [NEGRITA, TEXTO, CURSIVA, TEXTO, CURSIVA, NEGRITA,
                 SALTO_LINEA, FIN])
    v.verificar('"***" final con negrita en la cima: maximal munch normal',
                tipos(analizar('*cursiva **y negrita***\n').tokens),
                [CURSIVA, TEXTO, NEGRITA, TEXTO, NEGRITA, CURSIVA,
                 SALTO_LINEA, FIN])

    lexico = analizar('***a** b*\n')
    v.verificar('"***" inicial que se cierra con "**" y luego "*": la '
                'cursiva va afuera', tipos(lexico.tokens),
                [CURSIVA, NEGRITA, TEXTO, NEGRITA, TEXTO, CURSIVA,
                 SALTO_LINEA, FIN])
    v.verificar('... y no produce errores', lexico.gestor.cantidad(), 0)
    v.verificar('"***" inicial que se cierra con "*" y luego "**": la '
                'negrita va afuera', tipos(analizar('***a* b**\n').tokens),
                [NEGRITA, CURSIVA, TEXTO, CURSIVA, TEXTO, NEGRITA,
                 SALTO_LINEA, FIN])
    v.verificar('"***" inicial que nunca se cierra: los dos errores',
                resumen_errores(analizar('***a\n').gestor),
                ['NEGRITA_SIN_CERRAR 1:1', 'CURSIVA_SIN_CERRAR 1:3'])

    lexico = analizar('`**no es negrita**`\n')
    v.verificar('dentro de codigo en linea no se reconoce "**"',
                tipos(lexico.tokens),
                [CODIGO_INLINE, TEXTO_LITERAL, CODIGO_INLINE, SALTO_LINEA,
                 FIN])
    v.verificar('el contenido del codigo en linea queda literal',
                lexico.tokens[1].lexema, '**no es negrita**')

    v.verificar('"> >" y ">>" son la misma cita de nivel 2',
                [analizar('> > dos\n').tokens[0].lexema,
                 analizar('>> dos\n').tokens[0].lexema], ['> >', '>>'])
    v.verificar('">>>" es una cita de nivel 3',
                firma(analizar('>>> tres\n').tokens[0]), 'CITA ">>>" 1:1')
    v.verificar('una cita puede contener un encabezado',
                tipos(analizar('> # Titulo\n').tokens),
                [CITA, NUMERAL, TEXTO, SALTO_LINEA, FIN])

    lexico = analizar('>pegado\n')
    v.verificar('">pegado": el lexico no reporta (CITA_MAL_FORMADA es del '
                'parser)', lexico.gestor.cantidad(), 0)
    v.verificar('">pegado": el texto queda en la columna siguiente al ">"',
                firma(lexico.tokens[1]), 'TEXTO "pegado" 1:2')


# ======================================================================
# C. Errores lexicos (seccion 4.9 del enunciado)
# ======================================================================

def prueba_errores_lexicos(v):
    titulo('C. Errores lexicos y recuperacion (errores_lexicos.md)')
    lexico = analizar(leer_ejemplo('errores_lexicos.md'))
    gestor = lexico.gestor

    v.verificar('se detectan los 6 errores en una sola pasada',
                resumen_errores(gestor), [
                    'NEGRITA_SIN_CERRAR 3:20',
                    'CURSIVA_SIN_CERRAR 5:17',
                    'CODIGO_INLINE_SIN_CERRAR 7:10',
                    'ENCABEZADO_INVALIDO 9:1',
                    'INDENTACION_INVALIDA 12:4',
                    'BLOQUE_CODIGO_SIN_CERRAR 14:1',
                ])

    todos_lexicos = True
    i = 0
    while i < len(gestor.errores):
        if gestor.errores[i].fase != err.FASE_LEXICA:
            todos_lexicos = False
        i = i + 1
    v.verificar('los 6 son de fase lexica', todos_lexicos, True)

    v.verificar('el analisis continua hasta FIN despues de los errores',
                lexico.tokens[len(lexico.tokens) - 1].tipo, FIN)

    v.verificar('mensaje de NEGRITA_SIN_CERRAR (formato del enunciado)',
                gestor.errores[0].descripcion,
                'Negrita sin cerrar iniciada en línea 3, columna 20')
    v.verificar('mensaje de CURSIVA_SIN_CERRAR',
                gestor.errores[1].descripcion,
                'Cursiva sin cerrar iniciada en línea 5, columna 17')
    v.verificar('mensaje de CODIGO_INLINE_SIN_CERRAR',
                gestor.errores[2].descripcion,
                'Código en línea sin cerrar iniciado en línea 7, '
                'columna 10')
    v.verificar('mensaje de ENCABEZADO_INVALIDO',
                gestor.errores[3].descripcion,
                'Encabezado inválido en línea 9: máximo 6 niveles')
    v.verificar('mensaje de BLOQUE_CODIGO_SIN_CERRAR',
                gestor.errores[5].descripcion,
                'Bloque de código sin cerrar iniciado en línea 14')

    v.verificar('el "**" sin cerrar se reclasifica como TEXTO',
                firmas_de_linea(lexico.tokens, 3)[1], 'TEXTO "**" 3:20')
    v.verificar('el "#######" invalido queda como texto de la linea',
                firmas_de_linea(lexico.tokens, 9)[0],
                'TEXTO "####### Siete numerales no es un encabezado válido" '
                '9:1')

    lexico = analizar('**a `b\n')
    v.verificar('la tabla queda ordenada por posicion aunque el error de '
                'codigo se detecte primero', resumen_errores(lexico.gestor),
                ['NEGRITA_SIN_CERRAR 1:1', 'CODIGO_INLINE_SIN_CERRAR 1:5'])

    lexico = analizar('Usa `sin cierre y **esto si**\n')
    v.verificar('tras un "`" sin cierre, la negrita de la misma linea se '
                'sigue reconociendo', contar(lexico.tokens, NEGRITA), 2)


# ======================================================================
# D. Indentacion: INDENT y DEDENT
# ======================================================================

def prueba_indentacion(v):
    titulo('D. INDENT / DEDENT')

    v.verificar('3 niveles y cierre de todos los niveles al final',
                tipos(analizar('- a\n  - b\n    - c\n').tokens),
                [VINETA, TEXTO, SALTO_LINEA,
                 INDENT, VINETA, TEXTO, SALTO_LINEA,
                 INDENT, VINETA, TEXTO, SALTO_LINEA,
                 DEDENT, DEDENT, FIN])

    lexico = analizar('- a\n    - b\n')
    v.verificar('salto de 0 a 4 espacios: emite DOS INDENT',
                contar(lexico.tokens, INDENT), 2)
    v.verificar('salto de 0 a 4 espacios: el lexico no lo reporta (lo '
                'reporta el parser, D-06)', lexico.gestor.cantidad(), 0)

    v.verificar('una linea vacia cierra la lista',
                tipos(analizar('- a\n  - b\n\ntexto\n').tokens),
                [VINETA, TEXTO, SALTO_LINEA,
                 INDENT, VINETA, TEXTO, SALTO_LINEA,
                 DEDENT, SALTO_PARRAFO, TEXTO, SALTO_LINEA, FIN])

    v.verificar('una linea de texto cierra la lista',
                tipos(analizar('- a\n  - b\ntexto\n').tokens),
                [VINETA, TEXTO, SALTO_LINEA,
                 INDENT, VINETA, TEXTO, SALTO_LINEA,
                 DEDENT, TEXTO, SALTO_LINEA, FIN])

    lexico = analizar('- a\n\t- b\n')
    v.verificar('un tabulador en la sangria vale un nivel',
                [contar(lexico.tokens, INDENT), lexico.gestor.cantidad()],
                [1, 0])

    lexico = analizar('- a\n   - b\n')
    v.verificar('sangria de 3 espacios: INDENTACION_INVALIDA lexica',
                resumen_errores(lexico.gestor),
                ['INDENTACION_INVALIDA 2:4'])
    v.verificar('sangria de 3 espacios: se toma el nivel 1',
                contar(lexico.tokens, INDENT), 1)


# ======================================================================
# E. Bloques de codigo (modo literal)
# ======================================================================

def prueba_bloques_codigo(v):
    titulo('E. Bloques de codigo')

    lexico = analizar('```\n# no\n**sin cerrar\n```\n')
    v.verificar('el contenido no se tokeniza',
                tipos(lexico.tokens),
                [CERCA_CODIGO, SALTO_LINEA,
                 TEXTO_LITERAL, SALTO_LINEA,
                 TEXTO_LITERAL, SALTO_LINEA,
                 CERCA_CODIGO, SALTO_LINEA, FIN])
    v.verificar('un "**" sin cerrar dentro del bloque no es error',
                lexico.gestor.cantidad(), 0)

    lexico = analizar('```\na\n\nb\n```\n')
    v.verificar('una linea vacia dentro del bloque es TEXTO_LITERAL vacio',
                firmas_de_linea(lexico.tokens, 3),
                ['TEXTO_LITERAL "(vacío)" 3:1', 'SALTO_LINEA "\\n" 3:1'])

    lexico = analizar('```\n```python\n```\n')
    v.verificar('solo "```" exacto cierra el bloque',
                firma(lexico.tokens[2]), 'TEXTO_LITERAL "```python" 2:1')
    v.verificar('... y el bloque si se cierra en la linea 3',
                lexico.gestor.cantidad(), 0)

    lexico = analizar('```\n    x = 1\n```\n')
    v.verificar('la sangria del contenido se conserva',
                lexico.tokens[2].lexema, '    x = 1')


# ======================================================================
# F. Robustez
# ======================================================================

def prueba_robustez(v):
    titulo('F. Robustez del recorrido')

    lexico = analizar('# Hola')
    v.verificar('archivo sin "\\n" final: SALTO_LINEA virtual y FIN',
                [firma(lexico.tokens[2]), lexico.tokens[3].tipo],
                ['SALTO_LINEA "(virtual)" 1:7', FIN])

    con_lf = analizar('# Hola\nmundo\n')
    con_crlf = analizar('# Hola\r\nmundo\r\n')
    iguales = len(con_lf.tokens) == len(con_crlf.tokens)
    i = 0
    while iguales and i < len(con_lf.tokens):
        if firma(con_lf.tokens[i]) != firma(con_crlf.tokens[i]):
            iguales = False
        i = i + 1
    v.verificar('un archivo de Windows (\\r\\n) da los mismos tokens',
                iguales, True)

    v.verificar('la marca BOM inicial se ignora',
                firma(analizar('﻿# Hola\n').tokens[0]),
                'NUMERAL "#" 1:1')

    v.verificar('archivo vacio: solo FIN', tipos(analizar('').tokens), [FIN])

    gestor = GestorErrores()
    lexico = AnalizadorLexico('hola\n', gestor)
    lexico.analizar_todo()
    total = len(lexico.tokens)
    otra = lexico.siguiente_token()
    v.verificar('despues de FIN, siguiente_token() devuelve el mismo FIN',
                [otra.tipo, otra.numero, len(lexico.tokens)],
                [FIN, total, total])

    lexico = analizar(leer_ejemplo('casos_borde.md'))
    v.verificar('casos_borde.md no tiene errores lexicos',
                lexico.gestor.cantidad(), 0)


# ======================================================================
# G. Precision de lexema, linea y columna (criterio 2.3 del enunciado)
# ======================================================================

def prueba_precision(v):
    titulo('G. Cada token esta en su linea y columna exactas')
    carpetas = [os.path.join(CARPETA_PROYECTO, 'examples'),
                os.path.join(CARPETA_PROYECTO, 'examples', 'casos')]
    archivos = 0
    revisados = 0
    mal_ubicados = 0
    perdidos = 0
    c = 0
    while c < len(carpetas):
        nombres = os.listdir(carpetas[c])
        i = 0
        while i < len(nombres):
            ruta = os.path.join(carpetas[c], nombres[i])
            if os.path.isfile(ruta) and termina_en(nombres[i], '.md'):
                archivo = open(ruta, 'r', encoding='utf-8-sig')
                texto = archivo.read()
                archivo.close()
                resultado = revisar_posiciones(texto)
                archivos = archivos + 1
                revisados = revisados + resultado[0]
                mal_ubicados = mal_ubicados + resultado[1]
                perdidos = perdidos + resultado[2]
            i = i + 1
        c = c + 1

    print('          (' + str(revisados) + ' tokens de ' + str(archivos) +
          ' archivos)')
    v.verificar('el lexema de cada token esta en el archivo en su linea y '
                'columna', mal_ubicados, 0)
    v.verificar('ningun caracter visible del archivo queda sin token',
                perdidos, 0)


def revisar_posiciones(texto):
    """
    Devuelve [tokens revisados, tokens fuera de lugar, caracteres perdidos].
    Un token esta en su lugar si su lexema aparece letra por letra en el
    archivo a partir de su linea y columna. Un caracter visible (que no es
    espacio ni tabulacion) se pierde si ningun token lo cubre.
    """
    lexico = analizar(texto)
    lineas = lineas_de(texto)
    cubierto = []
    n = 0
    while n < len(lineas):
        fila = []
        k = 0
        while k < len(lineas[n]):
            fila.append(False)
            k = k + 1
        cubierto.append(fila)
        n = n + 1

    revisados = 0
    mal_ubicados = 0
    i = 0
    while i < len(lexico.tokens):
        token = lexico.tokens[i]
        if not token.es_virtual():
            revisados = revisados + 1
            if not esta_en_su_lugar(lineas, token):
                mal_ubicados = mal_ubicados + 1
            else:
                fila = cubierto[token.linea - 1]
                k = 0
                while k < len(token.lexema):
                    columna = token.columna - 1 + k
                    if columna < len(fila):
                        fila[columna] = True
                    k = k + 1
        i = i + 1

    perdidos = 0
    n = 0
    while n < len(lineas):
        k = 0
        while k < len(lineas[n]):
            c = lineas[n][k]
            if c != ' ' and c != '\t' and not cubierto[n][k]:
                perdidos = perdidos + 1
            k = k + 1
        n = n + 1
    return [revisados, mal_ubicados, perdidos]


def esta_en_su_lugar(lineas, token):
    if token.linea < 1 or token.linea > len(lineas):
        return False
    linea = lineas[token.linea - 1] + '\n'
    k = 0
    while k < len(token.lexema):
        columna = token.columna - 1 + k
        if columna >= len(linea) or linea[columna] != token.lexema[k]:
            return False
        k = k + 1
    return True


def lineas_de(texto):
    """Lineas del texto sin '\r' ni '\n', como las numera el analizador."""
    lineas = []
    actual = ''
    i = 0
    while i < len(texto):
        c = texto[i]
        if c == '\n':
            lineas.append(actual)
            actual = ''
        elif c != '\r':
            actual = actual + c
        i = i + 1
    lineas.append(actual)
    return lineas


def termina_en(nombre, final):
    if len(nombre) < len(final):
        return False
    inicio = len(nombre) - len(final)
    k = 0
    while k < len(final):
        if nombre[inicio + k] != final[k]:
            return False
        k = k + 1
    return True


# ======================================================================
# H. Delimitadores en varias lineas de un parrafo (D-02)
# ======================================================================

def prueba_delimitadores_de_parrafo(v):
    titulo('H. Un delimitador se cierra dentro de su bloque (D-02)')

    lexico = analizar('Un parrafo con **negrita que\ncontinua aqui** y '
                      'termina.\n')
    v.verificar('una negrita que se cierra en la linea siguiente del '
                'parrafo', tipos(lexico.tokens),
                [TEXTO, NEGRITA, TEXTO, SALTO_LINEA, TEXTO, NEGRITA, TEXTO,
                 SALTO_LINEA, FIN])
    v.verificar('... no es error', lexico.gestor.cantidad(), 0)
    v.verificar('una cursiva que cruza dos lineas',
                tipos(analizar('a *b\nc* d\n').tokens),
                [TEXTO, CURSIVA, TEXTO, SALTO_LINEA, TEXTO, CURSIVA, TEXTO,
                 SALTO_LINEA, FIN])

    lexico = analizar('a `b\n  c` d\n')
    v.verificar('un codigo en linea que cruza dos lineas: un TEXTO_LITERAL '
                'por linea', tipos(lexico.tokens),
                [TEXTO, CODIGO_INLINE, TEXTO_LITERAL, SALTO_LINEA,
                 TEXTO_LITERAL, CODIGO_INLINE, TEXTO, SALTO_LINEA, FIN])
    v.verificar('... la sangria de la segunda linea no es parte del codigo',
                firma(lexico.tokens[4]), 'TEXTO_LITERAL "c" 2:3')

    lexico = analizar('a **b\nc d\n\nx\n')
    v.verificar('si el parrafo termina sin cierre: error en la apertura',
                resumen_errores(lexico.gestor), ['NEGRITA_SIN_CERRAR 1:3'])
    v.verificar('... y el "**" pasa a ser TEXTO',
                firma(lexico.tokens[1]), 'TEXTO "**" 1:3')

    v.verificar('un encabezado en la linea siguiente termina el parrafo',
                resumen_errores(analizar('a **b\n# c**\n').gestor),
                ['NEGRITA_SIN_CERRAR 1:3', 'NEGRITA_SIN_CERRAR 2:4'])
    v.verificar('un item de lista es de una sola linea',
                resumen_errores(analizar('- a **b\n  c**\n').gestor),
                ['NEGRITA_SIN_CERRAR 1:5', 'NEGRITA_SIN_CERRAR 2:4'])
    v.verificar('cada linea de cita es su propio bloque (D-10)',
                resumen_errores(analizar('> a *b\n> c*\n').gestor),
                ['CURSIVA_SIN_CERRAR 1:5', 'CURSIVA_SIN_CERRAR 2:4'])
    v.verificar('un "`" no busca su cierre en el item de la linea '
                'siguiente', resumen_errores(analizar('a `b\n- c`\n').gestor),
                ['CODIGO_INLINE_SIN_CERRAR 1:3',
                 'CODIGO_INLINE_SIN_CERRAR 2:4'])
    v.verificar('"####### x" no es encabezado: el parrafo sigue',
                resumen_errores(analizar('**a\n####### b**\n').gestor),
                ['ENCABEZADO_INVALIDO 2:1'])


# ======================================================================
# I. Alcance opcional (seccion 3.5 del diseno, D-29 a D-33)
# ======================================================================

def prueba_alcance_opcional(v):
    titulo('I. Tokens del alcance opcional')

    lexico = analizar('1. uno\n10. diez\n')
    v.verificar('"1. " y "10. " son NUMERO_LISTA',
                [firma(lexico.tokens[0]), firma(lexico.tokens[3])],
                ['NUMERO_LISTA "1." 1:1', 'NUMERO_LISTA "10." 2:1'])
    v.verificar('"2024.fue" y "3.5 es" son texto, no items',
                [tipos(analizar('2024.fue\n').tokens),
                 tipos(analizar('3.5 es\n').tokens)],
                [[TEXTO, SALTO_LINEA, FIN], [TEXTO, SALTO_LINEA, FIN]])
    v.verificar('un item numerado con sangria emite INDENT como la viñeta',
                tipos(analizar('1. a\n  2. b\n').tokens),
                [NUMERO_LISTA, TEXTO, SALTO_LINEA, INDENT, NUMERO_LISTA,
                 TEXTO, SALTO_LINEA, DEDENT, FIN])

    lexico = analizar('- [x] hecho\n- [ ] falta\n1. [X] numerada\n')
    v.verificar('"[x]", "[ ]" y "[X]" despues del marcador son CASILLA',
                [firma(lexico.tokens[1]), firma(lexico.tokens[5]),
                 firma(lexico.tokens[9])],
                ['CASILLA "[x]" 1:3', 'CASILLA "[ ]" 2:3',
                 'CASILLA "[X]" 3:4'])
    v.verificar('"- [x](u)" es un enlace, no una casilla',
                tipos(analizar('- [x](u)\n').tokens),
                [VINETA, CORCHETE_ABRE, TEXTO, CORCHETE_CIERRA,
                 PARENTESIS_ABRE, URL, PARENTESIS_CIERRA, SALTO_LINEA, FIN])

    v.verificar('"~~" es TACHADO y pasa por la pila',
                tipos(analizar('a ~~b~~ c\n').tokens),
                [TEXTO, TACHADO, TEXTO, TACHADO, TEXTO, SALTO_LINEA, FIN])
    v.verificar('un "~" solo es texto',
                tipos(analizar('~a~ y 5~6\n').tokens), [TEXTO, SALTO_LINEA,
                                                         FIN])
    v.verificar('tachado sin cerrar: error en su apertura',
                resumen_errores(analizar('a ~~b\n').gestor),
                ['TACHADO_SIN_CERRAR 1:3'])
    lexico = analizar('~~***a** b*~~\n')
    v.verificar('"***" que abre dentro de un tachado sigue la regla D-04',
                [tipos(lexico.tokens), lexico.gestor.cantidad()],
                [[TACHADO, CURSIVA, NEGRITA, TEXTO, NEGRITA, TEXTO, CURSIVA,
                  TACHADO, SALTO_LINEA, FIN], 0])

    lexico = analizar('ver [la *doc*](https://x.org) fin\n')
    v.verificar('enlace completo: corchetes, contenido en linea y destino',
                tipos(lexico.tokens),
                [TEXTO, CORCHETE_ABRE, TEXTO, CURSIVA, TEXTO, CURSIVA,
                 CORCHETE_CIERRA, PARENTESIS_ABRE, URL, PARENTESIS_CIERRA,
                 TEXTO, SALTO_LINEA, FIN])
    v.verificar('la URL en su posicion exacta', firma(lexico.tokens[8]),
                'URL "https://x.org" 1:16')
    v.verificar('un "[" sin enlace completo es texto, sin error',
                [tipos(analizar('[a b](c d) y [e]\n').tokens),
                 analizar('[sin cierre\n').gestor.cantidad()],
                [[TEXTO, TEXTO, SALTO_LINEA, FIN], 0])
    v.verificar('"[a [b](u)": el primer "[" es texto y el segundo enlace',
                tipos(analizar('[a [b](u)\n').tokens),
                [TEXTO, CORCHETE_ABRE, TEXTO, CORCHETE_CIERRA,
                 PARENTESIS_ABRE, URL, PARENTESIS_CIERRA, SALTO_LINEA, FIN])
    v.verificar('un "]" dentro de codigo no cierra el enlace',
                contar(analizar('[a `]` b](u)\n').tokens, CORCHETE_CIERRA),
                1)
    v.verificar('el texto del enlace es un ambito: "[**a](u)**" da dos '
                'errores', resumen_errores(analizar('[**a](u)**\n').gestor),
                ['NEGRITA_SIN_CERRAR 1:2', 'NEGRITA_SIN_CERRAR 1:9'])
    v.verificar('"[t]()": destino vacio, sin URL',
                tipos(analizar('[t]()\n').tokens),
                [CORCHETE_ABRE, TEXTO, CORCHETE_CIERRA, PARENTESIS_ABRE,
                 PARENTESIS_CIERRA, SALTO_LINEA, FIN])

    lexico = analizar('![logo **x**](img/a.png)\n')
    v.verificar('imagen: el texto alternativo es un TEXTO_LITERAL',
                [tipos(lexico.tokens), firma(lexico.tokens[1])],
                [[IMAGEN_ABRE, TEXTO_LITERAL, CORCHETE_CIERRA,
                  PARENTESIS_ABRE, URL, PARENTESIS_CIERRA, SALTO_LINEA, FIN],
                 'TEXTO_LITERAL "logo **x**" 1:3'])

    lexico = analizar('| A | B |\n|:-|-:|\n')
    v.verificar('fila de tabla: BARRA por cada "|", y la fila separadora '
                'es un solo token', tipos(lexico.tokens),
                [BARRA, TEXTO, BARRA, TEXTO, BARRA, SALTO_LINEA,
                 SEPARADOR_TABLA, SALTO_LINEA, FIN])
    v.verificar('... el SEPARADOR_TABLA en su posicion',
                firma(lexico.tokens[6]), 'SEPARADOR_TABLA "|:-|-:|" 2:1')
    v.verificar('"|-:-|" no es fila separadora: es una fila',
                tipos(analizar('|-:-|\n').tokens),
                [BARRA, TEXTO, BARRA, SALTO_LINEA, FIN])
    v.verificar('cada celda es un bloque: "| **a | b** |" da dos errores',
                resumen_errores(analizar('| **a | b** |\n').gestor),
                ['NEGRITA_SIN_CERRAR 1:3', 'NEGRITA_SIN_CERRAR 1:10'])
    v.verificar('fuera de una tabla, "|" es texto',
                tipos(analizar('a | b\n').tokens), [TEXTO, SALTO_LINEA, FIN])
    v.verificar('un item numerado termina el parrafo anterior (D-02)',
                resumen_errores(analizar('texto **a\n1. b**\n').gestor),
                ['NEGRITA_SIN_CERRAR 1:7', 'NEGRITA_SIN_CERRAR 2:5'])


# ======================================================================

def main():
    v = Verificador()
    prueba_ejemplo_valido(v)
    prueba_prioridades(v)
    prueba_errores_lexicos(v)
    prueba_indentacion(v)
    prueba_bloques_codigo(v)
    prueba_robustez(v)
    prueba_precision(v)
    prueba_delimitadores_de_parrafo(v)
    prueba_alcance_opcional(v)

    print('')
    print('=' * 60)
    total = v.correctas + v.fallidas
    print('Verificaciones: ' + str(total) + '   correctas: ' +
          str(v.correctas) + '   fallidas: ' + str(v.fallidas))
    print('=' * 60)
    if v.fallidas > 0:
        sys.exit(1)


main()
