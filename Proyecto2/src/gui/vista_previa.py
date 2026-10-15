# -*- coding: utf-8 -*-
"""
vista_previa.py
VistaPrevia: muestra el documento ya formateado dentro de la ventana
(alcance opcional, D-34).

Tkinter no tiene un navegador para mostrar HTML, asi que la vista previa
hace lo mismo que GeneradorHTML pero con otro destino: RECORRE EL ARBOL DE
DERIVACION y, en vez de escribir etiquetas HTML, inserta el texto en un
tk.Text con etiquetas de formato (negrita, cursiva, tamano de titulo...).
Cada no terminal tiene su funcion, igual que en el Reporte 1:

    <encabezado> nivel n   texto grande               _encabezado()
    <parrafo>              lineas unidas con espacio  _parrafo()
    <lista>                '•' o '1.' con sangria     _lista(), _item()
    <cita>                 barra '▎' por nivel, gris  _cita()
    <bloque_codigo>        fondo oscuro, monoespacio  _bloque_codigo()
    <regla_horizontal>     una linea '─'              _bloque()
    <tabla>                columnas alineadas         _tabla()
    <negrita> <cursiva> <tachado> <codigo_inline>     _en_linea()
    <enlace>               azul y subrayado; clic     _en_linea()
    <imagen>               [imagen: texto]            _en_linea()

Tkinter solo admite una fuente por fragmento de texto, asi que negrita y
cursiva juntas usan su propia etiqueta ('f_nc').
"""

import webbrowser
import tkinter as tk

from lexico.token import TEXTO, TEXTO_LITERAL, SALTO_LINEA, LENGUAJE_CODIGO
from lexico.token import CASILLA
from sintactico.nodo_ast import NT_BLOQUE, NT_ENCABEZADO, NT_PARRAFO
from sintactico.nodo_ast import NT_LINEA_TEXTO, NT_LISTA, NT_ITEM_LISTA
from sintactico.nodo_ast import NT_SUBLISTA, NT_CITA, NT_CONTENIDO_CITA
from sintactico.nodo_ast import NT_BLOQUE_CODIGO, NT_CONTENIDO_CODIGO
from sintactico.nodo_ast import NT_REGLA_HORIZONTAL, NT_EN_LINEA
from sintactico.nodo_ast import NT_EN_LINEA_N, NT_EN_LINEA_C, NT_EN_LINEA_T
from sintactico.nodo_ast import NT_NEGRITA, NT_CURSIVA, NT_TACHADO
from sintactico.nodo_ast import NT_CODIGO_INLINE, NT_ENLACE, NT_IMAGEN
from sintactico.nodo_ast import NT_TABLA, NT_FILA_TABLA, NT_CELDA
from reportes import recorridos

FUENTE = 'Segoe UI'
FUENTE_CODIGO = 'Consolas'
TAMANO = 11
# Tamano de cada nivel de encabezado, de H1 a H6.
TAMANOS_ENCABEZADO = [20, 17, 15, 13, 12, 11]
SANGRIA_LISTA = 22
SANGRIA_CITA = 18
LINEA_HORIZONTAL = 48


class Estilo:
    """
    El formato que se va acumulando al bajar por el arbol: dentro de una
    negrita todo es negrita, dentro de una cursiva que esta en una negrita
    todo es negrita y cursiva, etc. Cada funcion recibe el estilo de su
    padre y hace una copia con lo que ella agrega.
    """

    def __init__(self):
        self.negrita = False
        self.cursiva = False
        self.tachado = False
        self.codigo = False
        self.encabezado = 0
        self.enlace = ''
        # Etiquetas de bloque (sangria de lista, nivel de cita...).
        self.bloque = []

    def copia(self):
        nuevo = Estilo()
        nuevo.negrita = self.negrita
        nuevo.cursiva = self.cursiva
        nuevo.tachado = self.tachado
        nuevo.codigo = self.codigo
        nuevo.encabezado = self.encabezado
        nuevo.enlace = self.enlace
        i = 0
        while i < len(self.bloque):
            nuevo.bloque.append(self.bloque[i])
            i = i + 1
        return nuevo

    def con_bloque(self, etiqueta):
        nuevo = self.copia()
        nuevo.bloque.append(etiqueta)
        return nuevo


