# -*- coding: utf-8 -*-
"""
prueba_interfaz.py
Prueba automatica de la interfaz grafica: abre la ventana, carga archivos,
analiza y revisa lo que muestran las pestanas y los botones, sin que nadie
tenga que hacer clic.

Uso, desde la carpeta Proyecto2:
    python tests/prueba_interfaz.py

Necesita una pantalla (en Windows siempre la hay).
"""

import os
import sys
import time
import tkinter as tk

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

from gui import ventana_principal
from gui.ventana_principal import VentanaPrincipal, quitar_extension
from gui.ventana_principal import extension_de

CARPETA_SALIDA = os.path.join(CARPETA_PROYECTO, 'salida')

# Los mensajes emergentes detendrian la prueba esperando un clic: se
# reemplazan por una funcion que solo los anota.
mensajes = []


def anotar_mensaje(titulo, texto):
    mensajes.append(texto)


ventana_principal.messagebox.showerror = anotar_mensaje
ventana_principal.messagebox.showinfo = anotar_mensaje


class Verificador:

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


def ejemplo(nombre):
    return os.path.join(CARPETA_PROYECTO, 'examples', nombre)


def esperar(ventana, segundos):
    """Deja correr la ventana un rato, como si el usuario esperara."""
    inicio = time.time()
    while time.time() - inicio < segundos:
        ventana.update()
        time.sleep(0.02)


def contiene(texto, buscado):
    """True si 'buscado' aparece dentro de 'texto' (busqueda manual)."""
    i = 0
    while i + len(buscado) <= len(texto):
        j = 0
        while j < len(buscado) and texto[i + j] == buscado[j]:
            j = j + 1
        if j == len(buscado):
            return True
        i = i + 1
    return False


def como_textos(rangos):
    """Los indices de Tk ('6.0', '6.42') como texto, para compararlos."""
    textos = []
    i = 0
    while i < len(rangos):
        textos.append(str(rangos[i]))
        i = i + 1
    return textos


def habilitado(boton):
    return not boton.instate(['disabled'])


