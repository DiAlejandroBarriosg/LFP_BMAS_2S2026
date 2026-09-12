# -*- coding: utf-8 -*-
"""
detector_choques.py

Detecta conflictos de programacion sobre los objetos que armo el Estructurador.

DEFINICION DE CHOQUE
Dos clases chocan si se cumplen las tres condiciones a la vez:
  1. estan el mismo dia
  2. sus intervalos de tiempo se traslapan
  3. comparten catedratico o comparten aula

TRASLAPE
    traslapan(a, b)  <=>  a.inicio < b.fin  Y  b.inicio < a.fin

La desigualdad es ESTRICTA en ambos lados, y esa es la decision que evita el
falso positivo mas comun: una clase que termina 08:40 y otra que empieza 08:40
comparten un instante, pero eso es continuidad, no conflicto. Con '<=' en
lugar de '<', todo horario encadenado de la facultad se reportaria como choque.

COMPLEJIDAD
Se agrupa por dia y se comparan todos los pares dentro de cada grupo: O(n^2)
sobre grupos pequenos. Un horario de facultad tiene decenas de clases por dia,
no miles, asi que no vale la pena una estructura mas elaborada. Agrupar primero
por dia ya reduce el problema a una fraccion del total.
"""

from modelos.choque import Choque, MOTIVO_CATEDRATICO, MOTIVO_AULA
from modelos.elementos import minutos_a_hora
from analizador import palabras_reservadas as pr

# Paso de la rejilla al sugerir bloques libres. 20 minutos porque los bloques
# institucionales arrancan en :00, :20 y :40.
PASO_SUGERENCIA = 20
MAX_SUGERENCIAS = 5


