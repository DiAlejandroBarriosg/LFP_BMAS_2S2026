# -*- coding: utf-8 -*-
"""
prueba_sintactico.py
Pruebas del AnalizadorSintactico desde consola (Fase 3).

Uso, desde la carpeta Proyecto2:
    python tests/prueba_sintactico.py

Para comparar arboles sin escribirlos completos, se resumen asi:
  - Elementos en linea, con etiquetas parecidas a HTML:
        '**a *b* c**'  ->  '<b>a <i>b</i> c</b>'
  - Listas, con corchetes por nivel:
        '- a' / '  - b' / '- c'  ->  '[a [b], c]'
  - Citas, con su nivel:
        '> a' / '>> b'  ->  'cita1[a, cita2[b]]'
"""

import os
import random
import sys

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

from lexico.analizador_lexico import AnalizadorLexico
from lexico.token import Token
from lexico.token import NUMERAL, VINETA, INDENT, DEDENT, CITA
from lexico.token import CERCA_CODIGO, LENGUAJE_CODIGO, TEXTO_LITERAL
from lexico.token import REGLA_HORIZONTAL, NEGRITA, CURSIVA, CODIGO_INLINE
from lexico.token import TEXTO, SALTO_LINEA, SALTO_PARRAFO, FIN
from sintactico.analizador_sintactico import AnalizadorSintactico
from sintactico.nodo_ast import NT_DOCUMENTO, NT_BLOQUE, NT_ENCABEZADO
from sintactico.nodo_ast import NT_PARRAFO, NT_LINEA_TEXTO, NT_LISTA
from sintactico.nodo_ast import NT_ITEM_LISTA, NT_SUBLISTA, NT_CITA
from sintactico.nodo_ast import NT_CONTENIDO_CITA, NT_BLOQUE_CODIGO
from sintactico.nodo_ast import NT_CONTENIDO_CODIGO, NT_EN_LINEA
from sintactico.nodo_ast import NT_NEGRITA, NT_CURSIVA, NT_CODIGO_INLINE
from sintactico.nodo_ast import NT_TACHADO, NT_ENLACE, NT_IMAGEN, NT_DESTINO
from sintactico.nodo_ast import NT_TABLA, NT_FILA_TABLA, NT_CELDA
from lexico.token import NUMERO_LISTA, CASILLA, TACHADO, CORCHETE_ABRE, URL
from lexico.token import IMAGEN_ABRE, CORCHETE_CIERRA, PARENTESIS_ABRE
from lexico.token import PARENTESIS_CIERRA, BARRA, SEPARADOR_TABLA
from errores.gestor_errores import GestorErrores
from errores import error_analisis as err


# ======================================================================
# Utilidades
# ======================================================================

class Verificador:
    """Cuenta las verificaciones correctas y fallidas, e imprime cada una."""

    def __init__(self):
        self.correctas = 0
        self.fallidas = 0

    def verificar(self, descripcion, obtenido, esperado):
        if obtenido == esperado:
            self.correctas = self.correctas + 1
            print('  [OK]    ' + descripcion)
        else:
            self.fallidas = self.fallidas + 1
            print('  [FALLO] ' + descripcion)
            print('          esperado: ' + str(esperado))
            print('          obtenido: ' + str(obtenido))


def analizar(texto):
    """Corre lexico + parser y devuelve el parser (tiene raiz y gestor)."""
    gestor = GestorErrores()
    lexico = AnalizadorLexico(texto, gestor)
    parser = AnalizadorSintactico(lexico, gestor)
    parser.analizar()
    return parser


def leer_ejemplo(nombre):
    ruta = os.path.join(CARPETA_PROYECTO, 'examples', nombre)
    archivo = open(ruta, 'r', encoding='utf-8-sig')
    texto = archivo.read()
    archivo.close()
    return texto


def titulo(texto):
    print('')
    print(texto)
    print('-' * len(texto))


def unir(partes, separador):
    resultado = ''
    i = 0
    while i < len(partes):
        if i > 0:
            resultado = resultado + separador
        resultado = resultado + partes[i]
        i = i + 1
    return resultado


def hijo_con_simbolo(nodo, simbolo):
    """El primer hijo con ese simbolo, o None."""
    i = 0
    while i < len(nodo.hijos):
        if nodo.hijos[i].es(simbolo):
            return nodo.hijos[i]
        i = i + 1
    return None


def buscar(nodo, simbolo, encontrados):
    """Todos los nodos con ese simbolo, recorriendo el arbol en preorden."""
    if nodo.es(simbolo):
        encontrados.append(nodo)
    i = 0
    while i < len(nodo.hijos):
        buscar(nodo.hijos[i], simbolo, encontrados)
        i = i + 1
    return encontrados


