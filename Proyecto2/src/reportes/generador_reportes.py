# -*- coding: utf-8 -*-
"""
generador_reportes.py
Punto unico para generar todos los archivos de salida de un analisis.

Decide que se genera segun haya o no errores (D-16):
  - sin errores: Reporte 1, Reporte 2, Reporte 3 y arbol.dot
  - con errores: reporte_errores.html y arbol.dot (el arbol se genera
    siempre porque muestra hasta donde llego el parser)

La interfaz grafica solo llama a generar_todos().
"""

import os

from reportes.generador_html import GeneradorHTML
from reportes.generador_estadisticas import GeneradorEstadisticas
from reportes.generador_indice import GeneradorIndice
from reportes.generador_errores import GeneradorErrores
from reportes.generador_dot import GeneradorDOT
from reportes.generador_html import NOMBRE_REPORTE as NOMBRE_REPORTE1
from reportes.generador_estadisticas import NOMBRE_REPORTE as NOMBRE_REPORTE2
from reportes.generador_indice import NOMBRE_REPORTE as NOMBRE_REPORTE3
from reportes.generador_errores import NOMBRE_REPORTE as NOMBRE_ERRORES
from reportes.generador_dot import NOMBRE_ARCHIVO as NOMBRE_DOT

# Todo lo que un analisis puede dejar en la carpeta de salida. arbol.png lo
# genera la interfaz con Graphviz a partir de arbol.dot.
ARCHIVOS_DE_SALIDA = [NOMBRE_REPORTE1, NOMBRE_REPORTE2, NOMBRE_REPORTE3,
                      NOMBRE_ERRORES, NOMBRE_DOT, 'arbol.png']


def generar_todos(raiz, gestor, nombre_archivo, carpeta):
    """
    Genera los archivos en 'carpeta' y devuelve un diccionario con la ruta
    de cada uno. Las claves posibles son: 'documento', 'estadisticas',
    'indice', 'errores' y 'arbol'.
    """
    borrar_salida_anterior(carpeta)
    rutas = {}
    if gestor.hay_errores():
        rutas['errores'] = GeneradorErrores(gestor,
                                            nombre_archivo).guardar(carpeta)
    else:
        rutas['documento'] = GeneradorHTML(raiz,
                                           nombre_archivo).guardar(carpeta)
        rutas['estadisticas'] = GeneradorEstadisticas(
            raiz, nombre_archivo).guardar(carpeta)
        rutas['indice'] = GeneradorIndice(raiz,
                                          nombre_archivo).guardar(carpeta)
    rutas['arbol'] = GeneradorDOT(raiz).guardar(carpeta)
    return rutas


def borrar_salida_anterior(carpeta):
    """
    Borra los archivos que dejo un analisis anterior del mismo documento.
    Sin esto, si el documento tenia errores y se corrigieron, quedaria un
    reporte_errores.html viejo junto a los reportes nuevos (o al reves).
    """
    i = 0
    while i < len(ARCHIVOS_DE_SALIDA):
        ruta = os.path.join(carpeta, ARCHIVOS_DE_SALIDA[i])
        if os.path.isfile(ruta):
            os.remove(ruta)
        i = i + 1