def main():
    v = Verificador()
    ventana = tk.Tk()
    app = VentanaPrincipal(ventana, CARPETA_SALIDA)
    ventana.update()

    print('')
    print('A. Estado inicial y carga de archivos')
    print('-------------------------------------')
    v.verificar('al inicio los botones de reportes estan deshabilitados',
                [habilitado(app.boton_r1), habilitado(app.boton_errores)],
                [False, False])
    v.verificar('un archivo que no existe se rechaza con un mensaje',
                [app.cargar_archivo(ejemplo('no_existe.md')), len(mensajes)],
                [False, 1])
    v.verificar('un archivo que no es .md se rechaza con un mensaje',
                [app.cargar_archivo(os.path.abspath(__file__)),
                 len(mensajes)], [False, 2])
    v.verificar('extension de "a.md", "A.MD", "x.md.bak" y "notas"',
                [extension_de('a.md'), extension_de('A.MD'),
                 extension_de('x.md.bak'), extension_de('notas')],
                ['md', 'MD', 'bak', ''])
    v.verificar('carga ejemplo_valido.md en el editor',
                app.cargar_archivo(ejemplo('ejemplo_valido.md')), True)
    v.verificar('26 lineas y la 27 vacia despues del ultimo salto, '
                'numeradas', [app._linea_de(app.editor.index('end-1c')),
                              app._linea_de(app.numeros.index('end-1c')) - 1],
                [27, 27])

    print('')
    print('B. Analisis de un archivo valido')
    print('--------------------------------')
    app.analizar()
    ventana.update()
    v.verificar('tabla de tokens: 77 filas',
                len(app.tabla_tokens.get_children()), 77)
    fila = app.tabla_tokens.item('0', 'values')
    v.verificar('primera fila: No., lexema, tipo, linea, columna',
                [str(fila[0]), fila[1], fila[2], str(fila[3]), str(fila[4])],
                ['1', '#', 'NUMERAL', '1', '1'])
    v.verificar('tabla de errores vacia',
                len(app.tabla_errores.get_children()), 0)
    raices = app.vista_arbol.get_children()
    v.verificar('el arbol empieza en <documento>',
                app.vista_arbol.item(raices[0], 'text'), '<documento>')
    v.verificar('botones de los 3 reportes y del arbol habilitados',
                [habilitado(app.boton_r1), habilitado(app.boton_r2),
                 habilitado(app.boton_r3), habilitado(app.boton_arbol)],
                [True, True, True, True])
    v.verificar('sin errores, el boton Errores queda deshabilitado',
                habilitado(app.boton_errores), False)
    carpeta = os.path.join(CARPETA_SALIDA, 'ejemplo_valido')
    v.verificar('los reportes quedan en salida/ejemplo_valido/',
                [os.path.isfile(os.path.join(carpeta,
                                             'reporte1_documento.html')),
                 os.path.isfile(os.path.join(carpeta, 'arbol.dot'))],
                [True, True])

    app.tabla_tokens.selection_set('19')
    app.tabla_tokens.focus('19')
    app._al_seleccionar_token(None)
    v.verificar('al elegir un token, el cursor va a su posicion',
                app.editor.index(tk.INSERT), '5.0')

    print('')
    print('C. Analisis de un archivo con errores')
    print('-------------------------------------')
    app.cargar_archivo(ejemplo('errores_sintacticos.md'))
    app.analizar()
    ventana.update()
    v.verificar('tabla de errores: 5 filas',
                len(app.tabla_errores.get_children()), 5)
    v.verificar('la pestana muestra la cantidad de errores',
                app.pestanas.tab(1, 'text'), 'Errores (5)')
    v.verificar('con errores, solo Errores y Arbol habilitados',
                [habilitado(app.boton_r1), habilitado(app.boton_errores),
                 habilitado(app.boton_arbol)], [False, True, True])
    v.verificar('los errores quedan marcados en el editor',
                len(app.editor.tag_ranges('error')) > 0, True)

    app.tabla_errores.selection_set('3')
    app.tabla_errores.focus('3')
    app._al_seleccionar_error(None)
    v.verificar('al elegir el error 4 (linea 11, columna 2) el cursor va '
                'ahi', app.editor.index(tk.INSERT), '11.1')
    v.verificar('la barra inferior muestra la posicion',
                app.etiqueta_cursor.cget('text'), 'Línea 11, columna 2')

    print('')
    print('D. Editar y volver a analizar sin guardar')
    print('-----------------------------------------')
    app.limpiar()
    app.editor.insert('1.0', '# Nuevo\n\n- uno\n  - dos\n')
    app.analizar()
    v.verificar('analiza lo escrito en el editor', [
        len(app.tabla_errores.get_children()), habilitado(app.boton_r1)],
        [0, True])
    v.verificar('sin archivo, la salida va a salida/sin_titulo/',
                os.path.isdir(os.path.join(CARPETA_SALIDA, 'sin_titulo')),
                True)
    v.verificar('quitar_extension', [quitar_extension('notas.md', 'x'),
                                     quitar_extension('a.b/notas', 'x'),
                                     quitar_extension('.md', 'x')],
                ['notas', 'a.b/notas', 'x'])

    print('')
    print('E. Alcance opcional: vista previa y anidamiento')
    print('-----------------------------------------------')
    v.verificar('hay una cuarta pestana "Vista previa"',
                app.pestanas.tab(3, 'text'), 'Vista previa')
    app.cargar_archivo(ejemplo(os.path.join('casos',
                                            'caso14_alcance_opcional.md')))
    ventana.update()
    vista = app.vista_previa.contenido()
    v.verificar('al cargar, la vista previa muestra el documento formateado '
                '(sin los "**" de la negrita)',
                [contiene(vista, 'Alcance opcional'),
                 contiene(vista, '1. Diseñar la gramática'),
                 contiene(vista, '☑  Funciones de bloques'),
                 contiene(vista, '[imagen: Diagrama del AFD]'),
                 contiene(vista, 'el **parser**')],
                [True, True, True, True, False])
    v.verificar('negrita, tachado y enlace tienen su formato',
                [len(app.vista_previa.texto.tag_ranges('f_n')) > 0,
                 len(app.vista_previa.texto.tag_ranges('tachado')) > 0,
                 len(app.vista_previa.texto.tag_ranges('enlace')) > 0],
                [True, True, True])
    v.verificar('la tabla queda en columnas alineadas',
                contiene(vista, ' TACHADO           │   ~~    │     Léxico '),
                True)

    app.editor.insert(tk.END, '\nUna línea **nueva** escrita a mano.\n')
    app._al_editar(None)
    v.verificar('al escribir no se actualiza en cada tecla...',
                contiene(app.vista_previa.contenido(), 'nueva'), False)
    esperar(ventana, 0.6)
    v.verificar('... sino al dejar de escribir: la vista previa es en vivo',
                contiene(app.vista_previa.contenido(),
                         'Una línea nueva escrita a mano.'), True)

    app.editor.insert(tk.END, '\nTexto ~~sin cerrar\n')
    app._al_editar(None)
    esperar(ventana, 0.6)
    v.verificar('con errores, la vista previa lo avisa',
                contiene(app.etiqueta_vista.cget('text'), '1 error(es)'),
                True)

    app.limpiar()
    app.editor.insert('1.0', '- a\n\n  - huerfano\n')
    app._actualizar_vista_previa()
    v.verificar('una sublista sin item padre (con error) igual se muestra',
                contiene(app.vista_previa.contenido(), 'huerfano'), True)

    app.limpiar()
    app.editor.insert('1.0', '[uno](https://a.org) y [dos](https://b.org)\n')
    app._actualizar_vista_previa()
    antes = len(ventana.tk.call('info', 'commands'))
    i = 0
    while i < 20:
        app._actualizar_vista_previa()
        i = i + 1
    v.verificar('redibujar enlaces no acumula comandos de Tk',
                len(ventana.tk.call('info', 'commands')), antes)

    app.limpiar()
    texto = ''
    i = 0
    while i < 600:
        texto = texto + '>'
        i = i + 1
    app.editor.insert('1.0', texto + ' x\n')
    app._actualizar_vista_previa()
    v.verificar('con un anidamiento imposible se avisa y no queda nada viejo',
                [contiene(app.etiqueta_vista.cget('text'), 'demasiado'),
                 app.vista_previa.contenido(), app.aviso_visible],
                [True, '', False])

    app.maximo_anidamiento.set('3')
    app.cargar_archivo(ejemplo(os.path.join('casos',
                                            'caso02_lista_profunda.md')))
    ventana.update()
    v.verificar('una lista de 4 niveles con maximo 3: aparece la advertencia',
                [app.aviso_visible,
                 contiene(app.aviso.cget('text'),
                          'lista de nivel 4 en la línea 6')], [True, True])
    v.verificar('... y su linea queda marcada en el editor',
                como_textos(app.editor.tag_ranges('anidamiento')),
                ['6.0', '6.42'])
    app.maximo_anidamiento.set('4')
    app._al_cambiar_maximo()
    v.verificar('con maximo 4 la advertencia desaparece',
                [app.aviso_visible,
                 len(app.editor.tag_ranges('anidamiento'))], [False, 0])
    app.maximo_anidamiento.set('x')
    v.verificar('si el maximo no es un numero se usa 3', app.maximo(), 3)

    ventana.destroy()

    print('')
    print('=' * 60)
    total = v.correctas + v.fallidas
    print('Verificaciones: ' + str(total) + '   correctas: ' +
          str(v.correctas) + '   fallidas: ' + str(v.fallidas))
    print('=' * 60)
    if v.fallidas > 0:
        sys.exit(1)


main()