def hojas(nodo, tokens):
    """Los tokens de las hojas, de izquierda a derecha (la frontera)."""
    if nodo.es_terminal():
        tokens.append(nodo.token)
    i = 0
    while i < len(nodo.hijos):
        hojas(nodo.hijos[i], tokens)
        i = i + 1
    return tokens


def frontera_es_la_entrada(parser):
    """
    True si las hojas del arbol, en orden, son exactamente todos los tokens
    que produjo el lexico. Es la definicion de arbol de derivacion: su
    frontera es la cadena de entrada.
    """
    frontera = hojas(parser.raiz, [])
    tokens = parser.lexico.tokens
    if len(frontera) != len(tokens):
        return False
    i = 0
    while i < len(tokens):
        if frontera[i].numero != tokens[i].numero:
            return False
        i = i + 1
    return True


def bloques(raiz):
    """El simbolo del no terminal que hay dentro de cada <bloque>."""
    resultado = []
    i = 0
    while i < len(raiz.hijos):
        if raiz.hijos[i].es(NT_BLOQUE):
            resultado.append(raiz.hijos[i].hijos[0].simbolo)
        i = i + 1
    return resultado


def primer_bloque(raiz):
    i = 0
    while i < len(raiz.hijos):
        if raiz.hijos[i].es(NT_BLOQUE):
            return raiz.hijos[i].hijos[0]
        i = i + 1
    return None


def en_linea_de(bloque):
    """El <en_linea> de un encabezado o de la 1a linea de un parrafo."""
    if bloque.es(NT_PARRAFO):
        return hijo_con_simbolo(bloque.hijos[0], NT_EN_LINEA)
    return hijo_con_simbolo(bloque, NT_EN_LINEA)


def literal_de(codigo_inline):
    """El contenido de un codigo en linea; '|' marca un salto de linea."""
    texto = ''
    i = 0
    while i < len(codigo_inline.hijos):
        if codigo_inline.hijos[i].es(TEXTO_LITERAL):
            texto = texto + codigo_inline.hijos[i].token.lexema
        elif codigo_inline.hijos[i].es(SALTO_LINEA):
            texto = texto + '|'
        i = i + 1
    return texto


def resumen_en_linea(nodo):
    """
    'Este <b>texto</b> y <i>esto</i>': la estructura en linea. Un '|' marca
    un SALTO_LINEA dentro de una negrita o cursiva que cruza lineas.
    """
    texto = ''
    i = 0
    while i < len(nodo.hijos):
        hijo = nodo.hijos[i]
        if hijo.es(TEXTO):
            texto = texto + hijo.token.lexema
        elif hijo.es(SALTO_LINEA):
            texto = texto + '|'
        elif hijo.es(NT_NEGRITA):
            texto = texto + '<b>' + resumen_en_linea(hijo.hijos[1]) + '</b>'
        elif hijo.es(NT_CURSIVA):
            texto = texto + '<i>' + resumen_en_linea(hijo.hijos[1]) + '</i>'
        elif hijo.es(NT_CODIGO_INLINE):
            texto = texto + '<code>' + literal_de(hijo) + '</code>'
        elif hijo.es(NT_TACHADO):
            texto = texto + '<s>' + resumen_en_linea(hijo.hijos[1]) + '</s>'
        elif hijo.es(NT_ENLACE):
            texto = (texto + '<a ' + url_de(hijo) + '>' +
                     resumen_en_linea(hijo.hijos[1]) + '</a>')
        elif hijo.es(NT_IMAGEN):
            texto = texto + '<img ' + literal_de(hijo) + '>'
        i = i + 1
    return texto


def url_de(nodo):
    """La URL del <destino> de un enlace o imagen."""
    destino = hijo_con_simbolo(nodo, NT_DESTINO)
    url = hijo_con_simbolo(destino, URL)
    if url is None:
        return ''
    return url.token.lexema


def resumen_lista(lista):
    """'[a [b, c], d]': cada item con su sublista entre corchetes."""
    partes = []
    i = 0
    while i < len(lista.hijos):
        item = lista.hijos[i]
        texto = resumen_en_linea(hijo_con_simbolo(item, NT_EN_LINEA))
        sublista = hijo_con_simbolo(item, NT_SUBLISTA)
        if sublista is not None:
            interna = hijo_con_simbolo(sublista, NT_LISTA)
            if interna is not None:
                texto = texto + ' ' + resumen_lista(interna)
        partes.append(texto)
        i = i + 1
    return '[' + unir(partes, ', ') + ']'


def resumen_cita(cita):
    """'cita1[a, cita2[b]]': las lineas de cada nivel y sus citas anidadas."""
    partes = []
    i = 0
    while i < len(cita.hijos):
        hijo = cita.hijos[i]
        if hijo.es(NT_CONTENIDO_CITA):
            encabezado = hijo_con_simbolo(hijo, NT_ENCABEZADO)
            if encabezado is not None:
                partes.append('H' + str(encabezado.nivel) + ':' +
                              resumen_en_linea(en_linea_de(encabezado)))
            else:
                partes.append(resumen_en_linea(
                    hijo_con_simbolo(hijo, NT_EN_LINEA)))
        elif hijo.es(NT_CITA):
            partes.append(resumen_cita(hijo))
        i = i + 1
    return 'cita' + str(cita.nivel) + '[' + unir(partes, ', ') + ']'


