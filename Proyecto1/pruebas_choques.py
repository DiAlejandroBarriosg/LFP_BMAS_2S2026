# -*- coding: utf-8 -*-
"""
pruebas_choques.py
Verificacion del DetectorChoques y de la sugerencia de bloques libres.

Uso:
    python pruebas_choques.py entradas/horario_choques.hor
    python pruebas_choques.py            (corre los archivos de ejemplo)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analizador.analizador_lexico import AnalizadorLexico
from logica.estructurador import Estructurador
from logica.detector_choques import DetectorChoques
from modelos.elementos import minutos_a_hora


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


def procesar(ruta):
    print('')
    print('=' * 96)
    print('ARCHIVO: ' + ruta)
    print('=' * 96)

    analizador = AnalizadorLexico()
    analizador.analizar(leer_archivo(ruta))

    estructura = Estructurador()
    estructura.estructurar(analizador.tokens)

    detector = DetectorChoques()
    detector.detectar(estructura)

    print('Clases analizadas: ' + str(len(estructura.clases)) +
          '   Errores lexicos: ' + str(analizador.gestor.total()) +
          '   Avisos: ' + str(len(estructura.avisos)))

    print('')
    print('CHOQUES DETECTADOS  (' + str(detector.total()) + ')')
    print('-' * 96)
    if not detector.hay_choques():
        print('  (ninguno)')
    for c in detector.choques:
        print('  ' + c.descripcion())

    print('')
    print('ESTADO DE CADA CLASE')
    print('-' * 96)
    for clase in estructura.clases:
        if clase.en_choque:
            estado = 'CHOQUE    '
        else:
            estado = 'CONFIRMADA'
        print('  ' + estado + '  L' + alinear_derecha(clase.linea, 3) + '  ' +
              rellenar(clase.dia, 10) + ' ' + clase.inicio_texto + '-' +
              clase.fin_texto + '  ' + rellenar(clase.codigo_curso, 10) +
              ' cat=' + rellenar(clase.codigo_catedratico, 8) +
              ' aula=' + clase.codigo_aula)

    print('')
    print('RESUMEN: ' + str(detector.resumen()))
    print('RECURSOS AFECTADOS: ' + str(detector.recursos_afectados()))

    print('')
    print('SUGERENCIAS DE REPROGRAMACION  (funcionalidad opcional)')
    print('-' * 96)
    propuestas = detector.sugerencias_para_todos(estructura)
    if len(propuestas) == 0:
        print('  (no hay clases en choque)')
    for p in propuestas:
        clase = p['clase']
        print('  ' + clase.codigo_curso + ' seccion ' + clase.seccion +
              ' (' + clase.dia + ' ' + clase.inicio_texto + '-' +
              clase.fin_texto + ', ' + str(clase.duracion_minutos()) +
              ' min) ->')
        if len(p['sugerencias']) == 0:
            print('      sin bloques libres ese dia')
        for s in p['sugerencias']:
            print('      ' + s['inicio'] + ' - ' + s['fin'])


def main():
    if len(sys.argv) > 1:
        procesar(sys.argv[1])
        return
    base = os.path.dirname(os.path.abspath(__file__))
    procesar(os.path.join(base, 'entradas', 'horario_choques.hor'))
    procesar(os.path.join(base, 'entradas', 'horario_valido.hor'))


if __name__ == '__main__':
    main()
