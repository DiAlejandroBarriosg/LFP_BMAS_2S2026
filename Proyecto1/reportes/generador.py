# -*- coding: utf-8 -*-
"""
generador.py

Produce los cuatro archivos HTML del sistema:
    reporte1_horario_semanal.html   rejilla Lunes-Sabado por seccion
    reporte2_carga_catedraticos.html
    reporte3_estadistico.html
    reporte_errores.html            errores lexicos y avisos estructurales

DECISIONES DE DISENO

1. Un solo archivo para el Reporte 1, con una rejilla por seccion. El enunciado
   pide el reporte "por cada seccion presente en el archivo"; generar N
   archivos sueltos obliga a abrirlos uno por uno y dificulta las capturas del
   manual. Un documento con todas las secciones cumple lo pedido y se navega
   mejor.

2. Las filas de la rejilla se derivan de los bloques que realmente aparecen en
   el archivo, no de una retahila fija de 06:00 a 21:00 cada 20 minutos. Una
   rejilla fija generaria 45 filas casi todas vacias; asi la tabla muestra solo
   los bloques usados y sigue siendo fiel al horario.

3. La ocupacion de aulas se mide en TIEMPO, no en cantidad de clases:
   minutos ocupados / (6 dias x 15 horas). Contar clases daria porcentajes sin
   sentido, porque un bloque de 100 minutos y uno de 50 contarian igual.
"""

import os

from reportes import estilos
from modelos.elementos import minutos_a_hora
from analizador import palabras_reservadas as pr


