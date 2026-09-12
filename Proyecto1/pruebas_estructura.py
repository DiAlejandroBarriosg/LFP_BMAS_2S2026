# -*- coding: utf-8 -*-
"""
pruebas_estructura.py
Verificacion del Estructurador: del flujo de tokens a los objetos de dominio.

Uso:
    python pruebas_estructura.py entradas/horario_valido.hor
    python pruebas_estructura.py            (corre los archivos de ejemplo)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analizador.analizador_lexico import AnalizadorLexico
from logica.estructurador import Estructurador


def leer_archivo(ruta):
    archivo = open(ruta, 'r', encoding='utf-8', newline='')
    contenido = archivo.read()
    archivo.close()
    return contenido


def imprimir_lista(titulo, elementos):
    print('')
    print(titulo + '  (' + str(len(elementos)) + ')')
    print('-' * 88)
    if len(elementos) == 0:
        print('  (vacio)')
        return
    for e in elementos:
        print('  L' + str(e.linea).rjust(3) + '  ' + str(e))


def procesar(ruta):
    print('')
    print('=' * 88)
    print('ARCHIVO: ' + ruta)
    print('=' * 88)

    analizador = AnalizadorLexico()
    analizador.analizar(leer_archivo(ruta))

    print('Tokens: ' + str(len(analizador.tokens)) +
          '   Errores lexicos: ' + str(analizador.gestor.total()))

    estructura = Estructurador()
    estructura.estructurar(analizador.tokens)

    imprimir_lista('CURSOS', estructura.cursos)
    imprimir_lista('CATEDRATICOS', estructura.catedraticos)
    imprimir_lista('AULAS', estructura.aulas)
    imprimir_lista('CLASES', estructura.clases)

    print('')
    print('AVISOS ESTRUCTURALES  (' + str(len(estructura.avisos)) + ')')
    print('-' * 88)
    if len(estructura.avisos) == 0:
        print('  (ninguno)')
    for a in estructura.avisos:
        print('  ' + str(a))

    print('')
    print('AGRUPACION POR DIA')
    print('-' * 88)
    grupos = estructura.clases_por_dia()
    for dia in grupos:
        print('  ' + dia.ljust(12) + str(len(grupos[dia])) + ' clase(s)')

    print('')
    print('RESUMEN: ' + str(estructura.resumen()))
    print('SECCIONES: ' + str(estructura.secciones()))


def main():
    if len(sys.argv) > 1:
        procesar(sys.argv[1])
        return
    base = os.path.dirname(os.path.abspath(__file__))
    procesar(os.path.join(base, 'entradas', 'horario_valido.hor'))
    procesar(os.path.join(base, 'entradas', 'horario_errores.hor'))


if __name__ == '__main__':
    main()
