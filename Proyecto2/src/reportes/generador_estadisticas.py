# -*- coding: utf-8 -*-
"""
generador_estadisticas.py
GeneradorEstadisticas: Reporte 2, resumen cuantitativo del documento.

Todo se cuenta recorriendo el arbol de derivacion: cada estadistica es la
cantidad de nodos de un no terminal (o el nivel maximo de alguno).

    Palabras            D-14: palabras de cada <en_linea> (sin bloques de
                        codigo). Cada linea con texto tiene un <en_linea>.
    Parrafos            nodos <parrafo>
    Encabezados         nodos <encabezado>, agrupados por su nivel
    Listas / items      <lista> de nivel 1 / <item_lista>
    Citas / lineas      <cita> de nivel 1 / <contenido_cita>
    Profundidades       nivel maximo de <lista> y de <cita>
    En linea            <negrita>, <cursiva>, <codigo_inline>
    Bloques y reglas    <bloque_codigo>, <regla_horizontal>
    Alcance opcional    <lista> numeradas, hojas CASILLA, <tachado>,
                        <enlace>, <imagen>, <tabla>. La seccion solo
                        aparece si el documento usa alguno.
"""

from lexico import alfabeto as alf
from sintactico.nodo_ast import NT_PARRAFO, NT_ENCABEZADO, NT_LISTA
from sintactico.nodo_ast import NT_ITEM_LISTA, NT_CITA, NT_CONTENIDO_CITA
from sintactico.nodo_ast import NT_BLOQUE_CODIGO, NT_REGLA_HORIZONTAL
from sintactico.nodo_ast import NT_EN_LINEA, NT_NEGRITA, NT_CURSIVA
from sintactico.nodo_ast import NT_CODIGO_INLINE, NT_TACHADO, NT_ENLACE
from sintactico.nodo_ast import NT_IMAGEN, NT_TABLA
from lexico.token import CASILLA
from reportes import recorridos
from reportes.plantilla import escapar, pagina, guardar

NOMBRE_REPORTE = 'reporte2_estadisticas.html'