def nivel_maximo(raiz, simbolo):
    nodos = buscar(raiz, simbolo, [])
    maximo = 0
    i = 0
    while i < len(nodos):
        if nodos[i].nivel > maximo:
            maximo = nodos[i].nivel
        i = i + 1
    return maximo


def resumen_errores(gestor):
    """Cada error como 'TIPO linea:columna', en el orden de la tabla."""
    resultado = []
    i = 0
    while i < len(gestor.errores):
        e = gestor.errores[i]
        resultado.append(e.tipo + ' ' + str(e.linea) + ':' + str(e.columna))
        i = i + 1
    return resultado


def resumen_simple(texto):
    """Resumen en linea del primer bloque, para las pruebas cortas."""
    parser = analizar(texto)
    return resumen_en_linea(en_linea_de(primer_bloque(parser.raiz)))


class LexicoDePrueba:
    """
    Un lexico falso que entrega una lista fija de tokens. Sirve para darle
    al parser secuencias que el lexico real nunca produce, y comprobar que
    la recuperacion de errores funciona y que el parser siempre termina.
    """

    def __init__(self, tipos):
        self.tokens = []
        i = 0
        while i < len(tipos):
            self.tokens.append(Token(i + 1, 'x', tipos[i], i + 1, 1))
            i = i + 1
        self.tokens.append(Token(len(tipos) + 1, '', FIN, len(tipos) + 1, 1))
        self.indice = 0

    def siguiente_token(self):
        if self.indice < len(self.tokens):
            token = self.tokens[self.indice]
            self.indice = self.indice + 1
            return token
        return self.tokens[len(self.tokens) - 1]


def analizar_tokens(tipos):
    gestor = GestorErrores()
    parser = AnalizadorSintactico(LexicoDePrueba(tipos), gestor)
    parser.analizar()
    return parser


# ======================================================================
# A. Archivo valido del enunciado
# ======================================================================

def prueba_ejemplo_valido(v):
    titulo('A. ejemplo_valido.md (archivo de la seccion 4.7 del enunciado)')
    parser = analizar(leer_ejemplo('ejemplo_valido.md'))
    raiz = parser.raiz

    v.verificar('sin errores lexicos ni sintacticos', parser.gestor.cantidad(),
                0)
    v.verificar('la raiz es <documento> y su ultima hoja es FIN',
                [raiz.simbolo, raiz.hijos[len(raiz.hijos) - 1].simbolo],
                [NT_DOCUMENTO, FIN])
    v.verificar('8 bloques, en el orden del archivo', bloques(raiz), [
        NT_ENCABEZADO, NT_PARRAFO, NT_ENCABEZADO, NT_LISTA, NT_CITA,
        NT_BLOQUE_CODIGO, '<regla_horizontal>', NT_PARRAFO,
    ])
    v.verificar('7 lineas vacias como hojas SALTO_PARRAFO del documento',
                len(buscar(raiz, SALTO_PARRAFO, [])), 7)

    encabezados = buscar(raiz, NT_ENCABEZADO, [])
    v.verificar('niveles de los encabezados (H1 y H2)',
                [encabezados[0].nivel, encabezados[1].nivel], [1, 2])

    parrafo = buscar(raiz, NT_PARRAFO, [])[0]
    v.verificar('linea 3: negrita, cursiva y codigo en linea en el arbol',
                resumen_en_linea(en_linea_de(parrafo)),
                'Este curso combina <b>teoría sólida</b> y '
                '<i>práctica de código</i>, con ejemplos en '
                '<code>Python</code> .')

    lista = buscar(raiz, NT_LISTA, [])[0]
    v.verificar('lista anidada en 3 niveles, con la jerarquia exacta',
                resumen_lista(lista),
                '[Análisis léxico [Autómatas finitos, Expresiones '
                'regulares], Análisis sintáctico [Gramáticas libres de '
                'contexto [Recursión por la izquierda, Recursión por la '
                'derecha]], Generación de código]')
    v.verificar('profundidad maxima de lista: 3',
                nivel_maximo(raiz, NT_LISTA), 3)

    cita = buscar(raiz, NT_CITA, [])[0]
    v.verificar('cita anidada en 2 niveles', resumen_cita(cita),
                'cita1[El análisis sintáctico es donde la teoría se '
                'encuentra con la práctica., cita2[Y donde más se aprende, '
                'según los estudiantes.]]')
    v.verificar('profundidad maxima de cita: 2',
                nivel_maximo(raiz, NT_CITA), 2)

    codigo = buscar(raiz, NT_BLOQUE_CODIGO, [])[0]
    lenguaje = hijo_con_simbolo(codigo, LENGUAJE_CODIGO)
    lineas = buscar(codigo, TEXTO_LITERAL, [])
    v.verificar('bloque de codigo: lenguaje y lineas literales',
                [lenguaje.token.lexema, lineas[0].token.lexema,
                 lineas[1].token.lexema],
                ['python', 'def hola():', '    print("Hola LFP")'])

    v.verificar('la frontera del arbol son los 77 tokens, en orden',
                frontera_es_la_entrada(parser), True)

    un_hijo = True
    nodos = buscar(raiz, NT_BLOQUE, [])
    i = 0
    while i < len(nodos):
        if len(nodos[i].hijos) != 1:
            un_hijo = False
        i = i + 1
    v.verificar('cada <bloque> tiene exactamente un hijo', un_hijo, True)


