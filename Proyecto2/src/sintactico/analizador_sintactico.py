# -*- coding: utf-8 -*-
"""
analizador_sintactico.py
AnalizadorSintactico: parser descendente recursivo de MarkdownCheck.

RESTRICCION DEL PROYECTO: no se usan librerias de parsing (ply, lark,
antlr4...). Cada simbolo no terminal de la gramatica (forma EBNF, seccion
4.3 del documento de diseno) es una funcion, y cada funcion:
  1. crea el nodo de su no terminal;
  2. consume los terminales que le tocan; cada uno queda como hoja;
  3. llama a la funcion de cada no terminal que contiene y agrega como hijo
     el nodo que esa funcion devuelve.
Cuando la gramatica es recursiva (una cursiva dentro de una negrita dentro
de una cursiva; una cita dentro de otra), la funcion termina llamandose a si
misma: esa es la recursion del "descendente recursivo".

Cada decision se toma mirando un solo token, self.actual: la gramatica es
LL(1). Las listas de PRIMEROS de abajo son los conjuntos FIRST de la
seccion 4.2 del diseno.

Mapa no terminal -> funcion
    <documento>          parsear_documento()
    <elemento_doc>       parsear_elemento_doc(padre)
    <bloque>             parsear_bloque()
    <encabezado>         parsear_encabezado()
    <parrafo>            parsear_parrafo()
    <linea_texto>        parsear_linea_texto()
    <lista>              parsear_lista(nivel)
    <item_lista>         parsear_item_lista(nivel)
    <sublista>           parsear_sublista(nivel)
    <cita(n)>            parsear_cita(n)
    <elemento_cita(n)>   parsear_elemento_cita(padre, n)
    <contenido_cita>     parsear_contenido_cita()
    <bloque_codigo>      parsear_bloque_codigo()
    <contenido_codigo>   parsear_contenido_codigo()
    <regla_horizontal>   parsear_regla_horizontal()
    <en_linea>           parsear_en_linea()
    <elemento_linea>     parsear_elemento_linea(padre)
    <negrita>            parsear_negrita()
    <en_linea_n>         parsear_en_linea_n()
    <elemento_n>         parsear_elemento_n(padre)
    <cursiva>            parsear_cursiva()
    <en_linea_c>         parsear_en_linea_c()
    <elemento_c>         parsear_elemento_c(padre)
    <codigo_inline>      parsear_codigo_inline()

  Alcance opcional (D-29 a D-33)
    <tachado>            parsear_tachado()
    <en_linea_t>         parsear_en_linea_t()
    <elemento_t>         parsear_elemento_t(padre)
    <enlace>             parsear_enlace()
    <imagen>             parsear_imagen()
    <destino>            parsear_destino()
    <tabla>              parsear_tabla()
    <fila_tabla>         parsear_fila_tabla()
    <celda>              parsear_celda()

Las funciones parsear_elemento_*() son SELECCIONES: deciden que alternativa
tomar y agregan el resultado al nodo padre, sin crear un nodo propio (D-17).

Recuperacion de errores (seccion 5 del diseno)
    INDENTACION_INVALIDA   parsear_sublista(), _recuperar_sublista_huerfana()
    CITA_MAL_FORMADA       _revisar_separacion_cita()
    TABLA_MAL_FORMADA      parsear_tabla(), parsear_fila_tabla()
    TOKEN_INESPERADO       _coincidir() + _sincronizar(), _descartar_linea()
"""

from lexico.token import NUMERAL, VINETA, INDENT, DEDENT, CITA
from lexico.token import CERCA_CODIGO, LENGUAJE_CODIGO, TEXTO_LITERAL
from lexico.token import REGLA_HORIZONTAL, NEGRITA, CURSIVA, CODIGO_INLINE
from lexico.token import TEXTO, SALTO_LINEA, SALTO_PARRAFO, FIN
from lexico.token import NUMERO_LISTA, CASILLA, TACHADO, CORCHETE_ABRE
from lexico.token import IMAGEN_ABRE, CORCHETE_CIERRA, PARENTESIS_ABRE, URL
from lexico.token import PARENTESIS_CIERRA, BARRA, SEPARADOR_TABLA
from sintactico.nodo_ast import no_terminal, terminal
from sintactico.nodo_ast import NT_DOCUMENTO, NT_BLOQUE, NT_ENCABEZADO
from sintactico.nodo_ast import NT_PARRAFO, NT_LINEA_TEXTO, NT_LISTA
from sintactico.nodo_ast import NT_ITEM_LISTA, NT_SUBLISTA, NT_CITA
from sintactico.nodo_ast import NT_CONTENIDO_CITA, NT_BLOQUE_CODIGO
from sintactico.nodo_ast import NT_CONTENIDO_CODIGO, NT_REGLA_HORIZONTAL
from sintactico.nodo_ast import NT_EN_LINEA, NT_EN_LINEA_N, NT_EN_LINEA_C
from sintactico.nodo_ast import NT_NEGRITA, NT_CURSIVA, NT_CODIGO_INLINE
from sintactico.nodo_ast import NT_TACHADO, NT_EN_LINEA_T, NT_ENLACE
from sintactico.nodo_ast import NT_IMAGEN, NT_DESTINO, NT_TABLA
from sintactico.nodo_ast import NT_FILA_TABLA, NT_CELDA
from errores import error_analisis as err

