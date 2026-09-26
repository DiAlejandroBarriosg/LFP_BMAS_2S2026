# -*- coding: utf-8 -*-
"""
pruebas_casos.py

Los ocho casos de prueba del proyecto, ejecutables y con aserciones.

Se escriben como pruebas automaticas y no como una descripcion en prosa para
que el resultado documentado en el Manual Tecnico sea verificable: cualquiera
puede correr este archivo y comparar. Cada caso imprime que verifica, que se
esperaba y que se obtuvo.

Uso:
    python pruebas_casos.py

Devuelve codigo de salida 0 si todos los casos pasan, 1 si alguno falla.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analizador.analizador_lexico import AnalizadorLexico
from logica.estructurador import Estructurador
from logica.detector_choques import DetectorChoques
from reportes.generador import GeneradorReportes
from reportes.graficador import Graficador
from analizador import alfabeto as alf

BASE = os.path.dirname(os.path.abspath(__file__))

fallos = []
total_verificaciones = 0


# ----------------------------------------------------------------------
# Infraestructura minima de pruebas
# ----------------------------------------------------------------------

def verificar(descripcion, esperado, obtenido):
    global total_verificaciones
    total_verificaciones = total_verificaciones + 1
    paso = (esperado == obtenido)
    if paso:
        marca = 'OK  '
    else:
        marca = 'FALLA'
    print('    [' + marca + '] ' + descripcion)
    if not paso:
        print('             esperado: ' + str(esperado))
        print('             obtenido: ' + str(obtenido))
        fallos.append(descripcion)
    return paso


def titulo(numero, nombre, objetivo):
    print('')
    print('=' * 78)
    print('CASO ' + str(numero) + ': ' + nombre)
    print('-' * 78)
    print('Objetivo: ' + objetivo)
    print('')


def leer(nombre_archivo):
    ruta = os.path.join(BASE, 'entradas', nombre_archivo)
    archivo = open(ruta, 'r', encoding='utf-8', newline='')
    contenido = archivo.read()
    archivo.close()
    return contenido


def analizar(texto):
    """Corre las tres capas y devuelve los tres objetos."""
    analizador = AnalizadorLexico()
    analizador.analizar(texto)
    estructura = Estructurador()
    estructura.estructurar(analizador.tokens)
    detector = DetectorChoques()
    detector.detectar(estructura)
    return (analizador, estructura, detector)


def tipos_de(tokens):
    lista = []
    i = 0
    while i < len(tokens):
        if tokens[i].tipo not in lista:
            lista.append(tokens[i].tipo)
        i = i + 1
    lista.sort()
    return lista


def tipos_de_error(gestor):
    lista = []
    i = 0
    while i < len(gestor.errores):
        if gestor.errores[i].tipo not in lista:
            lista.append(gestor.errores[i].tipo)
        i = i + 1
    lista.sort()
    return lista


def clasificar(texto):
    """Devuelve [(lexema, tipo)] de los tokens de un fragmento suelto."""
    analizador = AnalizadorLexico()
    analizador.analizar(texto)
    salida = []
    i = 0
    while i < len(analizador.tokens):
        salida.append((analizador.tokens[i].lexema, analizador.tokens[i].tipo))
        i = i + 1
    return salida


def errores_de(texto):
    analizador = AnalizadorLexico()
    analizador.analizar(texto)
    salida = []
    i = 0
    while i < len(analizador.gestor.errores):
        error = analizador.gestor.errores[i]
        salida.append((error.lexema, error.tipo))
        i = i + 1
    return salida


# ----------------------------------------------------------------------
# CASO 1
# ----------------------------------------------------------------------

def caso_1():
    titulo(1, 'Archivo valido del enunciado',
           'El AFD reconoce los 12 tipos de token sin reportar errores, y el '
           'estructurador arma todos los elementos declarados.')

    analizador, estructura, detector = analizar(leer('horario_valido.hor'))

    verificar('tokens reconocidos', 149, len(analizador.tokens))
    verificar('errores lexicos', 0, analizador.gestor.total())
    verificar('avisos estructurales', 0, len(estructura.avisos))
    verificar('choques detectados', 0, detector.total())
    verificar('tipos de token presentes', 12, len(tipos_de(analizador.tokens)))
    verificar('cursos armados', 2, len(estructura.cursos))
    verificar('catedraticos armados', 2, len(estructura.catedraticos))
    verificar('aulas armadas', 2, len(estructura.aulas))
    verificar('clases armadas', 2, len(estructura.clases))
    verificar('secciones detectadas', ['A', 'N'], estructura.secciones())


# ----------------------------------------------------------------------
# CASO 2
# ----------------------------------------------------------------------

def caso_2():
    titulo(2, 'Los cinco tipos de error lexico y la recuperacion en modo panico',
           'Un archivo con multiples errores debe reportarlos TODOS en una '
           'sola pasada, sin detenerse en el primero, y seguir produciendo '
           'tokens validos despues de cada error.')

    analizador, estructura, detector = analizar(leer('horario_errores.hor'))

    esperados = ['CADENA_SIN_CERRAR', 'CARACTER_NO_RECONOCIDO',
                 'CODIGO_MAL_FORMADO', 'DIA_NO_RECONOCIDO',
                 'HORA_FUERA_DE_RANGO']

    verificar('los cinco tipos de error aparecen', esperados,
              tipos_de_error(analizador.gestor))
    verificar('errores totales', 10, analizador.gestor.total())
    verificar('el analisis continua y sigue produciendo tokens', 132,
              len(analizador.tokens))
    verificar('el estructurador no se cae y arma lo que puede', 1,
              len(estructura.cursos))
    verificar('los avisos explican lo que quedo incompleto', 13,
              len(estructura.avisos))

    # Un valor descartado por error lexico no debe desfasar la lista de
    # atributos: se reporta como VALOR_PERDIDO, no como un tipo equivocado.
    perdidos = 0
    i = 0
    while i < len(estructura.avisos):
        if estructura.avisos[i].tipo == 'VALOR_PERDIDO':
            perdidos = perdidos + 1
        i = i + 1
    verificar('valores perdidos por error lexico, sin desfasar atributos',
              True, perdidos > 0)


# ----------------------------------------------------------------------
# CASO 3
# ----------------------------------------------------------------------

def caso_3():
    titulo(3, 'Ambiguedad entre HORA y ENTERO, y conteo de posicion',
           'Dos digitos seguidos de ":" solo forman HORA si vienen dos '
           'digitos mas. El lookahead no consume, asi que no hace falta '
           'retroceder el indice. Tambien se verifica el conteo de linea y '
           'columna con tabulaciones y con fin de linea CRLF.')

    verificar('40 seguido de ":" son ENTERO y SIMBOLO por separado',
              [('40', 'ENTERO'), (':', 'SIMBOLO'), ('5', 'ENTERO')],
              clasificar('40: 5'))

    verificar('07: sin minutos es ENTERO y SIMBOLO',
              [('07', 'ENTERO'), (':', 'SIMBOLO')],
              clasificar('07:'))

    verificar('07:00 es una sola HORA', [('07:00', 'HORA')],
              clasificar('07:00'))

    verificar('123: no es hora porque no tiene dos digitos',
              [('123', 'ENTERO'), (':', 'SIMBOLO'), ('45', 'ENTERO')],
              clasificar('123:45'))

    verificar('06:00 es el limite inferior valido', [('06:00', 'HORA')],
              clasificar('06:00'))
    verificar('21:00 es el limite superior valido', [('21:00', 'HORA')],
              clasificar('21:00'))
    verificar('05:59 queda fuera de rango',
              [('05:59', 'HORA_FUERA_DE_RANGO')], errores_de('05:59'))
    verificar('21:01 queda fuera de rango',
              [('21:01', 'HORA_FUERA_DE_RANGO')], errores_de('21:01'))
    verificar('07:75 se rechaza por los minutos',
              [('07:75', 'HORA_FUERA_DE_RANGO')], errores_de('07:75'))

    # Tabulacion: el AFD cuenta 4 columnas por tabulador
    tokens = clasificar('\tHORARIO')
    analizador = AnalizadorLexico()
    analizador.analizar('\tHORARIO')
    verificar('un tabulador desplaza la columna a 5', 5,
              analizador.tokens[0].columna)

    # CRLF: el retorno de carro no debe contar como columna ni como linea
    analizador = AnalizadorLexico()
    analizador.analizar('HORARIO {\r\nCURSOS {\r\n')
    verificar('con CRLF, CURSOS queda en la linea 2 columna 1',
              (2, 1),
              (analizador.tokens[2].linea, analizador.tokens[2].columna))

    analizador, estructura, detector = analizar(leer('horario_ambiguedades.hor'))
    verificar('archivo completo con CRLF y tabulaciones, sin errores', 0,
              analizador.gestor.total())
    verificar('la ultima linea del archivo CRLF es la 20', 20,
              analizador.tokens[len(analizador.tokens) - 1].linea)


# ----------------------------------------------------------------------
# CASO 4
# ----------------------------------------------------------------------

def caso_4():
    titulo(4, 'Clasificacion de literales: CADENA, CODIGO y CODIGO_MAL_FORMADO',
           'Decision D-01: al cerrar un literal, si no tiene espacios y tiene '
           'exactamente un guion, se valida como codigo. En cualquier otro '
           'caso es una cadena. Es lo que hace alcanzable el error '
           'CODIGO_MAL_FORMADO.')

    verificar('LFP-0796 entre comillas es CODIGO',
              [('"LFP-0796"', 'CODIGO')], clasificar('"LFP-0796"'))
    verificar('BD2-0812 es CODIGO aunque el prefijo tenga un digito',
              [('"BD2-0812"', 'CODIGO')], clasificar('"BD2-0812"'))
    verificar('A-101 es CODIGO', [('"A-101"', 'CODIGO')],
              clasificar('"A-101"'))
    verificar('N sin guion es CADENA', [('"N"', 'CADENA')], clasificar('"N"'))
    verificar('un texto con espacios es CADENA',
              [('"Bases de Datos 2"', 'CADENA')],
              clasificar('"Bases de Datos 2"'))
    verificar('un texto con guion pero con espacios sigue siendo CADENA',
              [('"Redes - Avanzadas"', 'CADENA')],
              clasificar('"Redes - Avanzadas"'))
    verificar('MAGNA es CADENA y sirve como nombre de aula',
              [('"MAGNA"', 'CADENA')], clasificar('"MAGNA"'))

    verificar('LFP0796 sin guion es codigo mal formado',
              [('"LFP0796"', 'CODIGO_MAL_FORMADO')], errores_de('"LFP0796"'))
    verificar('un literal de solo letras sigue siendo CADENA',
              [('"MAGNA"', 'CADENA')], clasificar('"MAGNA"'))
    verificar('un literal de solo digitos sigue siendo CADENA',
              [('"2026"', 'CADENA')], clasificar('"2026"'))
    verificar('CMP- sin digitos es codigo mal formado',
              [('"CMP-"', 'CODIGO_MAL_FORMADO')], errores_de('"CMP-"'))
    verificar('un sufijo con letras es codigo mal formado',
              [('"RED-08A2"', 'CODIGO_MAL_FORMADO')],
              errores_de('"RED-08A2"'))
    verificar('un prefijo que empieza con digito es codigo mal formado',
              [('"101-A"', 'CODIGO_MAL_FORMADO')], errores_de('"101-A"'))
    verificar('un codigo sin comillas tambien se reconoce',
              [('A-101', 'CODIGO')], clasificar('A-101'))
    verificar('una cadena sin cerrar se reporta en su posicion de apertura',
              [('"abierta', 'CADENA_SIN_CERRAR')], errores_de('"abierta'))


# ----------------------------------------------------------------------
# CASO 5
# ----------------------------------------------------------------------

def caso_5():
    titulo(5, 'Deteccion de choques por catedratico y por aula',
           'Dos clases chocan si coinciden en dia, se traslapan en el tiempo '
           'y comparten catedratico o aula.')

    analizador, estructura, detector = analizar(leer('horario_choques.hor'))

    verificar('choques detectados', 2, detector.total())
    verificar('desglose por motivo',
              {'total': 2, 'solo_catedratico': 1, 'solo_aula': 1, 'ambos': 0},
              detector.resumen())
    verificar('recursos en conflicto',
              {'catedraticos': ['DOC-001'], 'aulas': ['A-101']},
              detector.recursos_afectados())

    # cuatro clases marcadas: dos por cada choque
    marcadas = 0
    i = 0
    while i < len(estructura.clases):
        if estructura.clases[i].en_choque:
            marcadas = marcadas + 1
        i = i + 1
    verificar('clases marcadas en choque', 4, marcadas)

    verificar('el choque de catedratico es el LUNES', 'LUNES',
              detector.choques[0].dia)
    verificar('el traslape del choque de aula dura 40 minutos', 40,
              detector.choques[1].duracion_traslape())


# ----------------------------------------------------------------------
# CASO 6
# ----------------------------------------------------------------------

def caso_6():
    titulo(6, 'Casos que NO son choque, y casos borde del traslape',
           'La desigualdad estricta evita el falso positivo mas comun: una '
           'clase que termina 08:40 y otra que empieza 08:40 es continuidad, '
           'no conflicto. Tambien se verifican la contencion total, el doble '
           'motivo y las tres clases mutuamente traslapadas.')

    analizador, estructura, detector = analizar(
        leer('horario_choques_borde.hor'))

    verificar('choques detectados en el archivo de casos borde', 6,
              detector.total())

    # el JUEVES hay dos clases a la misma hora sin recurso compartido
    jueves = 0
    i = 0
    while i < len(detector.choques):
        if detector.choques[i].dia == 'JUEVES':
            jueves = jueves + 1
        i = i + 1
    verificar('misma hora sin recurso compartido no es choque', 0, jueves)

    # el MIERCOLES hay tres clases mutuamente traslapadas: tres pares
    miercoles = 0
    i = 0
    while i < len(detector.choques):
        if detector.choques[i].dia == 'MIERCOLES':
            miercoles = miercoles + 1
        i = i + 1
    verificar('tres clases mutuamente traslapadas dan tres pares', 3,
              miercoles)

    # el LUNES comparten catedratico Y aula: un solo choque con dos motivos
    lunes = None
    i = 0
    while i < len(detector.choques):
        if detector.choques[i].dia == 'LUNES':
            lunes = detector.choques[i]
        i = i + 1
    verificar('compartir catedratico y aula es UN choque con dos motivos', 2,
              len(lunes.motivos))

    # continuidad en el limite: se prueba sobre el archivo de choques
    analizador2, estructura2, detector2 = analizar(leer('horario_choques.hor'))
    miercoles_continuo = 0
    i = 0
    while i < len(detector2.choques):
        if detector2.choques[i].dia == 'MIERCOLES':
            miercoles_continuo = miercoles_continuo + 1
        i = i + 1
    verificar('08:40 fin y 08:40 inicio del mismo catedratico no es choque',
              0, miercoles_continuo)

    # mismo horario en dias distintos
    jueves_viernes = 0
    i = 0
    while i < len(detector2.choques):
        dia = detector2.choques[i].dia
        if dia == 'JUEVES' or dia == 'VIERNES':
            jueves_viernes = jueves_viernes + 1
        i = i + 1
    verificar('mismo horario en dias distintos no es choque', 0,
              jueves_viernes)

    # dia saturado de 06:00 a 21:00: no quedan bloques libres
    sin_hueco = 0
    propuestas = detector.sugerencias_para_todos(estructura)
    i = 0
    while i < len(propuestas):
        if (propuestas[i]['clase'].dia == 'VIERNES' and
                len(propuestas[i]['sugerencias']) == 0):
            sin_hueco = sin_hueco + 1
        i = i + 1
    verificar('en un dia ocupado de 06:00 a 21:00 no se sugiere ningun bloque',
              True, sin_hueco > 0)


# ----------------------------------------------------------------------
# CASO 7
# ----------------------------------------------------------------------

def caso_7():
    titulo(7, 'Validaciones estructurales y de referencia',
           'Con el flujo de tokens ya valido, el estructurador detecta '
           'codigos duplicados, referencias a elementos no declarados y '
           'rangos de hora invertidos. Son avisos, NO errores lexicos.')

    analizador, estructura, detector = analizar(leer('horario_choques.hor'))

    verificar('sin errores lexicos: el archivo es lexicamente correcto', 0,
              analizador.gestor.total())
    verificar('avisos estructurales', 5, len(estructura.avisos))

    conteo = {}
    i = 0
    while i < len(estructura.avisos):
        tipo = estructura.avisos[i].tipo
        if tipo in conteo:
            conteo[tipo] = conteo[tipo] + 1
        else:
            conteo[tipo] = 1
        i = i + 1

    verificar('desglose de avisos',
              {'CODIGO_DUPLICADO': 1, 'REFERENCIA_INEXISTENTE': 3,
               'RANGO_INVALIDO': 1}, conteo)

    # una clase sin dia u hora valida se descarta para no falsear el detector
    analizador2, estructura2, detector2 = analizar(
        'HORARIO { CLASES { clase: "A-1" con "D-1" en "B-1" '
        '[dia: LUNEZ, inicio: 07:00, fin: 08:40, seccion: "N"], }; };')
    verificar('una clase sin dia valido se descarta', 0,
              len(estructura2.clases))

    # el rango invertido no debe restar horas en el reporte de carga
    generador = GeneradorReportes(estructura, detector, analizador, 'prueba')
    negativas = 0
    i = 0
    while i < len(estructura.catedraticos):
        perfil = generador._perfil_catedratico(estructura.catedraticos[i])
        if perfil['horas'] < 0:
            negativas = negativas + 1
        i = i + 1
    verificar('ninguna carga docente resulta negativa', 0, negativas)


# ----------------------------------------------------------------------
# CASO 8
# ----------------------------------------------------------------------

def caso_8():
    titulo(8, 'Generacion de reportes, niveles de carga y ocupacion de aulas',
           'Los cuatro reportes HTML y el DOT se generan, y los umbrales de '
           'carga docente y de ocupacion de aula clasifican correctamente.')

    analizador, estructura, detector = analizar(leer('horario_completo.hor'))
    generador = GeneradorReportes(estructura, detector, analizador,
                                  'horario_completo.hor')

    verificar('sin errores lexicos', 0, analizador.gestor.total())
    verificar('clases programadas', 22, len(estructura.clases))
    verificar('choques detectados', 2, detector.total())

    niveles = []
    i = 0
    while i < len(estructura.catedraticos):
        catedratico = estructura.catedraticos[i]
        perfil = generador._perfil_catedratico(catedratico)
        niveles.append((catedratico.codigo,
                        generador._decimales(perfil['horas']),
                        generador._nivel_carga(perfil['horas'])[0]))
        i = i + 1

    verificar('los cuatro niveles de carga quedan representados',
              [('DOC-001', '15.0', 'ALTA'),
               ('DOC-002', '8.3', 'NORMAL'),
               ('DOC-003', '3.3', 'BAJA'),
               ('DOC-004', '78.0', 'SATURADA')], niveles)

    ocupacion = generador._ocupacion_aulas()
    saturadas = []
    i = 0
    while i < len(ocupacion):
        if ocupacion[i]['porcentaje'] > 80.0:
            saturadas.append(ocupacion[i]['aula'].codigo)
        i = i + 1
    verificar('LAB-3 supera el 80% de ocupacion', ['LAB-3'], saturadas)

    carpeta = os.path.join(BASE, 'salida')
    rutas = generador.generar_todos(carpeta)
    graficador = Graficador(estructura, detector)
    rutas['jerarquia'] = graficador.guardar(carpeta)

    esperados = ['carga', 'errores', 'estadistico', 'horario', 'jerarquia']
    claves = alf.claves_ordenadas(rutas)
    verificar('se generan los cinco archivos', esperados, claves)

    vacios = 0
    for clave in rutas:
        if os.path.getsize(rutas[clave]) < 1000:
            vacios = vacios + 1
    verificar('ningun archivo generado queda vacio', 0, vacios)

    # el lexema de un error no debe poder inyectar HTML
    analizador3 = AnalizadorLexico()
    analizador3.analizar('curso: <script>')
    estructura3 = Estructurador()
    estructura3.estructurar(analizador3.tokens)
    detector3 = DetectorChoques()
    detector3.detectar(estructura3)
    generador3 = GeneradorReportes(estructura3, detector3, analizador3, 'x')
    html = generador3.reporte_errores()
    verificar('los lexemas se escapan y no inyectan etiquetas HTML', False,
              '<script>' in html)


# ----------------------------------------------------------------------

def main():
    print('')
    print('HORARIOSCRIPT - SUITE DE CASOS DE PRUEBA')
    print('Proyecto 1, Lenguajes Formales y de Programacion, seccion B+, 2S2026')

    caso_1()
    caso_2()
    caso_3()
    caso_4()
    caso_5()
    caso_6()
    caso_7()
    caso_8()

    print('')
    print('=' * 78)
    print('RESULTADO FINAL')
    print('-' * 78)
    print('  Verificaciones ejecutadas: ' + str(total_verificaciones))
    print('  Fallos: ' + str(len(fallos)))
    if len(fallos) > 0:
        print('')
        i = 0
        while i < len(fallos):
            print('  - ' + fallos[i])
            i = i + 1
        print('')
        return 1
    print('')
    print('  Los ocho casos de prueba pasan.')
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