class GeneradorEstadisticas:

    def __init__(self, raiz, nombre_archivo):
        self.raiz = raiz
        self.nombre_archivo = nombre_archivo
        self.calcular()

    # ------------------------------------------------------------------
    # Calculo
    # ------------------------------------------------------------------

    def calcular(self):
        """Llena todos los atributos con lo que hay en el arbol."""
        self.palabras = self._contar_palabras()
        self.parrafos = self._contar(NT_PARRAFO)
        self.encabezados = self._contar(NT_ENCABEZADO)
        self.por_nivel = self._encabezados_por_nivel()

        self.listas = self._contar_con_nivel(NT_LISTA, 1)
        self.items = self._contar(NT_ITEM_LISTA)
        self.profundidad_listas = self._nivel_maximo(NT_LISTA)

        self.citas = self._contar_con_nivel(NT_CITA, 1)
        self.lineas_cita = self._contar(NT_CONTENIDO_CITA)
        self.profundidad_citas = self._nivel_maximo(NT_CITA)

        self.bloques_codigo = self._contar(NT_BLOQUE_CODIGO)
        self.reglas = self._contar(NT_REGLA_HORIZONTAL)
        self.negritas = self._contar(NT_NEGRITA)
        self.cursivas = self._contar(NT_CURSIVA)
        self.codigos_inline = self._contar(NT_CODIGO_INLINE)

        self.listas_numeradas = self._contar_numeradas()
        self.tareas = self._contar(CASILLA)
        self.tareas_hechas = self._contar_tareas_hechas()
        self.tachados = self._contar(NT_TACHADO)
        self.enlaces = self._contar(NT_ENLACE)
        self.imagenes = self._contar(NT_IMAGEN)
        self.tablas = self._contar(NT_TABLA)

    def usa_alcance_opcional(self):
        total = (self.listas_numeradas + self.tareas + self.tachados +
                 self.enlaces + self.imagenes + self.tablas)
        return total > 0

    def _contar_numeradas(self):
        """Todas las <lista> numeradas, tambien las sublistas."""
        nodos = recorridos.buscar(self.raiz, NT_LISTA, [])
        total = 0
        i = 0
        while i < len(nodos):
            if nodos[i].numerada:
                total = total + 1
            i = i + 1
        return total

    def _contar_tareas_hechas(self):
        """Las CASILLA marcadas: '[x]' o '[X]'."""
        casillas = recorridos.buscar(self.raiz, CASILLA, [])
        total = 0
        i = 0
        while i < len(casillas):
            if casillas[i].token.lexema != '[ ]':
                total = total + 1
            i = i + 1
        return total

    def _contar(self, simbolo):
        return len(recorridos.buscar(self.raiz, simbolo, []))

    def _contar_con_nivel(self, simbolo, nivel):
        nodos = recorridos.buscar(self.raiz, simbolo, [])
        total = 0
        i = 0
        while i < len(nodos):
            if nodos[i].nivel == nivel:
                total = total + 1
            i = i + 1
        return total

    def _nivel_maximo(self, simbolo):
        nodos = recorridos.buscar(self.raiz, simbolo, [])
        maximo = 0
        i = 0
        while i < len(nodos):
            if nodos[i].nivel > maximo:
                maximo = nodos[i].nivel
            i = i + 1
        return maximo

    def _encabezados_por_nivel(self):
        """Lista de 6 contadores: posicion 0 = H1, ..., posicion 5 = H6."""
        cuenta = [0, 0, 0, 0, 0, 0]
        nodos = recorridos.encabezados(self.raiz)
        i = 0
        while i < len(nodos):
            nivel = nodos[i].nivel
            if nivel >= 1 and nivel <= 6:
                cuenta[nivel - 1] = cuenta[nivel - 1] + 1
            i = i + 1
        return cuenta

    def _contar_palabras(self):
        """
        D-14: se toma el texto de cada <en_linea> sin delimitadores y se
        cuentan las secuencias separadas por espacios. El codigo en linea
        cuenta; los bloques de codigo no (no tienen <en_linea>). El texto
        de un enlace ya esta dentro del <en_linea> de su linea, por eso no
        se baja a los <en_linea> anidados.
        """
        total = 0
        lineas = recorridos.buscar_sin_anidar(self.raiz, NT_EN_LINEA, [])
        i = 0
        while i < len(lineas):
            total = total + contar_palabras(recorridos.texto_plano(lineas[i]))
            i = i + 1
        return total

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------

    def generar(self):
        cuerpo = ('<h1>Estadísticas del documento</h1>\n'
                  '<p class="subtitulo">' + escapar(self.nombre_archivo) +
                  '</p>\n')

        cuerpo = cuerpo + '<div class="tarjetas">\n'
        cuerpo = cuerpo + self._tarjeta(self.palabras, 'Palabras totales')
        cuerpo = cuerpo + self._tarjeta(self.parrafos, 'Párrafos')
        cuerpo = cuerpo + self._tarjeta(self.encabezados, 'Encabezados')
        cuerpo = cuerpo + self._tarjeta(self.listas, 'Listas')
        cuerpo = cuerpo + self._tarjeta(self.items, 'Ítems de lista')
        cuerpo = cuerpo + self._tarjeta(self.citas, 'Citas')
        cuerpo = cuerpo + self._tarjeta(self.lineas_cita, 'Líneas de cita')
        cuerpo = cuerpo + self._tarjeta(self.bloques_codigo,
                                        'Bloques de código')
        cuerpo = cuerpo + '</div>\n'

        cuerpo = cuerpo + '<h2 class="seccion">Encabezados por nivel</h2>\n'
        cuerpo = cuerpo + self._barras()

        cuerpo = cuerpo + ('<h2 class="seccion">Profundidad máxima de '
                           'anidamiento</h2>\n<div class="pares">\n')
        cuerpo = cuerpo + self._par('Listas',
                                    self._niveles(self.profundidad_listas))
        cuerpo = cuerpo + self._par('Citas',
                                    self._niveles(self.profundidad_citas))
        cuerpo = cuerpo + '</div>\n'

        cuerpo = cuerpo + ('<h2 class="seccion">Elementos en línea y '
                           'separadores</h2>\n<div class="pares">\n')
        cuerpo = cuerpo + self._par('Negrita (**texto**)',
                                    str(self.negritas))
        cuerpo = cuerpo + self._par('Cursiva (*texto*)', str(self.cursivas))
        cuerpo = cuerpo + self._par('Código en línea (`texto`)',
                                    str(self.codigos_inline))
        cuerpo = cuerpo + self._par('Regla horizontal (---)',
                                    str(self.reglas))
        cuerpo = cuerpo + '</div>\n'

        if self.usa_alcance_opcional():
            cuerpo = cuerpo + self._seccion_opcional()

        return pagina('Reporte 2 - ' + self.nombre_archivo, cuerpo,
                      self.nombre_archivo)

    def guardar(self, carpeta):
        return guardar(carpeta, NOMBRE_REPORTE, self.generar())

    def _seccion_opcional(self):
        html = ('<h2 class="seccion">Alcance opcional</h2>\n'
                '<div class="pares">\n')
        html = html + self._par('Listas numeradas (1. 2. 3.)',
                                str(self.listas_numeradas))
        tareas = str(self.tareas)
        if self.tareas_hechas == 1:
            tareas = tareas + ' (1 hecha)'
        elif self.tareas > 0:
            tareas = tareas + ' (' + str(self.tareas_hechas) + ' hechas)'
        html = html + self._par('Tareas (- [ ] / - [x])', tareas)
        html = html + self._par('Tachado (~~texto~~)', str(self.tachados))
        html = html + self._par('Enlaces [texto](url)', str(self.enlaces))
        html = html + self._par('Imágenes ![alt](url)', str(self.imagenes))
        html = html + self._par('Tablas (| a | b |)', str(self.tablas))
        return html + '</div>\n'

    def _tarjeta(self, numero, rotulo):
        return ('<div class="tarjeta"><div class="numero">' + str(numero) +
                '</div><div class="rotulo">' + rotulo + '</div></div>\n')

    def _par(self, rotulo, valor):
        return ('<div class="par"><span>' + escapar(rotulo) +
                '</span><span class="valor">' + valor + '</span></div>\n')

    def _niveles(self, cantidad):
        if cantidad == 1:
            return '1 nivel'
        return str(cantidad) + ' niveles'

    def _barras(self):
        """
        Grafico de barras simple: el ancho de cada barra es su cantidad
        como porcentaje del nivel con mas encabezados.
        """
        maximo = 0
        i = 0
        while i < 6:
            if self.por_nivel[i] > maximo:
                maximo = self.por_nivel[i]
            i = i + 1

        html = ''
        i = 0
        while i < 6:
            ancho = 0
            if maximo > 0:
                ancho = (self.por_nivel[i] * 100) // maximo
            html = (html + '<div class="barra-fila"><strong>H' + str(i + 1) +
                    '</strong><div class="barra-fondo"><div class="barra" '
                    'style="width: ' + str(ancho) + '%"></div></div><span>' +
                    str(self.por_nivel[i]) + '</span></div>\n')
            i = i + 1
        return html


def contar_palabras(texto):
    """
    Cuenta las secuencias de caracteres separadas por espacios o
    tabuladores. Se cuenta una palabra cada vez que empieza una: un
    caracter que no es separador y que viene despues de un separador (o al
    inicio).
    """
    total = 0
    dentro = False
    i = 0
    while i < len(texto):
        if alf.es_separador(texto[i]):
            dentro = False
        elif not dentro:
            total = total + 1
            dentro = True
        i = i + 1
    return total