# ======================================================================
# B. Elementos en linea (recursion mutua negrita / cursiva)
# ======================================================================

def prueba_en_linea(v):
    titulo('B. Elementos en linea')

    v.verificar('cursiva dentro de negrita',
                resumen_simple('**a *b* c**\n'), '<b>a <i>b</i> c</b>')
    v.verificar('negrita dentro de cursiva',
                resumen_simple('*a **b** c*\n'), '<i>a <b>b</b> c</i>')
    v.verificar('tres niveles alternados (recursion mutua)',
                resumen_simple('*a **b *c* d** e*\n'),
                '<i>a <b>b <i>c</i> d</b> e</i>')
    v.verificar('"***ambas***"', resumen_simple('***ambas***\n'),
                '<b><i>ambas</i></b>')
    v.verificar('"***" al cerrar con cursiva en la cima',
                resumen_simple('**negrita *y cursiva***\n'),
                '<b>negrita <i>y cursiva</i></b>')
    v.verificar('"***" al cerrar con negrita en la cima',
                resumen_simple('*cursiva **y negrita***\n'),
                '<i>cursiva <b>y negrita</b></i>')
    v.verificar('dos negritas seguidas',
                resumen_simple('**a** y **b**\n'), '<b>a</b> y <b>b</b>')
    v.verificar('"**" igual a la cima cierra (D-04): no hay negrita anidada',
                resumen_simple('**a **b** c**\n'), '<b>a </b>b<b> c</b>')
    v.verificar('codigo en linea: su contenido no se interpreta',
                resumen_simple('`**x**`\n'), '<code>**x**</code>')
    v.verificar('codigo en linea dentro de negrita',
                resumen_simple('**`x` en negrita**\n'),
                '<b><code>x</code> en negrita</b>')
    v.verificar('codigo en linea vacio', resumen_simple('``\n'),
                '<code></code>')
    v.verificar('formato dentro de un encabezado',
                resumen_simple('# Título con **negrita**\n'),
                'Título con <b>negrita</b>')

    v.verificar('negrita que cruza dos lineas de un parrafo (D-02): el '
                'SALTO_LINEA queda adentro', resumen_simple('a **b\nc** d\n'),
                'a <b>b|c</b> d')
    v.verificar('cursiva y negrita que cruzan lineas',
                resumen_simple('*a **b\nc** d\ne*\n'),
                '<i>a <b>b|c</b> d|e</i>')
    v.verificar('codigo en linea que cruza lineas',
                resumen_simple('`a\nb`\n'), '<code>a|b</code>')
    parrafo = primer_bloque(analizar('a **b\nc** d\ne\n').raiz)
    v.verificar('la 1a <linea_texto> abarca las dos lineas de la negrita',
                len(buscar(parrafo, NT_LINEA_TEXTO, [])), 2)

    sin_errores = True
    casos = ['**a *b* c**\n', '*a **b *c* d** e*\n', '***ambas***\n',
             '**negrita *y cursiva***\n', '*cursiva **y negrita***\n',
             'a **b\nc** d\n', '*a **b\nc** d\ne*\n', '`a\nb`\n']
    i = 0
    while i < len(casos):
        if analizar(casos[i]).gestor.hay_errores():
            sin_errores = False
        i = i + 1
    v.verificar('ninguno de los casos anidados produce errores', sin_errores,
                True)
    v.verificar('frontera completa con una negrita, una cursiva y un '
                'codigo que cruzan lineas',
                frontera_es_la_entrada(analizar('a **b\nc** *d\ne* `f\ng`\n')),
                True)


# ======================================================================
# C. Bloques simples
# ======================================================================

