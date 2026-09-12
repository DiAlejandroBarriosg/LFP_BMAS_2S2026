# -*- coding: utf-8 -*-
"""
graficador.py

Emite el codigo DOT de Graphviz con la jerarquia del horario y las relaciones
curso-catedratico-aula, exigido en el alcance obligatorio del enunciado.

Estructura del grafo:
    HORARIO
      |-- CURSOS, CATEDRATICOS, AULAS  (los elementos declarados)
      +-- CLASES                        (los nodos de clase)

Cada nodo de clase se conecta con su curso, su catedratico y su aula. Las
aristas que participan en un choque se dibujan en rojo y punteadas, de modo
que el conflicto se ve en el grafo y no solo en la tabla.

El metodo devuelve TEXTO. Renderizarlo a PNG requiere Graphviz instalado y es
responsabilidad del usuario:
    dot -Tpng jerarquia_horario.dot -o jerarquia_horario.png
Se entrega el DOT y no la imagen para que el proyecto no dependa de un binario
externo en tiempo de ejecucion.
"""

import os

from analizador import alfabeto as alf


class Graficador:

    def __init__(self, estructura, detector):
        self.estructura = estructura
        self.detector = detector

    # ------------------------------------------------------------------

    def _id(self, prefijo, codigo):
        """
        Convierte un codigo a un identificador valido de DOT: solo letras,
        digitos y guion bajo. 'A-101' se vuelve 'AULA_A_101'.
        """
        limpio = ''
        i = 0
        while i < len(codigo):
            c = codigo[i]
            if alf.es_letra(c) or alf.es_digito(c):
                limpio = limpio + c
            else:
                limpio = limpio + '_'
            i = i + 1
        if limpio == '':
            limpio = 'VACIO'
        return prefijo + '_' + limpio

    def _texto(self, valor):
        """Escapa las comillas dobles y las barras para las etiquetas DOT."""
        salida = ''
        i = 0
        while i < len(valor):
            c = valor[i]
            if c == '"':
                salida = salida + '\\"'
            elif c == '\\':
                salida = salida + '\\\\'
            else:
                salida = salida + c
            i = i + 1
        return salida

    def _recorte(self, texto, maximo):
        if len(texto) <= maximo:
            return texto
        return texto[0:maximo - 3] + '...'

    # ------------------------------------------------------------------

    def generar(self, rankdir='LR'):
        """
        rankdir='LR' por defecto: con TB el grafo crece a lo ancho (un horario
        de 22 clases dio 4381 px y resulto ilegible), mientras que en LR crece
        hacia abajo y cabe en una pagina vertical del manual.
        """
        lineas = []
        lineas.append('// Jerarquia del horario - generado por HorarioScript')
        lineas.append('// Render: dot -Tpng jerarquia_horario.dot -o jerarquia_horario.png')
        lineas.append('digraph Horario {')
        lineas.append('    rankdir = ' + rankdir + ';')
        lineas.append('    bgcolor = "white";')
        lineas.append('    nodesep = 0.22;')
        lineas.append('    ranksep = 1.1;')
        lineas.append('    node [fontname = "Helvetica", fontsize = 10];')
        lineas.append('    edge [fontname = "Helvetica", fontsize = 8, color = "#4a5b6c"];')
        lineas.append('')

        lineas.append('    HORARIO [label = "HORARIO", shape = box, style = "filled,bold", '
                      'fillcolor = "#16202a", fontcolor = "white", fontsize = 13];')
        lineas.append('')

        self._bloques(lineas)
        self._cursos(lineas)
        self._catedraticos(lineas)
        self._aulas(lineas)
        self._clases(lineas)
        self._leyenda(lineas)

        lineas.append('}')

        texto = ''
        i = 0
        while i < len(lineas):
            texto = texto + lineas[i] + '\n'
            i = i + 1
        return texto

    def _bloques(self, lineas):
        bloques = ('CURSOS', 'CATEDRATICOS', 'AULAS', 'CLASES')
        lineas.append('    node [shape = box, style = filled, '
                      'fillcolor = "#eef1f4", color = "#4a5b6c"];')
        i = 0
        while i < len(bloques):
            lineas.append('    ' + bloques[i] + ' [label = "' + bloques[i] +
                          '", fontsize = 12];')
            i = i + 1
        i = 0
        while i < len(bloques):
            lineas.append('    HORARIO -> ' + bloques[i] + ';')
            i = i + 1
        lineas.append('')

    def _cursos(self, lineas):
        lineas.append('    // --- cursos ---')
        lineas.append('    node [shape = box, style = "filled,rounded", '
                      'fillcolor = "#e6eff8", color = "#1f5f9e"];')
        i = 0
        while i < len(self.estructura.cursos):
            curso = self.estructura.cursos[i]
            identificador = self._id('CUR', curso.codigo)
            etiqueta = (self._texto(curso.codigo) + '\\n' +
                        self._texto(self._recorte(curso.nombre, 28)) + '\\n' +
                        str(curso.creditos) + ' creditos')
            lineas.append('    ' + identificador + ' [label = "' + etiqueta + '"];')
            lineas.append('    CURSOS -> ' + identificador + ';')
            i = i + 1
        lineas.append('')

    def _catedraticos(self, lineas):
        lineas.append('    // --- catedraticos ---')
        lineas.append('    node [shape = box, style = "filled,rounded", '
                      'fillcolor = "#e3f4e8", color = "#1f7a3f"];')
        i = 0
        while i < len(self.estructura.catedraticos):
            catedratico = self.estructura.catedraticos[i]
            identificador = self._id('CAT', catedratico.codigo)
            etiqueta = (self._texto(catedratico.codigo) + '\\n' +
                        self._texto(self._recorte(catedratico.nombre, 24)) +
                        '\\n' + self._texto(catedratico.categoria))
            lineas.append('    ' + identificador + ' [label = "' + etiqueta + '"];')
            lineas.append('    CATEDRATICOS -> ' + identificador + ';')
            i = i + 1
        lineas.append('')

    def _aulas(self, lineas):
        lineas.append('    // --- aulas ---')
        lineas.append('    node [shape = box, style = "filled,rounded", '
                      'fillcolor = "#fdeedd", color = "#b5651d"];')
        i = 0
        while i < len(self.estructura.aulas):
            aula = self.estructura.aulas[i]
            identificador = self._id('AUL', aula.codigo)
            etiqueta = (self._texto(aula.codigo) + '\\nedificio ' +
                        self._texto(aula.edificio) + '\\ncapacidad ' +
                        str(aula.capacidad))
            lineas.append('    ' + identificador + ' [label = "' + etiqueta + '"];')
            lineas.append('    AULAS -> ' + identificador + ';')
            i = i + 1
        lineas.append('')

    def _clases(self, lineas):
        lineas.append('    // --- clases y sus relaciones ---')
        i = 0
        while i < len(self.estructura.clases):
            clase = self.estructura.clases[i]
            identificador = self._id('CLS', clase.codigo_curso + '_' +
                                     clase.dia + '_' + clase.inicio_texto +
                                     '_' + clase.seccion)

            etiqueta = (self._texto(clase.dia) + ' ' +
                        self._texto(clase.inicio_texto) + '-' +
                        self._texto(clase.fin_texto) + '\\nseccion ' +
                        self._texto(clase.seccion))

            if clase.en_choque:
                lineas.append('    ' + identificador + ' [label = "' + etiqueta +
                              '\\nCHOQUE", shape = box, style = "filled,bold", '
                              'fillcolor = "#fbe6e6", color = "#a32626"];')
                estilo = ' [style = dashed, color = "#a32626"]'
            else:
                lineas.append('    ' + identificador + ' [label = "' + etiqueta +
                              '", shape = box, style = filled, '
                              'fillcolor = "#f7f9fb", color = "#4a5b6c"];')
                estilo = ''

            lineas.append('    CLASES -> ' + identificador + ';')
            lineas.append('    ' + identificador + ' -> ' +
                          self._id('CUR', clase.codigo_curso) +
                          ' [label = "imparte"' +
                          (', style = dashed, color = "#a32626"' if clase.en_choque else '') +
                          '];')
            lineas.append('    ' + identificador + ' -> ' +
                          self._id('CAT', clase.codigo_catedratico) +
                          ' [label = "con"' +
                          (', style = dashed, color = "#a32626"' if clase.en_choque else '') +
                          '];')
            lineas.append('    ' + identificador + ' -> ' +
                          self._id('AUL', clase.codigo_aula) +
                          ' [label = "en"' +
                          (', style = dashed, color = "#a32626"' if clase.en_choque else '') +
                          '];')
            i = i + 1
        lineas.append('')

    def _leyenda(self, lineas):
        total = self.detector.total()
        lineas.append('    // --- leyenda ---')
        lineas.append('    subgraph cluster_leyenda {')
        lineas.append('        label = "Leyenda";')
        lineas.append('        fontname = "Helvetica";')
        lineas.append('        fontsize = 10;')
        lineas.append('        color = "#d3dae1";')
        lineas.append('        style = rounded;')
        lineas.append('        LEYENDA [shape = plaintext, style = "", '
                      'label = <<table border="0" cellborder="0" cellspacing="2">'
                      '<tr><td align="left">Azul: cursos</td></tr>'
                      '<tr><td align="left">Verde: catedraticos</td></tr>'
                      '<tr><td align="left">Naranja: aulas</td></tr>'
                      '<tr><td align="left">Rojo punteado: clase en choque</td></tr>'
                      '<tr><td align="left">Choques detectados: ' + str(total) +
                      '</td></tr></table>>];')
        lineas.append('    }')

    # ------------------------------------------------------------------

    def guardar(self, carpeta, nombre='jerarquia_horario.dot', rankdir='LR'):
        if not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        ruta = os.path.join(carpeta, nombre)
        archivo = open(ruta, 'w', encoding='utf-8')
        archivo.write(self.generar(rankdir))
        archivo.close()
        return ruta
