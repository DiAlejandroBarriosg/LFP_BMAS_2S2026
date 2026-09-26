# -*- coding: utf-8 -*-
"""
pruebas_reportes.py
Genera los cuatro reportes HTML y el DOT de la jerarquia.

Uso:
    python pruebas_reportes.py entradas/horario_choques.hor
    python pruebas_reportes.py            (usa horario_choques.hor)

Los archivos salen en la carpeta 'salida/'.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analizador.analizador_lexico import AnalizadorLexico
from logica.estructurador import Estructurador
from logica.detector_choques import DetectorChoques
from reportes.generador import GeneradorReportes
from reportes.graficador import Graficador
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


def procesar(ruta, carpeta_salida):
    nombre = os.path.basename(ruta)

    analizador = AnalizadorLexico()
    analizador.analizar(leer_archivo(ruta))

    estructura = Estructurador()
    estructura.estructurar(analizador.tokens)

    detector = DetectorChoques()
    detector.detectar(estructura)

    generador = GeneradorReportes(estructura, detector, analizador, nombre)
    rutas = generador.generar_todos(carpeta_salida)

    graficador = Graficador(estructura, detector)
    rutas['jerarquia'] = graficador.guardar(carpeta_salida)

    print('')
    print('ARCHIVO: ' + nombre)
    print('  tokens: ' + str(len(analizador.tokens)) +
          '   errores: ' + str(analizador.gestor.total()) +
          '   avisos: ' + str(len(estructura.avisos)) +
          '   choques: ' + str(detector.total()))
    print('  reportes generados:')
    claves = alf.claves_ordenadas(rutas)
    i = 0
    while i < len(claves):
        clave = claves[i]
        i = i + 1
        tamano = os.path.getsize(rutas[clave])
        print('    ' + rellenar(clave, 13) + rutas[clave] +
              '  (' + str(tamano) + ' bytes)')


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    carpeta_salida = os.path.join(base, 'salida')

    if len(sys.argv) > 1:
        procesar(sys.argv[1], carpeta_salida)
        return

    procesar(os.path.join(base, 'entradas', 'horario_choques.hor'),
             carpeta_salida)


if __name__ == '__main__':
    main()