def prueba_bloques(v):
    titulo('C. Encabezados, parrafos, reglas y bloques de codigo')

    parser = analizar('linea uno\nlinea dos\n\notro\n')
    v.verificar('una linea vacia separa dos parrafos', bloques(parser.raiz),
                [NT_PARRAFO, NT_PARRAFO])
    v.verificar('lineas consecutivas forman un solo parrafo (D-13)',
                len(buscar(parser.raiz, NT_LINEA_TEXTO, [])), 3)

    v.verificar('un encabezado corta el parrafo sin linea vacia',
                bloques(analizar('texto\n# Titulo\n').raiz),
                [NT_PARRAFO, NT_ENCABEZADO])

    parser = analizar('# a\n## b\n### c\n#### d\n##### e\n###### f\n')
    encabezados = buscar(parser.raiz, NT_ENCABEZADO, [])
    niveles = []
    i = 0
    while i < len(encabezados):
        niveles.append(encabezados[i].nivel)
        i = i + 1
    v.verificar('niveles de encabezado H1 a H6', niveles, [1, 2, 3, 4, 5, 6])

    encabezado = primer_bloque(analizar('# \n').raiz)
    v.verificar('encabezado vacio: <en_linea> sin hijos',
                len(en_linea_de(encabezado).hijos), 0)

    v.verificar('regla horizontal entre parrafos',
                bloques(analizar('a\n\n---\n\nb\n').raiz),
                [NT_PARRAFO, '<regla_horizontal>', NT_PARRAFO])

    codigo = primer_bloque(analizar('```\nx\n```\n').raiz)
    v.verificar('bloque de codigo sin lenguaje',
                hijo_con_simbolo(codigo, LENGUAJE_CODIGO), None)

    codigo = primer_bloque(analizar('```\na\n\nb\n```\n').raiz)
    lineas = buscar(codigo, TEXTO_LITERAL, [])
    v.verificar('la linea vacia dentro del bloque se conserva',
                [lineas[0].token.lexema, lineas[1].token.lexema,
                 lineas[2].token.lexema], ['a', '', 'b'])

    parser = analizar('```js\nsin cerrar\n')
    v.verificar('bloque sin cerrar: solo el error lexico, ningun sintactico',
                resumen_errores(parser.gestor),
                ['BLOQUE_CODIGO_SIN_CERRAR 1:1'])
    v.verificar('bloque sin cerrar: el contenido llega hasta el final',
                buscar(parser.raiz, TEXTO_LITERAL, [])[0].token.lexema,
                'sin cerrar')


# ======================================================================
# D. Listas
# ======================================================================

def prueba_listas(v):
    titulo('D. Listas anidadas')

    parser = analizar('- a\n  - b\n    - c\n      - d\n')
    v.verificar('4 niveles de anidamiento',
                resumen_lista(primer_bloque(parser.raiz)), '[a [b [c [d]]]]')
    v.verificar('profundidad 4', nivel_maximo(parser.raiz, NT_LISTA), 4)

    v.verificar('volver dos niveles de una vez',
                resumen_lista(primer_bloque(
                    analizar('- a\n  - b\n    - c\n- d\n').raiz)),
                '[a [b [c]], d]')
    v.verificar('una linea vacia separa dos listas (D-08)',
                bloques(analizar('- a\n\n- b\n').raiz),
                [NT_LISTA, NT_LISTA])
    v.verificar('una linea de texto termina la lista',
                bloques(analizar('- a\ntexto\n').raiz),
                [NT_LISTA, NT_PARRAFO])
    v.verificar('formato en linea dentro de un item',
                resumen_lista(primer_bloque(
                    analizar('- **a** y *b*\n').raiz)),
                '[<b>a</b> y <i>b</i>]')
    v.verificar('-, * y + en la misma lista',
                resumen_lista(primer_bloque(
                    analizar('- a\n* b\n+ c\n').raiz)), '[a, b, c]')
    v.verificar('item vacio', resumen_lista(primer_bloque(
        analizar('- \n- b\n').raiz)), '[, b]')


# ======================================================================
# E. Citas
# ======================================================================