class GeneradorReportes:

    def __init__(self, estructura, detector, analizador, nombre_archivo=''):
        self.estructura = estructura
        self.detector = detector
        self.analizador = analizador
        self.nombre_archivo = nombre_archivo

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _escapar(self, texto):
        """
        Neutraliza los caracteres con significado en HTML. Es imprescindible
        en el reporte de errores: un lexema invalido puede contener '<' y sin
        escaparlo rompe la pagina o inyecta etiquetas.
        """
        salida = ''
        i = 0
        while i < len(texto):
            c = texto[i]
            if c == '&':
                salida = salida + '&amp;'
            elif c == '<':
                salida = salida + '&lt;'
            elif c == '>':
                salida = salida + '&gt;'
            elif c == '"':
                salida = salida + '&quot;'
            else:
                salida = salida + c
            i = i + 1
        return salida

    def _cabecera(self, titulo, subtitulo):
        origen = self.nombre_archivo
        if origen == '':
            origen = 'entrada sin nombre'
        return ('<!DOCTYPE html>\n'
                '<html lang="es">\n<head>\n'
                '<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                '<title>' + self._escapar(titulo) + '</title>\n'
                '<style>' + estilos.CSS + '</style>\n'
                '</head>\n<body>\n<div class="hoja">\n'
                '<div class="encabezado">\n'
                '<h1>' + self._escapar(titulo) + '</h1>\n'
                '<p>' + self._escapar(subtitulo) + '</p>\n'
                '<p>Archivo analizado: ' + self._escapar(origen) + '</p>\n'
                '</div>\n')

    def _pie(self):
        return ('<div class="pie">HorarioScript &mdash; Proyecto 1, '
                'Lenguajes Formales y de Programacion, seccion B+, '
                'segundo semestre 2026.</div>\n'
                '</div>\n</body>\n</html>\n')

    def _nombre_curso(self, codigo):
        """
        Nombre del curso, con el codigo como respaldo. El respaldo cubre dos
        casos: que la clase referencie un curso no declarado, y que el curso
        exista pero tenga el nombre vacio. Sin esto la celda del reporte
        quedaria en blanco y no se sabria de que clase se trata.
        """
        curso = self.estructura.buscar_curso(codigo)
        if curso is None or curso.nombre == '':
            return codigo
        return curso.nombre

    def _nombre_catedratico(self, codigo):
        catedratico = self.estructura.buscar_catedratico(codigo)
        if catedratico is None or catedratico.nombre == '':
            return codigo
        return catedratico.nombre

    def _etiqueta_seccion(self, seccion):
        """Una seccion con nombre vacio se rotula de forma legible."""
        if seccion == '':
            return '(sin nombre)'
        return seccion

    def _escribir(self, carpeta, nombre, contenido):
        if not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        ruta = os.path.join(carpeta, nombre)
        archivo = open(ruta, 'w', encoding='utf-8')
        archivo.write(contenido)
        archivo.close()
        return ruta

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def generar_todos(self, carpeta):
        rutas = {}
        rutas['horario'] = self._escribir(
            carpeta, 'reporte1_horario_semanal.html', self.reporte_horario())
        rutas['carga'] = self._escribir(
            carpeta, 'reporte2_carga_catedraticos.html', self.reporte_carga())
        rutas['estadistico'] = self._escribir(
            carpeta, 'reporte3_estadistico.html', self.reporte_estadistico())
        rutas['errores'] = self._escribir(
            carpeta, 'reporte_errores.html', self.reporte_errores())
        return rutas

    # ==================================================================
    # REPORTE 1: horario semanal por seccion
    # ==================================================================

    def reporte_horario(self):
        html = self._cabecera(
            'Horario semanal por seccion',
            'Cada celda muestra curso, catedratico y aula. Los bloques en rojo '
            'tienen un conflicto de catedratico o de aula.')

        secciones = self.estructura.secciones()

        if len(secciones) == 0:
            html = html + ('<p class="nota">El archivo no contiene clases '
                           'programadas, asi que no hay horario que mostrar.</p>\n')
            return html + self._pie()

        html = html + self._leyenda()

        i = 0
        while i < len(secciones):
            html = html + self._rejilla_seccion(secciones[i])
            i = i + 1

        html = html + self._bloque_sugerencias()
        return html + self._pie()

    def _leyenda(self):
        return ('<div class="leyenda">\n'
                '<div><span class="etiqueta e-ok">CONFIRMADO</span>'
                'el bloque no compite con ningun otro.</div>\n'
                '<div><span class="etiqueta e-mal">CHOQUE DE HORARIO</span>'
                'el catedratico o el aula ya estan ocupados a esa hora.</div>\n'
                '<div><span class="etiqueta e-alta">REVISAR RANGO</span>'
                'la hora de fin es anterior o igual a la de inicio.</div>\n'
                '</div>\n')

    def _clases_de_seccion(self, seccion):
        lista = []
        i = 0
        while i < len(self.estructura.clases):
            if self.estructura.clases[i].seccion == seccion:
                lista.append(self.estructura.clases[i])
            i = i + 1
        return lista

    def _bloques_horarios(self, clases):
        """
        Bloques (inicio, fin) distintos presentes en las clases dadas,
        ordenados por hora de inicio con insercion.
        """
        bloques = []
        i = 0
        while i < len(clases):
            par = (clases[i].inicio, clases[i].fin)
            if par not in bloques:
                bloques.append(par)
            i = i + 1

        i = 1
        while i < len(bloques):
            actual = bloques[i]
            j = i - 1
            while j >= 0 and (bloques[j][0] > actual[0] or
                              (bloques[j][0] == actual[0] and
                               bloques[j][1] > actual[1])):
                bloques[j + 1] = bloques[j]
                j = j - 1
            bloques[j + 1] = actual
            i = i + 1

        return bloques

    def _rejilla_seccion(self, seccion):
        clases = self._clases_de_seccion(seccion)
        bloques = self._bloques_horarios(clases)

        html = ('<h2>Seccion ' +
                self._escapar(self._etiqueta_seccion(seccion)) + '</h2>\n')
        html = html + '<table class="rejilla">\n<thead>\n<tr>\n'
        html = html + '<th class="hora">Bloque</th>\n'

        d = 0
        while d < len(pr.DIAS):
            dia = pr.DIAS[d]
            html = html + '<th>' + dia[0:1] + dia[1:len(dia)].lower() + '</th>\n'
            d = d + 1

        html = html + '</tr>\n</thead>\n<tbody>\n'

        b = 0
        while b < len(bloques):
            inicio = bloques[b][0]
            fin = bloques[b][1]
            html = html + '<tr>\n<td class="hora">'
            html = html + minutos_a_hora(inicio) + '<br>' + minutos_a_hora(fin)
            html = html + '</td>\n'

            d = 0
            while d < len(pr.DIAS):
                html = html + self._celda(clases, pr.DIAS[d], inicio, fin)
                d = d + 1

            html = html + '</tr>\n'
            b = b + 1

        html = html + '</tbody>\n</table>\n'
        return html

    def _celda(self, clases, dia, inicio, fin):
        ocupantes = []
        i = 0
        while i < len(clases):
            clase = clases[i]
            if clase.dia == dia and clase.inicio == inicio and clase.fin == fin:
                ocupantes.append(clase)
            i = i + 1

        if len(ocupantes) == 0:
            return '<td class="vacia"></td>\n'

        hay_choque = False
        hay_rango_invalido = False
        i = 0
        while i < len(ocupantes):
            if ocupantes[i].en_choque:
                hay_choque = True
            if ocupantes[i].fin <= ocupantes[i].inicio:
                hay_rango_invalido = True
            i = i + 1

        if hay_choque:
            clase_css = 'choque'
        elif hay_rango_invalido:
            clase_css = 'revisar'
        else:
            clase_css = 'confirmado'
        html = '<td class="' + clase_css + '">\n'

        i = 0
        while i < len(ocupantes):
            clase = ocupantes[i]
            html = html + '<div class="bloque">'
            html = html + ('<span class="curso">' +
                           self._escapar(self._nombre_curso(clase.codigo_curso)) +
                           '</span>')
            html = html + ('<span class="detalle">' +
                           self._escapar(self._nombre_catedratico(
                               clase.codigo_catedratico)) + '</span>')
            html = html + ('<span class="detalle">Aula ' +
                           self._escapar(clase.codigo_aula) + '</span>')

            if clase.en_choque:
                motivos = self.detector.choques_de(clase)
                texto = 'CHOQUE DE HORARIO'
                if len(motivos) > 0:
                    texto = texto + ': ' + motivos[0].texto_motivos()
                html = html + ('<span class="marca">&#9888; ' +
                               self._escapar(texto) + '</span>')
            elif clase.fin <= clase.inicio:
                html = html + ('<span class="marca">&#9888; REVISAR RANGO: '
                               'termina ' + self._escapar(clase.fin_texto) +
                               ' y empieza ' +
                               self._escapar(clase.inicio_texto) + '</span>')

            html = html + '</div>\n'
            i = i + 1

        return html + '</td>\n'

    def _bloque_sugerencias(self):
        propuestas = self.detector.sugerencias_para_todos(self.estructura)
        if len(propuestas) == 0:
            return ''

        html = '<h2>Reprogramacion sugerida</h2>\n'
        html = html + ('<p class="nota">Para cada clase en conflicto se '
                       'proponen bloques del mismo dia y la misma duracion en '
                       'los que el catedratico y el aula estan libres.</p>\n')
        html = html + ('<table>\n<thead>\n<tr><th>Curso</th><th>Seccion</th>'
                       '<th>Dia</th><th>Horario actual</th>'
                       '<th>Bloques libres</th></tr>\n</thead>\n<tbody>\n')

        i = 0
        while i < len(propuestas):
            clase = propuestas[i]['clase']
            sugerencias = propuestas[i]['sugerencias']

            texto = ''
            if len(sugerencias) == 0:
                texto = 'Sin bloques libres ese dia'
            else:
                j = 0
                while j < len(sugerencias):
                    if j > 0:
                        texto = texto + '<br>'
                    texto = (texto + sugerencias[j]['inicio'] + ' &ndash; ' +
                             sugerencias[j]['fin'])
                    j = j + 1

            html = html + '<tr>'
            html = html + ('<td>' +
                           self._escapar(self._nombre_curso(clase.codigo_curso)) +
                           '</td>')
            html = html + ('<td>' +
                           self._escapar(self._etiqueta_seccion(clase.seccion)) +
                           '</td>')
            html = html + '<td>' + self._escapar(clase.dia) + '</td>'
            html = html + ('<td class="numero">' + clase.inicio_texto +
                           ' &ndash; ' + clase.fin_texto + '</td>')
            html = html + '<td class="sugerencia">' + texto + '</td>'
            html = html + '</tr>\n'
            i = i + 1

        return html + '</tbody>\n</table>\n'

    # ==================================================================
    # REPORTE 2: carga de catedraticos
    # ==================================================================

    def _clases_de_catedratico(self, codigo):
        lista = []
        i = 0
        while i < len(self.estructura.clases):
            if self.estructura.clases[i].codigo_catedratico == codigo:
                lista.append(self.estructura.clases[i])
            i = i + 1
        return lista

    def _nivel_carga(self, horas):
        if horas <= 0:
            return ('SIN ASIGNACION', 'e-baja')
        if horas <= estilos.CARGA_BAJA_MAX:
            return ('BAJA', 'e-baja')
        if horas <= estilos.CARGA_NORMAL_MAX:
            return ('NORMAL', 'e-normal')
        if horas <= estilos.CARGA_ALTA_MAX:
            return ('ALTA', 'e-alta')
        return ('SATURADA', 'e-saturada')

    def _perfil_catedratico(self, catedratico):
        clases = self._clases_de_catedratico(catedratico.codigo)

        minutos = 0
        cursos = []
        secciones = []
        en_choque = 0

        i = 0
        while i < len(clases):
            clase = clases[i]
            # Una clase con rango invertido (fin antes que inicio) daria una
            # duracion negativa y restaria horas de la carga. El Estructurador
            # ya la reporto como RANGO_INVALIDO; aqui se excluye del calculo.
            if clase.fin > clase.inicio:
                minutos = minutos + clase.duracion_minutos()
            if clase.codigo_curso not in cursos:
                cursos.append(clase.codigo_curso)
            if clase.seccion not in secciones:
                secciones.append(clase.seccion)
            if clase.en_choque:
                en_choque = en_choque + 1
            i = i + 1

        horas = minutos / 60.0
        return {
            'clases': len(clases),
            'horas': horas,
            'cursos': len(cursos),
            'secciones': len(secciones),
            'en_choque': en_choque,
        }

    def reporte_carga(self):
        html = self._cabecera(
            'Carga de catedraticos',
            'Horas semanales asignadas a cada catedratico, con el nivel de '
            'carga resultante.')

        html = html + ('<p class="nota">Los umbrales son los sugeridos por el '
                       'enunciado: baja hasta ' + str(estilos.CARGA_BAJA_MAX) +
                       ' horas, normal hasta ' + str(estilos.CARGA_NORMAL_MAX) +
                       ', alta hasta ' + str(estilos.CARGA_ALTA_MAX) +
                       ', y saturada por encima de ese valor. Las horas se '
                       'calculan sumando la duracion real de cada bloque en '
                       'CLASES, no la cantidad de clases.</p>\n')

        if len(self.estructura.catedraticos) == 0:
            html = html + ('<p class="nota">El archivo no declara '
                           'catedraticos.</p>\n')
            return html + self._pie()

        html = html + ('<table>\n<thead>\n<tr>'
                       '<th>Catedratico</th><th>Codigo</th><th>Categoria</th>'
                       '<th>Horas semanales</th><th>Cursos</th>'
                       '<th>Secciones</th><th>Clases</th><th>Nivel de carga</th>'
                       '</tr>\n</thead>\n<tbody>\n')

        i = 0
        while i < len(self.estructura.catedraticos):
            catedratico = self.estructura.catedraticos[i]
            perfil = self._perfil_catedratico(catedratico)
            nivel = self._nivel_carga(perfil['horas'])

            html = html + '<tr>'
            html = html + '<td>' + self._escapar(catedratico.nombre) + '</td>'
            html = html + '<td>' + self._escapar(catedratico.codigo) + '</td>'
            html = html + '<td>' + self._escapar(catedratico.categoria) + '</td>'
            html = html + ('<td class="numero">' +
                           self._decimales(perfil['horas']) + '</td>')
            html = html + '<td class="numero">' + str(perfil['cursos']) + '</td>'
            html = html + ('<td class="numero">' + str(perfil['secciones']) +
                           '</td>')
            html = html + '<td class="numero">' + str(perfil['clases']) + '</td>'
            html = html + ('<td><span class="etiqueta ' + nivel[1] + '">' +
                           nivel[0] + '</span></td>')
            html = html + '</tr>\n'
            i = i + 1

        html = html + '</tbody>\n</table>\n'

        html = html + self._catedraticos_en_conflicto()
        return html + self._pie()

    def _catedraticos_en_conflicto(self):
        afectados = self.detector.recursos_afectados()['catedraticos']
        if len(afectados) == 0:
            return ('<div class="limpio">Ningun catedratico tiene clases '
                    'traslapadas.</div>\n')

        html = '<h3>Catedraticos con clases traslapadas</h3>\n<ul class="lista">\n'
        i = 0
        while i < len(afectados):
            html = html + ('<li>' + self._escapar(afectados[i]) + ' &mdash; ' +
                           self._escapar(self._nombre_catedratico(afectados[i])) +
                           '</li>\n')
            i = i + 1
        return html + '</ul>\n'

    def _decimales(self, valor):
        """Formatea un flotante con un decimal sin recurrir a format()."""
        signo = ''
        if valor < 0:
            signo = '-'
            valor = -valor
        entero = int(valor * 10 + 0.5)
        parte_entera = entero // 10
        parte_decimal = entero % 10
        return signo + str(parte_entera) + '.' + str(parte_decimal)

    # ==================================================================
    # REPORTE 3: estadistico general del ciclo
    # ==================================================================

    def _ocupacion_aulas(self):
        filas = []
        i = 0
        while i < len(self.estructura.aulas):
            aula = self.estructura.aulas[i]
            minutos = 0
            clases = 0

            j = 0
            while j < len(self.estructura.clases):
                clase = self.estructura.clases[j]
                if clase.codigo_aula == aula.codigo and clase.fin > clase.inicio:
                    minutos = minutos + clase.duracion_minutos()
                    clases = clases + 1
                j = j + 1

            porcentaje = 0.0
            if estilos.MINUTOS_SEMANA > 0:
                porcentaje = (minutos * 100.0) / estilos.MINUTOS_SEMANA

            filas.append({
                'aula': aula,
                'clases': clases,
                'minutos': minutos,
                'porcentaje': porcentaje,
            })
            i = i + 1
        return filas

    def _mayor_carga(self):
        mejor = None
        mejor_horas = -1.0
        i = 0
        while i < len(self.estructura.catedraticos):
            catedratico = self.estructura.catedraticos[i]
            horas = self._perfil_catedratico(catedratico)['horas']
            if horas > mejor_horas:
                mejor_horas = horas
                mejor = catedratico
            i = i + 1
        return (mejor, mejor_horas)

    def reporte_estadistico(self):
        html = self._cabecera(
            'Estadistico general del ciclo',
            'Resumen ejecutivo del horario procesado.')

        resumen = self.estructura.resumen()
        total_choques = self.detector.total()
        filas = self._ocupacion_aulas()
        catedratico, horas_max = self._mayor_carga()

        promedio = 0.0
        if len(self.estructura.catedraticos) > 0:
            total_horas = 0.0
            i = 0
            while i < len(self.estructura.catedraticos):
                total_horas = total_horas + self._perfil_catedratico(
                    self.estructura.catedraticos[i])['horas']
                i = i + 1
            promedio = total_horas / len(self.estructura.catedraticos)

        aula_top = None
        porcentaje_top = -1.0
        i = 0
        while i < len(filas):
            if filas[i]['porcentaje'] > porcentaje_top:
                porcentaje_top = filas[i]['porcentaje']
                aula_top = filas[i]
            i = i + 1

        html = html + '<div class="indicadores">\n'
        html = html + self._indicador(str(resumen['cursos']), 'Cursos', False)
        html = html + self._indicador(str(resumen['catedraticos']),
                                      'Catedraticos', False)
        html = html + self._indicador(str(resumen['aulas']), 'Aulas', False)
        html = html + self._indicador(str(resumen['clases']),
                                      'Clases programadas', False)
        html = html + self._indicador(str(total_choques), 'Choques de horario',
                                      total_choques > 0)
        html = html + self._indicador(str(resumen['secciones']), 'Secciones',
                                      False)
        html = html + '</div>\n'

        html = html + '<h2>Indicadores de carga y ocupacion</h2>\n'
        html = html + '<table>\n<tbody>\n'

        nombre_top = 'sin datos'
        if catedratico is not None:
            nombre_top = (catedratico.nombre + ' (' + catedratico.codigo +
                          '), ' + self._decimales(horas_max) + ' horas')
        html = html + ('<tr><th>Catedratico con mayor carga</th><td>' +
                       self._escapar(nombre_top) + '</td></tr>\n')

        texto_aula = 'sin datos'
        if aula_top is not None:
            texto_aula = (aula_top['aula'].codigo + ', ' +
                          self._decimales(aula_top['porcentaje']) +
                          '% de ocupacion')
        html = html + ('<tr><th>Aula con mayor ocupacion</th><td>' +
                       self._escapar(texto_aula) + '</td></tr>\n')

        html = html + ('<tr><th>Promedio de horas semanales por catedratico'
                       '</th><td>' + self._decimales(promedio) +
                       ' horas</td></tr>\n')
        html = html + ('<tr><th>Errores lexicos detectados</th><td>' +
                       str(self.analizador.gestor.total()) + '</td></tr>\n')
        html = html + ('<tr><th>Avisos estructurales</th><td>' +
                       str(len(self.estructura.avisos)) + '</td></tr>\n')
        html = html + '</tbody>\n</table>\n'

        html = html + '<h2>Ocupacion por aula</h2>\n'
        html = html + ('<p class="nota">La ocupacion se mide en tiempo: '
                       'minutos asignados sobre los ' +
                       str(estilos.MINUTOS_SEMANA) + ' minutos disponibles a '
                       'la semana (' + str(estilos.DIAS_HABILES) +
                       ' dias de 06:00 a 21:00). Las aulas por encima del ' +
                       self._decimales(estilos.UMBRAL_OCUPACION_ALTA) +
                       '% se marcan en rojo.</p>\n')

        if len(filas) == 0:
            html = html + '<p class="nota">El archivo no declara aulas.</p>\n'
            return html + self._pie()

        html = html + ('<table>\n<thead>\n<tr><th>Aula</th><th>Edificio</th>'
                       '<th>Capacidad</th><th>Clases asignadas</th>'
                       '<th>Horas ocupadas</th><th>Ocupacion</th>'
                       '<th>% </th></tr>\n</thead>\n<tbody>\n')

        i = 0
        while i < len(filas):
            fila = filas[i]
            saturada = fila['porcentaje'] > estilos.UMBRAL_OCUPACION_ALTA
            ancho = fila['porcentaje']
            if ancho > 100.0:
                ancho = 100.0

            clase_barra = 'barra saturada' if saturada else 'barra'

            html = html + '<tr>'
            html = html + '<td>' + self._escapar(fila['aula'].codigo) + '</td>'
            html = html + '<td>' + self._escapar(fila['aula'].edificio) + '</td>'
            html = html + ('<td class="numero">' +
                           str(fila['aula'].capacidad) + '</td>')
            html = html + '<td class="numero">' + str(fila['clases']) + '</td>'
            html = html + ('<td class="numero">' +
                           self._decimales(fila['minutos'] / 60.0) + '</td>')
            html = html + ('<td><div class="' + clase_barra +
                           '"><span style="width:' +
                           self._decimales(ancho) + '%"></span></div></td>')
            html = html + ('<td class="numero">' +
                           self._decimales(fila['porcentaje']) + '%</td>')
            html = html + '</tr>\n'
            i = i + 1

        html = html + '</tbody>\n</table>\n'
        return html + self._pie()

    def _indicador(self, valor, rotulo, alerta):
        clase = 'indicador alerta' if alerta else 'indicador'
        return ('<div class="' + clase + '">'
                '<span class="valor">' + valor + '</span>'
                '<span class="rotulo">' + self._escapar(rotulo) + '</span>'
                '</div>\n')

    # ==================================================================
    # REPORTE ADICIONAL: errores lexicos y avisos
    # ==================================================================

    def reporte_errores(self):
        html = self._cabecera(
            'Errores lexicos y avisos',
            'Todo lo que el analizador encontro en una sola pasada del archivo.')

        gestor = self.analizador.gestor

        html = html + '<h2>Errores lexicos</h2>\n'
        html = html + ('<p class="nota">Los detecta el AFD. El analisis no se '
                       'detiene ante el primer error: continua para reportar '
                       'todos los problemas de una vez.</p>\n')

        if not gestor.hay_errores():
            html = html + ('<div class="limpio">El archivo no tiene errores '
                           'lexicos.</div>\n')
        else:
            html = html + ('<table>\n<thead>\n<tr><th>No.</th>'
                           '<th>Lexema</th><th>Tipo de error</th>'
                           '<th>Descripcion</th><th>Linea</th><th>Columna</th>'
                           '</tr>\n</thead>\n<tbody>\n')
            i = 0
            while i < len(gestor.errores):
                error = gestor.errores[i]
                html = html + '<tr>'
                html = html + '<td class="numero">' + str(error.numero) + '</td>'
                html = html + '<td>' + self._escapar(error.lexema) + '</td>'
                html = html + ('<td><span class="etiqueta e-mal">' +
                               self._escapar(error.tipo) + '</span></td>')
                html = html + '<td>' + self._escapar(error.descripcion) + '</td>'
                html = html + '<td class="numero">' + str(error.linea) + '</td>'
                html = html + ('<td class="numero">' + str(error.columna) +
                               '</td>')
                html = html + '</tr>\n'
                i = i + 1
            html = html + '</tbody>\n</table>\n'

            html = html + '<h3>Errores por tipo</h3>\n<ul class="lista">\n'
            conteo = gestor.contar_por_tipo()
            for tipo in sorted(conteo.keys()):
                html = html + ('<li>' + self._escapar(tipo) + ': ' +
                               str(conteo[tipo]) + '</li>\n')
            html = html + '</ul>\n'

        html = html + '<h2>Avisos estructurales</h2>\n'
        html = html + ('<p class="nota">No son errores lexicos. Aparecen '
                       'cuando el flujo de tokens es valido pero el contenido '
                       'no cuadra: un atributo que falta, una clase que '
                       'referencia un codigo inexistente, un codigo repetido.'
                       '</p>\n')

        avisos = self.estructura.avisos
        if len(avisos) == 0:
            html = html + ('<div class="limpio">No hay inconsistencias '
                           'estructurales.</div>\n')
        else:
            html = html + ('<table>\n<thead>\n<tr><th>No.</th><th>Tipo</th>'
                           '<th>Descripcion</th><th>Linea</th></tr>\n'
                           '</thead>\n<tbody>\n')
            i = 0
            while i < len(avisos):
                aviso = avisos[i]
                html = html + '<tr>'
                html = html + '<td class="numero">' + str(aviso.numero) + '</td>'
                html = html + ('<td><span class="etiqueta e-alta">' +
                               self._escapar(aviso.tipo) + '</span></td>')
                html = html + '<td>' + self._escapar(aviso.descripcion) + '</td>'
                html = html + '<td class="numero">' + str(aviso.linea) + '</td>'
                html = html + '</tr>\n'
                i = i + 1
            html = html + '</tbody>\n</table>\n'

        html = html + '<h2>Frecuencia de tokens</h2>\n'
        conteo = self.analizador.contar_por_tipo()
        html = html + ('<table>\n<thead>\n<tr><th>Tipo de token</th>'
                       '<th>Cantidad</th></tr>\n</thead>\n<tbody>\n')
        for tipo in sorted(conteo.keys()):
            html = html + ('<tr><td>' + self._escapar(tipo) +
                           '</td><td class="numero">' + str(conteo[tipo]) +
                           '</td></tr>\n')
        html = html + ('<tr><td>Total de tokens</td><td class="numero">' +
                       str(len(self.analizador.tokens)) + '</td></tr>\n')
        html = html + '</tbody>\n</table>\n'

        return html + self._pie()
