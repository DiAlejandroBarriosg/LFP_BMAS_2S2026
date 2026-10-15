# -*- coding: utf-8 -*-
"""
analizador_lexico.py
AnalizadorLexico de MarkdownCheck: AFD implementado a mano.

RESTRICCION DEL PROYECTO: no se usa el modulo re. El texto se recorre
caracter por caracter con un indice (self.pos), y cada estado del automata
disenado en la seccion 3 del documento de diseno es un metodo.

Como trabaja
------------
El AFD analiza una LINEA completa cada vez y deja sus tokens en una cola
(self.cola). siguiente_token() entrega el primero de la cola y, cuando la
cola se vacia, manda a analizar la linea siguiente. Se trabaja por lineas
porque dos decisiones solo pueden tomarse viendo mas que un caracter:
  - cuantos INDENT o DEDENT van antes de una VIÑETA (capa 1);
  - si un ** o un * quedo abierto al terminar su bloque (capa 2, D-02).
    Un parrafo puede tener varias lineas, asi que mientras un parrafo
    tenga un ** o un * abierto, sus tokens se quedan en la cola hasta saber
    si se cierra.

Mapa estado -> metodo
    q0        INICIO DE LINEA      _analizar_linea_normal()
    q21       SALTO_PARRAFO        _analizar_linea_normal()
    q6, q7    VIÑETA               _estado_vineta()
    q1, q2    NUMERAL              _estado_numeral()
    q3..q5    REGLA_HORIZONTAL     _es_regla_horizontal(), _estado_regla()
    q8, q9    CITA                 _estado_cita()
    q10..q13  CERCA_CODIGO         _estado_cerca_apertura()
    q14       EN LINEA             _estado_en_linea()
    q15       TEXTO                _estado_texto()
    q16, q17  CURSIVA / NEGRITA    _estado_asterisco()
    q18, q19  CODIGO_INLINE        _estado_codigo_inline()
    q20       SALTO_LINEA          _estado_fin_linea()
    b0..b4    MODO LITERAL         _analizar_linea_literal()

  Alcance opcional (seccion 3.5 del diseno)
    q22, q23  NUMERO_LISTA         _es_numero_de_lista(),
                                   _estado_numero_lista()
    q24..q26  CASILLA              _estado_casilla()
    q27, q28  TACHADO              _estado_tachado()
    q29..q33  ENLACE               _estado_enlace(), _estado_cierre_enlace(),
                                   _estado_destino()
    q34..q36  IMAGEN               _estado_imagen()
    q37, q38  TABLA / BARRA        _estado_tabla(), _estado_barra()
    s0..s3    SEPARADOR_TABLA      _es_separador_tabla()

Capas posteriores al automata (seccion 3.4)
    1. nivel de lista          _ajustar_nivel_lista(), _cerrar_lista()
    2. pila de delimitadores   _registrar_delimitador(),
                               _cerrar_delimitadores()
    3. cola de tokens          siguiente_token()
"""

from lexico import alfabeto as alf
from lexico.token import Token
from lexico.token import NUMERAL, VINETA, INDENT, DEDENT, CITA
from lexico.token import CERCA_CODIGO, LENGUAJE_CODIGO, TEXTO_LITERAL
from lexico.token import REGLA_HORIZONTAL, NEGRITA, CURSIVA, CODIGO_INLINE
from lexico.token import TEXTO, SALTO_LINEA, SALTO_PARRAFO, FIN
from lexico.token import NUMERO_LISTA, CASILLA, TACHADO, CORCHETE_ABRE
from lexico.token import IMAGEN_ABRE, CORCHETE_CIERRA, PARENTESIS_ABRE, URL
from lexico.token import PARENTESIS_CIERRA, BARRA, SEPARADOR_TABLA
from errores import error_analisis as err

# Un nivel de lista son 2 espacios. Un tabulador en la sangria vale lo mismo
# que 2 espacios, es decir, un nivel (D-07).
ESPACIOS_POR_NIVEL = 2
ESPACIOS_POR_TABULADOR = 2

# Un encabezado admite de 1 a 6 '#' (H1 a H6).
MAXIMO_NUMERALES = 6

# Una regla horizontal necesita al menos 3 guiones.
MINIMO_GUIONES = 3

# Modos del automata (seccion 3 del documento de diseno)
MODO_NORMAL = 'NORMAL'
MODO_LITERAL = 'LITERAL'

# Estados del AFD pequeno que reconoce una celda de la fila separadora de
# una tabla ('---', ':---', '---:', ':---:'), en _es_separador_tabla().
S_INICIO = 's0'        # solo espacios
S_DOS_PUNTOS = 's1'    # leido ':' inicial
S_GUIONES = 's2'       # leido al menos un '-'
S_CERRADA = 's3'       # leido ':' final o espacios despues de los guiones