class VistaPrevia:

    def __init__(self, texto):
        """'texto' es el tk.Text donde se dibuja; queda de solo lectura."""
        self.texto = texto
        # Cada enlace dibujado: [etiqueta 'enlace_k', su URL].
        self.enlaces = []
        self._configurar_etiquetas()

    def _configurar_etiquetas(self):
        t = self.texto
        t.configure(wrap=tk.WORD, padx=14, pady=10, cursor='arrow',
                    font=(FUENTE, TAMANO), spacing1=2, spacing3=2)
        t.tag_configure('f_n', font=(FUENTE, TAMANO, 'bold'))
        t.tag_configure('f_c', font=(FUENTE, TAMANO, 'italic'))
        t.tag_configure('f_nc', font=(FUENTE, TAMANO, 'bold italic'))
        t.tag_configure('f_m', font=(FUENTE_CODIGO, TAMANO - 1))
        i = 0
        while i < len(TAMANOS_ENCABEZADO):
            t.tag_configure('h' + str(i + 1), spacing1=10, spacing3=6,
                            font=(FUENTE, TAMANOS_ENCABEZADO[i], 'bold'))
            i = i + 1
        t.tag_configure('codigo', background='#eff1f3')
        t.tag_configure('tachado', overstrike=1, foreground='#57606a')
        t.tag_configure('enlace', foreground='#2e75b6', underline=1)
        # Los eventos se enlazan una sola vez a la etiqueta 'enlace'; al
        # hacer clic se busca cual 'enlace_k' esta bajo el raton.
        t.tag_bind('enlace', '<Button-1>', self._al_hacer_clic_en_enlace)
        t.tag_bind('enlace', '<Enter>', self._mano)
        t.tag_bind('enlace', '<Leave>', self._flecha)
        t.tag_configure('imagen', foreground='#57606a',
                        font=(FUENTE, TAMANO, 'italic'))
        t.tag_configure('bloque', font=(FUENTE_CODIGO, TAMANO - 1),
                        background='#0f1419', foreground='#e6edf3',
                        lmargin1=12, lmargin2=12, rmargin=12)
        t.tag_configure('tabla', font=(FUENTE_CODIGO, TAMANO - 1),
                        lmargin1=6, lmargin2=6)
        # Se crea despues de 'tabla' para que su fuente tenga prioridad.
        t.tag_configure('tabla_encabezado',
                        font=(FUENTE_CODIGO, TAMANO - 1, 'bold'))
        t.tag_configure('regla', foreground='#d0d7de')
        t.tag_configure('barra_cita', foreground='#d0d7de')
        t.tag_configure('cita', foreground='#57606a')
        t.tag_configure('marcador', foreground='#57606a')
        t.tag_configure('parrafo', spacing3=8)

    # ==================================================================
    # Punto de entrada
    # ==================================================================

    def mostrar(self, raiz):
        """Borra lo que habia y dibuja el documento del arbol 'raiz'."""
        self.texto.configure(state=tk.NORMAL)
        self.texto.delete('1.0', tk.END)
        self._borrar_enlaces()
        if raiz is not None:
            i = 0
            while i < len(raiz.hijos):
                hijo = raiz.hijos[i]
                if hijo.es(NT_BLOQUE):
                    self._bloque(hijo.hijos[0], Estilo())
                elif hijo.es(NT_SUBLISTA):
                    # Sublista sin item padre (D-24): con error, pero se
                    # muestra lo que se reconocio.
                    self._sublista(hijo, Estilo(), 0)
                    self._escribir('\n', Estilo(), ['parrafo'])
                i = i + 1
        self.texto.configure(state=tk.DISABLED)

    def contenido(self):
        """El texto que se ve, sin formato. Lo usan las pruebas."""
        return self.texto.get('1.0', 'end-1c')

    def _borrar_enlaces(self):
        i = 0
        while i < len(self.enlaces):
            self.texto.tag_delete(self.enlaces[i][0])
            i = i + 1
        self.enlaces = []

    def _escribir(self, texto, estilo, extra):
        """
        Inserta 'texto' al final con las etiquetas que tocan segun el
        estilo: la de bloque, la de la fuente y las de formato.
        """
        etiquetas = []
        i = 0
        while i < len(estilo.bloque):
            etiquetas.append(estilo.bloque[i])
            i = i + 1
        fuente = self._etiqueta_de_fuente(estilo)
        if fuente != '':
            etiquetas.append(fuente)
        if estilo.codigo:
            etiquetas.append('codigo')
        if estilo.tachado:
            etiquetas.append('tachado')
        if estilo.enlace != '':
            etiquetas.append('enlace')
            etiquetas.append(estilo.enlace)
        i = 0
        while i < len(extra):
            etiquetas.append(extra[i])
            i = i + 1
        self.texto.insert(tk.END, texto, etiquetas)

    def _etiqueta_de_fuente(self, estilo):
        if estilo.encabezado > 0:
            return 'h' + str(estilo.encabezado)
        if estilo.codigo:
            return 'f_m'
        if estilo.negrita and estilo.cursiva:
            return 'f_nc'
        if estilo.negrita:
            return 'f_n'
        if estilo.cursiva:
            return 'f_c'
        return ''

    # ==================================================================
    # Bloques
    # ==================================================================

    def _bloque(self, nodo, estilo):
        if nodo.es(NT_ENCABEZADO):
            self._encabezado(nodo, estilo)
        elif nodo.es(NT_PARRAFO):
            self._parrafo(nodo, estilo)
        elif nodo.es(NT_LISTA):
            self._lista(nodo, estilo, 1)
            self._escribir('\n', estilo, ['parrafo'])
        elif nodo.es(NT_CITA):
            self._cita(nodo, estilo)
            self._escribir('\n', estilo, ['parrafo'])
        elif nodo.es(NT_BLOQUE_CODIGO):
            self._bloque_codigo(nodo, estilo)
        elif nodo.es(NT_REGLA_HORIZONTAL):
            linea = ''
            i = 0
            while i < LINEA_HORIZONTAL:
                linea = linea + '─'
                i = i + 1
            self._escribir(linea + '\n', estilo, ['regla', 'parrafo'])
        elif nodo.es(NT_TABLA):
            self._tabla(nodo, estilo)

    def _encabezado(self, nodo, estilo):
        propio = estilo.copia()
        propio.encabezado = nodo.nivel
        self._en_linea(recorridos.hijo_con_simbolo(nodo, NT_EN_LINEA), propio)
        self._escribir('\n', propio, [])

    def _parrafo(self, nodo, estilo):
        """Las lineas de un parrafo se unen con un espacio, como en HTML."""
        primera = True
        i = 0
        while i < len(nodo.hijos):
            linea = nodo.hijos[i]
            if linea.es(NT_LINEA_TEXTO):
                if not primera:
                    self._escribir(' ', estilo, [])
                self._en_linea(recorridos.hijo_con_simbolo(linea,
                                                           NT_EN_LINEA),
                               estilo)
                primera = False
            i = i + 1
        self._escribir('\n', estilo, ['parrafo'])

    def _lista(self, nodo, estilo, nivel):
        """
        Cada nivel de lista es una etiqueta con mas sangria. Los items de
        una lista numerada se cuentan desde el numero del primero.
        """
        etiqueta = 'lista_' + str(nivel)
        margen = SANGRIA_LISTA * nivel
        self.texto.tag_configure(etiqueta, lmargin1=margen - 16,
                                 lmargin2=margen)
        propio = estilo.con_bloque(etiqueta)
        numero = recorridos.numero_inicial(nodo)
        i = 0
        while i < len(nodo.hijos):
            item = nodo.hijos[i]
            if item.es(NT_ITEM_LISTA):
                marcador = '•  '
                if nodo.numerada:
                    marcador = str(numero) + '. '
                    numero = numero + 1
                self._item(item, propio, marcador, nivel)
            i = i + 1

    def _item(self, nodo, estilo, marcador, nivel):
        casilla = recorridos.hijo_con_simbolo(nodo, CASILLA)
        if casilla is not None:
            # Una tarea muestra su casilla en vez de la viñeta (D-30).
            marcador = '☐  '
            if casilla.token.lexema != '[ ]':
                marcador = '☑  '
        self._escribir(marcador, estilo, ['marcador'])
        self._en_linea(recorridos.hijo_con_simbolo(nodo, NT_EN_LINEA), estilo)
        self._escribir('\n', estilo, [])
        sublista = recorridos.hijo_con_simbolo(nodo, NT_SUBLISTA)
        if sublista is not None:
            self._sublista(sublista, estilo, nivel)

    def _sublista(self, nodo, estilo, nivel):
        """La sublista dibuja su lista (o sus listas) un nivel mas adentro."""
        sin_nivel = estilo.copia()
        sin_nivel.bloque = []
        i = 0
        while i < len(nodo.hijos):
            hijo = nodo.hijos[i]
            if hijo.es(NT_LISTA):
                self._lista(hijo, sin_nivel, nivel + 1)
            elif hijo.es(NT_SUBLISTA):
                self._sublista(hijo, sin_nivel, nivel + 1)
            i = i + 1

    def _cita(self, nodo, estilo):
        """
        Cada linea de la cita empieza con una barra '▎' por nivel; una
        cita anidada es una barra mas.
        """
        barras = ''
        i = 0
        while i < nodo.nivel:
            barras = barras + '▎ '
            i = i + 1
        propio = estilo.con_bloque('cita')
        i = 0
        while i < len(nodo.hijos):
            hijo = nodo.hijos[i]
            if hijo.es(NT_CONTENIDO_CITA):
                self._escribir(barras, propio, ['barra_cita'])
                encabezado = recorridos.hijo_con_simbolo(hijo, NT_ENCABEZADO)
                if encabezado is not None:
                    self._encabezado(encabezado, propio)
                else:
                    self._en_linea(recorridos.hijo_con_simbolo(hijo,
                                                               NT_EN_LINEA),
                                   propio)
                    self._escribir('\n', propio, [])
            elif hijo.es(NT_CITA):
                self._cita(hijo, estilo)
            i = i + 1

    def _bloque_codigo(self, nodo, estilo):
        cuerpo = recorridos.hijo_con_simbolo(nodo, NT_CONTENIDO_CODIGO)
        lenguaje = recorridos.hijo_con_simbolo(nodo, LENGUAJE_CODIGO)
        if lenguaje is not None:
            self._escribir(' ' + lenguaje.token.lexema + '\n', estilo,
                           ['bloque', 'marcador'])
        i = 0
        while i < len(cuerpo.hijos):
            hijo = cuerpo.hijos[i]
            if hijo.es(TEXTO_LITERAL):
                self._escribir(' ' + hijo.token.lexema + '\n', estilo,
                               ['bloque'])
            i = i + 1
        self._escribir('\n', estilo, ['parrafo'])

    def _tabla(self, nodo, estilo):
        """
        Las celdas se escriben como texto sin formato, rellenadas con
        espacios para que las columnas queden alineadas. El encabezado va
        en negrita y debajo una linea '─'.
        """
        filas = []
        i = 0
        while i < len(nodo.hijos):
            if nodo.hijos[i].es(NT_FILA_TABLA):
                filas.append(textos_de_fila(nodo.hijos[i]))
            i = i + 1
        hay_encabezado = recorridos.tabla_tiene_encabezado(nodo)
        anchos = anchos_de_columnas(filas)

        f = 0
        while f < len(filas):
            linea = ''
            c = 0
            while c < len(anchos):
                texto = ''
                if c < len(filas[f]):
                    texto = filas[f][c]
                alineacion = ''
                if c < len(nodo.alineaciones):
                    alineacion = nodo.alineaciones[c]
                linea = linea + ' ' + rellenar(texto, anchos[c],
                                               alineacion) + ' '
                if c < len(anchos) - 1:
                    linea = linea + '│'
                c = c + 1
            extra = ['tabla']
            if f == 0 and hay_encabezado:
                extra = ['tabla', 'tabla_encabezado']
            self._escribir(linea + '\n', estilo, extra)
            if f == 0 and hay_encabezado:
                self._escribir(linea_de_tabla(anchos) + '\n', estilo,
                               ['tabla', 'regla'])
            f = f + 1
        self._escribir('\n', estilo, ['parrafo'])

    # ==================================================================
    # Elementos en linea
    # ==================================================================

    def _en_linea(self, nodo, estilo):
        """
        Dibuja un <en_linea>, <en_linea_n>, <en_linea_c> o <en_linea_t>.
        Cada formato hace una copia del estilo, le agrega lo suyo y vuelve
        a llamar a esta funcion con su contenido.
        """
        if nodo is None:
            return
        i = 0
        while i < len(nodo.hijos):
            hijo = nodo.hijos[i]
            if hijo.es(TEXTO):
                self._escribir(hijo.token.lexema, estilo, [])
            elif hijo.es(SALTO_LINEA):
                self._escribir(' ', estilo, [])
            elif hijo.es(NT_NEGRITA):
                propio = estilo.copia()
                propio.negrita = True
                self._en_linea(recorridos.hijo_con_simbolo(hijo,
                                                           NT_EN_LINEA_N),
                               propio)
            elif hijo.es(NT_CURSIVA):
                propio = estilo.copia()
                propio.cursiva = True
                self._en_linea(recorridos.hijo_con_simbolo(hijo,
                                                           NT_EN_LINEA_C),
                               propio)
            elif hijo.es(NT_TACHADO):
                propio = estilo.copia()
                propio.tachado = True
                self._en_linea(recorridos.hijo_con_simbolo(hijo,
                                                           NT_EN_LINEA_T),
                               propio)
            elif hijo.es(NT_CODIGO_INLINE):
                propio = estilo.copia()
                propio.codigo = True
                self._escribir(recorridos.texto_plano(hijo), propio, [])
            elif hijo.es(NT_ENLACE):
                propio = estilo.copia()
                propio.enlace = self._nuevo_enlace(recorridos.destino(hijo))
                self._en_linea(recorridos.hijo_con_simbolo(hijo, NT_EN_LINEA),
                               propio)
            elif hijo.es(NT_IMAGEN):
                alternativo = recorridos.hijo_con_simbolo(hijo, TEXTO_LITERAL)
                texto = 'imagen'
                if alternativo is not None:
                    texto = 'imagen: ' + alternativo.token.lexema
                self._escribir('[' + texto + ']', estilo, ['imagen'])
            i = i + 1

    def _nuevo_enlace(self, url):
        """
        Crea la etiqueta 'enlace_k' de un enlace y guarda su URL. Esta
        etiqueta no tiene eventos propios: solo dice que URL abrir.
        """
        etiqueta = 'enlace_' + str(len(self.enlaces))
        self.enlaces.append([etiqueta, url])
        return etiqueta

    def _al_hacer_clic_en_enlace(self, evento):
        """Abre en el navegador la URL del enlace que esta bajo el raton."""
        etiquetas = self.texto.tag_names('current')
        i = 0
        while i < len(etiquetas):
            url = self._url_de(etiquetas[i])
            if url != '':
                webbrowser.open(url)
                return
            i = i + 1

    def _url_de(self, etiqueta):
        """La URL del enlace con esa etiqueta, o '' si no es un enlace."""
        i = 0
        while i < len(self.enlaces):
            if self.enlaces[i][0] == etiqueta:
                return self.enlaces[i][1]
            i = i + 1
        return ''

    def _mano(self, evento):
        self.texto.configure(cursor='hand2')

    def _flecha(self, evento):
        self.texto.configure(cursor='arrow')