def prueba_citas(v):
    titulo('E. Citas anidadas')

    v.verificar('3 niveles', resumen_cita(primer_bloque(
        analizar('> a\n>> b\n>>> c\n').raiz)),
        'cita1[a, cita2[b, cita3[c]]]')
    v.verificar('volver al nivel 1 despues del nivel 2',
                resumen_cita(primer_bloque(
                    analizar('> a\n>> b\n> c\n').raiz)),
                'cita1[a, cita2[b], c]')
    v.verificar('saltar del nivel 1 al 3 crea el nivel 2 vacio (D-09)',
                resumen_cita(primer_bloque(analizar('> a\n>>> c\n').raiz)),
                'cita1[a, cita2[cita3[c]]]')
    v.verificar('empezar directamente en el nivel 2',
                resumen_cita(primer_bloque(analizar('>> x\n').raiz)),
                'cita1[cita2[x]]')
    v.verificar('"> >" equivale a ">>"',
                resumen_cita(primer_bloque(analizar('> > x\n').raiz)),
                'cita1[cita2[x]]')
    v.verificar('encabezado dentro de una cita',
                resumen_cita(primer_bloque(
                    analizar('> # Titulo\n> texto\n').raiz)),
                'cita1[H1:Titulo, texto]')
    v.verificar('formato en linea dentro de una cita',
                resumen_cita(primer_bloque(
                    analizar('> **negrita** en cita\n').raiz)),
                'cita1[<b>negrita</b> en cita]')
    v.verificar('linea de cita vacia',
                resumen_cita(primer_bloque(analizar('> \n').raiz)),
                'cita1[]')
    v.verificar('una linea vacia separa dos citas',
                bloques(analizar('> a\n\n> b\n').raiz), [NT_CITA, NT_CITA])
    v.verificar('una linea sin ">" termina la cita',
                bloques(analizar('> a\nb\n').raiz), [NT_CITA, NT_PARRAFO])

    parser = analizar(leer_ejemplo('casos_borde.md'))
    v.verificar('casos_borde.md: sin errores lexicos ni sintacticos',
                parser.gestor.cantidad(), 0)


# ======================================================================
# F. Errores sintacticos y recuperacion
# ======================================================================

def prueba_errores(v):
    titulo('F. Errores sintacticos y recuperacion')

    parser = analizar('- a\n    - b\n')
    v.verificar('salto de 0 a 4 espacios: INDENTACION_INVALIDA',
                resumen_errores(parser.gestor),
                ['INDENTACION_INVALIDA 2:3'])
    e = parser.gestor.errores[0]
    v.verificar('... de fase sintactica, con mensaje y posicion',
                [e.fase, e.descripcion],
                [err.FASE_SINTACTICA, 'Indentación inválida en línea 2, '
                 'columna 3: la sangría sube más de un nivel de una vez'])

    parser = analizar('- a\n    - b\n- c\n\nfin\n')
    v.verificar('despues del error la lista sigue con "c" y luego el parrafo',
                [bloques(parser.raiz),
                 len(primer_bloque(parser.raiz).hijos)],
                [[NT_LISTA, NT_PARRAFO], 2])
    v.verificar('... y los INDENT/DEDENT quedan balanceados en el arbol',
                frontera_es_la_entrada(parser), True)

    v.verificar('salto de 3 niveles: se reporta una sola vez (D-22)',
                resumen_errores(analizar('- a\n      - b\n').gestor),
                ['INDENTACION_INVALIDA 2:3'])
    v.verificar('lista que empieza con sangria: sublista sin padre',
                resumen_errores(analizar('  - a\n').gestor),
                ['INDENTACION_INVALIDA 1:1'])

    parser = analizar('- a\n\n  - b\n- c\n')
    v.verificar('sublista despues de una linea vacia: sin padre',
                resumen_errores(parser.gestor), ['INDENTACION_INVALIDA 3:1'])
    v.verificar('... y la lista "- c" se sigue reconociendo',
                bloques(parser.raiz), [NT_LISTA, NT_LISTA])

    parser = analizar('- a\n     - b\n')
    fases = []
    i = 0
    while i < len(parser.gestor.errores):
        fases.append(parser.gestor.errores[i].fase)
        i = i + 1
    v.verificar('5 espacios: salto de nivel (sintactico) y sangria impar '
                '(lexico)',
                [resumen_errores(parser.gestor), fases],
                [['INDENTACION_INVALIDA 2:3', 'INDENTACION_INVALIDA 2:6'],
                 [err.FASE_SINTACTICA, err.FASE_LEXICA]])

    parser = analizar('>texto\n')
    v.verificar('">texto": CITA_MAL_FORMADA en la columna del ">"',
                resumen_errores(parser.gestor), ['CITA_MAL_FORMADA 1:1'])
    v.verificar('... mensaje del enunciado',
                parser.gestor.errores[0].descripcion,
                'Cita mal formada en línea 1, columna 1')
    v.verificar('">>texto": la columna es la del ultimo ">"',
                resumen_errores(analizar('>>texto\n').gestor),
                ['CITA_MAL_FORMADA 1:2'])
    v.verificar('"> >texto"', resumen_errores(analizar('> >texto\n').gestor),
                ['CITA_MAL_FORMADA 1:3'])
    v.verificar('"># Titulo" tambien esta mal formada',
                resumen_errores(analizar('># Titulo\n').gestor),
                ['CITA_MAL_FORMADA 1:1'])
    v.verificar('"> texto", ">" solo y "> # T" son validas',
                [analizar('> texto\n').gestor.cantidad(),
                 analizar('>\n').gestor.cantidad(),
                 analizar('> # T\n').gestor.cantidad()], [0, 0, 0])

    parser = analizar(leer_ejemplo('errores_sintacticos.md'))
    v.verificar('errores_sintacticos.md: errores lexicos y sintacticos '
                'ordenados por posicion', resumen_errores(parser.gestor), [
                    'INDENTACION_INVALIDA 4:3',
                    'INDENTACION_INVALIDA 7:1',
                    'CITA_MAL_FORMADA 9:1',
                    'CITA_MAL_FORMADA 11:2',
                    'NEGRITA_SIN_CERRAR 13:13',
                ])
    v.verificar('... el analisis llega hasta FIN y el arbol esta completo',
                frontera_es_la_entrada(parser), True)

    parser = analizar_tokens([NUMERAL, TEXTO, DEDENT, SALTO_LINEA,
                              TEXTO, SALTO_LINEA])
    v.verificar('token que sobra dentro de un encabezado: TOKEN_INESPERADO',
                resumen_errores(parser.gestor), ['TOKEN_INESPERADO 3:1'])
    v.verificar('... se sincroniza en el SALTO_LINEA y sigue el parrafo',
                bloques(parser.raiz), [NT_ENCABEZADO, NT_PARRAFO])

    parser = analizar_tokens([TEXTO_LITERAL, TEXTO, SALTO_LINEA,
                              TEXTO, SALTO_LINEA])
    v.verificar('token que no puede empezar un bloque: se descarta la linea',
                [resumen_errores(parser.gestor), bloques(parser.raiz),
                 len(buscar(parser.raiz, NT_LINEA_TEXTO, []))],
                [['TOKEN_INESPERADO 1:1'], [NT_PARRAFO], 1])


