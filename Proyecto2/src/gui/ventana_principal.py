# -*- coding: utf-8 -*-
"""
ventana_principal.py
VentanaPrincipal: interfaz grafica de MarkdownCheck (Tkinter).

La interfaz NO analiza nada por si misma: solo junta las piezas.
    1. lee el archivo y lo muestra en el editor;
    2. crea GestorErrores, AnalizadorLexico y AnalizadorSintactico;
    3. muestra la tabla de tokens, la de errores y el arbol;
    4. llama a generar_todos() para los reportes, y abre el que se pida.

Paneles
    Barra superior   abrir, guardar, analizar, limpiar y abrir reportes
    Aviso            advertencia de anidamiento (solo cuando se pasa)
    Editor           el documento .md, con numeros de linea
    Pestanas         Tokens | Errores | Arbol de derivacion | Vista previa
    Barra inferior   estado del analisis, anidamiento maximo y posicion
                     del cursor

Alcance opcional (D-34, D-35): la vista previa y la advertencia se
actualizan solas mientras se escribe, ESPERA_VISTA_PREVIA milisegundos
despues de la ultima tecla.

Atajos: Ctrl+O abrir, Ctrl+S guardar, F5 analizar.
"""

import os
import pathlib
import shutil
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from lexico.analizador_lexico import AnalizadorLexico
from sintactico.analizador_sintactico import AnalizadorSintactico
from errores.gestor_errores import GestorErrores
from reportes.generador_reportes import generar_todos
from reportes import recorridos
from gui.vista_previa import VistaPrevia

TITULO = 'MarkdownCheck'
FUENTE_EDITOR = ('Consolas', 11)
COLOR_ERROR = '#fde2e1'
COLOR_SELECCION = '#fff3b0'
COLOR_ANIDAMIENTO = '#ffedc7'

# Alcance opcional
ESPERA_VISTA_PREVIA = 400
ANIDAMIENTO_MAXIMO = 3
PESTANA_VISTA_PREVIA = 3


