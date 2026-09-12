# -*- coding: utf-8 -*-
"""
analizador_lexico.py

AFD de HorarioScript implementado manualmente. Cada estado del automata
disenado en la Seccion 3 del documento de diseno corresponde a un metodo
privado _estado_*. No se usa el modulo re ni funciones de alto nivel de
cadenas: el recorrido es caracter por caracter mediante indexacion.

Mapa estado -> metodo
    q0  INICIAL          siguiente_token()
    q1  PALABRA          _estado_palabra()
    q2  COD_GUION        _estado_codigo()
    q3  COD_DIGITOS      _estado_codigo()
    q4  NUMERO           _estado_numero()
    q5  HORA_SEP         _estado_hora()
    q6  HORA_MIN1        _estado_hora()
    q7  HORA_COMPLETA    _estado_hora()
    q8  CADENA_ABIERTA   _estado_literal()
    q9  CADENA_CERRADA   _clasificar_literal()
    q10 NUMERAL1         _estado_comentario()
    q11 COMENTARIO       _estado_comentario()
    q12 SIMBOLO          siguiente_token()
    qE  ERROR            se delega al GestorErrores
"""

from modelos.token import Token
from analizador.gestor_errores import GestorErrores
from analizador import alfabeto as alf
from analizador import palabras_reservadas as pr

ANCHO_TABULACION = 4


