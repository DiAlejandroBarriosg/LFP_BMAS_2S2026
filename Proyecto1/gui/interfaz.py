# -*- coding: utf-8 -*-
"""
interfaz.py

Ventana principal en Tkinter. Integra el motor lexico, el estructurador, el
detector de choques y el generador de reportes.

ESTRUCTURA DE LA VENTANA
    barra de herramientas   abrir / guardar / analizar / reportes / exportar
    panel superior          editor .hor con numeracion de linea
    panel inferior          pestanas: Tokens, Errores, Avisos, Choques, Resumen
    barra de estado         resultado del ultimo analisis

DECISIONES
1. Se analiza el CONTENIDO DEL EDITOR, no el archivo en disco. Asi el usuario
   puede corregir un error y reanalizar sin guardar ni volver a abrir.

2. La conversion de (linea, columna) a indice de Tkinter se hace recorriendo
   la linea caracter por caracter (_indice_tk). Es necesario porque el
   analizador cuenta un tabulador como 4 columnas, mientras que Tkinter lo
   cuenta como 1 caracter: sin esta conversion, el resaltado y el salto a la
   posicion del error se desalinean en cuanto el archivo usa tabuladores.

3. El resaltado se aplica despues de analizar y tambien mientras se escribe,
   con un retardo de 400 ms. Reanalizar en cada tecla congela la ventana en
   archivos grandes; el retardo agrupa las pulsaciones seguidas.
"""

import os
import time
import webbrowser

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from analizador.analizador_lexico import AnalizadorLexico
from logica.estructurador import Estructurador
from logica.detector_choques import DetectorChoques
from reportes.generador import GeneradorReportes
from reportes.graficador import Graficador
from modelos.elementos import minutos_a_hora

# --- paleta, la misma de los reportes HTML ---
TINTA = '#16202a'
PIZARRA = '#4a5b6c'
PAPEL = '#ffffff'
FONDO = '#eef1f4'
REGLA = '#d3dae1'
ROJO = '#a32626'
ROJO_FONDO = '#fbe6e6'
VERDE = '#1f7a3f'
NARANJA = '#b5651d'
NARANJA_FONDO = '#fdeedd'
AZUL = '#1f5f9e'

FUENTE_UI = ('Segoe UI', 10)
FUENTE_UI_FUERTE = ('Segoe UI', 10, 'bold')
FUENTE_CODIGO = ('Consolas', 11)
FUENTE_TITULO = ('Segoe UI', 15, 'bold')

RETARDO_RESALTADO = 400   # milisegundos

# Color de cada tipo de token en el editor
COLORES_TOKEN = {
    'RESERVADA_BLOQUE': ('#0d3b66', 'bold'),
    'RESERVADA_ELEMENTO': ('#1f5f9e', 'bold'),
    'RESERVADA_RELACION': ('#7048a8', 'normal'),
    'RESERVADA_ATRIBUTO': ('#1f5f9e', 'normal'),
    'DIA': ('#1f7a3f', 'bold'),
    'CATEGORIA': ('#1f7a3f', 'normal'),
    'CODIGO': ('#b5651d', 'normal'),
    'CADENA': ('#8a5a00', 'normal'),
    'HORA': ('#0f766e', 'bold'),
    'ENTERO': ('#0f766e', 'normal'),
    'SIMBOLO': ('#4a5b6c', 'normal'),
    'COMENTARIO_LINEA': ('#7c8794', 'italic'),
}


