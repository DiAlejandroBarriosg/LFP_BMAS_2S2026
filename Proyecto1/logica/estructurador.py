# -*- coding: utf-8 -*-
"""
estructurador.py

Segunda pasada del sistema. El AFD ya produjo una lista plana de tokens; aqui
se recorre esa lista para reconstruir los objetos del horario.

NO es un analizador sintactico. No valida la gramatica ni construye un arbol:
es un recorrido dirigido por palabras clave que reacciona a los tokens
RESERVADA_ELEMENTO (curso, catedratico, aula, clase) y lee lo que viene
despues. Esa eleccion es deliberada:

  1. El Proyecto 1 solo exige analisis lexico. Un parser formal corresponde al
     Proyecto 2 y meterlo aqui seria alcance que nadie pidio.
  2. El archivo puede traer errores lexicos, asi que faltaran tokens en medio
     del flujo. Un recorrido tolerante sigue armando lo que si se puede armar;
     un parser estricto abortaria y dejaria los reportes vacios.

Cuando algo no cuadra se registra un Aviso y se salta al siguiente elemento.
Los avisos son inconsistencias estructurales o de referencia, NO errores
lexicos: esos ya los reporto el AFD.
"""

from modelos.elementos import Curso, Catedratico, Aula, Clase, Aviso
from analizador import palabras_reservadas as pr
from analizador import alfabeto as alf

# Tipos de aviso
A_ATRIBUTO_FALTANTE = 'ATRIBUTO_FALTANTE'
A_TIPO_INCORRECTO = 'TIPO_INCORRECTO'
A_CODIGO_DUPLICADO = 'CODIGO_DUPLICADO'
A_REFERENCIA_INEXISTENTE = 'REFERENCIA_INEXISTENTE'
A_RANGO_INVALIDO = 'RANGO_INVALIDO'
A_BLOQUE_INCORRECTO = 'BLOQUE_INCORRECTO'
A_ESTRUCTURA_INCOMPLETA = 'ESTRUCTURA_INCOMPLETA'
A_VALOR_PERDIDO = 'VALOR_PERDIDO'
A_BLOQUE_DUPLICADO = 'BLOQUE_DUPLICADO'
A_BLOQUE_FALTANTE = 'BLOQUE_FALTANTE'

# El enunciado establece que cada palabra reservada de bloque aparece
# exactamente una vez en el archivo
BLOQUES_ESPERADOS = ('HORARIO', 'CURSOS', 'CATEDRATICOS', 'AULAS', 'CLASES')

# En que bloque debe aparecer cada elemento
BLOQUE_ESPERADO = {
    'curso': 'CURSOS',
    'catedratico': 'CATEDRATICOS',
    'aula': 'AULAS',
    'clase': 'CLASES',
}


