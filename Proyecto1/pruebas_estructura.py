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


def imprimir_lista(titulo, elementos):
    print('')
    print(titulo + '  (' + str(len(elementos)) + ')')
    print('-' * 88)
    if len(elementos) == 0:
        print('  (vacio)')
        return
    for e in elementos:
        print('  L' + alinear_derecha(e.linea, 3) + '  ' + e.descripcion())


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
        print('  ' + a.como_texto())

    print('')
    print('AGRUPACION POR DIA')
    print('-' * 88)
    grupos = estructura.clases_por_dia()
    for dia in grupos:
        print('  ' + rellenar(dia, 12) + str(len(grupos[dia])) + ' clase(s)')

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