class VentanaPrincipal:

    def __init__(self, ventana, carpeta_salida):
        self.ventana = ventana
        self.carpeta_salida = carpeta_salida

        self.ruta_archivo = ''
        self.nombre_archivo = 'sin_titulo.md'
        self.tokens = []
        self.gestor = None
        self.rutas = {}
        # Fraccion del editor que esta arriba de lo visible (0.0 = inicio).
        # Se guarda para que los numeros de linea sigan al editor.
        self.fraccion_visible = 0.0
        # Vista previa en vivo: el arbol del texto actual del editor y la
        # actualizacion que espera a que se deje de escribir.
        self.raiz_vivo = None
        self.pendiente = None

        self.ventana.title(TITULO)
        self.ventana.geometry('1280x760')
        self.ventana.minsize(900, 560)

        self._construir_barra()
        self._construir_estado()
        self._construir_aviso()
        self._construir_cuerpo()
        self._registrar_atajos()
        self._actualizar_botones_reportes()
        self._actualizar_vista_previa()
        self._mostrar_estado('Abra un archivo .md o escriba en el editor y '
                             'presione Analizar (F5).')

    # ==================================================================
    # Construccion de la ventana
    # ==================================================================

    def _construir_barra(self):
        barra = ttk.Frame(self.ventana, padding=(8, 6))
        barra.pack(side=tk.TOP, fill=tk.X)

        boton = ttk.Button(barra, text='Abrir .md', command=self.abrir_archivo)
        boton.pack(side=tk.LEFT)
        boton = ttk.Button(barra, text='Guardar', command=self.guardar_archivo)
        boton.pack(side=tk.LEFT, padx=(4, 0))
        boton = ttk.Button(barra, text='Analizar (F5)', command=self.analizar)
        boton.pack(side=tk.LEFT, padx=(4, 0))
        boton = ttk.Button(barra, text='Limpiar', command=self.limpiar)
        boton.pack(side=tk.LEFT, padx=(4, 0))

        ttk.Separator(barra, orient=tk.VERTICAL).pack(side=tk.LEFT,
                                                      fill=tk.Y, padx=12)
        ttk.Label(barra, text='Reportes:').pack(side=tk.LEFT, padx=(0, 6))

        self.boton_r1 = ttk.Button(barra, text='1. Documento',
                                   command=self.abrir_reporte1)
        self.boton_r1.pack(side=tk.LEFT)
        self.boton_r2 = ttk.Button(barra, text='2. Estadísticas',
                                   command=self.abrir_reporte2)
        self.boton_r2.pack(side=tk.LEFT, padx=(4, 0))
        self.boton_r3 = ttk.Button(barra, text='3. Índice',
                                   command=self.abrir_reporte3)
        self.boton_r3.pack(side=tk.LEFT, padx=(4, 0))
        self.boton_errores = ttk.Button(barra, text='Errores',
                                        command=self.abrir_reporte_errores)
        self.boton_errores.pack(side=tk.LEFT, padx=(4, 0))
        self.boton_arbol = ttk.Button(barra, text='Árbol',
                                      command=self.abrir_arbol)
        self.boton_arbol.pack(side=tk.LEFT, padx=(4, 0))
        self.boton_carpeta = ttk.Button(barra, text='Carpeta de salida',
                                        command=self.abrir_carpeta_salida)
        self.boton_carpeta.pack(side=tk.LEFT, padx=(4, 0))

    def _construir_estado(self):
        estado = ttk.Frame(self.ventana, padding=(8, 4))
        estado.pack(side=tk.BOTTOM, fill=tk.X)
        self.etiqueta_estado = ttk.Label(estado, text='')
        self.etiqueta_estado.pack(side=tk.LEFT)
        self.etiqueta_cursor = ttk.Label(estado, text='Línea 1, columna 1')
        self.etiqueta_cursor.pack(side=tk.RIGHT)

        # Anidamiento maximo configurable (D-35), a la izquierda del cursor.
        self.maximo_anidamiento = tk.StringVar(value=str(ANIDAMIENTO_MAXIMO))
        self.selector_maximo = ttk.Spinbox(
            estado, from_=1, to=20, width=4,
            textvariable=self.maximo_anidamiento,
            command=self._al_cambiar_maximo)
        self.selector_maximo.pack(side=tk.RIGHT, padx=(0, 36))
        self.selector_maximo.bind('<KeyRelease>', self._al_cambiar_maximo)
        ttk.Label(estado, text='Anidamiento máximo:').pack(side=tk.RIGHT,
                                                           padx=(12, 6))

    def _construir_aviso(self):
        """
        Franja amarilla de la advertencia de anidamiento. Se crea vacia y
        solo se muestra (pack) cuando el documento pasa el maximo.
        """
        self.aviso = tk.Label(self.ventana, text='', anchor=tk.W,
                              justify=tk.LEFT, background='#fff4d6',
                              foreground='#7a4b00', padx=10, pady=5)
        self.aviso_visible = False

    def _construir_cuerpo(self):
        paneles = ttk.PanedWindow(self.ventana, orient=tk.HORIZONTAL)
        paneles.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8)
        self.paneles = paneles

        izquierda = ttk.Frame(paneles)
        derecha = ttk.Frame(paneles)
        paneles.add(izquierda, weight=1)
        paneles.add(derecha, weight=1)

        self._construir_editor(izquierda)
        self._construir_pestanas(derecha)

    def _construir_editor(self, contenedor):
        self.etiqueta_archivo = ttk.Label(contenedor, text=self.nombre_archivo,
                                          font=('Segoe UI', 10, 'bold'))
        self.etiqueta_archivo.pack(side=tk.TOP, anchor=tk.W, pady=(4, 4))

        marco = ttk.Frame(contenedor)
        marco.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.barra_vertical = ttk.Scrollbar(marco, orient=tk.VERTICAL,
                                            command=self._desplazar_ambos)
        self.barra_vertical.pack(side=tk.RIGHT, fill=tk.Y)
        barra_horizontal = ttk.Scrollbar(marco, orient=tk.HORIZONTAL)
        barra_horizontal.pack(side=tk.BOTTOM, fill=tk.X)

        # Columna de numeros de linea: es otro Text, de solo lectura, que se
        # desplaza junto con el editor.
        self.numeros = tk.Text(marco, width=5, padx=4, takefocus=0,
                               font=FUENTE_EDITOR, background='#f0f0f0',
                               foreground='#8a8a8a', borderwidth=0,
                               state=tk.DISABLED, wrap=tk.NONE)
        self.numeros.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(marco, wrap=tk.NONE, undo=True,
                              font=FUENTE_EDITOR, borderwidth=0,
                              yscrollcommand=self._al_desplazar_editor,
                              xscrollcommand=barra_horizontal.set)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra_horizontal.configure(command=self.editor.xview)

        # El orden importa: la etiqueta creada despues tiene prioridad, asi
        # un error o la seleccion se ven encima del aviso de anidamiento.
        self.editor.tag_configure('anidamiento', background=COLOR_ANIDAMIENTO)
        self.editor.tag_configure('error', background=COLOR_ERROR)
        self.editor.tag_configure('seleccion', background=COLOR_SELECCION)
        self.editor.bind('<KeyRelease>', self._al_editar)
        self.editor.bind('<ButtonRelease-1>', self._al_mover_cursor)
        self._actualizar_numeros()

    def _construir_pestanas(self, contenedor):
        self.pestanas = ttk.Notebook(contenedor)
        self.pestanas.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                           pady=(4, 0))

        self.tabla_tokens = self._crear_tabla(
            self.pestanas, 'Tokens',
            ['No.', 'Lexema', 'Tipo', 'Línea', 'Columna'],
            [50, 260, 150, 60, 70])
        self.tabla_tokens.bind('<<TreeviewSelect>>',
                               self._al_seleccionar_token)

        self.tabla_errores = self._crear_tabla(
            self.pestanas, 'Errores',
            ['No.', 'Lexema', 'Tipo', 'Fase', 'Descripción', 'Línea',
             'Columna'],
            [40, 80, 170, 75, 240, 45, 60])
        self.tabla_errores.tag_configure('lexico', foreground='#9a3412')
        self.tabla_errores.tag_configure('sintactico', foreground='#1d4ed8')
        self.tabla_errores.bind('<<TreeviewSelect>>',
                                self._al_seleccionar_error)

        marco_arbol = ttk.Frame(self.pestanas)
        self.pestanas.add(marco_arbol, text='Árbol de derivación')
        barra = ttk.Scrollbar(marco_arbol, orient=tk.VERTICAL)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        self.vista_arbol = ttk.Treeview(marco_arbol, show='tree',
                                        yscrollcommand=barra.set)
        self.vista_arbol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.configure(command=self.vista_arbol.yview)

        marco_vista = ttk.Frame(self.pestanas)
        self.pestanas.add(marco_vista, text='Vista previa')
        self.etiqueta_vista = ttk.Label(marco_vista, text='',
                                        padding=(6, 4), foreground='#57606a')
        self.etiqueta_vista.pack(side=tk.TOP, anchor=tk.W)
        barra = ttk.Scrollbar(marco_vista, orient=tk.VERTICAL)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        texto = tk.Text(marco_vista, borderwidth=0, background='#ffffff',
                        yscrollcommand=barra.set)
        texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.configure(command=texto.yview)
        self.vista_previa = VistaPrevia(texto)

    def _crear_tabla(self, pestanas, titulo, columnas, anchos):
        """Crea una pestana con una tabla (Treeview) y su barra."""
        marco = ttk.Frame(pestanas)
        pestanas.add(marco, text=titulo)
        barra = ttk.Scrollbar(marco, orient=tk.VERTICAL)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        tabla = ttk.Treeview(marco, columns=columnas, show='headings',
                             yscrollcommand=barra.set)
        tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.configure(command=tabla.yview)
        i = 0
        while i < len(columnas):
            tabla.heading(columnas[i], text=columnas[i], anchor=tk.W)
            tabla.column(columnas[i], width=anchos[i], anchor=tk.W,
                         stretch=columnas[i] == 'Descripción' or
                         columnas[i] == 'Lexema')
            i = i + 1
        return tabla

    def _registrar_atajos(self):
        self.ventana.bind('<Control-o>', self._atajo_abrir)
        self.ventana.bind('<Control-s>', self._atajo_guardar)
        self.ventana.bind('<F5>', self._atajo_analizar)

    # ==================================================================
    # Archivo
    # ==================================================================

    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title='Abrir documento Markdown',
            filetypes=[('Markdown', '*.md'), ('Todos los archivos', '*.*')])
        if ruta:
            self.cargar_archivo(ruta)

    def cargar_archivo(self, ruta):
        """
        Valida que el archivo exista, que sea un .md y que se pueda leer como
        texto UTF-8, y lo muestra en el editor (criterio 2.1). Devuelve True
        si se cargo.
        """
        if not os.path.isfile(ruta):
            messagebox.showerror(TITULO, 'El archivo no existe:\n' + ruta)
            return False
        if extension_de(ruta).lower() != 'md':
            messagebox.showerror(TITULO, 'Solo se pueden analizar archivos '
                                 'Markdown con extensión .md:\n' + ruta)
            return False
        try:
            # utf-8-sig quita la marca BOM si el editor la agrego.
            archivo = open(ruta, 'r', encoding='utf-8-sig')
            texto = archivo.read()
            archivo.close()
        except UnicodeDecodeError:
            messagebox.showerror(TITULO, 'El archivo no está en UTF-8 y no '
                                 'se puede leer como texto:\n' + ruta)
            return False
        except OSError as error:
            messagebox.showerror(TITULO, 'No se pudo leer el archivo:\n' +
                                 str(error))
            return False

        self.ruta_archivo = ruta
        self.nombre_archivo = os.path.basename(ruta)
        self.editor.delete('1.0', tk.END)
        self.editor.insert('1.0', texto)
        self.editor.edit_reset()
        self.editor.mark_set(tk.INSERT, '1.0')
        self._limpiar_resultados()
        self._actualizar_numeros()
        self._actualizar_cursor()
        self._actualizar_vista_previa()
        self.etiqueta_archivo.configure(text=self.nombre_archivo)
        self.ventana.title(TITULO + ' - ' + self.nombre_archivo)
        self._mostrar_estado('Archivo cargado: ' + ruta)
        return True

    def guardar_archivo(self):
        ruta = self.ruta_archivo
        if ruta == '':
            ruta = filedialog.asksaveasfilename(
                title='Guardar documento', defaultextension='.md',
                filetypes=[('Markdown', '*.md')])
            if not ruta:
                return
        try:
            archivo = open(ruta, 'w', encoding='utf-8')
            archivo.write(self.editor.get('1.0', 'end-1c'))
            archivo.close()
        except OSError as error:
            messagebox.showerror(TITULO, 'No se pudo guardar:\n' + str(error))
            return
        self.ruta_archivo = ruta
        self.nombre_archivo = os.path.basename(ruta)
        self.etiqueta_archivo.configure(text=self.nombre_archivo)
        self.ventana.title(TITULO + ' - ' + self.nombre_archivo)
        self._mostrar_estado('Guardado: ' + ruta)

    def limpiar(self):
        self.editor.delete('1.0', tk.END)
        self.ruta_archivo = ''
        self.nombre_archivo = 'sin_titulo.md'
        self.etiqueta_archivo.configure(text=self.nombre_archivo)
        self.ventana.title(TITULO)
        self._limpiar_resultados()
        self._actualizar_numeros()
        self._actualizar_vista_previa()
        self._mostrar_estado('Editor vacío.')

    # ==================================================================
    # Analisis
    # ==================================================================

    def analizar(self):
        """
        Analiza lo que hay en el editor (asi se pueden probar cambios sin
        guardar). Llena las tres pestanas y genera los reportes.
        """
        texto = self.editor.get('1.0', 'end-1c')
        self._limpiar_resultados()

        self.gestor = GestorErrores()
        lexico = AnalizadorLexico(texto, self.gestor)
        parser = AnalizadorSintactico(lexico, self.gestor)
        try:
            raiz = parser.analizar()
        except RecursionError:
            messagebox.showerror(TITULO, 'El documento tiene un anidamiento '
                                 'demasiado profundo para analizarlo.')
            return
        self.tokens = lexico.tokens

        self._llenar_tokens()
        self._llenar_errores()
        self._llenar_arbol(raiz)
        self._marcar_errores_en_editor()
        self._mostrar_en_vivo(raiz, self.gestor)

        carpeta = os.path.join(self.carpeta_salida,
                               self._nombre_sin_extension())
        try:
            self.rutas = generar_todos(raiz, self.gestor, self.nombre_archivo,
                                       carpeta)
        except OSError as error:
            messagebox.showerror(TITULO, 'No se pudieron escribir los '
                                 'reportes:\n' + str(error))
            self.rutas = {}
        except RecursionError:
            messagebox.showerror(TITULO, 'El documento tiene un anidamiento '
                                 'demasiado profundo para generar los '
                                 'reportes.')
            self.rutas = {}
        self._dibujar_arbol_png()
        self._actualizar_botones_reportes()

        resumen = (str(len(self.tokens)) + ' tokens, ' +
                   str(self.gestor.cantidad()) + ' error(es). ')
        if self.gestor.hay_errores():
            self.pestanas.select(1)
            resumen = (resumen + 'Con errores no se generan los reportes '
                       '1, 2 y 3; revise la pestaña Errores.')
        else:
            self.pestanas.select(0)
            resumen = (resumen + 'Análisis exitoso: reportes en ' + carpeta)
        self._mostrar_estado(resumen)

    def _nombre_sin_extension(self):
        """'notas.md' -> 'notas': todo lo que esta antes del ultimo punto."""
        return quitar_extension(self.nombre_archivo, 'sin_titulo')

    def _dibujar_arbol_png(self):
        """
        Si Graphviz esta instalado, convierte arbol.dot en arbol.png. Si
        no, el boton Arbol abre la carpeta donde quedo arbol.dot.
        """
        if 'arbol' not in self.rutas or shutil.which('dot') is None:
            return
        ruta_png = quitar_extension(self.rutas['arbol'], 'arbol') + '.png'
        try:
            resultado = subprocess.run(['dot', '-Tpng', self.rutas['arbol'],
                                        '-o', ruta_png],
                                       capture_output=True, timeout=60)
        except OSError:
            return
        except subprocess.TimeoutExpired:
            return
        if resultado.returncode == 0:
            self.rutas['arbol_png'] = ruta_png

    # ------------------------------------------------------------------
    # Llenado de las pestanas
    # ------------------------------------------------------------------

    def _limpiar_resultados(self):
        self.tokens = []
        self.gestor = None
        self.rutas = {}
        self._vaciar(self.tabla_tokens)
        self._vaciar(self.tabla_errores)
        self._vaciar(self.vista_arbol)
        self.editor.tag_remove('error', '1.0', tk.END)
        self.editor.tag_remove('seleccion', '1.0', tk.END)
        self._actualizar_botones_reportes()

    def _vaciar(self, tabla):
        hijos = tabla.get_children()
        i = 0
        while i < len(hijos):
            tabla.delete(hijos[i])
            i = i + 1

    def _llenar_tokens(self):
        i = 0
        while i < len(self.tokens):
            t = self.tokens[i]
            self.tabla_tokens.insert('', tk.END, iid=str(i), values=[
                t.numero, t.lexema_visible(), t.tipo, t.linea, t.columna])
            i = i + 1

    def _llenar_errores(self):
        i = 0
        while i < len(self.gestor.errores):
            e = self.gestor.errores[i]
            etiqueta = 'sintactico'
            if e.fase == 'Léxico':
                etiqueta = 'lexico'
            self.tabla_errores.insert('', tk.END, iid=str(i), tags=[etiqueta],
                                      values=[e.numero, e.lexema, e.tipo,
                                              e.fase, e.descripcion, e.linea,
                                              e.columna])
            i = i + 1
        titulo = 'Errores'
        if self.gestor.hay_errores():
            titulo = 'Errores (' + str(self.gestor.cantidad()) + ')'
        self.pestanas.tab(1, text=titulo)

    def _llenar_arbol(self, raiz):
        self._insertar_nodo('', raiz, 0)

    def _insertar_nodo(self, padre, nodo, profundidad):
        """
        Inserta el nodo y, recursivamente, a sus hijos. Los primeros
        niveles quedan desplegados; los demas se abren con un clic.
        """
        abierto = profundidad < 3
        elemento = self.vista_arbol.insert(padre, tk.END, open=abierto,
                                           text=nodo.descripcion())
        i = 0
        while i < len(nodo.hijos):
            self._insertar_nodo(elemento, nodo.hijos[i], profundidad + 1)
            i = i + 1

    # ------------------------------------------------------------------
    # Editor: errores marcados y seleccion desde las tablas
    # ------------------------------------------------------------------

    def _marcar_errores_en_editor(self):
        i = 0
        while i < len(self.gestor.errores):
            e = self.gestor.errores[i]
            self._marcar(e.linea, e.columna, e.lexema, 'error')
            i = i + 1

    def _marcar(self, linea, columna, lexema, etiqueta):
        """
        Marca el lexema en el editor. Si el lexema no es texto del archivo
        (por ejemplo '(sangría)' o un token virtual), se marca la linea
        completa.
        """
        if lexema == '' or lexema[0] == '(':
            inicio = str(linea) + '.0'
            fin = str(linea) + '.end'
        else:
            inicio = str(linea) + '.' + str(columna - 1)
            fin = inicio + '+' + str(len(lexema)) + 'c'
        self.editor.tag_add(etiqueta, inicio, fin)
        return inicio

    def _ir_a(self, linea, columna, lexema):
        """Lleva el cursor a la posicion y la resalta en amarillo."""
        self.editor.tag_remove('seleccion', '1.0', tk.END)
        inicio = self._marcar(linea, columna, lexema, 'seleccion')
        self.editor.mark_set(tk.INSERT, inicio)
        self.editor.see(inicio)
        self._actualizar_cursor()

    def _al_seleccionar_token(self, evento):
        elegido = self.tabla_tokens.focus()
        if elegido == '':
            return
        t = self.tokens[int(elegido)]
        lexema = t.lexema
        if t.es_virtual() or lexema == '\n':
            lexema = '(virtual)'
        self._ir_a(t.linea, t.columna, lexema)

    def _al_seleccionar_error(self, evento):
        elegido = self.tabla_errores.focus()
        if elegido == '' or self.gestor is None:
            return
        e = self.gestor.errores[int(elegido)]
        self._ir_a(e.linea, e.columna, e.lexema)

    # ==================================================================
    # Reportes
    # ==================================================================

    def _actualizar_botones_reportes(self):
        self._habilitar(self.boton_r1, 'documento' in self.rutas)
        self._habilitar(self.boton_r2, 'estadisticas' in self.rutas)
        self._habilitar(self.boton_r3, 'indice' in self.rutas)
        self._habilitar(self.boton_errores, 'errores' in self.rutas)
        self._habilitar(self.boton_arbol, 'arbol' in self.rutas)
        self._habilitar(self.boton_carpeta, 'arbol' in self.rutas)

    def _habilitar(self, boton, activo):
        if activo:
            boton.state(['!disabled'])
        else:
            boton.state(['disabled'])

    def abrir_reporte1(self):
        self._abrir('documento')

    def abrir_reporte2(self):
        self._abrir('estadisticas')

    def abrir_reporte3(self):
        self._abrir('indice')

    def abrir_reporte_errores(self):
        self._abrir('errores')

    def abrir_arbol(self):
        if 'arbol_png' in self.rutas:
            self._abrir('arbol_png')
            return
        messagebox.showinfo(TITULO, 'Se generó arbol.dot, pero Graphviz no '
                            'está instalado para convertirlo en imagen.\n\n'
                            'Instale Graphviz o ejecute:\n'
                            'dot -Tpng arbol.dot -o arbol.png\n\n'
                            'Se abrirá la carpeta donde está el archivo.')
        self.abrir_carpeta_salida()

    def abrir_carpeta_salida(self):
        if 'arbol' in self.rutas:
            self._abrir_en_sistema(os.path.dirname(self.rutas['arbol']))

    def _abrir(self, clave):
        if clave in self.rutas:
            self._abrir_en_sistema(self.rutas[clave])

    def _abrir_en_sistema(self, ruta):
        """Abre un archivo o carpeta con el programa predeterminado."""
        webbrowser.open(pathlib.Path(os.path.abspath(ruta)).as_uri())

    # ==================================================================
    # Alcance opcional: vista previa en vivo y aviso de anidamiento
    # ==================================================================

    def _programar_vista_previa(self):
        """
        Cada tecla cancela la actualizacion pendiente y programa otra: asi
        se analiza una sola vez cuando se deja de escribir, no en cada
        tecla.
        """
        if self.pendiente is not None:
            self.ventana.after_cancel(self.pendiente)
        self.pendiente = self.ventana.after(ESPERA_VISTA_PREVIA,
                                            self._actualizar_vista_previa)

    def _actualizar_vista_previa(self):
        """
        Analiza el texto del editor con su propio GestorErrores (no toca
        las tablas ni los reportes, que siguen siendo del ultimo Analizar)
        y redibuja la vista previa y el aviso de anidamiento.
        """
        self.pendiente = None
        texto = self.editor.get('1.0', 'end-1c')
        gestor = GestorErrores()
        parser = AnalizadorSintactico(AnalizadorLexico(texto, gestor),
                                      gestor)
        try:
            raiz = parser.analizar()
        except RecursionError:
            # No queda nada viejo a la vista: ni la vista previa ni el aviso
            # de otro texto.
            self.raiz_vivo = None
            self.vista_previa.mostrar(None)
            self._revisar_anidamiento()
            self.etiqueta_vista.configure(text='El documento tiene un '
                                          'anidamiento demasiado profundo.')
            return
        self._mostrar_en_vivo(raiz, gestor)

    def _mostrar_en_vivo(self, raiz, gestor):
        self.raiz_vivo = raiz
        self.vista_previa.mostrar(raiz)
        if gestor.hay_errores():
            self.etiqueta_vista.configure(
                text='Vista previa en vivo: ' + str(gestor.cantidad()) +
                ' error(es). Se muestra lo que se pudo reconocer; presione '
                'Analizar para ver la tabla de errores.')
        else:
            self.etiqueta_vista.configure(
                text='Vista previa en vivo: se actualiza mientras escribe. '
                'Sin errores.')
        self._revisar_anidamiento()

    def _al_cambiar_maximo(self, evento=None):
        self._revisar_anidamiento()

    def maximo(self):
        """El anidamiento maximo del selector; si no es un numero, 3."""
        try:
            valor = int(self.maximo_anidamiento.get())
        except ValueError:
            return ANIDAMIENTO_MAXIMO
        if valor < 1:
            return 1
        return valor

    def _revisar_anidamiento(self):
        """
        Advertencia visual (D-35): si alguna lista o cita pasa del maximo,
        se muestra la franja amarilla con el nivel mas profundo de cada una
        y sus lineas se pintan en el editor. No es un error.
        """
        self.editor.tag_remove('anidamiento', '1.0', tk.END)
        excesos = []
        if self.raiz_vivo is not None:
            excesos = recorridos.excesos_de_anidamiento(self.raiz_vivo,
                                                        self.maximo())
        if len(excesos) == 0:
            self._ocultar_aviso()
            return

        partes = []
        clases = ['lista', 'cita']
        c = 0
        while c < len(clases):
            peor = mas_profundo(excesos, clases[c])
            if peor is not None:
                partes.append(clases[c] + ' de nivel ' + str(peor[1]) +
                              ' en la línea ' + str(peor[2]))
            c = c + 1
        i = 0
        while i < len(excesos):
            self.editor.tag_add('anidamiento', str(excesos[i][2]) + '.0',
                                str(excesos[i][3]) + '.end')
            i = i + 1
        mensaje = ('⚠  El documento pasa el anidamiento máximo (' +
                   str(self.maximo()) + '): ' + unir(partes, '; ') +
                   '. Las líneas quedan marcadas en el editor.')
        self.aviso.configure(text=mensaje)
        if not self.aviso_visible:
            self.aviso.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 4),
                            before=self.paneles)
            self.aviso_visible = True

    def _ocultar_aviso(self):
        if self.aviso_visible:
            self.aviso.pack_forget()
            self.aviso_visible = False

    # ==================================================================
    # Numeros de linea, cursor y estado
    # ==================================================================

    def _al_desplazar_editor(self, primero, ultimo):
        """El editor se movio: se mueven la barra y los numeros con el."""
        self.barra_vertical.set(primero, ultimo)
        self.numeros.yview_moveto(primero)
        self.fraccion_visible = primero

    def _desplazar_ambos(self, *argumentos):
        """La barra se movio: se mueven el editor y los numeros."""
        self.editor.yview(*argumentos)
        self.numeros.yview(*argumentos)

    def _al_editar(self, evento):
        self._actualizar_numeros()
        self._actualizar_cursor()
        self._programar_vista_previa()

    def _al_mover_cursor(self, evento):
        self._actualizar_cursor()

    def _actualizar_numeros(self):
        total = self._linea_de(self.editor.index('end-1c'))
        texto = ''
        i = 1
        while i <= total:
            texto = texto + str(i) + '\n'
            i = i + 1
        self.numeros.configure(state=tk.NORMAL)
        self.numeros.delete('1.0', tk.END)
        self.numeros.insert('1.0', texto)
        self.numeros.configure(state=tk.DISABLED)
        self.numeros.yview_moveto(self.fraccion_visible)

    def _actualizar_cursor(self):
        indice = self.editor.index(tk.INSERT)
        linea = self._linea_de(indice)
        columna = self._columna_de(indice) + 1
        self.etiqueta_cursor.configure(text='Línea ' + str(linea) +
                                       ', columna ' + str(columna))

    def _linea_de(self, indice):
        """Tk escribe las posiciones como 'linea.columna'; esta es la linea."""
        numero = ''
        i = 0
        while i < len(indice) and indice[i] != '.':
            numero = numero + indice[i]
            i = i + 1
        return int(numero)

    def _columna_de(self, indice):
        """La parte despues del punto en 'linea.columna' (empieza en 0)."""
        numero = ''
        i = 0
        while i < len(indice) and indice[i] != '.':
            i = i + 1
        i = i + 1
        while i < len(indice):
            numero = numero + indice[i]
            i = i + 1
        return int(numero)

    def _mostrar_estado(self, texto):
        self.etiqueta_estado.configure(text=texto)

    # ------------------------------------------------------------------
    # Atajos de teclado (Tk les pasa el evento)
    # ------------------------------------------------------------------

    def _atajo_abrir(self, evento):
        self.abrir_archivo()

    def _atajo_guardar(self, evento):
        self.guardar_archivo()

    def _atajo_analizar(self, evento):
        self.analizar()