# ----------------------------------------------------------------------
# Conjuntos FIRST (seccion 4.2 del diseno)
# ----------------------------------------------------------------------
PRIMEROS_EN_LINEA = [TEXTO, NEGRITA, CURSIVA, TACHADO, CODIGO_INLINE,
                     CORCHETE_ABRE, IMAGEN_ABRE]
# Dentro de una negrita, una cursiva o un tachado puede venir un
# SALTO_LINEA: en un parrafo se pueden cerrar en una linea siguiente (D-02).
# Cada variante deja afuera a su propio delimitador (D-05).
PRIMEROS_EN_LINEA_N = [TEXTO, CURSIVA, TACHADO, CODIGO_INLINE, CORCHETE_ABRE,
                       IMAGEN_ABRE, SALTO_LINEA]
PRIMEROS_EN_LINEA_C = [TEXTO, NEGRITA, TACHADO, CODIGO_INLINE, CORCHETE_ABRE,
                       IMAGEN_ABRE, SALTO_LINEA]
PRIMEROS_EN_LINEA_T = [TEXTO, NEGRITA, CURSIVA, CODIGO_INLINE, CORCHETE_ABRE,
                       IMAGEN_ABRE, SALTO_LINEA]

# Un parrafo empieza con un elemento en linea: una linea sin contenido
# nunca llega como SALTO_LINEA solo, el lexico la convierte en SALTO_PARRAFO.
PRIMEROS_PARRAFO = PRIMEROS_EN_LINEA

PRIMEROS_BLOQUE = [NUMERAL, VINETA, NUMERO_LISTA, CITA, CERCA_CODIGO,
                   REGLA_HORIZONTAL, BARRA, SEPARADOR_TABLA, TEXTO, NEGRITA,
                   CURSIVA, TACHADO, CODIGO_INLINE, CORCHETE_ABRE,
                   IMAGEN_ABRE]

# Una <celda> puede estar vacia, asi que una fila sigue mientras venga algo
# que empiece una celda o la BARRA que la cierra.
PRIMEROS_CELDA = [BARRA, TEXTO, NEGRITA, CURSIVA, TACHADO, CODIGO_INLINE,
                  CORCHETE_ABRE, IMAGEN_ABRE]

# Modo panico: puntos seguros desde donde se puede seguir analizando.
TOKENS_SINCRONIZACION = [SALTO_LINEA, SALTO_PARRAFO, FIN]