class DetectorChoques:

    def __init__(self):
        self.choques = []
        self.contador = 0

    # ------------------------------------------------------------------
    # Deteccion
    # ------------------------------------------------------------------

    def detectar(self, estructura):
        self.choques = []
        self.contador = 0

        # Se limpian las banderas para que reanalizar no arrastre resultados
        i = 0
        while i < len(estructura.clases):
            estructura.clases[i].en_choque = False
            i = i + 1

        grupos = estructura.clases_por_dia()

        # Se recorre en el orden LUNES..SABADO para que la numeracion de los
        # choques sea estable entre ejecuciones
        d = 0
        while d < len(pr.DIAS):
            dia = pr.DIAS[d]
            if dia in grupos:
                self._revisar_dia(grupos[dia])
            d = d + 1

        return self.choques

    def _revisar_dia(self, clases_del_dia):
        lista = self._ordenar_por_inicio(clases_del_dia)

        i = 0
        while i < len(lista):
            j = i + 1
            while j < len(lista):
                self._comparar(lista[i], lista[j])
                j = j + 1
            i = i + 1

    def _comparar(self, a, b):
        if not self._es_evaluable(a) or not self._es_evaluable(b):
            return
        if not self._traslapan(a, b):
            return

        motivos = []

        if a.codigo_catedratico != '' and \
                a.codigo_catedratico == b.codigo_catedratico:
            motivos.append((MOTIVO_CATEDRATICO, a.codigo_catedratico))

        if a.codigo_aula != '' and a.codigo_aula == b.codigo_aula:
            motivos.append((MOTIVO_AULA, a.codigo_aula))

        # Se traslapan pero no comparten recurso: dos clases distintas a la
        # misma hora en aulas distintas con catedraticos distintos es normal.
        if len(motivos) == 0:
            return

        inicio_traslape = a.inicio
        if b.inicio > inicio_traslape:
            inicio_traslape = b.inicio

        fin_traslape = a.fin
        if b.fin < fin_traslape:
            fin_traslape = b.fin

        self.contador = self.contador + 1
        choque = Choque(self.contador, a, b, motivos,
                        inicio_traslape, fin_traslape)
        self.choques.append(choque)

        a.en_choque = True
        b.en_choque = True

    def _traslapan(self, a, b):
        """Desigualdad estricta: tocarse en un extremo no es traslape."""
        return a.inicio < b.fin and b.inicio < a.fin

    def _es_evaluable(self, clase):
        """
        Una clase con rango invertido o de duracion cero no se evalua. El
        Estructurador ya la reporto como RANGO_INVALIDO; meterla aqui daria
        resultados sin sentido en la formula de traslape.
        """
        return clase.fin > clase.inicio

    def _ordenar_por_inicio(self, clases):
        """
        Ordenamiento por insercion sobre una copia. Se ordena para que la
        numeracion de los choques siga el reloj y el reporte se lea natural.
        """
        lista = []
        i = 0
        while i < len(clases):
            lista.append(clases[i])
            i = i + 1

        i = 1
        while i < len(lista):
            actual = lista[i]
            j = i - 1
            while j >= 0 and lista[j].inicio > actual.inicio:
                lista[j + 1] = lista[j]
                j = j - 1
            lista[j + 1] = actual
            i = i + 1

        return lista

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def total(self):
        return len(self.choques)

    def hay_choques(self):
        return len(self.choques) > 0

    def choques_de(self, clase):
        """Choques en los que participa una clase concreta."""
        encontrados = []
        i = 0
        while i < len(self.choques):
            if self.choques[i].involucra(clase):
                encontrados.append(self.choques[i])
            i = i + 1
        return encontrados

    def resumen(self):
        por_catedratico = 0
        por_aula = 0
        ambos = 0

        i = 0
        while i < len(self.choques):
            tiene_cat = self.choques[i].tiene_motivo(MOTIVO_CATEDRATICO)
            tiene_aula = self.choques[i].tiene_motivo(MOTIVO_AULA)
            if tiene_cat and tiene_aula:
                ambos = ambos + 1
            elif tiene_cat:
                por_catedratico = por_catedratico + 1
            else:
                por_aula = por_aula + 1
            i = i + 1

        return {
            'total': len(self.choques),
            'solo_catedratico': por_catedratico,
            'solo_aula': por_aula,
            'ambos': ambos,
        }

    def recursos_afectados(self):
        """Codigos de catedraticos y aulas involucrados en algun choque."""
        catedraticos = []
        aulas = []

        i = 0
        while i < len(self.choques):
            motivos = self.choques[i].motivos
            j = 0
            while j < len(motivos):
                motivo = motivos[j][0]
                recurso = motivos[j][1]
                if motivo == MOTIVO_CATEDRATICO:
                    if recurso not in catedraticos:
                        catedraticos.append(recurso)
                else:
                    if recurso not in aulas:
                        aulas.append(recurso)
                j = j + 1
            i = i + 1

        catedraticos.sort()
        aulas.sort()
        return {'catedraticos': catedraticos, 'aulas': aulas}

    # ------------------------------------------------------------------
    # Funcionalidad opcional: sugerir bloques libres (seccion 4.2)
    # ------------------------------------------------------------------

    def sugerir_bloques_libres(self, estructura, clase,
                               paso=PASO_SUGERENCIA, maximo=MAX_SUGERENCIAS):
        """
        Propone horarios alternativos para una clase en conflicto, el mismo dia.

        Recorre el dia en una rejilla de 'paso' minutos dentro del rango
        institucional y devuelve los bloques donde el catedratico Y el aula de
        la clase estan libres, manteniendo la duracion original.

        La propia clase se excluye de la comprobacion: se la esta moviendo, asi
        que su horario actual no debe bloquearse a si mismo.
        """
        duracion = clase.duracion_minutos()
        if duracion <= 0:
            return []

        ocupadas = self._clases_que_bloquean(estructura, clase)

        sugerencias = []
        inicio = pr.MIN_HORA_INSTITUCIONAL

        while inicio + duracion <= pr.MAX_HORA_INSTITUCIONAL:
            if len(sugerencias) >= maximo:
                break
            if self._bloque_libre(inicio, inicio + duracion, ocupadas):
                sugerencias.append({
                    'inicio': minutos_a_hora(inicio),
                    'fin': minutos_a_hora(inicio + duracion),
                    'inicio_min': inicio,
                    'fin_min': inicio + duracion,
                })
            inicio = inicio + paso

        return sugerencias

    def _clases_que_bloquean(self, estructura, clase):
        """
        Clases del mismo dia que comparten catedratico o aula con la que se
        quiere reprogramar. Son las unicas que pueden estorbar.
        """
        bloqueantes = []
        i = 0
        while i < len(estructura.clases):
            otra = estructura.clases[i]
            i = i + 1

            if otra is clase:
                continue
            if otra.dia != clase.dia:
                continue
            if not self._es_evaluable(otra):
                continue

            mismo_catedratico = (clase.codigo_catedratico != '' and
                                 otra.codigo_catedratico == clase.codigo_catedratico)
            misma_aula = (clase.codigo_aula != '' and
                          otra.codigo_aula == clase.codigo_aula)

            if mismo_catedratico or misma_aula:
                bloqueantes.append(otra)

        return bloqueantes

    def _bloque_libre(self, inicio, fin, ocupadas):
        i = 0
        while i < len(ocupadas):
            otra = ocupadas[i]
            if inicio < otra.fin and otra.inicio < fin:
                return False
            i = i + 1
        return True

    def sugerencias_para_todos(self, estructura):
        """
        Sugerencias para cada clase en choque. Devuelve una lista de
        diccionarios lista para volcarse al Reporte 1.
        """
        resultado = []
        i = 0
        while i < len(estructura.clases):
            clase = estructura.clases[i]
            if clase.en_choque:
                resultado.append({
                    'clase': clase,
                    'sugerencias': self.sugerir_bloques_libres(estructura, clase),
                })
            i = i + 1
        return resultado