def extension_de(nombre):
    """
    Lo que va despues del ultimo punto del nombre: 'notas.md' -> 'md'.
    Devuelve '' si no hay punto. Un punto antes de la ultima barra es de una
    carpeta, no una extension, asi que una barra vuelve a empezar.
    """
    extension = ''
    hay_punto = False
    i = 0
    while i < len(nombre):
        c = nombre[i]
        if c == '.':
            extension = ''
            hay_punto = True
        elif c == '/' or c == '\\':
            extension = ''
            hay_punto = False
        else:
            extension = extension + c
        i = i + 1
    if hay_punto:
        return extension
    return ''


def quitar_extension(nombre, si_queda_vacio):
    """
    Quita la extension (desde el ultimo punto) de un nombre o ruta:
    'notas.md' -> 'notas'. Un punto que este antes de la ultima barra es
    parte de una carpeta, no una extension, y no se toma en cuenta.
    """
    ultimo_punto = -1
    i = 0
    while i < len(nombre):
        if nombre[i] == '.':
            ultimo_punto = i
        elif nombre[i] == '/' or nombre[i] == '\\':
            ultimo_punto = -1
        i = i + 1
    if ultimo_punto == -1:
        resultado = nombre
    else:
        resultado = ''
        i = 0
        while i < ultimo_punto:
            resultado = resultado + nombre[i]
            i = i + 1
    if resultado == '':
        return si_queda_vacio
    return resultado


def mas_profundo(excesos, clase):
    """El exceso de mayor nivel de esa clase ('lista' o 'cita'), o None."""
    peor = None
    i = 0
    while i < len(excesos):
        if excesos[i][0] == clase:
            if peor is None or excesos[i][1] > peor[1]:
                peor = excesos[i]
        i = i + 1
    return peor


def unir(partes, separador):
    texto = ''
    i = 0
    while i < len(partes):
        if i > 0:
            texto = texto + separador
        texto = texto + partes[i]
        i = i + 1
    return texto