class AnalizadorSintactico:

    def __init__(self, lexico, gestor):
        self.lexico = lexico
        self.gestor = gestor
        self.raiz = None
        # El token de lookahead. Se pide el primero desde ya.
        self.actual = lexico.siguiente_token()

    def analizar(self):
        """Analiza el documento completo y devuelve la raiz del arbol."""
        self.raiz = self.parsear_documento()
        return self.raiz

    # ==================================================================
    # Primitivas
    # ==================================================================

    def _es(self, tipo):
        return self.actual.tipo == tipo

    def _actual_es_uno_de(self, tipos):
        i = 0
        while i < len(tipos):
            if self.actual.tipo == tipos[i]:
                return True
            i = i + 1
        return False

    def _avanzar(self):
        """Consume el token actual y pide el siguiente al lexico."""
        consumido = self.actual
        self.actual = self.lexico.siguiente_token()
        return consumido

    def _coincidir(self, tipo, padre):
        """
        Consume un terminal que la gramatica exige y lo agrega como hoja del
        nodo padre. Devuelve el token, o None si no se pudo recuperar.

        Si el token actual no es el esperado: TOKEN_INESPERADO y modo panico.
        Si al sincronizar se llega justo al token esperado (lo normal cuando
        se esperaba un SALTO_LINEA), se consume y el analisis sigue como si
        nada.
        """
        if not self._es(tipo):
            self._token_inesperado(tipo)
            self._sincronizar()
            if not self._es(tipo):
                return None
        token = self._avanzar()
        padre.agregar(terminal(token))
        return token

    def _nivel_cita(self, token):
        """El nivel de una CITA es la cantidad de '>' de su lexema (D-09)."""
        nivel = 0
        i = 0
        while i < len(token.lexema):
            if token.lexema[i] == '>':
                nivel = nivel + 1
            i = i + 1
        return nivel

    # ==================================================================
    # Documento y bloques
    # ==================================================================

    def parsear_documento(self):
        """<documento> ::= { <elemento_doc> } FIN"""
        nodo = no_terminal(NT_DOCUMENTO)
        while not self._es(FIN):
            self.parsear_elemento_doc(nodo)
        self._coincidir(FIN, nodo)
        return nodo

    def parsear_elemento_doc(self, padre):
        """
        <elemento_doc> ::= <bloque> | SALTO_PARRAFO

        Seleccion: agrega al padre lo que reconozca. Si el token no puede
        empezar un bloque, se recupera aqui. Cada camino consume al menos
        un token, asi que el ciclo de parsear_documento() siempre avanza.
        """
        if self._es(SALTO_PARRAFO):
            self._coincidir(SALTO_PARRAFO, padre)
        elif self._actual_es_uno_de(PRIMEROS_BLOQUE):
            padre.agregar(self.parsear_bloque())
        elif self._es(INDENT):
            self._recuperar_sublista_huerfana(padre)
        else:
            self._token_inesperado('el inicio de un bloque')
            self._descartar_linea()

    def parsear_bloque(self):
        """
        <bloque> ::= <encabezado> | <parrafo> | <lista> | <cita(1)>
                   | <bloque_codigo> | <regla_horizontal> | <tabla>

        Los FIRST de las alternativas son disjuntos: el token actual decide.
        """
        nodo = no_terminal(NT_BLOQUE)
        if self._es(NUMERAL):
            nodo.agregar(self.parsear_encabezado())
        elif self._es(VINETA) or self._es(NUMERO_LISTA):
            nodo.agregar(self.parsear_lista(1))
        elif self._es(BARRA) or self._es(SEPARADOR_TABLA):
            nodo.agregar(self.parsear_tabla())
        elif self._es(CITA):
            nodo.agregar(self.parsear_cita(1))
        elif self._es(CERCA_CODIGO):
            nodo.agregar(self.parsear_bloque_codigo())
        elif self._es(REGLA_HORIZONTAL):
            nodo.agregar(self.parsear_regla_horizontal())
        else:
            nodo.agregar(self.parsear_parrafo())
        return nodo

    def parsear_encabezado(self):
        """<encabezado> ::= NUMERAL <en_linea> SALTO_LINEA"""
        nodo = no_terminal(NT_ENCABEZADO)
        numeral = self._coincidir(NUMERAL, nodo)
        if numeral is not None:
            nodo.nivel = len(numeral.lexema)
        nodo.agregar(self.parsear_en_linea())
        self._coincidir(SALTO_LINEA, nodo)
        return nodo

    def parsear_parrafo(self):
        """
        <parrafo> ::= <linea_texto> { <linea_texto> }

        Voraz (seccion 4.2): sigue agregando lineas mientras la siguiente
        pueda empezar una. Termina con una linea vacia (SALTO_PARRAFO) o con
        una linea que empieza otro bloque (D-13).
        """
        nodo = no_terminal(NT_PARRAFO)
        nodo.agregar(self.parsear_linea_texto())
        while self._actual_es_uno_de(PRIMEROS_PARRAFO):
            nodo.agregar(self.parsear_linea_texto())
        return nodo

    def parsear_linea_texto(self):
        """
        <linea_texto> ::= <elemento_linea> <en_linea> SALTO_LINEA

        El primer <elemento_linea> lo garantiza quien llama (solo se llega
        aqui si el token actual esta en PRIMEROS_PARRAFO), asi que basta con
        analizar un <en_linea>, que ya incluye ese primer elemento.
        """
        nodo = no_terminal(NT_LINEA_TEXTO)
        nodo.agregar(self.parsear_en_linea())
        self._coincidir(SALTO_LINEA, nodo)
        return nodo

    def parsear_regla_horizontal(self):
        """<regla_horizontal> ::= REGLA_HORIZONTAL SALTO_LINEA"""
        nodo = no_terminal(NT_REGLA_HORIZONTAL)
        self._coincidir(REGLA_HORIZONTAL, nodo)
        self._coincidir(SALTO_LINEA, nodo)
        return nodo

    # ==================================================================
    # Bloques de codigo
    # ==================================================================

    def parsear_bloque_codigo(self):
        """
        <bloque_codigo> ::= CERCA_CODIGO [ LENGUAJE_CODIGO ] SALTO_LINEA
                            <contenido_codigo> CERCA_CODIGO SALTO_LINEA

        Si el archivo termina sin la cerca de cierre, el lexico ya reporto
        BLOQUE_CODIGO_SIN_CERRAR: el bloque llega hasta el fin del archivo y
        aqui no se vuelve a reportar.
        """
        nodo = no_terminal(NT_BLOQUE_CODIGO)
        self._coincidir(CERCA_CODIGO, nodo)
        if self._es(LENGUAJE_CODIGO):
            self._coincidir(LENGUAJE_CODIGO, nodo)
        self._coincidir(SALTO_LINEA, nodo)
        nodo.agregar(self.parsear_contenido_codigo())
        if self._es(FIN):
            return nodo
        self._coincidir(CERCA_CODIGO, nodo)
        self._coincidir(SALTO_LINEA, nodo)
        return nodo

    def parsear_contenido_codigo(self):
        """<contenido_codigo> ::= { TEXTO_LITERAL SALTO_LINEA }"""
        nodo = no_terminal(NT_CONTENIDO_CODIGO)
        while self._es(TEXTO_LITERAL):
            self._coincidir(TEXTO_LITERAL, nodo)
            self._coincidir(SALTO_LINEA, nodo)
        return nodo

    # ==================================================================
    # Listas
    # ==================================================================

    def parsear_lista(self, nivel):
        """
        <lista(t)> ::= <item_lista(t)> { <item_lista(t)> }

        'nivel' es la profundidad de esta lista (la raiz es 1). Queda como
        atributo del nodo para el Reporte 2.

        El atributo t es el tipo del marcador del primer item: VIÑETA o
        NUMERO_LISTA (D-29). La lista sigue mientras venga un item con el
        mismo marcador; si cambia, esta lista termina y empieza otra, igual
        que en Markdown.
        """
        nodo = no_terminal(NT_LISTA)
        nodo.nivel = nivel
        marcador = self.actual.tipo
        if marcador == NUMERO_LISTA:
            nodo.numerada = True
        nodo.agregar(self.parsear_item_lista(nivel, marcador))
        while self._es(marcador):
            nodo.agregar(self.parsear_item_lista(nivel, marcador))
        return nodo

    def parsear_item_lista(self, nivel, marcador):
        """
        <item_lista(t)> ::= MARCADOR[t] [ CASILLA ] <en_linea> SALTO_LINEA
                            [ <sublista> ]

        MARCADOR[t] es una VIÑETA o un NUMERO_LISTA, segun la lista. La
        CASILLA ('[ ]' o '[x]') hace del item una tarea (D-30).
        """
        nodo = no_terminal(NT_ITEM_LISTA)
        self._coincidir(marcador, nodo)
        if self._es(CASILLA):
            self._coincidir(CASILLA, nodo)
        nodo.agregar(self.parsear_en_linea())
        self._coincidir(SALTO_LINEA, nodo)
        if self._es(INDENT):
            nodo.agregar(self.parsear_sublista(nivel))
        return nodo

    def parsear_sublista(self, nivel):
        """
        <sublista> ::= INDENT <lista> { <lista> } DEDENT

        'nivel' es el de la lista que contiene a esta sublista; la lista de
        adentro es nivel + 1. Puede haber mas de una lista si a mitad de la
        sublista cambia el tipo de marcador ('- a' y despues '1. b').

        Recuperacion (D-06): si despues del INDENT viene OTRO INDENT, la
        sangria subio mas de un nivel de una vez. Se reporta
        INDENTACION_INVALIDA y el nivel que sobra se analiza como otra
        sublista (llamada recursiva). Asi cada INDENT encuentra su DEDENT y
        lo que sigue en el archivo no se desbalancea.
        """
        nodo = no_terminal(NT_SUBLISTA)
        self._coincidir(INDENT, nodo)
        if self._es(INDENT):
            self._error_indentacion('la sangría sube más de un nivel de '
                                    'una vez')
            nodo.agregar(self.parsear_sublista(nivel + 1))
        while self._es(VINETA) or self._es(NUMERO_LISTA):
            nodo.agregar(self.parsear_lista(nivel + 1))
        self._coincidir(DEDENT, nodo)
        return nodo

    def _recuperar_sublista_huerfana(self, padre):
        """
        Llego un INDENT donde deberia empezar un bloque: una lista que
        arranca con sangria, o una sublista despues de una linea vacia (que
        ya habia cerrado la lista, D-08). No hay item padre. Se reporta y se
        analiza como sublista, para consumir sus INDENT y DEDENT.
        """
        self._error_indentacion('sublista sin ítem padre')
        padre.agregar(self.parsear_sublista(0))

    # ==================================================================
    # Citas
    # ==================================================================

    def parsear_cita(self, nivel):
        """
        <cita(n)> ::= <elemento_cita(n)> { <elemento_cita(n)> }

        Sigue mientras venga una CITA de nivel n o mayor. Una de nivel menor
        pertenece a una cita de afuera: se termina y la funcion que llamo
        continua con ella.
        """
        nodo = no_terminal(NT_CITA)
        nodo.nivel = nivel
        self.parsear_elemento_cita(nodo, nivel)
        while self._es(CITA) and self._nivel_cita(self.actual) >= nivel:
            self.parsear_elemento_cita(nodo, nivel)
        return nodo

    def parsear_elemento_cita(self, padre, nivel):
        """
        <elemento_cita(n)> ::= CITA[n] <contenido_cita> | <cita(n+1)>

        Seleccion por el atributo: si la CITA es de nivel mayor que n,
        empieza una cita anidada; si no, es una linea de esta cita. Si salta
        de nivel 1 a 3, <cita(2)> queda sin lineas propias y solo contiene a
        <cita(3)>, igual que en Markdown (D-09).

        Se pregunta por "mayor" y no por "igual" a proposito: asi la rama de
        la linea siempre consume la CITA, y el parser avanza aunque llegara
        una cita con un nivel que no corresponde.
        """
        if self._nivel_cita(self.actual) > nivel:
            padre.agregar(self.parsear_cita(nivel + 1))
        else:
            cita = self._coincidir(CITA, padre)
            if cita is not None:
                self._revisar_separacion_cita(cita)
            padre.agregar(self.parsear_contenido_cita())

    def parsear_contenido_cita(self):
        """<contenido_cita> ::= <encabezado> | <en_linea> SALTO_LINEA"""
        nodo = no_terminal(NT_CONTENIDO_CITA)
        if self._es(NUMERAL):
            nodo.agregar(self.parsear_encabezado())
        else:
            nodo.agregar(self.parsear_en_linea())
            self._coincidir(SALTO_LINEA, nodo)
        return nodo

    def _revisar_separacion_cita(self, cita):
        """
        CITA_MAL_FORMADA (D-11): el ultimo '>' tiene que ir seguido de un
        espacio. El lexico salta ese espacio sin crear token, asi que se
        detecta con las posiciones: si el token siguiente empieza en la
        columna justo despues del ultimo '>', no hubo espacio.
        Un '>' solo al final de la linea es una linea de cita vacia, valida.
        """
        if self._es(SALTO_LINEA):
            return
        columna_siguiente = cita.columna + len(cita.lexema)
        if (self.actual.linea == cita.linea and
                self.actual.columna == columna_siguiente):
            columna_mayor = columna_siguiente - 1
            self._error(cita.lexema, err.CITA_MAL_FORMADA,
                        'Cita mal formada en línea ' + str(cita.linea) +
                        ', columna ' + str(columna_mayor),
                        cita.linea, columna_mayor)

    # ==================================================================
    # Tablas (alcance opcional, D-33)
    # ==================================================================

    def parsear_tabla(self):
        """
        <tabla> ::= <fila_tabla> SEPARADOR_TABLA SALTO_LINEA
                    { <fila_tabla> }

        Las alternativas se distinguen con un solo token: una fila empieza
        con BARRA y la fila separadora es un solo SEPARADOR_TABLA.

        TABLA_MAL_FORMADA (semantica, despues de reconocer cada fila): falta
        el encabezado o la fila separadora, la fila separadora se repite, o
        una fila no tiene tantas celdas como el encabezado. En todos los
        casos la tabla se sigue analizando; lo reconocido queda en el arbol.
        """
        nodo = no_terminal(NT_TABLA)
        columnas = -1
        inicio = self.actual
        if self._es(BARRA):
            encabezado = self.parsear_fila_tabla()
            nodo.agregar(encabezado)
            columnas = self._contar_celdas(encabezado)
        else:
            self._error_tabla(inicio, 'falta la fila de encabezado')

        if self._es(SEPARADOR_TABLA):
            separador = self._coincidir(SEPARADOR_TABLA, nodo)
            nodo.alineaciones = alineaciones_de(separador.lexema)
            self._revisar_separador(separador, columnas)
            if columnas < 0:
                # Sin encabezado, las filas se comparan con la separadora.
                columnas = len(nodo.alineaciones)
            self._coincidir(SALTO_LINEA, nodo)
        else:
            # Se reporta en el encabezado, que es la fila a la que le falta
            # su separadora.
            self._error_tabla(inicio, 'falta la fila separadora (|---|) '
                              'después del encabezado')

        while self._es(BARRA) or self._es(SEPARADOR_TABLA):
            if self._es(BARRA):
                inicio = self.actual
                fila = self.parsear_fila_tabla()
                nodo.agregar(fila)
                self._revisar_celdas(inicio, self._contar_celdas(fila),
                                     columnas)
            else:
                self._error_tabla(self.actual, 'fila separadora fuera de '
                                  'lugar: va una sola vez, justo después '
                                  'del encabezado')
                self._coincidir(SEPARADOR_TABLA, nodo)
                self._coincidir(SALTO_LINEA, nodo)
        return nodo

    def parsear_fila_tabla(self):
        """
        <fila_tabla> ::= BARRA { <celda> BARRA } SALTO_LINEA

        Toda fila empieza y termina con '|'. Si la ultima celda no se
        cierra con BARRA, se reporta TABLA_MAL_FORMADA y la fila se acepta.
        """
        nodo = no_terminal(NT_FILA_TABLA)
        primera = self._coincidir(BARRA, nodo)
        while self._actual_es_uno_de(PRIMEROS_CELDA):
            nodo.agregar(self.parsear_celda())
            if self._es(BARRA):
                self._coincidir(BARRA, nodo)
            else:
                self._error_tabla(primera, "la fila no termina con '|'")
        self._coincidir(SALTO_LINEA, nodo)
        return nodo

    def parsear_celda(self):
        """<celda> ::= <en_linea>     (puede estar vacia: '||')"""
        nodo = no_terminal(NT_CELDA)
        nodo.agregar(self.parsear_en_linea())
        return nodo

    def _contar_celdas(self, fila):
        total = 0
        i = 0
        while i < len(fila.hijos):
            if fila.hijos[i].es(NT_CELDA):
                total = total + 1
            i = i + 1
        return total

    def _revisar_separador(self, separador, columnas):
        """La fila separadora termina en '|' y tiene una celda por columna."""
        lexema = separador.lexema
        if lexema[len(lexema) - 1] != '|':
            self._error_tabla(separador, "la fila no termina con '|'")
        elif columnas >= 0:
            self._revisar_celdas(separador,
                                 len(alineaciones_de(lexema)), columnas)

    def _revisar_celdas(self, inicio, celdas, columnas):
        if columnas >= 0 and celdas != columnas:
            self._error_tabla(inicio, 'la fila tiene ' + cantidad(celdas) +
                              ' y la tabla ' + cantidad_columnas(columnas))

    def _error_tabla(self, token, detalle):
        """TABLA_MAL_FORMADA en la posicion de 'token' (D-33)."""
        self._error(token.lexema_visible(), err.TABLA_MAL_FORMADA,
                    'Tabla mal formada en línea ' + str(token.linea) +
                    ', columna ' + str(token.columna) + ': ' + detalle,
                    token.linea, token.columna)

    # ==================================================================
    # Elementos en linea
    # ==================================================================

    def parsear_en_linea(self):
        """<en_linea> ::= { <elemento_linea> }"""
        nodo = no_terminal(NT_EN_LINEA)
        while self._actual_es_uno_de(PRIMEROS_EN_LINEA):
            self.parsear_elemento_linea(nodo)
        return nodo

    def parsear_elemento_linea(self, padre):
        """
        <elemento_linea> ::= <negrita> | <cursiva> | <tachado>
                           | <codigo_inline> | <enlace> | <imagen> | TEXTO
        """
        if self._es(NEGRITA):
            padre.agregar(self.parsear_negrita())
        elif self._es(CURSIVA):
            padre.agregar(self.parsear_cursiva())
        elif self._es(TACHADO):
            padre.agregar(self.parsear_tachado())
        elif self._es(CODIGO_INLINE):
            padre.agregar(self.parsear_codigo_inline())
        elif self._es(CORCHETE_ABRE):
            padre.agregar(self.parsear_enlace())
        elif self._es(IMAGEN_ABRE):
            padre.agregar(self.parsear_imagen())
        else:
            self._coincidir(TEXTO, padre)

    def parsear_negrita(self):
        """
        <negrita> ::= NEGRITA <en_linea_n> NEGRITA

        Dentro de una negrita, el siguiente NEGRITA siempre la cierra:
        <en_linea_n> no admite otra negrita directa (D-05).
        """
        nodo = no_terminal(NT_NEGRITA)
        self._coincidir(NEGRITA, nodo)
        nodo.agregar(self.parsear_en_linea_n())
        self._coincidir(NEGRITA, nodo)
        return nodo

    def parsear_en_linea_n(self):
        """<en_linea_n> ::= { <elemento_n> }"""
        nodo = no_terminal(NT_EN_LINEA_N)
        while self._actual_es_uno_de(PRIMEROS_EN_LINEA_N):
            self.parsear_elemento_n(nodo)
        return nodo

    def parsear_elemento_n(self, padre):
        """
        <elemento_n> ::= <cursiva> | <tachado> | <codigo_inline> | <enlace>
                       | <imagen> | TEXTO | SALTO_LINEA
        """
        if self._es(CURSIVA):
            padre.agregar(self.parsear_cursiva())
        elif self._es(TACHADO):
            padre.agregar(self.parsear_tachado())
        elif self._es(CODIGO_INLINE):
            padre.agregar(self.parsear_codigo_inline())
        elif self._es(CORCHETE_ABRE):
            padre.agregar(self.parsear_enlace())
        elif self._es(IMAGEN_ABRE):
            padre.agregar(self.parsear_imagen())
        elif self._es(SALTO_LINEA):
            self._coincidir(SALTO_LINEA, padre)
        else:
            self._coincidir(TEXTO, padre)

    def parsear_cursiva(self):
        """
        <cursiva> ::= CURSIVA <en_linea_c> CURSIVA

        Dentro de una cursiva, el siguiente CURSIVA siempre la cierra.
        """
        nodo = no_terminal(NT_CURSIVA)
        self._coincidir(CURSIVA, nodo)
        nodo.agregar(self.parsear_en_linea_c())
        self._coincidir(CURSIVA, nodo)
        return nodo

    def parsear_en_linea_c(self):
        """<en_linea_c> ::= { <elemento_c> }"""
        nodo = no_terminal(NT_EN_LINEA_C)
        while self._actual_es_uno_de(PRIMEROS_EN_LINEA_C):
            self.parsear_elemento_c(nodo)
        return nodo

    def parsear_elemento_c(self, padre):
        """
        <elemento_c> ::= <negrita> | <tachado> | <codigo_inline> | <enlace>
                       | <imagen> | TEXTO | SALTO_LINEA
        """
        if self._es(NEGRITA):
            padre.agregar(self.parsear_negrita())
        elif self._es(TACHADO):
            padre.agregar(self.parsear_tachado())
        elif self._es(CODIGO_INLINE):
            padre.agregar(self.parsear_codigo_inline())
        elif self._es(CORCHETE_ABRE):
            padre.agregar(self.parsear_enlace())
        elif self._es(IMAGEN_ABRE):
            padre.agregar(self.parsear_imagen())
        elif self._es(SALTO_LINEA):
            self._coincidir(SALTO_LINEA, padre)
        else:
            self._coincidir(TEXTO, padre)

    def parsear_codigo_inline(self):
        """
        <codigo_inline> ::= CODIGO_INLINE { TEXTO_LITERAL | SALTO_LINEA }
                            CODIGO_INLINE

        En una sola linea el contenido es un TEXTO_LITERAL (o nada, en
        '``'). Si el codigo cruza lineas de un parrafo, llega un
        TEXTO_LITERAL por linea con un SALTO_LINEA entre ellos (D-02).
        """
        nodo = no_terminal(NT_CODIGO_INLINE)
        self._coincidir(CODIGO_INLINE, nodo)
        while self._es(TEXTO_LITERAL) or self._es(SALTO_LINEA):
            if self._es(TEXTO_LITERAL):
                self._coincidir(TEXTO_LITERAL, nodo)
            else:
                self._coincidir(SALTO_LINEA, nodo)
        self._coincidir(CODIGO_INLINE, nodo)
        return nodo

    # ------------------------------------------------------------------
    # Alcance opcional en linea: tachado, enlaces e imagenes
    # ------------------------------------------------------------------

    def parsear_tachado(self):
        """
        <tachado> ::= TACHADO <en_linea_t> TACHADO

        Igual que la negrita: dentro de un tachado, el siguiente TACHADO
        siempre lo cierra, por eso <en_linea_t> no admite otro tachado.
        """
        nodo = no_terminal(NT_TACHADO)
        self._coincidir(TACHADO, nodo)
        nodo.agregar(self.parsear_en_linea_t())
        self._coincidir(TACHADO, nodo)
        return nodo

    def parsear_en_linea_t(self):
        """<en_linea_t> ::= { <elemento_t> }"""
        nodo = no_terminal(NT_EN_LINEA_T)
        while self._actual_es_uno_de(PRIMEROS_EN_LINEA_T):
            self.parsear_elemento_t(nodo)
        return nodo

    def parsear_elemento_t(self, padre):
        """
        <elemento_t> ::= <negrita> | <cursiva> | <codigo_inline> | <enlace>
                       | <imagen> | TEXTO | SALTO_LINEA
        """
        if self._es(NEGRITA):
            padre.agregar(self.parsear_negrita())
        elif self._es(CURSIVA):
            padre.agregar(self.parsear_cursiva())
        elif self._es(CODIGO_INLINE):
            padre.agregar(self.parsear_codigo_inline())
        elif self._es(CORCHETE_ABRE):
            padre.agregar(self.parsear_enlace())
        elif self._es(IMAGEN_ABRE):
            padre.agregar(self.parsear_imagen())
        elif self._es(SALTO_LINEA):
            self._coincidir(SALTO_LINEA, padre)
        else:
            self._coincidir(TEXTO, padre)

    def parsear_enlace(self):
        """
        <enlace> ::= CORCHETE_ABRE <en_linea> CORCHETE_CIERRA <destino>

        El texto del enlace es un <en_linea> completo: admite negrita,
        cursiva, tachado y codigo. Es LL(1) porque CORCHETE_CIERRA no esta
        en PRIMEROS(<en_linea>): el ciclo se detiene justo en el ']'.
        """
        nodo = no_terminal(NT_ENLACE)
        self._coincidir(CORCHETE_ABRE, nodo)
        nodo.agregar(self.parsear_en_linea())
        self._coincidir(CORCHETE_CIERRA, nodo)
        nodo.agregar(self.parsear_destino())
        return nodo

    def parsear_imagen(self):
        """
        <imagen> ::= IMAGEN_ABRE [ TEXTO_LITERAL ] CORCHETE_CIERRA <destino>

        El texto alternativo es literal, como el de un codigo en linea.
        """
        nodo = no_terminal(NT_IMAGEN)
        self._coincidir(IMAGEN_ABRE, nodo)
        if self._es(TEXTO_LITERAL):
            self._coincidir(TEXTO_LITERAL, nodo)
        self._coincidir(CORCHETE_CIERRA, nodo)
        nodo.agregar(self.parsear_destino())
        return nodo

    def parsear_destino(self):
        """<destino> ::= PARENTESIS_ABRE [ URL ] PARENTESIS_CIERRA"""
        nodo = no_terminal(NT_DESTINO)
        self._coincidir(PARENTESIS_ABRE, nodo)
        if self._es(URL):
            self._coincidir(URL, nodo)
        self._coincidir(PARENTESIS_CIERRA, nodo)
        return nodo

    # ==================================================================
    # Errores y recuperacion (modo panico)
    # ==================================================================

    def _error(self, lexema, tipo, descripcion, linea, columna):
        """
        Registra un error sintactico. Si ya hay uno del mismo tipo en la
        misma linea, no lo repite: es el mismo problema visto otra vez
        mientras el parser se recupera (D-22).
        """
        if self.gestor.existe(tipo, linea, err.FASE_SINTACTICA):
            return
        self.gestor.agregar(lexema, tipo, descripcion, linea, columna,
                            err.FASE_SINTACTICA)

    def _error_indentacion(self, detalle):
        """INDENTACION_INVALIDA en la posicion del INDENT actual."""
        token = self.actual
        self._error('(sangría)', err.INDENTACION_INVALIDA,
                    'Indentación inválida en línea ' + str(token.linea) +
                    ', columna ' + str(token.columna) + ': ' + detalle,
                    token.linea, token.columna)

    def _token_inesperado(self, esperado):
        token = self.actual
        self._error(token.lexema_visible(), err.TOKEN_INESPERADO,
                    'Token inesperado en línea ' + str(token.linea) +
                    ', columna ' + str(token.columna) + ': se esperaba ' +
                    esperado + ' y se encontró ' + token.tipo,
                    token.linea, token.columna)

    def _sincronizar(self):
        """
        Modo panico: descarta tokens hasta un punto seguro (SALTO_LINEA,
        SALTO_PARRAFO o FIN). No consume el token de sincronizacion: puede
        ser justo el que esperaba quien llamo. Los descartados no entran al
        arbol.
        """
        while not self._actual_es_uno_de(TOKENS_SINCRONIZACION):
            self._avanzar()

    def _descartar_linea(self):
        """
        Modo panico al nivel de los bloques: descarta el resto de la linea,
        incluido su SALTO_LINEA, para empezar limpio en la siguiente.
        """
        self._sincronizar()
        if self._es(SALTO_LINEA):
            self._avanzar()


