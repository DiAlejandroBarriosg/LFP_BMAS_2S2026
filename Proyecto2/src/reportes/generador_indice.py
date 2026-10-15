# -*- coding: utf-8 -*-
"""
generador_indice.py
GeneradorIndice: Reporte 3, tabla de contenido del documento.

Se construye UNICAMENTE con los encabezados que reconocio el parser. Cada
entrada enlaza a su seccion dentro del Reporte 1: el ancla seccion-k sale
de recorridos.encabezados(), la misma lista que usa el GeneradorHTML, asi
que los enlaces siempre coinciden (D-15). La sangria de cada entrada
depende de su nivel: un H3 queda mas adentro que el H2 que lo contiene.
"""

from reportes import recorridos
from reportes.generador_html import NOMBRE_REPORTE as NOMBRE_REPORTE1
from reportes.plantilla import escapar, pagina, guardar
from sintactico.nodo_ast import NT_EN_LINEA

NOMBRE_REPORTE = 'reporte3_indice.html'

# Sangria por nivel, en pixeles.
SANGRIA_POR_NIVEL = 24


class GeneradorIndice:

    def __init__(self, raiz, nombre_archivo):
        self.raiz = raiz
        self.nombre_archivo = nombre_archivo
        self.encabezados = recorridos.encabezados(raiz)

    def generar(self):
        cuerpo = ('<h1>Tabla de contenido</h1>\n'
                  '<p class="subtitulo">' + escapar(self.nombre_archivo) +
                  ' &mdash; generada a partir de los encabezados '
                  'reconocidos</p>\n')

        if len(self.encabezados) == 0:
            # El enunciado pide decirlo, no mostrar un indice vacio.
            cuerpo = cuerpo + ('<div class="indice"><p class="nota">El '
                               'documento no tiene encabezados (# a ######), '
                               'así que no hay secciones que listar.</p>'
                               '</div>\n')
        else:
            cuerpo = cuerpo + '<div class="indice">\n'
            i = 0
            while i < len(self.encabezados):
                cuerpo = cuerpo + self._entrada(self.encabezados[i], i + 1)
                i = i + 1
            cuerpo = cuerpo + '</div>\n'
            cuerpo = cuerpo + ('<p class="nota">Cada entrada enlaza a su '
                               'sección dentro del Reporte 1 (' +
                               NOMBRE_REPORTE1 + ').</p>\n')

        return pagina('Reporte 3 - ' + self.nombre_archivo, cuerpo,
                      self.nombre_archivo)

    def guardar(self, carpeta):
        return guardar(carpeta, NOMBRE_REPORTE, self.generar())

    def _entrada(self, encabezado, numero):
        sangria = (encabezado.nivel - 1) * SANGRIA_POR_NIVEL
        texto = recorridos.texto_plano(
            recorridos.hijo_con_simbolo(encabezado, NT_EN_LINEA))
        if texto == '':
            texto = '(encabezado sin texto)'
        enlace = NOMBRE_REPORTE1 + '#' + recorridos.ancla(numero)
        return ('<div class="entrada" style="padding-left: ' + str(sangria) +
                'px"><span class="nivel">H' + str(encabezado.nivel) +
                '</span><a href="' + enlace + '">' + escapar(texto) +
                '</a></div>\n')