# ======================================================================
# G. Robustez: documentos y secuencias generados al azar
# ======================================================================

def prueba_robustez(v):
    titulo('G. Robustez (semilla fija, siempre los mismos casos)')
    generador = random.Random(2026)

    piezas = ['#', '##', '#######', '-', '- ', '* ', '+ ', '*', '**', '`',
              '```', '>', '> ', '>>', '---', '  ', '    ', ' ', '\t',
              'texto', 'a', '1.', '\n', '\n', '\n', '1. ', '[ ] ', '~~',
              '[', ']', '(', ')', '![', '|', '|---|', ':']
    documentos = 400
    terminan_en_fin = 0
    fronteras_completas = 0
    inesperados = 0
    i = 0
    while i < documentos:
        texto = ''
        cantidad = generador.randint(0, 40)
        j = 0
        while j < cantidad:
            texto = texto + generador.choice(piezas)
            j = j + 1
        parser = analizar(texto)
        ultimo = parser.raiz.hijos[len(parser.raiz.hijos) - 1]
        if ultimo.es(FIN):
            terminan_en_fin = terminan_en_fin + 1
        if frontera_es_la_entrada(parser):
            fronteras_completas = fronteras_completas + 1
        inesperados = (inesperados +
                       parser.gestor.contar_tipo(err.TOKEN_INESPERADO))
        i = i + 1

    v.verificar(str(documentos) + ' documentos al azar: el parser siempre '
                'llega a FIN', terminan_en_fin, documentos)
    v.verificar('... el arbol siempre contiene todos los tokens, en orden',
                fronteras_completas, documentos)
    v.verificar('... el lexico nunca le entrega al parser una secuencia '
                'imposible (0 TOKEN_INESPERADO)', inesperados, 0)

    tipos = [NUMERAL, VINETA, INDENT, DEDENT, CITA, CERCA_CODIGO,
             LENGUAJE_CODIGO, TEXTO_LITERAL, REGLA_HORIZONTAL, NEGRITA,
             CURSIVA, CODIGO_INLINE, TEXTO, SALTO_LINEA, SALTO_PARRAFO,
             NUMERO_LISTA, CASILLA, TACHADO, CORCHETE_ABRE, IMAGEN_ABRE,
             CORCHETE_CIERRA, PARENTESIS_ABRE, URL, PARENTESIS_CIERRA, BARRA,
             SEPARADOR_TABLA]
    secuencias = 300
    terminan = 0
    i = 0
    while i < secuencias:
        secuencia = []
        j = 0
        while j < 25:
            secuencia.append(generador.choice(tipos))
            j = j + 1
        parser = analizar_tokens(secuencia)
        if parser.raiz.hijos[len(parser.raiz.hijos) - 1].es(FIN):
            terminan = terminan + 1
        i = i + 1
    v.verificar(str(secuencias) + ' secuencias de tokens al azar: el modo '
                'panico siempre termina en FIN', terminan, secuencias)


# ======================================================================
# H. Alcance opcional (D-29 a D-33)
# ======================================================================

