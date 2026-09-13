# -*- coding: utf-8 -*-
"""
elementos.py
Objetos de dominio que el Estructurador arma a partir del flujo de tokens.

Este modulo usa analizador.alfabeto para convertir digitos a numero. Es la
unica dependencia de modelos, y es admisible porque alfabeto no importa nada
a su vez: es la tabla de caracteres del lenguaje, la capa mas baja de todas.
Tenerla como fuente unica evita duplicar la conversion de digitos en cada
modulo que la necesite.

Las horas se guardan en DOS formas:
  - texto original ('07:00'), para mostrarlo tal cual en los reportes
  - minutos desde medianoche (420), para comparar traslapes con enteros
Guardar ambas evita reconvertir en cada comparacion y mantiene los reportes
fieles al archivo de entrada.
"""

from analizador import alfabeto as alf


def hora_a_minutos(texto):
    """Convierte 'HH:MM' a minutos desde medianoche, caracter por caracter."""
    hh = ''
    mm = ''
    despues_de_dos_puntos = False
    i = 0
    while i < len(texto):
        c = texto[i]
        if c == ':':
            despues_de_dos_puntos = True
        elif despues_de_dos_puntos:
            mm = mm + c
        else:
            hh = hh + c
        i = i + 1

    return alf.valor_entero(hh) * 60 + alf.valor_entero(mm)


def minutos_a_hora(total):
    """Convierte minutos desde medianoche a 'HH:MM' con relleno de ceros."""
    horas = total // 60
    minutos = total % 60
    texto_h = str(horas)
    if len(texto_h) < 2:
        texto_h = '0' + texto_h
    texto_m = str(minutos)
    if len(texto_m) < 2:
        texto_m = '0' + texto_m
    return texto_h + ':' + texto_m


class Curso:

    def __init__(self, nombre, codigo, creditos, linea):
        self.nombre = nombre
        self.codigo = codigo
        self.creditos = creditos
        self.linea = linea

    def descripcion(self):
        return ('Curso(' + self.codigo + ', "' + self.nombre +
                '", creditos=' + str(self.creditos) + ')')


class Catedratico:

    def __init__(self, nombre, codigo, categoria, linea):
        self.nombre = nombre
        self.codigo = codigo
        self.categoria = categoria
        self.linea = linea

    def descripcion(self):
        return ('Catedratico(' + self.codigo + ', "' + self.nombre +
                '", ' + self.categoria + ')')


class Aula:

    def __init__(self, codigo, capacidad, edificio, linea):
        self.codigo = codigo
        self.capacidad = capacidad
        self.edificio = edificio
        self.linea = linea

    def descripcion(self):
        return ('Aula(' + self.codigo + ', capacidad=' + str(self.capacidad) +
                ', edificio=' + self.edificio + ')')


class Clase:

    def __init__(self, codigo_curso, codigo_catedratico, codigo_aula,
                 dia, inicio_texto, fin_texto, seccion, linea):
        self.codigo_curso = codigo_curso
        self.codigo_catedratico = codigo_catedratico
        self.codigo_aula = codigo_aula
        self.dia = dia
        self.inicio_texto = inicio_texto
        self.fin_texto = fin_texto
        self.inicio = hora_a_minutos(inicio_texto)
        self.fin = hora_a_minutos(fin_texto)
        self.seccion = seccion
        self.linea = linea
        # Lo llena el DetectorChoques en la Sesion 4
        self.en_choque = False

    def duracion_minutos(self):
        return self.fin - self.inicio

    def duracion_horas(self):
        return self.duracion_minutos() / 60.0

    def descripcion(self):
        return ('Clase(' + self.codigo_curso + ' / ' + self.codigo_catedratico +
                ' / ' + self.codigo_aula + ', ' + self.dia + ' ' +
                self.inicio_texto + '-' + self.fin_texto +
                ', seccion ' + self.seccion + ')')


class Aviso:
    """
    Inconsistencia ESTRUCTURAL o de referencia detectada al armar los objetos.

    IMPORTANTE: un Aviso NO es un error lexico. Los errores lexicos los produce
    el AFD y viven en GestorErrores. Los avisos aparecen despues, cuando el
    flujo de tokens ya es valido pero el contenido no cuadra: un atributo que
    falta, una clase que referencia un curso inexistente, un codigo repetido.
    Se muestran en un panel aparte para no confundir al usuario ni al evaluador.
    """

    def __init__(self, numero, tipo, descripcion, linea):
        self.numero = numero
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea

    def a_fila(self):
        return (self.numero, self.tipo, self.descripcion, self.linea)

    def como_texto(self):
        """
        Texto legible del aviso, para imprimir en consola.

        Se llama 'como_texto' y no 'descripcion' porque el atributo
        self.descripcion ya existe y guarda el mensaje del aviso.
        """
        return ('[A' + str(self.numero) + '] ' + self.tipo +
                ': ' + self.descripcion + ' (linea ' + str(self.linea) + ')')