class InterfazHorarioScript:

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title('HorarioScript - Analizador Lexico | Proyecto 1 LFP 2S2026')
        self.raiz.geometry('1280x860')
        self.raiz.minsize(1000, 640)
        self.raiz.configure(bg=FONDO)

        # estado
        self.ruta_archivo = ''
        self.analizador = AnalizadorLexico()
        self.estructura = Estructurador()
        self.detector = DetectorChoques()
        self.rutas_reportes = {}
        self.tarea_resaltado = None
        self.ultimo_ms = 0.0
        self.analizado = False

        self._configurar_estilos()
        self._construir_barra()
        # La barra de estado se empaqueta ANTES del cuerpo: en Tkinter el orden
        # de pack define quien reclama el espacio primero, y el cuerpo lleva
        # expand=True. Si se empaqueta al final, queda fuera de la ventana.
        self._construir_estado()
        self._construir_cuerpo()
        self._atajos()

        self.raiz.protocol('WM_DELETE_WINDOW', self._al_cerrar)

    # ==================================================================
    # Construccion de la ventana
    # ==================================================================

    def _configurar_estilos(self):
        estilo = ttk.Style()
        try:
            estilo.theme_use('clam')
        except tk.TclError:
            pass

        estilo.configure('TFrame', background=FONDO)
        estilo.configure('Papel.TFrame', background=PAPEL)
        estilo.configure('TLabel', background=FONDO, foreground=TINTA,
                         font=FUENTE_UI)
        estilo.configure('Titulo.TLabel', background=FONDO, foreground=TINTA,
                         font=FUENTE_TITULO)
        estilo.configure('Sub.TLabel', background=FONDO, foreground=PIZARRA,
                         font=('Segoe UI', 9))
        estilo.configure('TButton', font=FUENTE_UI, padding=(11, 6))
        estilo.configure('Primario.TButton', font=FUENTE_UI_FUERTE,
                         padding=(13, 6))
        estilo.configure('TNotebook', background=FONDO, borderwidth=0)
        estilo.configure('TNotebook.Tab', font=FUENTE_UI, padding=(15, 7))

        estilo.configure('Treeview', font=('Consolas', 10), rowheight=23,
                         background=PAPEL, fieldbackground=PAPEL,
                         foreground=TINTA, borderwidth=1)
        estilo.configure('Treeview.Heading', font=FUENTE_UI_FUERTE,
                         background=TINTA, foreground=PAPEL, relief='flat',
                         padding=(6, 5))
        estilo.map('Treeview.Heading', background=[('active', PIZARRA)])

    def _construir_barra(self):
        barra = ttk.Frame(self.raiz, padding=(14, 12, 14, 8))
        barra.pack(fill='x')

        titulo = ttk.Frame(barra)
        titulo.pack(side='left')
        ttk.Label(titulo, text='HorarioScript', style='Titulo.TLabel').pack(anchor='w')
        self.etiqueta_archivo = ttk.Label(
            titulo, text='Ningun archivo abierto', style='Sub.TLabel')
        self.etiqueta_archivo.pack(anchor='w')

        botones = ttk.Frame(barra)
        botones.pack(side='right')

        ttk.Button(botones, text='Abrir .hor',
                   command=self.abrir_archivo).pack(side='left', padx=3)
        ttk.Button(botones, text='Guardar',
                   command=self.guardar_archivo).pack(side='left', padx=3)
        ttk.Button(botones, text='Analizar', style='Primario.TButton',
                   command=self.analizar).pack(side='left', padx=3)
        ttk.Button(botones, text='Generar reportes',
                   command=self.generar_reportes).pack(side='left', padx=3)

        self.menu_exportar = tk.Menubutton(
            botones, text='Exportar', font=FUENTE_UI, relief='raised',
            bg=PAPEL, fg=TINTA, padx=11, pady=5, borderwidth=1)
        menu = tk.Menu(self.menu_exportar, tearoff=0, font=FUENTE_UI)
        menu.add_command(label='Tabla de tokens a CSV',
                         command=self.exportar_csv)
        menu.add_command(label='Tabla de tokens a JSON',
                         command=self.exportar_json)
        self.menu_exportar.configure(menu=menu)
        self.menu_exportar.pack(side='left', padx=3)

    def _construir_cuerpo(self):
        paneles = tk.PanedWindow(self.raiz, orient='vertical', bg=FONDO,
                                 sashwidth=7, sashrelief='flat',
                                 borderwidth=0)
        paneles.pack(fill='both', expand=True, padx=14, pady=(0, 8))

        paneles.add(self._construir_editor(paneles), minsize=200, height=330)
        paneles.add(self._construir_pestanas(paneles), minsize=220)

    def _construir_editor(self, padre):
        marco = ttk.Frame(padre, style='Papel.TFrame')

        cabecera = ttk.Frame(marco, padding=(10, 7))
        cabecera.pack(fill='x')
        ttk.Label(cabecera, text='Archivo de entrada',
                  font=FUENTE_UI_FUERTE).pack(side='left')
        self.etiqueta_posicion = ttk.Label(cabecera, text='linea 1, columna 1',
                                           style='Sub.TLabel')
        self.etiqueta_posicion.pack(side='right')

        contenedor = tk.Frame(marco, bg=REGLA, bd=1, relief='solid')
        contenedor.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.gutter = tk.Text(contenedor, width=5, padx=6, pady=8,
                              bg='#f2f5f8', fg=PIZARRA, font=FUENTE_CODIGO,
                              relief='flat', state='disabled', takefocus=0,
                              cursor='arrow')
        self.gutter.pack(side='left', fill='y')

        barra_v = ttk.Scrollbar(contenedor, orient='vertical')
        barra_v.pack(side='right', fill='y')

        self.texto = tk.Text(contenedor, wrap='none', undo=True,
                             padx=10, pady=8, bg=PAPEL, fg=TINTA,
                             insertbackground=TINTA, font=FUENTE_CODIGO,
                             relief='flat', selectbackground='#cfe0f0',
                             tabs='36')
        self.texto.pack(side='left', fill='both', expand=True)

        barra_h = ttk.Scrollbar(marco, orient='horizontal',
                                command=self.texto.xview)
        barra_h.pack(fill='x', padx=10, pady=(0, 8))
        self.texto.configure(xscrollcommand=barra_h.set)

        # el gutter y el editor comparten el desplazamiento vertical
        def desplazar(*args):
            self.texto.yview(*args)
            self.gutter.yview(*args)

        def sincronizar(inicio, fin):
            barra_v.set(inicio, fin)
            self.gutter.yview('moveto', inicio)

        barra_v.configure(command=desplazar)
        self.texto.configure(yscrollcommand=sincronizar)

        self._preparar_etiquetas()

        self.texto.bind('<KeyRelease>', self._al_escribir)
        self.texto.bind('<ButtonRelease-1>', self._actualizar_posicion)
        self.texto.bind('<MouseWheel>', self._rueda)
        self.texto.bind('<Button-4>', self._rueda)
        self.texto.bind('<Button-5>', self._rueda)

        self._numerar_lineas()
        return marco

    def _preparar_etiquetas(self):
        """Registra una etiqueta de color por tipo de token, mas la de error."""
        for tipo in COLORES_TOKEN:
            color = COLORES_TOKEN[tipo][0]
            peso = COLORES_TOKEN[tipo][1]
            fuente = (FUENTE_CODIGO[0], FUENTE_CODIGO[1])
            if peso == 'bold':
                fuente = (FUENTE_CODIGO[0], FUENTE_CODIGO[1], 'bold')
            elif peso == 'italic':
                fuente = (FUENTE_CODIGO[0], FUENTE_CODIGO[1], 'italic')
            self.texto.tag_configure('t_' + tipo, foreground=color, font=fuente)

        self.texto.tag_configure('t_ERROR', background=ROJO_FONDO,
                                 foreground=ROJO,
                                 font=(FUENTE_CODIGO[0], FUENTE_CODIGO[1], 'bold'))
        self.texto.tag_configure('t_FOCO', background='#fff3bf')

    def _construir_pestanas(self, padre):
        marco = ttk.Frame(padre)
        self.pestanas = ttk.Notebook(marco)
        self.pestanas.pack(fill='both', expand=True)

        self.tabla_tokens = self._crear_tabla(
            [('No.', 55), ('Lexema', 330), ('Tipo de token', 190),
             ('Linea', 70), ('Columna', 80)], 'Tokens')

        self.tabla_errores = self._crear_tabla(
            [('No.', 55), ('Lexema', 200), ('Tipo de error', 200),
             ('Descripcion', 430), ('Linea', 70), ('Columna', 80)],
            'Errores lexicos')

        self.tabla_avisos = self._crear_tabla(
            [('No.', 55), ('Tipo', 210), ('Descripcion', 620), ('Linea', 70)],
            'Avisos estructurales')

        self.tabla_choques = self._crear_tabla(
            [('No.', 55), ('Dia', 110), ('Traslape', 130), ('Motivo', 300),
             ('Clase A', 170), ('Clase B', 170)], 'Choques de horario')

        self._construir_resumen()
        return marco

    def _crear_tabla(self, columnas, titulo):
        marco = ttk.Frame(self.pestanas, style='Papel.TFrame')
        self.pestanas.add(marco, text=titulo)

        nombres = []
        i = 0
        while i < len(columnas):
            nombres.append('c' + str(i))
            i = i + 1

        tabla = ttk.Treeview(marco, columns=nombres, show='headings',
                             selectmode='browse')

        i = 0
        while i < len(columnas):
            tabla.heading(nombres[i], text=columnas[i][0])
            ancla = 'w'
            if columnas[i][0] in ('No.', 'Linea', 'Columna'):
                ancla = 'e'
            tabla.column(nombres[i], width=columnas[i][1], anchor=ancla,
                         stretch=(columnas[i][1] > 250))
            i = i + 1

        barra_v = ttk.Scrollbar(marco, orient='vertical', command=tabla.yview)
        barra_h = ttk.Scrollbar(marco, orient='horizontal', command=tabla.xview)
        tabla.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)

        tabla.grid(row=0, column=0, sticky='nsew')
        barra_v.grid(row=0, column=1, sticky='ns')
        barra_h.grid(row=1, column=0, sticky='ew')
        marco.grid_rowconfigure(0, weight=1)
        marco.grid_columnconfigure(0, weight=1)

        tabla.tag_configure('error', background=ROJO_FONDO, foreground=ROJO)
        tabla.tag_configure('aviso', background=NARANJA_FONDO,
                            foreground=NARANJA)
        tabla.tag_configure('par', background='#f7f9fb')

        # doble clic: llevar el cursor del editor a la posicion de la fila
        tabla.bind('<Double-1>', self._ir_a_posicion)
        return tabla

    def _construir_resumen(self):
        marco = ttk.Frame(self.pestanas, style='Papel.TFrame', padding=14)
        self.pestanas.add(marco, text='Resumen')

        self.texto_resumen = tk.Text(marco, wrap='word', bg=PAPEL, fg=TINTA,
                                     font=('Consolas', 10), relief='flat',
                                     state='disabled', padx=10, pady=8)
        self.texto_resumen.pack(fill='both', expand=True)

        self.marco_enlaces = ttk.Frame(marco, style='Papel.TFrame')
        self.marco_enlaces.pack(fill='x', pady=(10, 0))

    def _construir_estado(self):
        barra = tk.Frame(self.raiz, bg=TINTA, height=30)
        barra.pack(fill='x', side='bottom')
        self.etiqueta_estado = tk.Label(
            barra, text='Abri un archivo .hor o escribi directamente en el editor.',
            bg=TINTA, fg=PAPEL, font=FUENTE_UI, anchor='w', padx=14, pady=5)
        self.etiqueta_estado.pack(fill='x')

    def _atajos(self):
        self.raiz.bind('<Control-o>', lambda e: self.abrir_archivo())
        self.raiz.bind('<Control-s>', lambda e: self.guardar_archivo())
        self.raiz.bind('<Control-r>', lambda e: self.analizar())
        self.raiz.bind('<F5>', lambda e: self.analizar())

    # ==================================================================
    # Editor: numeracion, posicion, resaltado
    # ==================================================================

    def _numerar_lineas(self):
        total = int(self.texto.index('end-1c').split('.')[0])
        numeros = ''
        i = 1
        while i <= total:
            numeros = numeros + str(i) + '\n'
            i = i + 1
        self.gutter.configure(state='normal')
        self.gutter.delete('1.0', 'end')
        self.gutter.insert('1.0', numeros)
        self.gutter.tag_configure('der', justify='right')
        self.gutter.tag_add('der', '1.0', 'end')
        self.gutter.configure(state='disabled')
        self.gutter.yview('moveto', self.texto.yview()[0])

    def _rueda(self, evento):
        self.gutter.yview('moveto', self.texto.yview()[0])

    def _actualizar_posicion(self, evento=None):
        posicion = self.texto.index('insert')
        partes = posicion.split('.')
        self.etiqueta_posicion.configure(
            text='linea ' + partes[0] + ', columna ' + str(int(partes[1]) + 1))

    def _al_escribir(self, evento=None):
        self._numerar_lineas()
        self._actualizar_posicion()
        if self.tarea_resaltado is not None:
            self.raiz.after_cancel(self.tarea_resaltado)
        self.tarea_resaltado = self.raiz.after(RETARDO_RESALTADO,
                                               self._resaltar_al_vuelo)

    def _resaltar_al_vuelo(self):
        """
        Reanaliza en segundo plano solo para repintar el editor. No toca las
        tablas ni la barra de estado: el usuario decide cuando analizar de
        verdad. Asi el resaltado se siente inmediato sin que los resultados
        cambien sin que el lo pida.
        """
        self.tarea_resaltado = None
        contenido = self.texto.get('1.0', 'end-1c')
        auxiliar = AnalizadorLexico()
        auxiliar.analizar(contenido)
        self._pintar(auxiliar)

    def _indice_tk(self, linea, columna):
        """
        Convierte (linea, columna) del analizador a un indice de Tkinter.

        El analizador cuenta un tabulador como 4 columnas; Tkinter lo cuenta
        como 1 caracter. Por eso hay que recorrer la linea acumulando la misma
        metrica que usa el AFD hasta alcanzar la columna buscada.
        """
        texto_linea = self.texto.get(str(linea) + '.0', str(linea) + '.end')
        acumulada = 1
        i = 0
        while i < len(texto_linea):
            if acumulada >= columna:
                return str(linea) + '.' + str(i)
            if texto_linea[i] == '\t':
                acumulada = acumulada + 4
            else:
                acumulada = acumulada + 1
            i = i + 1
        return str(linea) + '.' + str(len(texto_linea))

    def _pintar(self, analizador):
        for tipo in COLORES_TOKEN:
            self.texto.tag_remove('t_' + tipo, '1.0', 'end')
        self.texto.tag_remove('t_ERROR', '1.0', 'end')

        i = 0
        while i < len(analizador.tokens):
            token = analizador.tokens[i]
            i = i + 1
            if token.tipo not in COLORES_TOKEN:
                continue
            inicio = self._indice_tk(token.linea, token.columna)
            fin = self.texto.index(inicio + ' + ' + str(len(token.lexema)) +
                                   ' chars')
            self.texto.tag_add('t_' + token.tipo, inicio, fin)

        i = 0
        while i < len(analizador.gestor.errores):
            error = analizador.gestor.errores[i]
            i = i + 1
            inicio = self._indice_tk(error.linea, error.columna)
            largo = len(error.lexema)
            if largo < 1:
                largo = 1
            fin = self.texto.index(inicio + ' + ' + str(largo) + ' chars')
            self.texto.tag_add('t_ERROR', inicio, fin)

    def _ir_a_posicion(self, evento):
        tabla = evento.widget
        seleccion = tabla.selection()
        if len(seleccion) == 0:
            return
        valores = tabla.item(seleccion[0], 'values')

        # la columna de linea es la penultima o la ultima segun la tabla
        linea = ''
        columna = '1'
        encabezados = []
        for nombre in tabla['columns']:
            encabezados.append(tabla.heading(nombre, 'text'))

        i = 0
        while i < len(encabezados):
            if encabezados[i] == 'Linea' and i < len(valores):
                linea = str(valores[i])
            if encabezados[i] == 'Columna' and i < len(valores):
                columna = str(valores[i])
            i = i + 1

        if linea == '':
            return

        indice = self._indice_tk(int(linea), int(columna))
        self.texto.tag_remove('t_FOCO', '1.0', 'end')
        self.texto.tag_add('t_FOCO', str(int(linea)) + '.0',
                           str(int(linea)) + '.end')
        self.texto.mark_set('insert', indice)
        self.texto.see(indice)
        self.texto.focus_set()
        self._actualizar_posicion()

    # ==================================================================
    # Archivo
    # ==================================================================

    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title='Abrir archivo HorarioScript',
            filetypes=[('Archivos HorarioScript', '*.hor'),
                       ('Todos los archivos', '*.*')])
        if not ruta:
            return
        try:
            archivo = open(ruta, 'r', encoding='utf-8', newline='')
            contenido = archivo.read()
            archivo.close()
        except (IOError, OSError, UnicodeDecodeError) as detalle:
            messagebox.showerror(
                'No se pudo abrir el archivo',
                'El archivo no se pudo leer.\n\n' + str(detalle))
            return

        self.ruta_archivo = ruta
        self.texto.delete('1.0', 'end')
        self.texto.insert('1.0', contenido)
        self.texto.edit_reset()
        self._numerar_lineas()
        self.etiqueta_archivo.configure(text=ruta)
        self._limpiar_resultados()
        self._estado('Archivo cargado. Presiona Analizar o F5 para procesarlo.')
        self.analizar()

    def guardar_archivo(self):
        ruta = self.ruta_archivo
        if ruta == '':
            ruta = filedialog.asksaveasfilename(
                title='Guardar archivo HorarioScript',
                defaultextension='.hor',
                filetypes=[('Archivos HorarioScript', '*.hor')])
            if not ruta:
                return

        try:
            archivo = open(ruta, 'w', encoding='utf-8')
            archivo.write(self.texto.get('1.0', 'end-1c'))
            archivo.close()
        except (IOError, OSError) as detalle:
            messagebox.showerror('No se pudo guardar',
                                 'El archivo no se pudo escribir.\n\n' +
                                 str(detalle))
            return

        self.ruta_archivo = ruta
        self.etiqueta_archivo.configure(text=ruta)
        self._estado('Cambios guardados en ' + os.path.basename(ruta) + '.')

    # ==================================================================
    # Analisis
    # ==================================================================

    def analizar(self, evento=None):
        contenido = self.texto.get('1.0', 'end-1c')
        if len(contenido) == 0:
            messagebox.showinfo('Nada que analizar',
                                'El editor esta vacio. Abri un archivo .hor '
                                'o escribi el contenido antes de analizar.')
            return

        arranque = time.perf_counter()
        self.analizador = AnalizadorLexico()
        self.analizador.analizar(contenido)
        self.estructura = Estructurador()
        self.estructura.estructurar(self.analizador.tokens)
        self.detector = DetectorChoques()
        self.detector.detectar(self.estructura)
        self.ultimo_ms = (time.perf_counter() - arranque) * 1000.0

        self.analizado = True
        self.rutas_reportes = {}

        self._llenar_tokens()
        self._llenar_errores()
        self._llenar_avisos()
        self._llenar_choques()
        self._llenar_resumen()
        self._pintar(self.analizador)

        mensaje = (str(len(self.analizador.tokens)) + ' tokens, ' +
                   str(self.analizador.gestor.total()) + ' errores lexicos, ' +
                   str(len(self.estructura.avisos)) + ' avisos, ' +
                   str(self.detector.total()) + ' choques   |   ' +
                   self._ms(self.ultimo_ms) + ' ms')
        self._estado(mensaje)

        if self.analizador.gestor.hay_errores():
            self.pestanas.select(1)
        elif self.detector.hay_choques():
            self.pestanas.select(3)
        else:
            self.pestanas.select(0)

    def _ms(self, valor):
        entero = int(valor * 100 + 0.5)
        return str(entero // 100) + '.' + str(entero % 100).rjust(2, '0')

    def _limpiar_tabla(self, tabla):
        for fila in tabla.get_children():
            tabla.delete(fila)

    def _limpiar_resultados(self):
        self._limpiar_tabla(self.tabla_tokens)
        self._limpiar_tabla(self.tabla_errores)
        self._limpiar_tabla(self.tabla_avisos)
        self._limpiar_tabla(self.tabla_choques)
        self.analizado = False

    def _etiqueta_fila(self, indice):
        return ('par',) if indice % 2 == 1 else ()

    def _llenar_tokens(self):
        self._limpiar_tabla(self.tabla_tokens)
        i = 0
        while i < len(self.analizador.tokens):
            token = self.analizador.tokens[i]
            self.tabla_tokens.insert('', 'end', values=token.a_fila(),
                                     tags=self._etiqueta_fila(i))
            i = i + 1
        self.pestanas.tab(0, text='Tokens (' + str(i) + ')')

    def _llenar_errores(self):
        self._limpiar_tabla(self.tabla_errores)
        errores = self.analizador.gestor.errores
        i = 0
        while i < len(errores):
            self.tabla_errores.insert('', 'end', values=errores[i].a_fila(),
                                      tags=('error',))
            i = i + 1
        self.pestanas.tab(1, text='Errores lexicos (' + str(i) + ')')

    def _llenar_avisos(self):
        self._limpiar_tabla(self.tabla_avisos)
        avisos = self.estructura.avisos
        i = 0
        while i < len(avisos):
            self.tabla_avisos.insert('', 'end', values=avisos[i].a_fila(),
                                     tags=('aviso',))
            i = i + 1
        self.pestanas.tab(2, text='Avisos (' + str(i) + ')')

    def _llenar_choques(self):
        self._limpiar_tabla(self.tabla_choques)
        i = 0
        while i < len(self.detector.choques):
            choque = self.detector.choques[i]
            self.tabla_choques.insert('', 'end', values=choque.a_fila(),
                                      tags=('error',))
            i = i + 1
        self.pestanas.tab(3, text='Choques (' + str(i) + ')')

    def _llenar_resumen(self):
        resumen = self.estructura.resumen()
        conteo = self.analizador.contar_por_tipo()
        detalle_choques = self.detector.resumen()

        lineas = []
        lineas.append('RESULTADO DEL ANALISIS')
        lineas.append('')
        lineas.append('  Tiempo de analisis        ' + self._ms(self.ultimo_ms) + ' ms')
        lineas.append('  Tokens reconocidos        ' + str(len(self.analizador.tokens)))
        lineas.append('  Errores lexicos           ' + str(self.analizador.gestor.total()))
        lineas.append('  Avisos estructurales      ' + str(len(self.estructura.avisos)))
        lineas.append('')
        lineas.append('ELEMENTOS DEL HORARIO')
        lineas.append('')
        lineas.append('  Cursos                    ' + str(resumen['cursos']))
        lineas.append('  Catedraticos              ' + str(resumen['catedraticos']))
        lineas.append('  Aulas                     ' + str(resumen['aulas']))
        lineas.append('  Clases programadas        ' + str(resumen['clases']))
        lineas.append('  Secciones                 ' + str(resumen['secciones']))
        lineas.append('')
        lineas.append('CHOQUES DE HORARIO')
        lineas.append('')
        lineas.append('  Total                     ' + str(detalle_choques['total']))
        lineas.append('  Solo por catedratico      ' + str(detalle_choques['solo_catedratico']))
        lineas.append('  Solo por aula             ' + str(detalle_choques['solo_aula']))
        lineas.append('  Por ambos motivos         ' + str(detalle_choques['ambos']))
        lineas.append('')
        lineas.append('FRECUENCIA POR TIPO DE TOKEN')
        lineas.append('')
        for tipo in sorted(conteo.keys()):
            lineas.append('  ' + tipo.ljust(26) + str(conteo[tipo]))

        if self.detector.hay_choques():
            lineas.append('')
            lineas.append('REPROGRAMACION SUGERIDA')
            lineas.append('')
            propuestas = self.detector.sugerencias_para_todos(self.estructura)
            i = 0
            while i < len(propuestas):
                clase = propuestas[i]['clase']
                sugerencias = propuestas[i]['sugerencias']
                lineas.append('  ' + clase.codigo_curso + '  seccion ' +
                              clase.seccion + '  ' + clase.dia + ' ' +
                              clase.inicio_texto + '-' + clase.fin_texto)
                if len(sugerencias) == 0:
                    lineas.append('      sin bloques libres ese dia')
                j = 0
                while j < len(sugerencias):
                    lineas.append('      libre: ' + sugerencias[j]['inicio'] +
                                  ' - ' + sugerencias[j]['fin'])
                    j = j + 1
                i = i + 1

        texto = ''
        i = 0
        while i < len(lineas):
            texto = texto + lineas[i] + '\n'
            i = i + 1

        self.texto_resumen.configure(state='normal')
        self.texto_resumen.delete('1.0', 'end')
        self.texto_resumen.insert('1.0', texto)
        self.texto_resumen.configure(state='disabled')

    # ==================================================================
    # Reportes
    # ==================================================================

    def generar_reportes(self):
        if not self.analizado:
            messagebox.showinfo('Falta analizar',
                                'Analiza el archivo antes de generar los '
                                'reportes.')
            return

        if self.ruta_archivo != '':
            base = os.path.dirname(self.ruta_archivo)
            nombre = os.path.basename(self.ruta_archivo)
        else:
            base = os.getcwd()
            nombre = 'entrada sin guardar'

        carpeta = os.path.join(base, 'salida')

        try:
            generador = GeneradorReportes(self.estructura, self.detector,
                                          self.analizador, nombre)
            self.rutas_reportes = generador.generar_todos(carpeta)
            graficador = Graficador(self.estructura, self.detector)
            self.rutas_reportes['jerarquia'] = graficador.guardar(carpeta)
        except (IOError, OSError) as detalle:
            messagebox.showerror('No se pudieron generar los reportes',
                                 str(detalle))
            return

        self._mostrar_enlaces()
        self.pestanas.select(4)
        self._estado('Reportes generados en ' + carpeta)

    def _mostrar_enlaces(self):
        for hijo in self.marco_enlaces.winfo_children():
            hijo.destroy()

        ttk.Label(self.marco_enlaces, text='Abrir en el navegador:',
                  font=FUENTE_UI_FUERTE).pack(side='left', padx=(0, 10))

        etiquetas = [('horario', 'Horario semanal'),
                     ('carga', 'Carga de catedraticos'),
                     ('estadistico', 'Estadistico general'),
                     ('errores', 'Errores y avisos')]

        i = 0
        while i < len(etiquetas):
            clave = etiquetas[i][0]
            if clave in self.rutas_reportes:
                ruta = self.rutas_reportes[clave]
                ttk.Button(self.marco_enlaces, text=etiquetas[i][1],
                           command=lambda r=ruta: self._abrir_en_navegador(r)
                           ).pack(side='left', padx=3)
            i = i + 1

    def _abrir_en_navegador(self, ruta):
        try:
            webbrowser.open('file://' + os.path.abspath(ruta))
        except Exception:
            messagebox.showinfo(
                'Abri el archivo a mano',
                'No se pudo lanzar el navegador. El reporte esta en:\n\n' +
                os.path.abspath(ruta))

    # ==================================================================
    # Exportacion (funcionalidad opcional)
    # ==================================================================

    def _validar_exportacion(self):
        if not self.analizado or len(self.analizador.tokens) == 0:
            messagebox.showinfo('Nada que exportar',
                                'Analiza un archivo con tokens antes de '
                                'exportar la tabla.')
            return False
        return True

    def _entrecomillar(self, valor):
        """Escapa un campo para CSV: comillas dobladas y campo entre comillas."""
        salida = '"'
        i = 0
        while i < len(valor):
            if valor[i] == '"':
                salida = salida + '""'
            else:
                salida = salida + valor[i]
            i = i + 1
        return salida + '"'

    def exportar_csv(self):
        if not self._validar_exportacion():
            return
        ruta = filedialog.asksaveasfilename(
            title='Exportar tabla de tokens', defaultextension='.csv',
            filetypes=[('Archivo CSV', '*.csv')])
        if not ruta:
            return

        texto = 'numero,lexema,tipo,linea,columna\n'
        i = 0
        while i < len(self.analizador.tokens):
            token = self.analizador.tokens[i]
            texto = (texto + str(token.numero) + ',' +
                     self._entrecomillar(token.lexema) + ',' +
                     token.tipo + ',' + str(token.linea) + ',' +
                     str(token.columna) + '\n')
            i = i + 1

        self._escribir_export(ruta, texto, 'CSV')

    def exportar_json(self):
        if not self._validar_exportacion():
            return
        ruta = filedialog.asksaveasfilename(
            title='Exportar tabla de tokens', defaultextension='.json',
            filetypes=[('Archivo JSON', '*.json')])
        if not ruta:
            return

        texto = '[\n'
        i = 0
        while i < len(self.analizador.tokens):
            token = self.analizador.tokens[i]
            texto = (texto + '  {"numero": ' + str(token.numero) +
                     ', "lexema": ' + self._json_cadena(token.lexema) +
                     ', "tipo": "' + token.tipo +
                     '", "linea": ' + str(token.linea) +
                     ', "columna": ' + str(token.columna) + '}')
            if i < len(self.analizador.tokens) - 1:
                texto = texto + ','
            texto = texto + '\n'
            i = i + 1
        texto = texto + ']\n'

        self._escribir_export(ruta, texto, 'JSON')

    def _json_cadena(self, valor):
        salida = '"'
        i = 0
        while i < len(valor):
            c = valor[i]
            if c == '"':
                salida = salida + '\\"'
            elif c == '\\':
                salida = salida + '\\\\'
            elif c == '\n':
                salida = salida + '\\n'
            elif c == '\t':
                salida = salida + '\\t'
            elif c == '\r':
                salida = salida + '\\r'
            else:
                salida = salida + c
            i = i + 1
        return salida + '"'

    def _escribir_export(self, ruta, contenido, formato):
        try:
            archivo = open(ruta, 'w', encoding='utf-8')
            archivo.write(contenido)
            archivo.close()
        except (IOError, OSError) as detalle:
            messagebox.showerror('No se pudo exportar', str(detalle))
            return
        self._estado('Tabla de tokens exportada a ' + formato + ': ' + ruta)

    # ==================================================================
    # Varios
    # ==================================================================

    def _estado(self, mensaje):
        self.etiqueta_estado.configure(text=mensaje)

    def cargar_texto(self, contenido, nombre=''):
        """Carga contenido en el editor. Se usa para pruebas automatizadas."""
        self.texto.delete('1.0', 'end')
        self.texto.insert('1.0', contenido)
        self._numerar_lineas()
        if nombre != '':
            self.ruta_archivo = nombre
            self.etiqueta_archivo.configure(text=nombre)

    def _al_cerrar(self):
        if self.tarea_resaltado is not None:
            self.raiz.after_cancel(self.tarea_resaltado)
        self.raiz.destroy()