def prueba_alcance_opcional(v):
    titulo('H. Alcance opcional')

    raiz = analizar('1. a\n2. b\n').raiz
    lista = primer_bloque(raiz)
    v.verificar('lista numerada: <lista> con el atributo numerada',
                [lista.simbolo, lista.numerada, len(lista.hijos)],
                [NT_LISTA, True, 2])
    v.verificar('si cambia el marcador empieza otra lista (<lista(t)>)',
                bloques(analizar('- a\n- b\n1. c\n').raiz),
                [NT_LISTA, NT_LISTA])
    raiz = analizar('- a\n  - b\n  1. c\n').raiz
    sublista = buscar(raiz, NT_SUBLISTA, [])[0]
    v.verificar('una sublista puede tener dos listas de distinto marcador',
                len(buscar(sublista, NT_LISTA, [])), 2)
    item = buscar(analizar('- [x] hecho\n').raiz, NT_ITEM_LISTA, [])[0]
    v.verificar('item de tarea: la CASILLA es una hoja del <item_lista>',
                [item.hijos[0].simbolo, item.hijos[1].simbolo],
                [VINETA, CASILLA])

    v.verificar('tachado con negrita adentro',
                resumen_simple('a ~~b **c** d~~\n'),
                'a <s>b <b>c</b> d</s>')
    v.verificar('tachado dentro de cursiva dentro de negrita',
                resumen_simple('**a *b ~~c~~ d* e**\n'),
                '<b>a <i>b <s>c</s> d</i> e</b>')
    v.verificar('enlace con formato en su texto',
                resumen_simple('ver [la *doc*](https://x.org) ya\n'),
                'ver <a https://x.org>la <i>doc</i></a> ya')
    v.verificar('enlace dentro de negrita',
                resumen_simple('**[a](u)**\n'), '<b><a u>a</a></b>')
    v.verificar('imagen: el texto alternativo queda literal',
                resumen_simple('![logo *x*](a.png)\n'), '<img logo *x*>')

    raiz = analizar('| A | B | C |\n|:--|:-:|--:|\n| 1 | 2 | 3 |\n'
                    '| 4 || 6 |\n').raiz
    tabla = primer_bloque(raiz)
    filas = buscar(tabla, NT_FILA_TABLA, [])
    v.verificar('tabla: encabezado, separadora y dos filas',
                [tabla.simbolo, len(filas)], [NT_TABLA, 3])
    v.verificar('las alineaciones salen del SEPARADOR_TABLA',
                tabla.alineaciones, ['left', 'center', 'right'])
    v.verificar('cada fila tiene sus <celda>; "||" es una celda vacia',
                [len(buscar(filas[1], NT_CELDA, [])),
                 len(buscar(filas[2], NT_CELDA, [])),
                 resumen_en_linea(buscar(filas[2], NT_EN_LINEA, [])[1])],
                [3, 3, ''])

    texto = ('| a | b |\n| c | d |\n\n|---|\n| e |\n\n'
             '| f | g |\n|---|---|\n| h |\n| i | j\n|---|---|\n')
    parser = analizar(texto)
    v.verificar('TABLA_MAL_FORMADA: sin separadora, sin encabezado, celdas '
                "de menos, sin '|' final y separadora repetida",
                resumen_errores(parser.gestor),
                ['TABLA_MAL_FORMADA 1:1', 'TABLA_MAL_FORMADA 4:1',
                 'TABLA_MAL_FORMADA 9:1', 'TABLA_MAL_FORMADA 10:1',
                 'TABLA_MAL_FORMADA 11:1'])
    v.verificar('mensaje de TABLA_MAL_FORMADA',
                parser.gestor.errores[2].descripcion,
                'Tabla mal formada en línea 9, columna 1: la fila tiene 1 '
                'celda y la tabla 2 columnas')
    v.verificar('la frontera sigue completa con las tablas mal formadas',
                frontera_es_la_entrada(parser), True)
    v.verificar('sin encabezado, las filas se comparan con la separadora',
                resumen_errores(analizar('|-|-|\n|a|\n').gestor),
                ['TABLA_MAL_FORMADA 1:1', 'TABLA_MAL_FORMADA 2:1'])

    texto = ('1. [x] **a** ~~b~~ [c](d) ![e](f)\n  - [ ] g\n\n'
             '| h | *i* |\n|---|:-:|\n| `j` | [k](l) |\n')
    parser = analizar(texto)
    v.verificar('documento con todo el alcance opcional: sin errores y con '
                'la frontera completa',
                [parser.gestor.cantidad(), frontera_es_la_entrada(parser)],
                [0, True])


# ======================================================================

def main():
    v = Verificador()
    prueba_ejemplo_valido(v)
    prueba_en_linea(v)
    prueba_bloques(v)
    prueba_listas(v)
    prueba_citas(v)
    prueba_errores(v)
    prueba_robustez(v)
    prueba_alcance_opcional(v)

    print('')
    print('=' * 60)
    total = v.correctas + v.fallidas
    print('Verificaciones: ' + str(total) + '   correctas: ' +
          str(v.correctas) + '   fallidas: ' + str(v.fallidas))
    print('=' * 60)
    if v.fallidas > 0:
        sys.exit(1)


main()
