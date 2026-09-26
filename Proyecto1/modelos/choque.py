# -*- coding: utf-8 -*-
"""
choque.py
Representa un conflicto entre dos clases que se traslapan en el mismo dia.

REGLA DE CONTEO (importante para el Reporte 3): se registra UN Choque por cada
PAR de clases en conflicto, no uno por motivo. Si dos clases comparten a la vez
catedratico y aula, es un solo choque con dos motivos. Contar por motivo
inflaria el total y haria que el KPI 'choques detectados' no coincidiera con
las celdas resaltadas en el Reporte 1.
"""

from modelos.elementos import minutos_a_hora

MOTIVO_CATEDRATICO = 'CATEDRATICO'
MOTIVO_AULA = 'AULA'


class Choque:

    def __init__(self, numero, clase_a, clase_b, motivos,
                 traslape_inicio, traslape_fin):
        self.numero = numero
        self.clase_a = clase_a
        self.clase_b = clase_b
        # lista de diccionarios, uno por motivo:
        #   {'tipo': 'CATEDRATICO', 'recurso': 'DOC-001'}
        #   {'tipo': 'AULA',        'recurso': 'A-101'}
        self.motivos = motivos
        self.dia = clase_a.dia
        self.traslape_inicio = traslape_inicio    # minutos desde medianoche
        self.traslape_fin = traslape_fin

    def duracion_traslape(self):
        return self.traslape_fin - self.traslape_inicio

    def tiene_motivo(self, tipo):
        i = 0
        while i < len(self.motivos):
            if self.motivos[i]['tipo'] == tipo:
                return True
            i = i + 1
        return False

    def recursos_en_conflicto(self):
        """Devuelve los codigos compartidos, por ejemplo ['DOC-001', 'A-101']."""
        recursos = []
        i = 0
        while i < len(self.motivos):
            recursos.append(self.motivos[i]['recurso'])
            i = i + 1
        return recursos

    def texto_motivos(self):
        texto = ''
        i = 0
        while i < len(self.motivos):
            if i > 0:
                texto = texto + ' y '
            tipo = self.motivos[i]['tipo']
            recurso = self.motivos[i]['recurso']
            if tipo == MOTIVO_CATEDRATICO:
                texto = texto + 'mismo catedratico (' + recurso + ')'
            else:
                texto = texto + 'misma aula (' + recurso + ')'
            i = i + 1
        return texto

    def involucra(self, clase):
        return clase is self.clase_a or clase is self.clase_b

    def a_fila(self):
        return (self.numero,
                self.dia,
                minutos_a_hora(self.traslape_inicio) + '-' +
                minutos_a_hora(self.traslape_fin),
                self.texto_motivos(),
                self.clase_a.codigo_curso + ' (L' + str(self.clase_a.linea) + ')',
                self.clase_b.codigo_curso + ' (L' + str(self.clase_b.linea) + ')')

    def descripcion(self):
        """Texto legible del choque, para imprimir en consola."""
        return ('[C' + str(self.numero) + '] ' + self.dia + ' ' +
                minutos_a_hora(self.traslape_inicio) + '-' +
                minutos_a_hora(self.traslape_fin) + ' | ' +
                self.texto_motivos() + ' | ' +
                self.clase_a.codigo_curso + ' (L' + str(self.clase_a.linea) +
                ') vs ' + self.clase_b.codigo_curso +
                ' (L' + str(self.clase_b.linea) + ')')