class AnalizadorLexico:

    def __init__(self, texto, gestor):
        self.texto = self._normalizar(texto)
        self.gestor = gestor
        self.pos = 0
        self.linea = 1
        self.columna = 1

        # Todos los tokens reconocidos, en orden: es la tabla de tokens.
        self.tokens = []
        # Tokens ya reconocidos que el parser todavia no ha pedido.
        self.cola = []
        self.contador_token = 0
        self.token_fin = None

        # Modo literal: dentro de un bloque de codigo no se tokeniza nada.
        self.modo = MODO_NORMAL
        self.linea_apertura_codigo = 0
        self.columna_apertura_codigo = 0

        # Capa 1: nivel de la lista abierta (0 = no hay lista abierta).
        self.nivel_lista = 0
        # Capa 2: NEGRITA, CURSIVA y TACHADO abiertos en el bloque actual.
        # Un CORCHETE_ABRE en la pila marca el inicio de un enlace (D-32).
        self.pila_delimitadores = []
        # True si la linea actual es una linea de texto de un parrafo: el
        # unico bloque que puede seguir en la linea siguiente (D-02).
        self.linea_de_parrafo = False
        # True si la linea anterior termino dentro de un codigo en linea
        # que se cierra en esta linea o en otra del mismo parrafo.
        self.dentro_de_codigo = False
        # True si la linea actual es una fila de tabla: ahi cada '|' es una
        # BARRA y termina la celda (D-33).
        self.linea_de_tabla = False
        # True entre el '[' y el ']' de un enlace.
        self.dentro_de_enlace = False

    def _normalizar(self, texto):
        """
        Quita los '\\r' de los archivos guardados en Windows ('\\r\\n') y la
        marca BOM que algunos editores ponen al inicio. Asi el resto del
        automata solo tiene que conocer '\\n'.
        """
        limpio = ''
        i = 0
        if len(texto) > 0 and texto[0] == '﻿':
            i = 1
        while i < len(texto):
            if texto[i] != '\r':
                limpio = limpio + texto[i]
            i = i + 1
        return limpio

    # ==================================================================
    # Interfaz publica
    # ==================================================================

    def siguiente_token(self):
        """
        Devuelve el siguiente Token. Al terminar el archivo devuelve el token
        FIN, y lo sigue devolviendo en cada llamada posterior.

        Mientras haya un ** o un * abierto no se entrega nada, aunque la
        cola tenga tokens: todavia no se sabe si se cierra en una linea
        siguiente del parrafo o si pasa a ser TEXTO (D-02). Asi el parser
        nunca recibe un delimitador sin pareja. El codigo en linea no
        necesita esperar: solo se abre si el lookahead ya encontro su cierre.
        """
        while len(self.cola) == 0 or len(self.pila_delimitadores) > 0:
            if self.token_fin is not None:
                return self.token_fin
            self._analizar_siguiente_linea()
        return self.cola.pop(0)

    def analizar_todo(self):
        """
        Pide tokens hasta llegar a FIN y devuelve la lista completa.
        Lo usan las pruebas de consola; el parser usa siguiente_token().
        """
        token = self.siguiente_token()
        while not token.es(FIN):
            token = self.siguiente_token()
        return self.tokens

    # ==================================================================
    # Primitivas de recorrido
    # ==================================================================

    def _hay_mas(self):
        return self.pos < len(self.texto)

    def _actual(self):
        """Caracter en la posicion actual, o '' si se llego al final."""
        if self.pos < len(self.texto):
            return self.texto[self.pos]
        return ''

    def _ver(self, desplazamiento):
        """
        Lookahead SIN consumir: el caracter que esta 'desplazamiento'
        posiciones adelante, o '' si queda fuera del texto. Como no consume,
        el automata nunca tiene que retroceder el indice.
        """
        indice = self.pos + desplazamiento
        if indice < len(self.texto):
            return self.texto[indice]
        return ''

    def _avanzar(self):
        """
        Consume un caracter y actualiza linea y columna.
        La columna cuenta caracteres: un tabulador ocupa una columna (D-19).
        """
        c = self.texto[self.pos]
        self.pos = self.pos + 1
        if c == '\n':
            self.linea = self.linea + 1
            self.columna = 1
        else:
            self.columna = self.columna + 1
        return c

    def _saltar_separadores(self):
        """Consume espacios y tabuladores sin generar token."""
        while alf.es_separador(self._actual()):
            self._avanzar()

    def _contar_seguidos(self, caracter):
        """Cuantas veces seguidas aparece 'caracter' desde la posicion."""
        k = 0
        while self._ver(k) == caracter:
            k = k + 1
        return k

    def _leer_hasta_fin_de_linea(self):
        """
        Consume el resto de la linea (sin el '\\n') y lo devuelve sin los
        espacios del final. Los espacios se guardan aparte y solo se pegan
        al lexema si despues aparece otro caracter.
        """
        lexema = ''
        pendientes = ''
        while not alf.es_fin_de_linea(self._actual()):
            c = self._avanzar()
            if alf.es_separador(c):
                pendientes = pendientes + c
            else:
                lexema = lexema + pendientes + c
                pendientes = ''
        return lexema

    def _crear(self, lexema, tipo, linea, columna):
        """Crea un token numerado y lo deja en la tabla y en la cola."""
        self.contador_token = self.contador_token + 1
        token = Token(self.contador_token, lexema, tipo, linea, columna)
        self.tokens.append(token)
        self.cola.append(token)
        return token

    def _error(self, lexema, tipo, descripcion, linea, columna):
        self.gestor.agregar(lexema, tipo, descripcion, linea, columna,
                            err.FASE_LEXICA)

    def _posicion(self, linea, columna):
        """Texto 'linea L, columna C' para los mensajes de error."""
        return 'línea ' + str(linea) + ', columna ' + str(columna)

    # ==================================================================
    # Despacho por linea
    # ==================================================================

    def _analizar_siguiente_linea(self):
        self.linea_de_parrafo = False
        self.linea_de_tabla = False
        if not self._hay_mas():
            self._fin_de_archivo()
        elif self.modo == MODO_LITERAL:
            self._analizar_linea_literal()
        else:
            self._analizar_linea_normal()

    def _fin_de_archivo(self):
        """
        Se acabo el texto. Si quedo un bloque de codigo abierto se reporta;
        luego se cierran los niveles de lista abiertos y se emite FIN.
        """
        if self.modo == MODO_LITERAL:
            self._error('```', err.BLOQUE_CODIGO_SIN_CERRAR,
                        'Bloque de código sin cerrar iniciado en línea ' +
                        str(self.linea_apertura_codigo),
                        self.linea_apertura_codigo,
                        self.columna_apertura_codigo)
            self.modo = MODO_NORMAL
        self._cerrar_delimitadores()
        self._cerrar_lista(self.linea, self.columna)
        self.token_fin = self._crear('', FIN, self.linea, self.columna)

    # ------------------------------------------------------------------
    # q0 - Inicio de linea en modo normal
    # ------------------------------------------------------------------

    def _analizar_linea_normal(self):
        linea = self.linea
        # Lookahead: se decide antes de consumir si la linea es de texto.
        # Es la misma funcion que usa el fin de la linea anterior para saber
        # si el parrafo sigue, asi las dos decisiones siempre coinciden.
        self.linea_de_parrafo = self._es_linea_de_parrafo(0)

        # q0: la sangria se cuenta en espacios (un tabulador vale 2).
        espacios = 0
        while alf.es_separador(self._actual()):
            if self._actual() == '\t':
                espacios = espacios + ESPACIOS_POR_TABULADOR
            else:
                espacios = espacios + 1
            self._avanzar()
        c = self._actual()

        # q21: linea vacia o de solo espacios.
        if alf.es_fin_de_linea(c):
            self._cerrar_lista(linea, 1)
            if c == '\n':
                self._crear('\n', SALTO_PARRAFO, self.linea, self.columna)
                self._avanzar()
            else:
                self._crear('', SALTO_PARRAFO, self.linea, self.columna)
            return

        # q6/q7: marcador de lista seguido de separador -> item de lista.
        # Se decide con lookahead ANTES de crear tokens, porque los INDENT
        # y DEDENT tienen que quedar antes de la VIÑETA.
        if alf.es_marcador_lista(c) and alf.es_separador(self._ver(1)):
            self._ajustar_nivel_lista(espacios, linea)
            self._estado_vineta()
            self._estado_en_linea()
            return
        # q22: '1. ' es un item de lista numerada; la sangria funciona igual.
        if self._es_numero_de_lista(0):
            self._ajustar_nivel_lista(espacios, linea)
            self._estado_numero_lista()
            self._estado_en_linea()
            return

        # Cualquier otra linea cierra la lista que estuviera abierta.
        self._cerrar_lista(linea, 1)

        # Si la linea empieza dentro de un codigo en linea que viene de la
        # linea anterior, sus '#' son contenido del codigo: no se revisan,
        # para no reportar ENCABEZADO_INVALIDO por un '####### x' que esta
        # adentro del codigo. (Un encabezado valido nunca llega aqui: habria
        # terminado el parrafo y el codigo no se habria abierto.)
        if c == '#' and not self.dentro_de_codigo:
            self._estado_numeral()
            self._estado_en_linea()
        elif c == '-' and self._es_regla_horizontal(0):
            self._estado_regla()
        elif c == '>':
            self._estado_cita()
        elif c == '`' and self._ver(1) == '`' and self._ver(2) == '`':
            self._estado_cerca_apertura()
        elif c == '|':
            self._estado_tabla()
        else:
            self._estado_en_linea()

    # ------------------------------------------------------------------
    # q6 - VIÑETA
    # ------------------------------------------------------------------

    def _estado_vineta(self):
        """El marcador (-, * o +) es el lexema; el separador no es token."""
        linea = self.linea
        columna = self.columna
        marcador = self._avanzar()
        self._crear(marcador, VINETA, linea, columna)
        self._saltar_separadores()
        self._estado_casilla()

    # ------------------------------------------------------------------
    # q1, q2 - NUMERAL
    # ------------------------------------------------------------------

    def _estado_numeral(self):
        """
        Cuenta los '#' con lookahead. Tres salidas:
          - 1 a 6 '#' y separador: NUMERAL (q2).
          - mas de 6 '#' y separador: ENCABEZADO_INVALIDO; la linea sigue
            como texto.
          - sin separador ('#sinespacio'): no es encabezado. No se consume
            nada y _estado_en_linea() lo toma como TEXTO (q1 -> q15).
        """
        linea = self.linea
        columna = self.columna
        cuantos = self._contar_seguidos('#')
        if not alf.es_separador(self._ver(cuantos)):
            return

        if cuantos > MAXIMO_NUMERALES:
            numerales = ''
            i = 0
            while i < cuantos:
                numerales = numerales + '#'
                i = i + 1
            self._error(numerales, err.ENCABEZADO_INVALIDO,
                        'Encabezado inválido en línea ' + str(linea) +
                        ': máximo ' + str(MAXIMO_NUMERALES) + ' niveles',
                        linea, columna)
            return

        lexema = ''
        i = 0
        while i < cuantos:
            lexema = lexema + self._avanzar()
            i = i + 1
        self._crear(lexema, NUMERAL, linea, columna)
        self._saltar_separadores()

    # ------------------------------------------------------------------
    # q3, q4, q5 - REGLA_HORIZONTAL
    # ------------------------------------------------------------------

    def _es_regla_horizontal(self, inicio):
        """
        Simula q3 -> q4 -> q5 con lookahead, sin consumir, desde el '-' que
        esta 'inicio' posiciones adelante. La linea es una regla si solo
        tiene guiones y espacios, con al menos 3 guiones antes del primer
        espacio. Ejemplos:
            '---'    regla        '--- -'  regla
            '--'     texto        '-- -'   texto (q4 con espacio)
            '---x'   texto (q5 con otro caracter)
        """
        k = inicio
        guiones = 0
        while not alf.es_fin_de_linea(self._ver(k)):
            c = self._ver(k)
            if c == '-':
                guiones = guiones + 1
            elif alf.es_separador(c):
                if guiones < MINIMO_GUIONES:
                    return False
            else:
                return False
            k = k + 1
        return guiones >= MINIMO_GUIONES

    def _estado_regla(self):
        linea = self.linea
        columna = self.columna
        lexema = self._leer_hasta_fin_de_linea()
        self._crear(lexema, REGLA_HORIZONTAL, linea, columna)
        self._estado_fin_linea()

    # ------------------------------------------------------------------
    # q8, q9 - CITA
    # ------------------------------------------------------------------

    def _estado_cita(self):
        """
        Lee los '>' seguidos. '>>' y '> >' son la misma cita de nivel 2
        (D-09): un separador forma parte del marcador solo si despues viene
        otro '>'. El nivel no se guarda aparte: es la cantidad de '>' del
        lexema, y la cuenta el parser.

        Si falta el espacio despues del ultimo '>' ('>texto'), el lexico no
        reporta nada: CITA_MAL_FORMADA es un error sintactico y lo detecta
        el parser comparando columnas (D-11).
        """
        linea = self.linea
        columna = self.columna
        lexema = ''
        seguir = True
        while seguir:
            if self._actual() == '>':
                lexema = lexema + self._avanzar()
            elif (alf.es_separador(self._actual()) and
                  self._hay_mayor_despues_de_separadores()):
                lexema = lexema + self._avanzar()
            else:
                seguir = False
        self._crear(lexema, CITA, linea, columna)
        self._saltar_separadores()

        # Dentro de una cita puede ir un encabezado (D-10).
        if self._actual() == '#':
            self._estado_numeral()
        self._estado_en_linea()

    def _hay_mayor_despues_de_separadores(self):
        k = 0
        while alf.es_separador(self._ver(k)):
            k = k + 1
        return self._ver(k) == '>'

    # ------------------------------------------------------------------
    # q10..q13 - CERCA_CODIGO de apertura y LENGUAJE_CODIGO
    # ------------------------------------------------------------------

    def _estado_cerca_apertura(self):
        linea = self.linea
        columna = self.columna
        lexema = self._avanzar() + self._avanzar() + self._avanzar()
        self._crear(lexema, CERCA_CODIGO, linea, columna)

        self._saltar_separadores()
        if not alf.es_fin_de_linea(self._actual()):
            linea_lenguaje = self.linea
            columna_lenguaje = self.columna
            lenguaje = self._leer_hasta_fin_de_linea()
            self._crear(lenguaje, LENGUAJE_CODIGO, linea_lenguaje,
                        columna_lenguaje)

        self._estado_fin_linea()
        # Desde la linea siguiente el automata trabaja en modo literal.
        self.modo = MODO_LITERAL
        self.linea_apertura_codigo = linea
        self.columna_apertura_codigo = columna

    # ------------------------------------------------------------------
    # b0..b4 - Modo literal (dentro de un bloque de codigo)
    # ------------------------------------------------------------------

    def _analizar_linea_literal(self):
        """
        En modo literal solo hay dos posibilidades por linea:
          - la cerca de cierre: '```' sola, con espacios opcionales (D-12);
          - contenido: la linea completa, con su sangria, es TEXTO_LITERAL.
        Nada de lo que hay adentro se tokeniza: un '**' o un '#' aqui son
        parte del contenido.
        """
        linea = self.linea
        if self._es_cerca_cierre():
            self._saltar_separadores()
            columna = self.columna
            lexema = self._avanzar() + self._avanzar() + self._avanzar()
            self._crear(lexema, CERCA_CODIGO, linea, columna)
            self._saltar_separadores()
            self.modo = MODO_NORMAL
            self._estado_fin_linea()
            return

        columna = self.columna
        contenido = ''
        while not alf.es_fin_de_linea(self._actual()):
            contenido = contenido + self._avanzar()
        self._crear(contenido, TEXTO_LITERAL, linea, columna)
        self._estado_fin_linea()

    def _es_cerca_cierre(self):
        """b0 -> b1 -> b2 -> b3 con lookahead: '```' y nada mas en la linea."""
        k = 0
        while alf.es_separador(self._ver(k)):
            k = k + 1
        if self._ver(k) != '`' or self._ver(k + 1) != '`':
            return False
        if self._ver(k + 2) != '`':
            return False
        k = k + 3
        while alf.es_separador(self._ver(k)):
            k = k + 1
        return alf.es_fin_de_linea(self._ver(k))

    # ------------------------------------------------------------------
    # q14 - Elementos en linea
    # ------------------------------------------------------------------

    def _estado_en_linea(self):
        """
        Reconoce el contenido de una linea hasta su final. Cada vuelta del
        ciclo consume al menos un caracter, asi que siempre termina.
        Si la linea anterior del parrafo termino dentro de un codigo en
        linea, primero se termina de leer ese codigo.
        """
        if self.dentro_de_codigo:
            self._leer_codigo_inline()
        terminado = False
        while not terminado:
            c = self._actual()
            if alf.es_fin_de_linea(c):
                self._estado_fin_linea()
                terminado = True
            elif c == '*':
                self._estado_asterisco()
            elif c == '`':
                self._estado_codigo_inline()
            elif c == '~' and self._ver(1) == '~':
                self._estado_tachado()
            elif c == '[':
                self._estado_enlace()
            elif c == '!' and self._ver(1) == '[':
                self._estado_imagen()
            elif c == ']' and self.dentro_de_enlace:
                self._estado_cierre_enlace()
            elif c == '|' and self.linea_de_tabla:
                self._estado_barra()
            else:
                self._estado_texto('', self.linea, self.columna)

    # ------------------------------------------------------------------
    # q15 - TEXTO
    # ------------------------------------------------------------------

    def _estado_texto(self, lexema, linea, columna):
        """
        Acumula caracteres hasta el fin de linea o hasta un caracter con el
        que puede empezar otro token en linea (_termina_texto). Recibe un
        lexema inicial porque un '`' sin cierre, o un '[' que no abre un
        enlace, empiezan un TEXTO.
        """
        while not self._termina_texto():
            lexema = lexema + self._avanzar()
        self._crear(lexema, TEXTO, linea, columna)

    def _termina_texto(self):
        """
        True si el caracter actual corta un TEXTO (q15): el fin de linea,
        '*', '`', '~~', '[' o '!['; ademas ']' dentro de un enlace y '|' en
        una fila de tabla. En cualquier otro lugar, ']' y '|' son texto.
        """
        c = self._actual()
        if alf.es_fin_de_linea(c) or alf.es_delimitador_en_linea(c):
            return True
        if c == '~' and self._ver(1) == '~':
            return True
        if c == '[':
            return True
        if c == '!' and self._ver(1) == '[':
            return True
        if c == ']' and self.dentro_de_enlace:
            return True
        if c == '|' and self.linea_de_tabla:
            return True
        return False

    # ------------------------------------------------------------------
    # q16, q17 - CURSIVA y NEGRITA
    # ------------------------------------------------------------------

    def _estado_asterisco(self):
        """
        Maximal munch: '**' es NEGRITA antes que dos CURSIVA.

        Excepciones con exactamente tres asteriscos (D-04):
          - Al CERRAR: si la cima de la pila es una CURSIVA, primero va un
            '*' que la cierra y despues '**'. Asi '**a *b***' cierra bien.
          - Al ABRIR (sin '**' ni '*' en la cima): '***' puede ser negrita
            con cursiva adentro o cursiva con negrita adentro.
            Se prueba primero la negrita afuera; si asi los delimitadores
            del bloque no se cierran, la cursiva va afuera. Asi '***a** b*'
            es una cursiva que contiene una negrita.
        """
        linea = self.linea
        columna = self.columna
        cuantos = self._contar_seguidos('*')

        usar_negrita = False
        if cuantos >= 2:
            usar_negrita = True
            if cuantos == 3 and self._tipo_cima() == CURSIVA:
                usar_negrita = False
            elif cuantos == 3 and self._cima_sin_asteriscos():
                if self._cursiva_va_afuera():
                    usar_negrita = False

        if usar_negrita:
            lexema = self._avanzar() + self._avanzar()
            token = self._crear(lexema, NEGRITA, linea, columna)
        else:
            lexema = self._avanzar()
            token = self._crear(lexema, CURSIVA, linea, columna)
        self._registrar_delimitador(token)

    def _cursiva_va_afuera(self):
        """
        Para un '***' que abre con la pila vacia. True solo si con la
        negrita afuera los delimitadores no se cierran y con la cursiva
        afuera si. Si las dos formas sirven ('***a***'), o ninguna, se deja
        la negrita afuera (maximal munch).
        """
        if self._se_cierra_todo(NEGRITA, CURSIVA):
            return False
        return self._se_cierra_todo(CURSIVA, NEGRITA)

    def _se_cierra_todo(self, afuera, adentro):
        """
        Simula, sin consumir nada, el resto del bloque despues del '***'
        con la pila [afuera, adentro], aplicando las mismas reglas que
        _estado_asterisco(). True si en algun momento la pila queda vacia,
        es decir, si los dos delimitadores que abre el '***' se cierran.
        Los codigos en linea se saltan completos: un '*' dentro de `...` no
        es delimitador.
        """
        pila = [afuera, adentro]
        k = 3
        while not self._es_fin_de_bloque(k):
            c = self._ver(k)
            if c == ']' and self.dentro_de_enlace:
                # Termina el texto del enlace: ahi termina el ambito.
                return False
            if c == '`':
                k = self._fin_de_codigo_inline(k)
            elif c == '[' or (c == '!' and self._ver(k + 1) == '['):
                # Un enlace completo es un ambito aparte (D-32): se salta.
                k = self._saltar_enlace(k)
            elif c == '~' and self._ver(k + 1) == '~':
                k = k + 2
                aplicar_en_pila(pila, TACHADO)
                if len(pila) == 0:
                    return True
            elif c == '*':
                cuantos = 0
                while self._ver(k + cuantos) == '*':
                    cuantos = cuantos + 1
                k = k + cuantos
                while cuantos > 0:
                    cima = pila[len(pila) - 1]
                    if cuantos >= 2 and not (cuantos == 3 and cima == CURSIVA):
                        tipo = NEGRITA
                        cuantos = cuantos - 2
                    else:
                        tipo = CURSIVA
                        cuantos = cuantos - 1
                    aplicar_en_pila(pila, tipo)
                    if len(pila) == 0:
                        return True
            else:
                k = k + 1
        return False

    def _fin_de_codigo_inline(self, k):
        """
        Posicion siguiente al codigo en linea que empieza en el '`' de la
        posicion k. Si ese '`' no tiene cierre en el bloque, no abre nada y
        se avanza solo un caracter.
        """
        cierre = k + 1
        while (not self._es_fin_de_bloque(cierre) and
               self._ver(cierre) != '`'):
            cierre = cierre + 1
        if self._ver(cierre) == '`':
            return cierre + 1
        return k + 1

    # ------------------------------------------------------------------
    # q18, q19 - CODIGO_INLINE
    # ------------------------------------------------------------------

    def _estado_codigo_inline(self):
        """
        Antes de abrir se busca, con lookahead, otro '`' mas adelante en el
        mismo bloque: en esta linea o, si es un parrafo, en sus lineas
        siguientes (D-02, D-03). Si no hay, el '`' no abre nada: se reporta
        CODIGO_INLINE_SIN_CERRAR y el '`' pasa a ser el inicio de un TEXTO.
        Si hay, lo de en medio es TEXTO_LITERAL: no se buscan '*' adentro.
        """
        linea = self.linea
        columna = self.columna

        if not self._hay_cierre_de_codigo():
            self._error('`', err.CODIGO_INLINE_SIN_CERRAR,
                        'Código en línea sin cerrar iniciado en ' +
                        self._posicion(linea, columna),
                        linea, columna)
            primero = self._avanzar()
            self._estado_texto(primero, linea, columna)
            return

        self._crear(self._avanzar(), CODIGO_INLINE, linea, columna)
        self._leer_codigo_inline()

    def _leer_codigo_inline(self):
        """
        Lee el contenido de un codigo en linea hasta su '`' de cierre, que
        ya se sabe que existe. Si el cierre esta en una linea siguiente del
        parrafo, aqui se lee hasta el fin de esta linea y queda marcado
        dentro_de_codigo: la linea siguiente empieza dentro del codigo, y
        el SALTO_LINEA de en medio queda dentro del <codigo_inline>.
        '``' sin nada en medio no lleva TEXTO_LITERAL.
        """
        if (not alf.es_fin_de_linea(self._actual()) and
                self._actual() != '`'):
            linea_literal = self.linea
            columna_literal = self.columna
            contenido = ''
            while (not alf.es_fin_de_linea(self._actual()) and
                   self._actual() != '`'):
                contenido = contenido + self._avanzar()
            self._crear(contenido, TEXTO_LITERAL, linea_literal,
                        columna_literal)

        if self._actual() == '`':
            linea_cierre = self.linea
            columna_cierre = self.columna
            self._crear(self._avanzar(), CODIGO_INLINE, linea_cierre,
                        columna_cierre)
            self.dentro_de_codigo = False
        else:
            self.dentro_de_codigo = True

    def _hay_cierre_de_codigo(self):
        """
        True si el '`' de la posicion actual tiene otro '`' mas adelante en
        el mismo bloque, que lo cierre.
        """
        k = 1
        while not self._es_fin_de_bloque(k):
            if self._ver(k) == '`':
                return True
            k = k + 1
        return False

    # ------------------------------------------------------------------
    # q20 - SALTO_LINEA
    # ------------------------------------------------------------------

    def _estado_fin_linea(self):
        """
        Fin de una linea con contenido. Si con ella termina su bloque, se
        revisa la pila de delimitadores (capa 2); si el bloque es un parrafo
        que sigue en la linea siguiente, los ** y * abiertos se quedan
        abiertos, porque todavia se pueden cerrar (D-02). Luego se emite
        SALTO_LINEA. Si el archivo termina sin '\\n', el SALTO_LINEA es
        virtual (lexema vacio, D-01).
        """
        if self._es_fin_de_bloque(0):
            self._cerrar_delimitadores()
        if self._actual() == '\n':
            self._crear('\n', SALTO_LINEA, self.linea, self.columna)
            self._avanzar()
        else:
            self._crear('', SALTO_LINEA, self.linea, self.columna)

    # ==================================================================
    # Fin del bloque: los delimitadores se cierran dentro de su bloque
    # ==================================================================

    def _es_fin_de_bloque(self, k):
        """
        True si el caracter que esta k posiciones adelante termina el
        bloque actual: el fin del archivo, o un '\\n' despues del cual el
        bloque no sigue. El unico bloque de varias lineas es el parrafo; un
        encabezado, un item de lista o una linea de cita terminan con su
        linea (D-02, D-10). Dentro del bloque, un '\\n' es un caracter mas.
        Se usa siempre desde la linea actual hacia adelante, por eso basta
        con saber si la linea actual es de parrafo (linea_de_parrafo): las
        lineas siguientes que se revisan ya se sabe que lo son.
        """
        c = self._ver(k)
        if c == '':
            return True
        if c == '|' and self.linea_de_tabla:
            # En una fila de tabla, cada celda es su propio bloque (D-33).
            return True
        if c != '\n':
            return False
        if not self.linea_de_parrafo:
            return True
        return not self._es_linea_de_parrafo(k + 1)

    def _es_linea_de_parrafo(self, inicio):
        """
        Lookahead, sin consumir: True si la linea que empieza 'inicio'
        posiciones adelante es una linea de texto, es decir, si no empieza
        ningun otro bloque. Repite, en el mismo orden, las decisiones de
        _analizar_linea_normal(): linea vacia, item (con viñeta o numerado),
        encabezado, regla, cita, cerca de codigo y fila de tabla.
        '#sinespacio' y '####### x' si son texto.
        """
        k = inicio
        while alf.es_separador(self._ver(k)):
            k = k + 1
        c = self._ver(k)
        if alf.es_fin_de_linea(c):
            return False
        if alf.es_marcador_lista(c) and alf.es_separador(self._ver(k + 1)):
            return False
        if self._es_numero_de_lista(k):
            return False
        if c == '|':
            return False
        if c == '#' and self._es_encabezado(k):
            return False
        if c == '-' and self._es_regla_horizontal(k):
            return False
        if c == '>':
            return False
        if c == '`' and self._ver(k + 1) == '`' and self._ver(k + 2) == '`':
            return False
        return True

    def _es_encabezado(self, inicio):
        """
        True si en 'inicio' empiezan de 1 a 6 '#' seguidos de un separador:
        la misma condicion con que _estado_numeral() crea un NUMERAL.
        """
        cuantos = 0
        while self._ver(inicio + cuantos) == '#':
            cuantos = cuantos + 1
        if cuantos > MAXIMO_NUMERALES:
            return False
        return alf.es_separador(self._ver(inicio + cuantos))

    # ==================================================================
    # Alcance opcional (seccion 3.5 del diseno, D-29 a D-33)
    # ==================================================================

    # ------------------------------------------------------------------
    # q22, q23 - NUMERO_LISTA y q24..q26 - CASILLA
    # ------------------------------------------------------------------

    def _es_numero_de_lista(self, inicio):
        """
        Lookahead de q22 -> q23, sin consumir: uno o mas digitos, un '.' y
        un separador ('1. ', '10. '). '2024.fue' o '3.5' no son items.
        """
        k = inicio
        while alf.es_digito(self._ver(k)):
            k = k + 1
        if k == inicio or self._ver(k) != '.':
            return False
        return alf.es_separador(self._ver(k + 1))

    def _estado_numero_lista(self):
        """El numero con su punto es el lexema ('1.'); el separador no."""
        linea = self.linea
        columna = self.columna
        lexema = ''
        while alf.es_digito(self._actual()):
            lexema = lexema + self._avanzar()
        lexema = lexema + self._avanzar()
        self._crear(lexema, NUMERO_LISTA, linea, columna)
        self._saltar_separadores()
        self._estado_casilla()

    def _estado_casilla(self):
        """
        Lista de tareas (D-30): justo despues del marcador de un item,
        '[ ]' o '[x]' seguido de un separador es una CASILLA. Si no, no se
        consume nada y el '[' es parte del contenido del item.
        """
        marca = self._ver(1)
        if self._actual() != '[' or self._ver(2) != ']':
            return
        if marca != ' ' and marca != 'x' and marca != 'X':
            return
        if not alf.es_separador(self._ver(3)):
            return
        linea = self.linea
        columna = self.columna
        lexema = self._avanzar() + self._avanzar() + self._avanzar()
        self._crear(lexema, CASILLA, linea, columna)
        self._saltar_separadores()

    # ------------------------------------------------------------------
    # q27, q28 - TACHADO
    # ------------------------------------------------------------------

    def _estado_tachado(self):
        """
        '~~' es TACHADO y pasa por la pila igual que NEGRITA (D-31): si es
        igual a la cima la cierra, si no abre. Un '~' solo es texto.
        """
        linea = self.linea
        columna = self.columna
        lexema = self._avanzar() + self._avanzar()
        token = self._crear(lexema, TACHADO, linea, columna)
        self._registrar_delimitador(token)

    # ------------------------------------------------------------------
    # q29..q33 - ENLACE y q34..q36 - IMAGEN
    # ------------------------------------------------------------------

    def _estado_enlace(self):
        """
        q29: '[' abre un enlace solo si el lookahead encuentra su ']' y su
        '(url)' en la misma linea (D-32). Si no, el '[' es el inicio de un
        TEXTO, sin error: en Markdown un corchete suelto es texto.

        Dentro del texto de un enlace nunca llega otro '[' fuera de un
        codigo: el lookahead no acepta un '[' antes del ']'. Por eso los
        enlaces no se anidan.
        """
        linea = self.linea
        columna = self.columna
        if self._cierre_de_corchete(0) == -1:
            primero = self._avanzar()
            self._estado_texto(primero, linea, columna)
            return
        token = self._crear(self._avanzar(), CORCHETE_ABRE, linea, columna)
        # El enlace es un ambito de la pila: lo que se abra en su texto se
        # tiene que cerrar antes del ']'.
        self.pila_delimitadores.append(token)
        self.dentro_de_enlace = True

    def _estado_cierre_enlace(self):
        """
        q30: el ']' de un enlace. Lo que quedo abierto en su texto se
        reporta, se saca la marca del enlace de la pila y sigue el destino.
        """
        marca = self._posicion_de_marca()
        self._cerrar_delimitadores_desde(marca + 1)
        self.pila_delimitadores.pop()
        self.dentro_de_enlace = False
        linea = self.linea
        columna = self.columna
        self._crear(self._avanzar(), CORCHETE_CIERRA, linea, columna)
        self._estado_destino()

    def _posicion_de_marca(self):
        """Posicion en la pila del CORCHETE_ABRE del enlace abierto."""
        i = len(self.pila_delimitadores) - 1
        while i >= 0 and not self.pila_delimitadores[i].es(CORCHETE_ABRE):
            i = i - 1
        return i

    def _estado_destino(self):
        """
        q31..q33: '(' URL ')'. La URL es todo lo que hay entre los
        parentesis; el lookahead ya comprobo que no tiene espacios. Puede
        estar vacia: '[texto]()'.
        """
        linea = self.linea
        columna = self.columna
        self._crear(self._avanzar(), PARENTESIS_ABRE, linea, columna)
        if self._actual() != ')':
            linea_url = self.linea
            columna_url = self.columna
            url = ''
            while self._actual() != ')':
                url = url + self._avanzar()
            self._crear(url, URL, linea_url, columna_url)
        linea = self.linea
        columna = self.columna
        self._crear(self._avanzar(), PARENTESIS_CIERRA, linea, columna)

    def _estado_imagen(self):
        """
        q34..q36: '![' abre una imagen con la misma condicion que un enlace
        (D-32). El texto alternativo es literal: llega como un solo
        TEXTO_LITERAL, igual que el contenido de un codigo en linea.
        """
        linea = self.linea
        columna = self.columna
        cierre = self._cierre_de_corchete(1)
        if cierre == -1:
            primero = self._avanzar() + self._avanzar()
            self._estado_texto(primero, linea, columna)
            return
        lexema = self._avanzar() + self._avanzar()
        self._crear(lexema, IMAGEN_ABRE, linea, columna)

        # 'cierre' se midio desde el '!'; ya se consumieron 2 caracteres.
        faltan = cierre - 2
        if faltan > 0:
            linea_alt = self.linea
            columna_alt = self.columna
            alternativo = ''
            while faltan > 0:
                alternativo = alternativo + self._avanzar()
                faltan = faltan - 1
            self._crear(alternativo, TEXTO_LITERAL, linea_alt, columna_alt)

        linea = self.linea
        columna = self.columna
        self._crear(self._avanzar(), CORCHETE_CIERRA, linea, columna)
        self._estado_destino()

    def _cierre_de_corchete(self, inicio):
        """
        Lookahead de q29 y q35. El '[' que esta 'inicio' posiciones adelante
        abre un enlace (o una imagen) solo si, en la misma linea:
          - le sigue un ']' sin otro '[' antes. Los codigos en linea se
            saltan completos: un ']' dentro de `...` no cuenta;
          - justo despues del ']' viene '(' + una URL sin espacios + ')'.
        Devuelve el desplazamiento del ']' o -1 si no es un enlace.
        """
        k = inicio + 1
        cierre = -1
        while cierre == -1:
            c = self._ver(k)
            if alf.es_fin_de_linea(c) or c == '[' or self._es_barra(c):
                return -1
            if c == ']':
                cierre = k
            elif c == '`':
                fin = self._fin_de_codigo_inline(k)
                if self._hay_salto_entre(k, fin):
                    return -1
                k = fin
            else:
                k = k + 1
        if self._ver(cierre + 1) != '(':
            return -1
        if self._fin_de_destino(cierre) == -1:
            return -1
        return cierre

    def _fin_de_destino(self, cierre):
        """
        Lookahead del '(url)' que sigue al ']' de la posicion 'cierre'.
        Devuelve la posicion siguiente al ')', o -1 si la URL tiene un
        espacio, otro '(' o no se cierra en la linea.
        """
        k = cierre + 2
        while self._ver(k) != ')':
            c = self._ver(k)
            if alf.es_fin_de_linea(c) or alf.es_separador(c):
                return -1
            if c == '(' or self._es_barra(c):
                return -1
            k = k + 1
        return k + 1

    def _saltar_enlace(self, k):
        """
        Para la simulacion de '***': la posicion siguiente al enlace o
        imagen completo que empieza en k, porque su texto es un ambito
        aparte. Si en k no empieza uno, se avanza un caracter.
        """
        corchete = k
        if self._ver(k) == '!':
            corchete = k + 1
        cierre = self._cierre_de_corchete(corchete)
        if cierre == -1:
            return k + 1
        return self._fin_de_destino(cierre)

    def _hay_salto_entre(self, desde, hasta):
        """True si hay un '\\n' entre las dos posiciones del lookahead."""
        k = desde
        while k < hasta:
            if self._ver(k) == '\n':
                return True
            k = k + 1
        return False

    # ------------------------------------------------------------------
    # q37, q38 - TABLA y s0..s3 - SEPARADOR_TABLA
    # ------------------------------------------------------------------

    def _estado_tabla(self):
        """
        q37: linea que empieza con '|' (D-33). La fila separadora
        ('|---|:---:|') es un solo token SEPARADOR_TABLA, como una regla
        horizontal. Cualquier otra es una fila: cada '|' es una BARRA y lo
        que hay entre dos BARRA es el contenido en linea de una celda.
        """
        if self._es_separador_tabla():
            linea = self.linea
            columna = self.columna
            lexema = self._leer_hasta_fin_de_linea()
            self._crear(lexema, SEPARADOR_TABLA, linea, columna)
            self._estado_fin_linea()
            return
        self.linea_de_tabla = True
        self._estado_en_linea()

    def _estado_barra(self):
        """
        q38: cada '|' de una fila es una BARRA. La BARRA termina la celda,
        asi que antes se revisa la pila: un delimitador abierto en una
        celda se tiene que cerrar en esa misma celda.
        """
        self._cerrar_delimitadores()
        linea = self.linea
        columna = self.columna
        self._crear(self._avanzar(), BARRA, linea, columna)
        self._saltar_separadores()

    def _es_barra(self, c):
        """True si c es un '|' que separa celdas (solo en filas de tabla)."""
        return c == '|' and self.linea_de_tabla

    def _es_separador_tabla(self):
        """
        Lookahead desde el primer '|': True si la linea solo tiene celdas
        de la forma ':?-+:?' separadas por '|', con espacios alrededor.
        Cada celda se reconoce con un AFD pequeno:
            s0 --':'--> s1 --'-'--> s2      s0 --'-'--> s2
            s2 --'-'--> s2   s2 --':' o espacio--> s3   s3 --espacio--> s3
            s2 o s3 --'|'--> s0 (celda aceptada)
        Una celda vacia entre dos '|' no es valida; la ultima '|' es
        opcional.
        """
        k = 1
        celdas = 0
        estado = S_INICIO
        while not alf.es_fin_de_linea(self._ver(k)):
            c = self._ver(k)
            if c == '|':
                if estado != S_GUIONES and estado != S_CERRADA:
                    return False
                celdas = celdas + 1
                estado = S_INICIO
            elif alf.es_separador(c):
                if estado == S_DOS_PUNTOS:
                    return False
                if estado == S_GUIONES:
                    estado = S_CERRADA
            elif c == ':':
                if estado == S_INICIO:
                    estado = S_DOS_PUNTOS
                elif estado == S_GUIONES:
                    estado = S_CERRADA
                else:
                    return False
            elif c == '-':
                if estado == S_CERRADA:
                    return False
                estado = S_GUIONES
            else:
                return False
            k = k + 1
        if estado == S_GUIONES or estado == S_CERRADA:
            return True
        return estado == S_INICIO and celdas > 0

    # ==================================================================
    # Capa 1 - Nivel de lista (INDENT / DEDENT)
    # ==================================================================

    def _ajustar_nivel_lista(self, espacios, linea):
        """
        Compara la sangria de este item con el nivel de la lista abierta y
        emite un INDENT por cada nivel que sube o un DEDENT por cada nivel
        que baja (D-06). Un salto de 0 a 4 espacios emite DOS INDENT: el
        lexico no lo reporta, lo reporta el parser como error sintactico.

        Una sangria impar (3 espacios) si es un error lexico: no se puede
        partir un nivel a la mitad (D-07). Se usa el nivel inferior.
        """
        nivel = espacios // ESPACIOS_POR_NIVEL
        if espacios % ESPACIOS_POR_NIVEL != 0:
            self._error('(' + str(espacios) + ' espacios)',
                        err.INDENTACION_INVALIDA,
                        'Indentación inválida en ' +
                        self._posicion(linea, self.columna) +
                        ': la sangría debe ser múltiplo de ' +
                        str(ESPACIOS_POR_NIVEL) + ' espacios',
                        linea, self.columna)

        while self.nivel_lista < nivel:
            columna_nivel = self.nivel_lista * ESPACIOS_POR_NIVEL + 1
            self._crear('', INDENT, linea, columna_nivel)
            self.nivel_lista = self.nivel_lista + 1

        while self.nivel_lista > nivel:
            self._crear('', DEDENT, linea, 1)
            self.nivel_lista = self.nivel_lista - 1

    def _cerrar_lista(self, linea, columna):
        """
        Una linea que no es item, una linea vacia o el fin del archivo
        cierran todos los niveles de lista abiertos (D-08).
        """
        while self.nivel_lista > 0:
            self._crear('', DEDENT, linea, columna)
            self.nivel_lista = self.nivel_lista - 1

    # ==================================================================
    # Capa 2 - Pila de delimitadores (NEGRITA / CURSIVA)
    # ==================================================================

    def _tipo_cima(self):
        """Tipo del delimitador en la cima de la pila, o '' si esta vacia."""
        if len(self.pila_delimitadores) == 0:
            return ''
        cima = self.pila_delimitadores[len(self.pila_delimitadores) - 1]
        return cima.tipo

    def _cima_sin_asteriscos(self):
        """
        True si en la cima no hay una NEGRITA ni una CURSIVA: la pila esta
        vacia, o su cima es un TACHADO o la marca de un enlace. Ahi un
        '***' no puede cerrar nada, solo abrir (D-04).
        """
        cima = self._tipo_cima()
        return cima != NEGRITA and cima != CURSIVA

    def _registrar_delimitador(self, token):
        """
        Un delimitador igual a la cima la cierra (se saca de la pila); si no,
        abre uno nuevo (se mete). Ver D-04.
        """
        if self._tipo_cima() == token.tipo:
            self.pila_delimitadores.pop()
        else:
            self.pila_delimitadores.append(token)

    def _cerrar_delimitadores(self):
        """Al terminar el bloque se revisa la pila completa."""
        self._cerrar_delimitadores_desde(0)

    def _cerrar_delimitadores_desde(self, inicio):
        """
        Lo que esta en la pila desde la posicion 'inicio' hasta la cima
        nunca se cerro en su bloque (o en el texto de su enlace). Cada uno
        se reporta en su posicion de apertura y pasa a ser TEXTO, para que
        el parser no reciba un delimitador sin pareja (D-03). Se recorre
        desde abajo, que es el orden del archivo, y luego se saca.
        """
        i = inicio
        while i < len(self.pila_delimitadores):
            token = self.pila_delimitadores[i]
            self._reportar_sin_cerrar(token)
            token.tipo = TEXTO
            i = i + 1
        while len(self.pila_delimitadores) > inicio:
            self.pila_delimitadores.pop()

    def _reportar_sin_cerrar(self, token):
        posicion = self._posicion(token.linea, token.columna)
        if token.es(NEGRITA):
            self._error(token.lexema, err.NEGRITA_SIN_CERRAR,
                        'Negrita sin cerrar iniciada en ' + posicion,
                        token.linea, token.columna)
        elif token.es(CURSIVA):
            self._error(token.lexema, err.CURSIVA_SIN_CERRAR,
                        'Cursiva sin cerrar iniciada en ' + posicion,
                        token.linea, token.columna)
        elif token.es(TACHADO):
            self._error(token.lexema, err.TACHADO_SIN_CERRAR,
                        'Tachado sin cerrar iniciado en ' + posicion,
                        token.linea, token.columna)


def aplicar_en_pila(pila, tipo):
    """
    La regla de la pila de delimitadores (D-04) sobre una pila de tipos:
    si el tipo es igual a la cima la cierra; si no, lo abre. La usa la
    simulacion de '***' en _se_cierra_todo().
    """
    if len(pila) > 0 and pila[len(pila) - 1] == tipo:
        pila.pop()
    else:
        pila.append(tipo)
