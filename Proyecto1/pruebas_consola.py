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


def leer_archivo(ruta):
    archivo = open(ruta, 'r', encoding='utf-8', newline='')
    contenido = archivo.read()
    archivo.close()
    return contenido


def imprimir_tokens(tokens):
    print('')
    print('TABLA DE TOKENS  (' + str(len(tokens)) + ')')
    print('-' * 92)
    print('{:<5} {:<42} {:<22} {:>6} {:>8}'.format(
        'No.', 'Lexema', 'Tipo', 'Linea', 'Columna'))
    print('-' * 92)
    for t in tokens:
        lexema = t.lexema
        if len(lexema) > 40:
            lexema = lexema[0:37] + '...'
        print('{:<5} {:<42} {:<22} {:>6} {:>8}'.format(
            t.numero, lexema, t.tipo, t.linea, t.columna))


def imprimir_errores(gestor):
    print('')
    print('TABLA DE ERRORES LEXICOS  (' + str(gestor.total()) + ')')
    print('-' * 92)
    if not gestor.hay_errores():
        print('Sin errores.')
        return
    print('{:<5} {:<24} {:<24} {:>6} {:>8}'.format(
        'No.', 'Lexema', 'Tipo', 'Linea', 'Columna'))
    print('-' * 92)
    for e in gestor.errores:
        lexema = e.lexema
        if len(lexema) > 22:
            lexema = lexema[0:19] + '...'
        print('{:<5} {:<24} {:<24} {:>6} {:>8}'.format(
            e.numero, lexema, e.tipo, e.linea, e.columna))
    print('')
    for e in gestor.errores:
        print('  E' + str(e.numero) + ': ' + e.descripcion)


def imprimir_resumen(analizador):
    print('')
    print('FRECUENCIA POR TIPO DE TOKEN')
    print('-' * 92)
    conteo = analizador.contar_por_tipo()
    for tipo in sorted(conteo.keys()):
        print('  {:<24} {:>4}'.format(tipo, conteo[tipo]))


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