class AnalizadorLexico:

    def __init__(self, texto=''):
        self.texto = texto
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.tokens = []
        self.contador_token = 0
        self.gestor = GestorErrores()
        # Memoria de un token: ultimo RESERVADA_ATRIBUTO visto.
        # Permite clasificar una palabra desconocida como DIA_NO_RECONOCIDO
        # (decision D-04 del documento de diseno).
        self.ultimo_atributo = ''

    # ------------------------------------------------------------------
    # Control del recorrido
    # ------------------------------------------------------------------

    def reiniciar(self, texto):
        self.texto = texto
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.tokens = []
        self.contador_token = 0
        self.gestor.limpiar()
        self.ultimo_atributo = ''

    def _hay_mas(self):
        return self.pos < len(self.texto)

    def _actual(self):
        """Caracter en la posicion actual, o '' si se llego al final."""
        if self.pos < len(self.texto):
            return self.texto[self.pos]
        return ''

    def _ver(self, desplazamiento):
        """
        Lookahead SIN consumir. Devuelve '' si la posicion queda fuera del
        texto. Al no consumir, el AFD no necesita retroceder el indice: la
        decision HORA vs ENTERO se toma antes de avanzar.
        """
        indice = self.pos + desplazamiento
        if indice < len(self.texto):
            return self.texto[indice]
        return ''

    def _avanzar(self):
        """
        Consume un caracter y actualiza los contadores de posicion.
        - '\\n' incrementa la linea y reinicia la columna a 1
        - '\\t' cuenta como ANCHO_TABULACION columnas
        - '\\r' avanza la posicion sin mover la columna (archivos con CRLF)
        """
        c = self.texto[self.pos]
        self.pos = self.pos + 1
        if c == '\n':
            self.linea = self.linea + 1
            self.columna = 1
        elif c == '\t':
            self.columna = self.columna + ANCHO_TABULACION
        elif c == '\r':
            pass
        else:
            self.columna = self.columna + 1
        return c

    def _saltar_espacios(self):
        """Los espacios son delimitadores silenciosos: no generan token."""
        while self._hay_mas() and alf.es_espacio(self._actual()):
            self._avanzar()

    def _crear(self, lexema, tipo, linea, columna):
        self.contador_token = self.contador_token + 1
        return Token(self.contador_token, lexema, tipo, linea, columna)

    def _error(self, lexema, tipo, descripcion, linea, columna):
        mensaje = descripcion + ' en linea ' + str(linea) + ', columna ' + str(columna)
        self.gestor.agregar(lexema, tipo, mensaje, linea, columna)
        return None

    # ------------------------------------------------------------------
    # q0 - Estado inicial: despacha segun el primer caracter
    # ------------------------------------------------------------------

    def siguiente_token(self):
        """
        Devuelve el siguiente Token, o None si se encontro un error o se
        llego al final del archivo. El llamador distingue ambos casos
        consultando _hay_mas().
        """
        self._saltar_espacios()
        if not self._hay_mas():
            return None

        c = self._actual()
        linea_ini = self.linea
        col_ini = self.columna

        if alf.es_letra(c):
            return self._estado_palabra(linea_ini, col_ini)

        if alf.es_digito(c):
            return self._estado_numero(linea_ini, col_ini)

        if c == '"':
            return self._estado_literal(linea_ini, col_ini)

        if c == '#':
            return self._estado_comentario(linea_ini, col_ini)

        if alf.es_simbolo(c):
            self._avanzar()
            return self._crear(c, pr.T_SIMBOLO, linea_ini, col_ini)

        # qE: el caracter no inicia ningun patron valido
        self._avanzar()
        return self._error(c, pr.E_CARACTER,
                           "Caracter no reconocido: '" + c + "'",
                           linea_ini, col_ini)

    def analizar(self, texto=None):
        """
        Recorre todo el texto en una sola pasada acumulando tokens y errores.
        No se detiene ante el primer error (modo panico).
        """
        if texto is not None:
            self.reiniciar(texto)

        while True:
            token = self.siguiente_token()
            if token is None:
                if not self._hay_mas():
                    break      # fin del archivo
                continue       # hubo un error: se sigue analizando
            self.tokens.append(token)

        return self.tokens

    # ------------------------------------------------------------------
    # q1 - Palabras y codigos sin comillas
    # ------------------------------------------------------------------

    def _estado_palabra(self, linea_ini, col_ini):
        lexema = ''
        while self._hay_mas() and alf.es_alfanumerico(self._actual()):
            lexema = lexema + self._avanzar()

        # q1 --'-'--> q2 : la secuencia continua como codigo sin comillas
        if self._hay_mas() and self._actual() == '-':
            return self._estado_codigo(lexema, linea_ini, col_ini)

        return self._clasificar_palabra(lexema, linea_ini, col_ini)

    def _clasificar_palabra(self, lexema, linea_ini, col_ini):
        """
        Clasificacion en la aceptacion de q1. El orden importa: las listas se
        consultan de la mas especifica a la mas general.
        """
        if alf.pertenece(lexema, pr.BLOQUES):
            return self._crear(lexema, pr.T_RESERVADA_BLOQUE, linea_ini, col_ini)

        if alf.pertenece(lexema, pr.ELEMENTOS):
            return self._crear(lexema, pr.T_RESERVADA_ELEMENTO, linea_ini, col_ini)

        if alf.pertenece(lexema, pr.RELACIONES):
            return self._crear(lexema, pr.T_RESERVADA_RELACION, linea_ini, col_ini)

        if alf.pertenece(lexema, pr.ATRIBUTOS):
            self.ultimo_atributo = lexema
            return self._crear(lexema, pr.T_RESERVADA_ATRIBUTO, linea_ini, col_ini)

        if alf.pertenece(lexema, pr.DIAS):
            self.ultimo_atributo = ''
            return self._crear(lexema, pr.T_DIA, linea_ini, col_ini)

        if alf.pertenece(lexema, pr.CATEGORIAS):
            self.ultimo_atributo = ''
            return self._crear(lexema, pr.T_CATEGORIA, linea_ini, col_ini)

        # Palabra desconocida: se clasifica con la memoria de un token (D-04).
        # La memoria se reinicia para no arrastrar el contexto al resto del
        # archivo: solo aplica al valor inmediatamente siguiente al atributo.
        atributo = self.ultimo_atributo
        self.ultimo_atributo = ''

        if alf.son_iguales(atributo, 'dia'):
            return self._error(lexema, pr.E_DIA,
                               "Dia no reconocido: '" + lexema + "'",
                               linea_ini, col_ini)

        if alf.son_iguales(atributo, 'categoria'):
            return self._error(lexema, pr.E_DIA,
                               "Categoria no reconocida: '" + lexema + "'",
                               linea_ini, col_ini)

        return self._error(lexema, pr.E_CARACTER,
                           "Palabra no reconocida: '" + lexema + "'",
                           linea_ini, col_ini)

    # ------------------------------------------------------------------
    # q2 / q3 - Codigo sin comillas: L (L|D)* '-' D+
    # ------------------------------------------------------------------

    def _estado_codigo(self, prefijo, linea_ini, col_ini):
        """
        Consume '-' y el resto de la secuencia alfanumerica, luego valida la
        forma. Se consume TODO el lexema antes de decidir para que un codigo
        malo genere un solo error y no una cascada de errores falsos.
        """
        lexema = prefijo + self._avanzar()   # el guion
        digitos = 0
        forma_valida = True

        while self._hay_mas() and (alf.es_alfanumerico(self._actual()) or
                                   self._actual() == '-'):
            c = self._avanzar()
            if alf.es_digito(c):
                digitos = digitos + 1
            else:
                # una letra o un segundo guion despues del guion invalidan
                # el patron L(L|D)*-D+
                forma_valida = False
            lexema = lexema + c

        # el prefijo debe empezar con letra
        if len(prefijo) == 0 or not alf.es_letra(prefijo[0]):
            forma_valida = False

        if forma_valida and digitos > 0:
            return self._crear(lexema, pr.T_CODIGO, linea_ini, col_ini)

        return self._error(lexema, pr.E_CODIGO,
                           "Codigo mal formado: '" + lexema + "'",
                           linea_ini, col_ini)

    # ------------------------------------------------------------------
    # q4 - Numero: puede resolverse como ENTERO o como HORA
    # ------------------------------------------------------------------

    def _estado_numero(self, linea_ini, col_ini):
        lexema = ''
        while self._hay_mas() and alf.es_digito(self._actual()):
            lexema = lexema + self._avanzar()

        # q4 --':'--> q5 solo con exactamente 2 digitos y lookahead DD (D-02)
        if len(lexema) == 2 and self._actual() == ':':
            if alf.es_digito(self._ver(1)) and alf.es_digito(self._ver(2)):
                return self._estado_hora(lexema, linea_ini, col_ini)
            # sin lookahead valido: no se consume el ':', que sera SIMBOLO

        # digitos seguidos de guion: intento de codigo (fallara la validacion
        # del prefijo, que debe empezar con letra)
        if self._hay_mas() and self._actual() == '-':
            return self._estado_codigo(lexema, linea_ini, col_ini)

        return self._crear(lexema, pr.T_ENTERO, linea_ini, col_ini)

    # ------------------------------------------------------------------
    # q5 / q6 / q7 - Hora HH:MM
    # ------------------------------------------------------------------

    def _estado_hora(self, hh, linea_ini, col_ini):
        lexema = hh + self._avanzar()        # los dos puntos
        mm = ''
        contador = 0
        while contador < 2:
            c = self._avanzar()
            mm = mm + c
            lexema = lexema + c
            contador = contador + 1

        # Si siguen mas digitos (por ejemplo 07:000) el lexema esta mal formado.
        # Se consumen todos para no generar un ENTERO fantasma despues.
        if alf.es_digito(self._actual()):
            while self._hay_mas() and alf.es_digito(self._actual()):
                lexema = lexema + self._avanzar()
            return self._error(lexema, pr.E_HORA,
                               "Hora fuera de rango: '" + lexema + "'",
                               linea_ini, col_ini)

        horas = alf.valor_entero(hh)
        minutos = alf.valor_entero(mm)

        if minutos > 59:
            return self._error(lexema, pr.E_HORA,
                               "Hora fuera de rango: '" + lexema + "'",
                               linea_ini, col_ini)

        total = horas * 60 + minutos
        if total < pr.MIN_HORA_INSTITUCIONAL or total > pr.MAX_HORA_INSTITUCIONAL:
            return self._error(lexema, pr.E_HORA,
                               "Hora fuera de rango: '" + lexema + "'",
                               linea_ini, col_ini)

        return self._crear(lexema, pr.T_HORA, linea_ini, col_ini)

    # ------------------------------------------------------------------
    # q8 / q9 - Literal entre comillas
    # ------------------------------------------------------------------

    def _estado_literal(self, linea_ini, col_ini):
        self._avanzar()                      # comilla de apertura
        contenido = ''
        cerrada = False

        while self._hay_mas():
            c = self._actual()
            if c == '\n':
                break                        # fin de linea sin cierre
            self._avanzar()
            if c == '"':
                cerrada = True
                break
            contenido = contenido + c

        if not cerrada:
            return self._error('"' + contenido, pr.E_CADENA,
                               'Cadena sin cerrar iniciada',
                               linea_ini, col_ini)

        return self._clasificar_literal(contenido, linea_ini, col_ini)

    def _clasificar_literal(self, contenido, linea_ini, col_ini):
        """
        Decision D-01: un literal sin espacios y con exactamente un guion es
        un candidato a CODIGO; cualquier otro literal es una CADENA.
        """
        lexema = '"' + contenido + '"'
        espacios = 0
        guiones = 0
        i = 0
        while i < len(contenido):
            if contenido[i] == ' ':
                espacios = espacios + 1
            elif contenido[i] == '-':
                guiones = guiones + 1
            i = i + 1

        if espacios > 0 or guiones != 1:
            return self._crear(lexema, pr.T_CADENA, linea_ini, col_ini)

        if self._es_codigo_valido(contenido):
            return self._crear(lexema, pr.T_CODIGO, linea_ini, col_ini)

        return self._error(lexema, pr.E_CODIGO,
                           "Codigo mal formado: '" + lexema + "'",
                           linea_ini, col_ini)

    def _es_codigo_valido(self, contenido):
        """
        Valida el patron L (L|D)* '-' D+ sobre el contenido de un literal.
        Nota: el prefijo admite digitos despues de la primera letra porque el
        propio enunciado usa 'BD2-0812' como codigo valido.
        """
        if len(contenido) == 0:
            return False
        if not alf.es_letra(contenido[0]):
            return False

        i = 0
        # prefijo alfanumerico
        while i < len(contenido) and alf.es_alfanumerico(contenido[i]):
            i = i + 1
        if i == 0 or i >= len(contenido):
            return False
        if contenido[i] != '-':
            return False
        i = i + 1
        if i >= len(contenido):
            return False
        # sufijo: al menos un digito y solo digitos
        while i < len(contenido):
            if not alf.es_digito(contenido[i]):
                return False
            i = i + 1
        return True

    # ------------------------------------------------------------------
    # q10 / q11 - Comentario de linea
    # ------------------------------------------------------------------

    def _estado_comentario(self, linea_ini, col_ini):
        self._avanzar()                      # primer '#'

        if not (self._hay_mas() and self._actual() == '#'):
            return self._error('#', pr.E_CARACTER,
                               "Caracter no reconocido: '#'",
                               linea_ini, col_ini)

        self._avanzar()                      # segundo '#'
        lexema = '##'
        while self._hay_mas() and self._actual() != '\n':
            lexema = lexema + self._avanzar()

        return self._crear(lexema, pr.T_COMENTARIO, linea_ini, col_ini)

    # ------------------------------------------------------------------
    # Utilidades de consulta
    # ------------------------------------------------------------------

    def contar_por_tipo(self):
        conteo = {}
        i = 0
        while i < len(self.tokens):
            tipo = self.tokens[i].tipo
            if tipo in conteo:
                conteo[tipo] = conteo[tipo] + 1
            else:
                conteo[tipo] = 1
            i = i + 1
        return conteo