# ======================================================================
# Funciones de apoyo
# ======================================================================

def textos_de_fila(fila):
    """El texto sin formato de cada <celda> de una fila."""
    textos = []
    i = 0
    while i < len(fila.hijos):
        if fila.hijos[i].es(NT_CELDA):
            texto = recorridos.texto_plano(fila.hijos[i])
            textos.append(recorridos.quitar_espacios_finales(texto))
        i = i + 1
    return textos


def anchos_de_columnas(filas):
    """El ancho de cada columna es el de su celda mas larga."""
    anchos = []
    f = 0
    while f < len(filas):
        c = 0
        while c < len(filas[f]):
            if c >= len(anchos):
                anchos.append(0)
            if len(filas[f][c]) > anchos[c]:
                anchos[c] = len(filas[f][c])
            c = c + 1
        f = f + 1
    return anchos


def rellenar(texto, ancho, alineacion):
    """Completa con espacios hasta 'ancho' segun la alineacion."""
    faltan = ancho - len(texto)
    izquierda = 0
    if alineacion == 'right':
        izquierda = faltan
    elif alineacion == 'center':
        izquierda = faltan // 2
    derecha = faltan - izquierda
    return espacios(izquierda) + texto + espacios(derecha)


def espacios(cantidad):
    texto = ''
    i = 0
    while i < cantidad:
        texto = texto + ' '
        i = i + 1
    return texto


def linea_de_tabla(anchos):
    """La linea '───┼───' que separa el encabezado de las filas."""
    linea = ''
    c = 0
    while c < len(anchos):
        i = 0
        while i < anchos[c] + 2:
            linea = linea + '─'
            i = i + 1
        if c < len(anchos) - 1:
            linea = linea + '┼'
        c = c + 1
    return linea
