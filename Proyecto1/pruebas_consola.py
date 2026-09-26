# -*- coding: utf-8 -*-
"""
pruebas_consola.py
Verificacion del motor lexico ANTES de integrarlo con la GUI.

Uso:
    python pruebas_consola.py entradas/horario_valido.hor
    python pruebas_consola.py            (corre los dos archivos de ejemplo)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analizador.analizador_lexico import AnalizadorLexico
from analizador import alfabeto as alf


# --------------------------------------------------------------------------
# Ayudas para alinear columnas en consola, escritas a mano
# --------------------------------------------------------------------------

def rellenar(texto, ancho):
    """Agrega espacios a la DERECHA hasta que el texto mida 'ancho'."""
    resultado = str(texto)
    while len(resultado) < ancho:
        resultado = resultado + ' '
    return resultado


def alinear_derecha(texto, ancho):
    """Agrega espacios a la IZQUIERDA hasta que el texto mida 'ancho'."""
    resultado = str(texto)
    while len(resultado) < ancho:
        resultado = ' ' + resultado
    return resultado


def recortar(texto, maximo):
    """Si el texto pasa del maximo, lo corta y agrega tres puntos."""
    if len(texto) <= maximo:
        return texto
    resultado = ''
    i = 0
    while i < maximo - 3:
        resultado = resultado + texto[i]
        i = i + 1
    return resultado + '...'



def leer_archivo(ruta):
    archivo = open(ruta, 'r', encoding='utf-8', newline='')
    contenido = archivo.read()
    archivo.close()
    return contenido


def imprimir_tokens(tokens):
    print('')
    print('TABLA DE TOKENS  (' + str(len(tokens)) + ')')
    print('-' * 92)
    print(rellenar('No.', 6) + rellenar('Lexema', 43) + rellenar('Tipo', 23) +
          alinear_derecha('Linea', 6) + alinear_derecha('Columna', 9))
    print('-' * 92)
    for t in tokens:
        print(rellenar(t.numero, 6) + rellenar(recortar(t.lexema, 40), 43) +
              rellenar(t.tipo, 23) + alinear_derecha(t.linea, 6) +
              alinear_derecha(t.columna, 9))


def imprimir_errores(gestor):
    print('')
    print('TABLA DE ERRORES LEXICOS  (' + str(gestor.total()) + ')')
    print('-' * 92)
    if not gestor.hay_errores():
        print('Sin errores.')
        return
    print(rellenar('No.', 6) + rellenar('Lexema', 25) + rellenar('Tipo', 25) +
          alinear_derecha('Linea', 6) + alinear_derecha('Columna', 9))
    print('-' * 92)
    for e in gestor.errores:
        print(rellenar(e.numero, 6) + rellenar(recortar(e.lexema, 22), 25) +
              rellenar(e.tipo, 25) + alinear_derecha(e.linea, 6) +
              alinear_derecha(e.columna, 9))
    print('')
    for e in gestor.errores:
        print('  E' + str(e.numero) + ': ' + e.descripcion)


def imprimir_resumen(analizador):
    print('')
    print('FRECUENCIA POR TIPO DE TOKEN')
    print('-' * 92)
    conteo = analizador.contar_por_tipo()
    tipos = alf.claves_ordenadas(conteo)
    i = 0
    while i < len(tipos):
        tipo = tipos[i]
        print('  ' + rellenar(tipo, 25) + alinear_derecha(conteo[tipo], 4))
        i = i + 1


def procesar(ruta):
    print('')
    print('=' * 92)
    print('ARCHIVO: ' + ruta)
    print('=' * 92)
    contenido = leer_archivo(ruta)
    analizador = AnalizadorLexico()
    analizador.analizar(contenido)
    imprimir_tokens(analizador.tokens)
    imprimir_errores(analizador.gestor)
    imprimir_resumen(analizador)


def main():
    if len(sys.argv) > 1:
        procesar(sys.argv[1])
        return
    base = os.path.dirname(os.path.abspath(__file__))
    procesar(os.path.join(base, 'entradas', 'horario_valido.hor'))
    procesar(os.path.join(base, 'entradas', 'horario_errores.hor'))


if __name__ == '__main__':
    main()
