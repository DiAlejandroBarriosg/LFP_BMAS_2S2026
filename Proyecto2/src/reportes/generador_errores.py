# -*- coding: utf-8 -*-
"""
generador_errores.py
GeneradorErrores: tabla de errores lexicos y sintacticos en HTML.

Se genera cuando el analisis encontro errores, en lugar de los tres
reportes (D-16). Muestra todos los errores en una sola tabla, ordenados por
posicion, con los campos de la seccion 4.9: numero, lexema, tipo, fase,
descripcion, linea y columna.
"""

from reportes.plantilla import escapar, pagina, guardar

NOMBRE_REPORTE = 'reporte_errores.html'


class GeneradorErrores:

    def __init__(self, gestor, nombre_archivo):
        self.gestor = gestor
        self.nombre_archivo = nombre_archivo

    def generar(self):
        cantidad = self.gestor.cantidad()
        cuerpo = ('<div class="estado con-errores">&#10007; ' + str(cantidad) +
                  ' error(es): no se generan los reportes 1, 2 y 3</div>\n'
                  '<h1>Tabla de errores</h1>\n'
                  '<p class="subtitulo">' + escapar(self.nombre_archivo) +
                  '</p>\n'
                  '<table class="tabla-errores">\n'
                  '<tr><th>No.</th><th>Lexema</th><th>Tipo</th>'
                  '<th>Fase</th><th>Descripción</th><th>Línea</th>'
                  '<th>Columna</th></tr>\n')
        i = 0
        while i < len(self.gestor.errores):
            e = self.gestor.errores[i]
            cuerpo = (cuerpo + '<tr><td>' + str(e.numero) + '</td>'
                      '<td><code>' + escapar(e.lexema) + '</code></td>'
                      '<td class="tipo">' + e.tipo + '</td>'
                      '<td>' + e.fase + '</td>'
                      '<td class="descripcion">' +
                      escapar(e.descripcion) + '</td>'
                      '<td>' + str(e.linea) + '</td>'
                      '<td>' + str(e.columna) + '</td></tr>\n')
            i = i + 1
        cuerpo = cuerpo + '</table>\n'
        return pagina('Errores - ' + self.nombre_archivo, cuerpo,
                      self.nombre_archivo)

    def guardar(self, carpeta):
        return guardar(carpeta, NOMBRE_REPORTE, self.generar())