def alineaciones_de(lexema):
    """
    Alineacion de cada columna segun el SEPARADOR_TABLA (D-33):
        ':---:' -> 'center'    '---:' -> 'right'    ':---' -> 'left'
        '---'   -> ''  (sin alineacion)
    Se recorre el lexema y cada '|' cierra una celda; los espacios no
    cuentan. Es un atributo de la tabla, igual que el nivel de una cita se
    saca de la cantidad de '>'.
    """
    alineaciones = []
    celda = ''
    i = 1
    while i <= len(lexema):
        c = ''
        if i < len(lexema):
            c = lexema[i]
        if c == '|' or c == '':
            if celda != '':
                alineaciones.append(alineacion_de_celda(celda))
            celda = ''
        elif c != ' ' and c != '\t':
            celda = celda + c
        i = i + 1
    return alineaciones


def alineacion_de_celda(celda):
    izquierda = celda[0] == ':'
    derecha = celda[len(celda) - 1] == ':'
    if izquierda and derecha:
        return 'center'
    if derecha:
        return 'right'
    if izquierda:
        return 'left'
    return ''


def cantidad(celdas):
    """'1 celda', '3 celdas'."""
    if celdas == 1:
        return '1 celda'
    return str(celdas) + ' celdas'


def cantidad_columnas(columnas):
    """'1 columna', '2 columnas'."""
    if columnas == 1:
        return '1 columna'
    return str(columnas) + ' columnas'
