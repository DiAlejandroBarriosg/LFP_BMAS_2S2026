# -*- coding: utf-8 -*-
"""
palabras_reservadas.py
Catalogo de palabras reservadas y enumeraciones de HorarioScript.

La comparacion es SENSIBLE A MAYUSCULAS: 'HORARIO' es palabra reservada de
bloque, 'horario' es una palabra desconocida. El lenguaje usa mayusculas para
bloques y enumeraciones, y minusculas para elementos y atributos.
"""

BLOQUES = ('HORARIO', 'CURSOS', 'CATEDRATICOS', 'AULAS', 'CLASES')

ELEMENTOS = ('curso', 'catedratico', 'aula', 'clase')

RELACIONES = ('con', 'en')

ATRIBUTOS = ('codigo', 'creditos', 'categoria', 'capacidad',
             'edificio', 'dia', 'inicio', 'fin', 'seccion')

DIAS = ('LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO')

CATEGORIAS = ('TITULAR', 'INTERINO', 'AUXILIAR')

# --- Tipos de token ---
T_RESERVADA_BLOQUE = 'RESERVADA_BLOQUE'
T_RESERVADA_ELEMENTO = 'RESERVADA_ELEMENTO'
T_RESERVADA_RELACION = 'RESERVADA_RELACION'
T_RESERVADA_ATRIBUTO = 'RESERVADA_ATRIBUTO'
T_DIA = 'DIA'
T_CATEGORIA = 'CATEGORIA'
T_CODIGO = 'CODIGO'
T_CADENA = 'CADENA'
T_HORA = 'HORA'
T_ENTERO = 'ENTERO'
T_SIMBOLO = 'SIMBOLO'
T_COMENTARIO = 'COMENTARIO_LINEA'

# --- Tipos de error lexico (seccion 4.8 del enunciado) ---
E_CARACTER = 'CARACTER_NO_RECONOCIDO'
E_CADENA = 'CADENA_SIN_CERRAR'
E_HORA = 'HORA_FUERA_DE_RANGO'
E_DIA = 'DIA_NO_RECONOCIDO'
E_CODIGO = 'CODIGO_MAL_FORMADO'

# Rango institucional en minutos desde medianoche: 06:00 = 360, 21:00 = 1260
MIN_HORA_INSTITUCIONAL = 360
MAX_HORA_INSTITUCIONAL = 1260
