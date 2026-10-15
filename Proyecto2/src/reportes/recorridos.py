# -*- coding: utf-8 -*-
"""
recorridos.py
Recorridos del arbol de derivacion que comparten los generadores de
reportes. Todos trabajan sobre el AST, nunca sobre el texto original.
"""

from lexico.token import TEXTO, TEXTO_LITERAL, SALTO_LINEA, URL
from lexico.token import NUMERO_LISTA, SEPARADOR_TABLA
from sintactico.nodo_ast import NT_ENCABEZADO, NT_IMAGEN, NT_DESTINO
from sintactico.nodo_ast import NT_LISTA, NT_CITA, NT_ITEM_LISTA
from sintactico.nodo_ast import NT_FILA_TABLA


def buscar(nodo, simbolo, encontrados):
    """
    Agrega a 'encontrados' todos los nodos con ese simbolo, en preorden
    (primero el nodo, despues sus hijos de izquierda a derecha). Ese es el
    orden en que aparecen en el archivo.
    """
    if nodo.es(simbolo):
        encontrados.append(nodo)
    i = 0
    while i < len(nodo.hijos):
        buscar(nodo.hijos[i], simbolo, encontrados)
        i = i + 1
    return encontrados


def buscar_sin_anidar(nodo, simbolo, encontrados):
    """
    Como buscar(), pero cuando encuentra un nodo con ese simbolo no sigue
    bajando por el. Sirve para contar cada <en_linea> una sola vez: el
    <en_linea> del texto de un enlace esta DENTRO de otro <en_linea>.
    """
    if nodo.es(simbolo):
        encontrados.append(nodo)
        return encontrados
    i = 0
    while i < len(nodo.hijos):
        buscar_sin_anidar(nodo.hijos[i], simbolo, encontrados)
        i = i + 1
    return encontrados


def hijo_con_simbolo(nodo, simbolo):
    """El primer hijo con ese simbolo, o None si no hay."""
    i = 0
    while i < len(nodo.hijos):
        if nodo.hijos[i].es(simbolo):
            return nodo.hijos[i]
        i = i + 1
    return None


def encabezados(raiz):
    """
    Todos los encabezados del documento en orden, incluidos los que estan
    dentro de citas. La posicion en esta lista da el ancla de cada uno:
    el primero es 'seccion-1' (D-15). El Reporte 1 y el Reporte 3 usan esta
    misma funcion, por eso sus anclas siempre coinciden.
    """
    return buscar(raiz, NT_ENCABEZADO, [])


def ancla(numero):
    """Identificador del encabezado numero 'numero' (1, 2, 3...)."""
    return 'seccion-' + str(numero)


def texto_plano(nodo):
    """
    El texto de un nodo sin ningun formato: concatena los lexemas de sus
    hojas TEXTO y TEXTO_LITERAL. Los delimitadores (**, *, `) no son TEXTO,
    asi que no aparecen. Un SALTO_LINEA dentro de una negrita, una cursiva
    o un codigo que cruzan lineas (D-02) vale un espacio, para que las
    palabras de las dos lineas no queden pegadas. Una <imagen> no aporta
    texto: su texto alternativo no se ve en el documento (D-32).
    """
    if nodo.es(NT_IMAGEN):
        return ''
    if nodo.es_terminal():
        if nodo.es(TEXTO) or nodo.es(TEXTO_LITERAL):
            return nodo.token.lexema
        if nodo.es(SALTO_LINEA):
            return ' '
        return ''
    texto = ''
    i = 0
    while i < len(nodo.hijos):
        texto = texto + texto_plano(nodo.hijos[i])
        i = i + 1
    return texto


def destino(nodo):
    """
    La URL del <destino> de un <enlace> o <imagen>, o '' si esta vacia.
    Una URL 'javascript:' se descarta: un reporte no debe ejecutar codigo
    al hacer clic en un enlace del documento.
    """
    nodo_destino = hijo_con_simbolo(nodo, NT_DESTINO)
    if nodo_destino is None:
        return ''
    url = hijo_con_simbolo(nodo_destino, URL)
    if url is None:
        return ''
    if empieza_con(url.token.lexema.lower(), 'javascript:'):
        return ''
    return url.token.lexema


def empieza_con(texto, prefijo):
    if len(texto) < len(prefijo):
        return False
    i = 0
    while i < len(prefijo):
        if texto[i] != prefijo[i]:
            return False
        i = i + 1
    return True


def numero_inicial(lista):
    """
    El numero del primer item de una lista numerada: '3.' -> 3. Para una
    lista con viñetas, 1. Lo usan el Reporte 1 (start) y la vista previa.
    """
    i = 0
    while i < len(lista.hijos):
        item = lista.hijos[i]
        if item.es(NT_ITEM_LISTA):
            marcador = hijo_con_simbolo(item, NUMERO_LISTA)
            if marcador is None:
                return 1
            digitos = ''
            j = 0
            while j < len(marcador.token.lexema) - 1:
                digitos = digitos + marcador.token.lexema[j]
                j = j + 1
            return int(digitos)
        i = i + 1
    return 1


def tabla_tiene_encabezado(tabla):
    """
    True si la <tabla> empieza con una fila y justo despues viene su
    SEPARADOR_TABLA: esa primera fila es el encabezado.
    """
    if len(tabla.hijos) < 2:
        return False
    return tabla.hijos[0].es(NT_FILA_TABLA) and tabla.hijos[1].es(
        SEPARADOR_TABLA)


def quitar_espacios_finales(texto):
    """'abc  ' -> 'abc'. Las celdas de una tabla terminan en espacios."""
    fin = len(texto)
    while fin > 0 and (texto[fin - 1] == ' ' or texto[fin - 1] == '\t'):
        fin = fin - 1
    resultado = ''
    i = 0
    while i < fin:
        resultado = resultado + texto[i]
        i = i + 1
    return resultado


def primera_y_ultima_linea(nodo):
    """
    [primera, ultima]: las lineas del primer y del ultimo token con texto
    que hay debajo del nodo. Los tokens virtuales (INDENT, DEDENT) no
    cuentan. [0, 0] si no hay ninguno.
    """
    hojas = []
    _hojas_con_texto(nodo, hojas)
    if len(hojas) == 0:
        return [0, 0]
    return [hojas[0].linea, hojas[len(hojas) - 1].linea]


def _hojas_con_texto(nodo, hojas):
    if nodo.es_terminal():
        if not nodo.token.es_virtual():
            hojas.append(nodo.token)
        return
    i = 0
    while i < len(nodo.hijos):
        _hojas_con_texto(nodo.hijos[i], hojas)
        i = i + 1


def excesos_de_anidamiento(raiz, maximo):
    """
    Advertencia de anidamiento (D-35): cada <lista> y cada <cita> cuyo
    nivel pasa de 'maximo'. Devuelve una lista de [clase, nivel, primera,
    ultima], donde clase es 'lista' o 'cita' y primera/ultima son las
    lineas que ocupa. No es un error: el documento sigue siendo valido.
    """
    excesos = []
    clases = [[NT_LISTA, 'lista'], [NT_CITA, 'cita']]
    c = 0
    while c < len(clases):
        nodos = buscar(raiz, clases[c][0], [])
        i = 0
        while i < len(nodos):
            if nodos[i].nivel > maximo:
                lineas = primera_y_ultima_linea(nodos[i])
                excesos.append([clases[c][1], nodos[i].nivel, lineas[0],
                                lineas[1]])
            i = i + 1
        c = c + 1
    return excesos