class Estructurador:

    def __init__(self):
        self.cursos = []
        self.catedraticos = []
        self.aulas = []
        self.clases = []
        self.avisos = []
        self.tokens = []
        self.pos = 0
        self.bloque_actual = ''
        self.contador_aviso = 0
        self.bloques_vistos = {}

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def estructurar(self, tokens):
        self.cursos = []
        self.catedraticos = []
        self.aulas = []
        self.clases = []
        self.avisos = []
        self.contador_aviso = 0
        self.bloque_actual = ''
        self.bloques_vistos = {}
        self.pos = 0
        self.tokens = self._sin_comentarios(tokens)

        while self._hay_mas():
            token = self._actual()

            if token.tipo == pr.T_RESERVADA_BLOQUE:
                self._registrar_bloque(token)
                self.bloque_actual = token.lexema
                self._avanzar()
                continue

            if token.tipo == pr.T_RESERVADA_ELEMENTO:
                self._leer_elemento()
                continue

            self._avanzar()

        self._validar_bloques()
        self._validar_duplicados()
        self._validar_referencias()
        self._validar_horas()
        return self

    # ------------------------------------------------------------------
    # Recorrido
    # ------------------------------------------------------------------

    def _sin_comentarios(self, tokens):
        """Los comentarios son tokens validos, pero no aportan estructura."""
        limpios = []
        i = 0
        while i < len(tokens):
            if tokens[i].tipo != pr.T_COMENTARIO:
                limpios.append(tokens[i])
            i = i + 1
        return limpios

    def _hay_mas(self):
        return self.pos < len(self.tokens)

    def _actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _avanzar(self):
        token = self.tokens[self.pos]
        self.pos = self.pos + 1
        return token

    def _es_lexema(self, token, texto):
        return token is not None and token.lexema == texto

    def _consumir_si(self, texto):
        """Consume el token actual solo si su lexema coincide."""
        if self._hay_mas() and self._es_lexema(self._actual(), texto):
            self._avanzar()
            return True
        return False

    def _es_delimitador(self, token):
        """
        Un delimitador nunca puede ser el valor de un atributo. Comprobarlo
        antes de consumirlo es lo que evita que el lector se desfase cuando el
        AFD descarto un valor por ser un error lexico: en 'dia: LUNEZ,' el
        lexema LUNEZ no llega como token, y sin esta guarda la coma ocuparia
        su lugar y el resto de la lista se leeria corrida.
        """
        if token is None:
            return True
        if token.tipo != pr.T_SIMBOLO:
            return False
        i = 0
        cierres = (',', ']', ';', '[', '{', '}')
        while i < len(cierres):
            if token.lexema == cierres[i]:
                return True
            i = i + 1
        return False

    def _aviso(self, tipo, descripcion, linea):
        self.contador_aviso = self.contador_aviso + 1
        aviso = Aviso(self.contador_aviso, tipo, descripcion, linea)
        self.avisos.append(aviso)
        return aviso

    def _saltar_hasta_fin_de_elemento(self):
        """
        Recuperacion: avanza hasta la coma o el punto y coma que cierra el
        elemento actual, sin cruzar el inicio de otro elemento o bloque.
        """
        while self._hay_mas():
            token = self._actual()
            if token.tipo == pr.T_RESERVADA_ELEMENTO:
                return
            if token.tipo == pr.T_RESERVADA_BLOQUE:
                return
            self._avanzar()
            if token.lexema == ',' or token.lexema == ';':
                return

    # ------------------------------------------------------------------
    # Lectura de un elemento
    # ------------------------------------------------------------------

    def _leer_elemento(self):
        token_elemento = self._avanzar()
        nombre_elemento = token_elemento.lexema
        linea = token_elemento.linea

        esperado = BLOQUE_ESPERADO[nombre_elemento]
        if self.bloque_actual != esperado:
            if self.bloque_actual == '':
                descripcion = ("'" + nombre_elemento + "' no esta dentro de "
                               'ningun bloque y deberia declararse en ' +
                               esperado)
            else:
                descripcion = ("'" + nombre_elemento + "' aparece dentro de " +
                               self.bloque_actual + ' y deberia declararse en ' +
                               esperado)
            self._aviso(A_BLOQUE_INCORRECTO, descripcion, linea)

        if not self._consumir_si(':'):
            self._aviso(A_ESTRUCTURA_INCOMPLETA,
                        "falta ':' despues de '" + nombre_elemento + "'", linea)
            self._saltar_hasta_fin_de_elemento()
            return

        if nombre_elemento == 'clase':
            self._leer_clase(linea)
        elif nombre_elemento == 'curso':
            self._leer_curso(linea)
        elif nombre_elemento == 'catedratico':
            self._leer_catedratico(linea)
        elif nombre_elemento == 'aula':
            self._leer_aula(linea)

    def _leer_identificador(self, nombre_elemento, linea):
        """
        Lee el valor que sigue a 'elemento:'. Se acepta CADENA o CODIGO porque
        un nombre de aula puede ser 'A-101' (CODIGO) o 'MAGNA' (CADENA).
        """
        if not self._hay_mas():
            self._aviso(A_ESTRUCTURA_INCOMPLETA,
                        "'" + nombre_elemento + "' sin valor", linea)
            return None

        token = self._actual()
        if token.tipo == pr.T_CADENA or token.tipo == pr.T_CODIGO:
            self._avanzar()
            return token

        self._aviso(A_TIPO_INCORRECTO,
                    "el valor de '" + nombre_elemento + "' es " + token.tipo +
                    " y se esperaba CADENA o CODIGO", token.linea)
        return None

    def _leer_atributos(self, linea):
        """
        Lee el bloque '[ atributo: valor, ... ]' y devuelve un diccionario
        {nombre_atributo: token_valor}. Tolera atributos repetidos (gana el
        ultimo) y basura intercalada.
        """
        atributos = {}

        if not self._consumir_si('['):
            self._aviso(A_ESTRUCTURA_INCOMPLETA,
                        "falta '[' con los atributos", linea)
            return atributos

        while self._hay_mas():
            token = self._actual()

            if token.lexema == ']':
                self._avanzar()
                return atributos

            # un elemento o bloque nuevo significa que nunca se cerro el '['
            if token.tipo == pr.T_RESERVADA_ELEMENTO or token.tipo == pr.T_RESERVADA_BLOQUE:
                self._aviso(A_ESTRUCTURA_INCOMPLETA,
                            "falta ']' al cerrar los atributos", linea)
                return atributos

            if token.tipo == pr.T_RESERVADA_ATRIBUTO:
                nombre = self._avanzar().lexema
                if not self._consumir_si(':'):
                    self._aviso(A_ESTRUCTURA_INCOMPLETA,
                                "falta ':' despues de '" + nombre + "'",
                                token.linea)
                    continue
                if not self._hay_mas():
                    self._aviso(A_ATRIBUTO_FALTANTE,
                                "'" + nombre + "' quedo sin valor", token.linea)
                    continue
                siguiente = self._actual()
                valor_perdido = False
                if self._es_delimitador(siguiente):
                    valor_perdido = True
                if siguiente.tipo == pr.T_RESERVADA_ATRIBUTO:
                    valor_perdido = True

                if valor_perdido:
                    self._aviso(A_VALOR_PERDIDO,
                                "el valor de '" + nombre + "' no llego como " +
                                "token; revise la tabla de errores lexicos",
                                token.linea)
                    # se registra con valor None para que los extractores no
                    # vuelvan a avisar 'atributo faltante' por lo mismo
                    atributos[nombre] = None
                    continue
                atributos[nombre] = self._avanzar()
                continue

            self._avanzar()

        self._aviso(A_ESTRUCTURA_INCOMPLETA,
                    "falta ']' al cerrar los atributos", linea)
        return atributos

    # ------------------------------------------------------------------
    # Extraccion de valores con validacion de tipo
    # ------------------------------------------------------------------

    def _sin_comillas(self, lexema):
        """
        Quita la comilla de apertura y la de cierre: '"LFP-0796"' -> 'LFP-0796'.
        Copia caracter por caracter desde el segundo hasta el penultimo.
        """
        if len(lexema) < 2:
            return lexema

        ultimo = len(lexema) - 1
        if lexema[0] != '"' or lexema[ultimo] != '"':
            return lexema

        resultado = ''
        i = 1
        while i < ultimo:
            resultado = resultado + lexema[i]
            i = i + 1
        return resultado

    def _texto(self, atributos, nombre, tipos_validos, contexto, linea,
               por_defecto=''):
        if nombre not in atributos:
            self._aviso(A_ATRIBUTO_FALTANTE,
                        contexto + ' sin atributo ' + nombre, linea)
            return por_defecto

        token = atributos[nombre]
        if token is None:
            return por_defecto      # ya se reporto como VALOR_PERDIDO

        i = 0
        while i < len(tipos_validos):
            if token.tipo == tipos_validos[i]:
                return self._sin_comillas(token.lexema)
            i = i + 1

        esperados = ''
        i = 0
        while i < len(tipos_validos):
            if i > 0:
                esperados = esperados + ' o '
            esperados = esperados + tipos_validos[i]
            i = i + 1

        self._aviso(A_TIPO_INCORRECTO,
                    contexto + ': el atributo ' + nombre + ' es ' + token.tipo +
                    ' y se esperaba ' + esperados, token.linea)
        return por_defecto

    def _entero(self, atributos, nombre, contexto, linea):
        if nombre not in atributos:
            self._aviso(A_ATRIBUTO_FALTANTE,
                        contexto + ' sin atributo ' + nombre, linea)
            return 0

        token = atributos[nombre]
        if token is None:
            return 0                # ya se reporto como VALOR_PERDIDO

        if token.tipo != pr.T_ENTERO:
            self._aviso(A_TIPO_INCORRECTO,
                        contexto + ': el atributo ' + nombre + ' es ' +
                        token.tipo + ' y se esperaba ENTERO', token.linea)
            return 0

        return alf.valor_entero(token.lexema)

    # ------------------------------------------------------------------
    # Constructores de cada elemento
    # ------------------------------------------------------------------

    def _leer_curso(self, linea):
        token_nombre = self._leer_identificador('curso', linea)
        if token_nombre is None:
            self._saltar_hasta_fin_de_elemento()
            return

        nombre = self._sin_comillas(token_nombre.lexema)
        atributos = self._leer_atributos(linea)
        contexto = 'curso "' + nombre + '"'

        codigo = self._texto(atributos, 'codigo', (pr.T_CODIGO,), contexto, linea)
        creditos = self._entero(atributos, 'creditos', contexto, linea)

        if codigo == '':
            return
        self.cursos.append(Curso(nombre, codigo, creditos, linea))

    def _leer_catedratico(self, linea):
        token_nombre = self._leer_identificador('catedratico', linea)
        if token_nombre is None:
            self._saltar_hasta_fin_de_elemento()
            return

        nombre = self._sin_comillas(token_nombre.lexema)
        atributos = self._leer_atributos(linea)
        contexto = 'catedratico "' + nombre + '"'

        codigo = self._texto(atributos, 'codigo', (pr.T_CODIGO,), contexto, linea)
        categoria = self._texto(atributos, 'categoria', (pr.T_CATEGORIA,),
                                contexto, linea, 'SIN CATEGORIA')

        if codigo == '':
            return
        self.catedraticos.append(Catedratico(nombre, codigo, categoria, linea))

    def _leer_aula(self, linea):
        token_codigo = self._leer_identificador('aula', linea)
        if token_codigo is None:
            self._saltar_hasta_fin_de_elemento()
            return

        codigo = self._sin_comillas(token_codigo.lexema)
        atributos = self._leer_atributos(linea)
        contexto = 'aula "' + codigo + '"'

        capacidad = self._entero(atributos, 'capacidad', contexto, linea)
        edificio = self._texto(atributos, 'edificio',
                               (pr.T_CODIGO, pr.T_CADENA), contexto, linea,
                               'SIN EDIFICIO')

        self.aulas.append(Aula(codigo, capacidad, edificio, linea))

    def _leer_clase(self, linea):
        """
        clase: "CURSO" con "CATEDRATICO" en "AULA" [dia, inicio, fin, seccion]
        """
        token_curso = self._leer_identificador('clase', linea)
        if token_curso is None:
            self._saltar_hasta_fin_de_elemento()
            return
        codigo_curso = self._sin_comillas(token_curso.lexema)
        contexto = 'clase de "' + codigo_curso + '"'

        codigo_catedratico = ''
        if self._consumir_si('con'):
            token = self._leer_identificador('con', linea)
            if token is not None:
                codigo_catedratico = self._sin_comillas(token.lexema)
        else:
            self._aviso(A_ESTRUCTURA_INCOMPLETA,
                        contexto + ": falta la relacion 'con'", linea)

        codigo_aula = ''
        if self._consumir_si('en'):
            token = self._leer_identificador('en', linea)
            if token is not None:
                codigo_aula = self._sin_comillas(token.lexema)
        else:
            self._aviso(A_ESTRUCTURA_INCOMPLETA,
                        contexto + ": falta la relacion 'en'", linea)

        atributos = self._leer_atributos(linea)

        dia = self._texto(atributos, 'dia', (pr.T_DIA,), contexto, linea)
        inicio = self._texto(atributos, 'inicio', (pr.T_HORA,), contexto, linea)
        fin = self._texto(atributos, 'fin', (pr.T_HORA,), contexto, linea)
        seccion = self._texto(atributos, 'seccion',
                              (pr.T_CADENA, pr.T_CODIGO), contexto, linea,
                              'SIN SECCION')

        # Sin dia u horas no se puede evaluar traslape: la clase se descarta
        # para no producir falsos negativos en el detector de choques.
        if dia == '' or inicio == '' or fin == '':
            self._aviso(A_ESTRUCTURA_INCOMPLETA,
                        contexto + ' se descarta: le falta dia, inicio o fin',
                        linea)
            return

        self.clases.append(Clase(codigo_curso, codigo_catedratico, codigo_aula,
                                 dia, inicio, fin, seccion, linea))

    # ------------------------------------------------------------------
    # Validaciones posteriores
    # ------------------------------------------------------------------

    def _registrar_bloque(self, token):
        nombre = token.lexema
        if nombre in self.bloques_vistos:
            self._aviso(A_BLOQUE_DUPLICADO,
                        'el bloque ' + nombre + ' ya se habia declarado en la '
                        'linea ' + str(self.bloques_vistos[nombre]),
                        token.linea)
        else:
            self.bloques_vistos[nombre] = token.linea

    def _validar_bloques(self):
        """
        El enunciado establece que cada bloque aparece exactamente una vez.
        Un bloque ausente se reporta en la linea 0 porque no tiene posicion:
        el problema es justamente que no esta en el archivo.
        """
        i = 0
        while i < len(BLOQUES_ESPERADOS):
            nombre = BLOQUES_ESPERADOS[i]
            if nombre not in self.bloques_vistos:
                self._aviso(A_BLOQUE_FALTANTE,
                            'el archivo no declara el bloque ' + nombre, 0)
            i = i + 1

    def _codigos(self, lista):
        codigos = []
        i = 0
        while i < len(lista):
            codigos.append(lista[i].codigo)
            i = i + 1
        return codigos

    def _validar_duplicados(self):
        self._buscar_duplicados('curso', self.cursos)
        self._buscar_duplicados('catedratico', self.catedraticos)
        self._buscar_duplicados('aula', self.aulas)

    def _buscar_duplicados(self, etiqueta, lista):
        """
        Recorre una lista de elementos y avisa si un codigo se repite.
        'vistos' guarda cada codigo junto con la linea donde aparecio primero.
        """
        vistos = {}
        i = 0
        while i < len(lista):
            codigo = lista[i].codigo
            if codigo in vistos:
                self._aviso(A_CODIGO_DUPLICADO,
                            'el codigo ' + codigo + ' del ' + etiqueta +
                            ' ya se habia declarado en la linea ' +
                            str(vistos[codigo]), lista[i].linea)
            else:
                vistos[codigo] = lista[i].linea
            i = i + 1

    def _validar_referencias(self):
        codigos_curso = self._codigos(self.cursos)
        codigos_catedratico = self._codigos(self.catedraticos)
        codigos_aula = self._codigos(self.aulas)

        i = 0
        while i < len(self.clases):
            clase = self.clases[i]

            if clase.codigo_curso not in codigos_curso:
                self._aviso(A_REFERENCIA_INEXISTENTE,
                            'la clase referencia el curso ' + clase.codigo_curso +
                            ', que no esta declarado en CURSOS', clase.linea)

            if clase.codigo_catedratico not in codigos_catedratico:
                self._aviso(A_REFERENCIA_INEXISTENTE,
                            'la clase referencia el catedratico ' +
                            clase.codigo_catedratico +
                            ', que no esta declarado en CATEDRATICOS',
                            clase.linea)

            if clase.codigo_aula not in codigos_aula:
                self._aviso(A_REFERENCIA_INEXISTENTE,
                            'la clase referencia el aula ' + clase.codigo_aula +
                            ', que no esta declarada en AULAS', clase.linea)
            i = i + 1

    def _validar_horas(self):
        i = 0
        while i < len(self.clases):
            clase = self.clases[i]
            if clase.fin <= clase.inicio:
                self._aviso(A_RANGO_INVALIDO,
                            'la clase de ' + clase.codigo_curso +
                            ' termina a las ' + clase.fin_texto +
                            ' y empieza a las ' + clase.inicio_texto,
                            clase.linea)
            i = i + 1

    # ------------------------------------------------------------------
    # Consultas para las siguientes sesiones
    # ------------------------------------------------------------------

    def buscar_curso(self, codigo):
        return self._buscar(self.cursos, codigo)

    def buscar_catedratico(self, codigo):
        return self._buscar(self.catedraticos, codigo)

    def buscar_aula(self, codigo):
        return self._buscar(self.aulas, codigo)

    def _buscar(self, lista, codigo):
        i = 0
        while i < len(lista):
            if lista[i].codigo == codigo:
                return lista[i]
            i = i + 1
        return None

    def clases_por_dia(self):
        """Agrupa las clases por dia. Base del detector de choques."""
        grupos = {}
        i = 0
        while i < len(self.clases):
            dia = self.clases[i].dia
            if dia not in grupos:
                grupos[dia] = []
            grupos[dia].append(self.clases[i])
            i = i + 1
        return grupos

    def secciones(self):
        """Lista ordenada de las secciones presentes en el archivo."""
        encontradas = []
        i = 0
        while i < len(self.clases):
            seccion = self.clases[i].seccion
            if seccion not in encontradas:
                encontradas.append(seccion)
            i = i + 1
        encontradas.sort()
        return encontradas

    def resumen(self):
        return {
            'cursos': len(self.cursos),
            'catedraticos': len(self.catedraticos),
            'aulas': len(self.aulas),
            'clases': len(self.clases),
            'avisos': len(self.avisos),
            'secciones': len(self.secciones()),
        }
