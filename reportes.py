"""

Aqui se calculan las estadisticas y se generan los archivos HTML.

Los reportes usan solamente etiquetas de HTML: titulos (h1),
parrafos (p) y tablas (table, tr, th, td).
"""

import os

from validacion import buscar_jugador, buscar_tablero



# Funciones de calculo


def calcular_promedio(lista_de_numeros):
    """
    Suma todos los numeros de la lista y divide entre cuantos hay.

    Si la lista esta vacia devolvemos 0, porque dividir entre 0
    hace que de error
    """
    if len(lista_de_numeros) == 0:
        return 0

    suma = 0

    for numero in lista_de_numeros:
        suma = suma + numero

    promedio = suma / len(lista_de_numeros)
    return promedio


def calcular_tasa_de_exito(cantidad_resueltos, cantidad_total):
    """Calcula que porcentaje de los intentos quedo resuelto."""
    if cantidad_total == 0:
        return 0

    tasa = (cantidad_resueltos / cantidad_total) * 100
    return tasa


def formato_porcentaje(numero):
    """
    Convierte un numero a texto con dos decimales y el simbolo %.

    Se necesita porque round(50.0, 2) devuelve 50.0, y al convertirlo
    a texto queda "50.0" con un solo decimal. Aqui le agregamos los
    ceros que le falten para que siempre se vea "50.00%".
    """
    redondeado = round(numero, 2)
    texto = str(redondeado)

    partes = texto.split(".")
    parte_entera = partes[0]

    if len(partes) == 1:
        parte_decimal = ""
    else:
        parte_decimal = partes[1]

    while len(parte_decimal) < 2:
        parte_decimal = parte_decimal + "0"

    return parte_entera + "." + parte_decimal + "%"


def convertir_a_minutos(segundos):
    """
    Convierte una cantidad de segundos a un texto tipo 05:43

    Ejemplo con 343 segundos:
        minutos  = 343 // 60 = 5
        restante = 343 %  60 = 43
    """
    segundos_enteros = round(segundos)

    minutos = segundos_enteros // 60
    restante = segundos_enteros % 60

    texto_minutos = str(minutos)
    texto_segundos = str(restante)

    # Si queda de un solo digito le agregamos un cero adelante
    if len(texto_minutos) == 1:
        texto_minutos = "0" + texto_minutos
    if len(texto_segundos) == 1:
        texto_segundos = "0" + texto_segundos

    return texto_minutos + ":" + texto_segundos


def clasificar_dificultad_real(tasa_de_exito):
    """
    Calcula que tan dificil resulto el tablero segun cuantas veces
    los jugadores lograron resolverlo.
    """
    if tasa_de_exito >= 80:
        return "Facil"

    if tasa_de_exito >= 60:
        return "Media"

    if tasa_de_exito >= 40:
        return "Dificil"

    return "Experto"


# Armado del archivo HTML

def armar_documento_html(titulo, subtitulo, contenido):
    """
    Junta el titulo, el subtitulo y el contenido dentro de la
    estructura basica de una pagina HTML.

    Toda pagina HTML tiene la misma forma:
        <html>
          <head>   informacion de la pagina (titulo, codificacion)
          <body>   lo que se ve en la pantalla
    """
    documento = "<!DOCTYPE html>\n"
    documento = documento + "<html lang='es'>\n"
    documento = documento + "<head>\n"
    documento = documento + "<meta charset='UTF-8'>\n"
    documento = documento + "<title>" + titulo + "</title>\n"
    documento = documento + "</head>\n"
    documento = documento + "<body>\n"
    documento = documento + "<h1>" + titulo + "</h1>\n"
    documento = documento + "<p>Torneo de Sudoku - Numerix Academy</p>\n"
    documento = documento + "<p>" + subtitulo + "</p>\n"
    documento = documento + contenido
    documento = documento + "<hr>\n"
    documento = documento + "<p>Lenguajes Formales y de Programacion - Practica 1</p>\n"
    documento = documento + "</body>\n"
    documento = documento + "</html>"

    return documento


def armar_encabezado_tabla(lista_de_titulos):
    """
    Arma la primera fila de la tabla, la que lleva los nombres
    de las columnas. Se usa la etiqueta <th> en lugar de <td>
    porque asi el navegador la muestra en negrita.

    El atributo border='1' de la tabla dibuja las lineas de la
    cuadricula sin necesidad de CSS.
    """
    encabezado = "<table border='1'>\n<tr>"

    for titulo in lista_de_titulos:
        encabezado = encabezado + "<th>" + titulo + "</th>"

    encabezado = encabezado + "</tr>\n"
    return encabezado


def guardar_archivo_html(carpeta, nombre_archivo, contenido):
    """
    Guarda el texto en un archivo dentro de la carpeta indicada.
    Si la carpeta no existe, la crea.
    Devuelve la ruta completa del archivo creado.
    """
    if os.path.exists(carpeta) is False:
        os.makedirs(carpeta)

    ruta = os.path.join(carpeta, nombre_archivo)

    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)

    return ruta


# REPORTE 1: Resumen por Sudoku

def reporte_resumen_sudokus(lista_tableros, lista_jugadores, lista_intentos, carpeta):
    """
    Para cada tablero muestra: cuantos intentos recibio, cuantos se
    resolvieron, el tiempo promedio y la tasa de exito.
    """
    filas_html = ""

    for tablero in lista_tableros:

        # Buscamos los intentos que son de este tablero
        intentos_de_este_tablero = []

        for intento in lista_intentos:
            if intento.id_sudoku == tablero.id_sudoku:
                intentos_de_este_tablero.append(intento)

        # Juntamos los tiempos y los porcentajes en listas aparte
        tiempos = []
        porcentajes = []
        cantidad_resueltos = 0

        for intento in intentos_de_este_tablero:
            tiempos.append(intento.tiempo_segundos)
            porcentajes.append(intento.porcentaje_validez)

            if intento.resuelto_correctamente is True:
                cantidad_resueltos = cantidad_resueltos + 1

        cantidad_intentos = len(intentos_de_este_tablero)
        tiempo_promedio = calcular_promedio(tiempos)
        validez_promedio = calcular_promedio(porcentajes)
        tasa = calcular_tasa_de_exito(cantidad_resueltos, cantidad_intentos)

        if cantidad_intentos == 0:
            dificultad_real = "Sin datos"
        else:
            dificultad_real = clasificar_dificultad_real(tasa)

        # Armamos la fila de la tabla
        filas_html = filas_html + "<tr>"
        filas_html = filas_html + "<td>" + str(tablero.id_sudoku) + "</td>"
        filas_html = filas_html + "<td>" + tablero.dificultad + "</td>"
        filas_html = filas_html + "<td>" + dificultad_real + "</td>"
        filas_html = filas_html + "<td>" + str(tablero.contar_pistas()) + "</td>"
        filas_html = filas_html + "<td>" + str(cantidad_intentos) + "</td>"
        filas_html = filas_html + "<td>" + str(cantidad_resueltos) + "</td>"
        filas_html = filas_html + "<td>" + convertir_a_minutos(tiempo_promedio) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(validez_promedio) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(tasa) + "</td>"
        filas_html = filas_html + "</tr>\n"

    if len(lista_tableros) == 0:
        contenido = "<p>No hay tableros cargados.</p>\n"
    else:
        titulos = ["Sudoku", "Dificultad declarada", "Dificultad real", "Pistas",
                   "Intentos", "Resueltos", "Tiempo prom.", "Validez prom.",
                   "Tasa de exito"]
        contenido = armar_encabezado_tabla(titulos) + filas_html + "</table>\n"

    documento = armar_documento_html(
        "Reporte 1: Resumen por Sudoku",
        "Intentos recibidos, tiempo promedio y tasa de exito de cada tablero",
        contenido
    )

    return guardar_archivo_html(carpeta, "reporte_resumen_sudokus.html", documento)


# REPORTE 2: Rendimiento por Jugador

def ordenar_por_validez_de_mayor_a_menor(lista_de_datos):
    """
    Ordena una lista de diccionarios usando el metodo de la burbuja.

    se compara cada elemento con
    el siguiente. Si estan en el orden equivocado, se intercambian.
    Se repite el recorrido varias veces hasta que todo queda ordenado.
    """
    cantidad = len(lista_de_datos)

    for vuelta in range(cantidad):
        for posicion in range(cantidad - 1 - vuelta):

            actual = lista_de_datos[posicion]
            siguiente = lista_de_datos[posicion + 1]

            # Queremos el mayor primero, asi que intercambiamos
            # cuando el actual es menor que el siguiente
            if actual["validez_promedio"] < siguiente["validez_promedio"]:
                lista_de_datos[posicion] = siguiente
                lista_de_datos[posicion + 1] = actual


def reporte_rendimiento_jugadores(lista_tableros, lista_jugadores, lista_intentos, carpeta):
    """
    Para cada jugador muestra: cuantos tableros intento, su validez
    promedio, su tiempo promedio y cuantos resolvio perfectos.
    """
    datos_de_jugadores = []

    for jugador in lista_jugadores:

        # Buscamos los intentos de este jugador
        intentos_del_jugador = []

        for intento in lista_intentos:
            if intento.carnet == jugador.carnet:
                intentos_del_jugador.append(intento)

        tiempos = []
        porcentajes = []
        cantidad_perfectos = 0

        # Aqui guardamos los id de tablero que ya contamos,
        # para no contar dos veces el mismo tablero
        tableros_intentados = []
        tableros_perfectos = []

        for intento in intentos_del_jugador:
            tiempos.append(intento.tiempo_segundos)
            porcentajes.append(intento.porcentaje_validez)

            if intento.id_sudoku not in tableros_intentados:
                tableros_intentados.append(intento.id_sudoku)

            if intento.resuelto_correctamente is True:
                cantidad_perfectos = cantidad_perfectos + 1

                if intento.id_sudoku not in tableros_perfectos:
                    tableros_perfectos.append(intento.id_sudoku)

        total_intentos = len(intentos_del_jugador)

        datos = {}
        datos["nombre_completo"] = jugador.obtener_nombre_completo()
        datos["carnet"] = jugador.carnet
        datos["nivel"] = jugador.nivel
        datos["tableros_intentados"] = len(tableros_intentados)
        datos["total_intentos"] = total_intentos
        datos["validez_promedio"] = calcular_promedio(porcentajes)
        datos["tiempo_promedio"] = calcular_promedio(tiempos)
        datos["tableros_perfectos"] = len(tableros_perfectos)
        datos["tasa_exito"] = calcular_tasa_de_exito(cantidad_perfectos, total_intentos)

        datos_de_jugadores.append(datos)

    # Ordenamos del mejor al peor
    ordenar_por_validez_de_mayor_a_menor(datos_de_jugadores)

    filas_html = ""

    for datos in datos_de_jugadores:
        filas_html = filas_html + "<tr>"
        filas_html = filas_html + "<td>" + datos["nombre_completo"] + "</td>"
        filas_html = filas_html + "<td>" + str(datos["carnet"]) + "</td>"
        filas_html = filas_html + "<td>" + datos["nivel"] + "</td>"
        filas_html = filas_html + "<td>" + str(datos["tableros_intentados"]) + "</td>"
        filas_html = filas_html + "<td>" + str(datos["total_intentos"]) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(datos["validez_promedio"])
        filas_html = filas_html + "</td>"
        filas_html = filas_html + "<td>" + convertir_a_minutos(datos["tiempo_promedio"])
        filas_html = filas_html + "</td>"
        filas_html = filas_html + "<td>" + str(datos["tableros_perfectos"]) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(datos["tasa_exito"]) + "</td>"
        filas_html = filas_html + "</tr>\n"

    if len(datos_de_jugadores) == 0:
        contenido = "<p>No hay jugadores cargados.</p>\n"
    else:
        titulos = ["Jugador", "Carnet", "Nivel", "Tableros", "Intentos",
                   "Validez prom.", "Tiempo prom.", "Perfectos", "Tasa de exito"]
        contenido = armar_encabezado_tabla(titulos) + filas_html + "</table>\n"

    documento = armar_documento_html(
        "Reporte 2: Rendimiento por Jugador",
        "Validez promedio, tiempos y tableros resueltos perfectamente",
        contenido
    )

    return guardar_archivo_html(carpeta, "reporte_rendimiento_jugadores.html", documento)


# 
# REPORTE 3: Top 10 Mejores Tiempos
# 

def ordenar_intentos_por_tiempo(lista_intentos):
    """
    Ordena los intentos del tiempo mas bajo al mas alto,
    usando el metodo de la burbuja.
    """
    cantidad = len(lista_intentos)

    for vuelta in range(cantidad):
        for posicion in range(cantidad - 1 - vuelta):

            actual = lista_intentos[posicion]
            siguiente = lista_intentos[posicion + 1]

            # Queremos el menor primero, asi que intercambiamos
            # cuando el actual es mayor que el siguiente
            if actual.tiempo_segundos > siguiente.tiempo_segundos:
                lista_intentos[posicion] = siguiente
                lista_intentos[posicion + 1] = actual


def reporte_top_tiempos(lista_tableros, lista_jugadores, lista_intentos, carpeta):
    """
    Muestra los 10 mejores tiempos, pero solo entre los intentos
    que quedaron resueltos al 100%.
    """

    # Primero separamos unicamente los intentos resueltos
    intentos_resueltos = []

    for intento in lista_intentos:
        if intento.resuelto_correctamente is True:
            intentos_resueltos.append(intento)

    # Los ordenamos del mas rapido al mas lento
    ordenar_intentos_por_tiempo(intentos_resueltos)

    filas_html = ""
    posicion_en_la_tabla = 0

    for intento in intentos_resueltos:

        # Solo queremos los primeros 10
        if posicion_en_la_tabla >= 10:
            break

        posicion_en_la_tabla = posicion_en_la_tabla + 1

        jugador = buscar_jugador(lista_jugadores, intento.carnet)
        tablero = buscar_tablero(lista_tableros, intento.id_sudoku)

        if jugador is None:
            nombre = "Desconocido"
        else:
            nombre = jugador.obtener_nombre_completo()

        if tablero is None:
            dificultad = "No definida"
        else:
            dificultad = tablero.dificultad

        filas_html = filas_html + "<tr>"
        filas_html = filas_html + "<td>" + str(posicion_en_la_tabla) + "</td>"
        filas_html = filas_html + "<td>" + str(intento.carnet) + "</td>"
        filas_html = filas_html + "<td>" + nombre + "</td>"
        filas_html = filas_html + "<td>" + str(intento.id_sudoku) + "</td>"
        filas_html = filas_html + "<td>" + dificultad + "</td>"
        filas_html = filas_html + "<td>" + str(intento.tiempo_segundos) + "</td>"
        filas_html = filas_html + "<td>" + convertir_a_minutos(intento.tiempo_segundos)
        filas_html = filas_html + "</td>"
        filas_html = filas_html + "<td>" + intento.fecha + "</td>"
        filas_html = filas_html + "</tr>\n"

    if len(intentos_resueltos) == 0:
        contenido = "<p>Todavia no hay intentos resueltos al 100%.</p>\n"
    else:
        titulos = ["Posicion", "Carnet", "Jugador", "Sudoku", "Dificultad",
                   "Tiempo (segundos)", "Minutos", "Fecha"]
        contenido = armar_encabezado_tabla(titulos) + filas_html + "</table>\n"

    documento = armar_documento_html(
        "Reporte 3: Top 10 Mejores Tiempos",
        "Solo se toman en cuenta los intentos con 100% de validez",
        contenido
    )

    return guardar_archivo_html(carpeta, "reporte_top_tiempos.html", documento)



# REPORTE 4: Sudokus mas dificiles


def ordenar_por_tasa_de_menor_a_mayor(lista_de_datos):
    """
    Ordena una lista de diccionarios por la tasa de exito,
    de la mas baja a la mas alta. Metodo de la burbuja.
    """
    cantidad = len(lista_de_datos)

    for vuelta in range(cantidad):
        for posicion in range(cantidad - 1 - vuelta):

            actual = lista_de_datos[posicion]
            siguiente = lista_de_datos[posicion + 1]

            if actual["tasa_exito"] > siguiente["tasa_exito"]:
                lista_de_datos[posicion] = siguiente
                lista_de_datos[posicion + 1] = actual


def reporte_sudokus_dificiles(lista_tableros, lista_jugadores, lista_intentos, carpeta):
    """
    Muestra los tableros ordenados del mas dificil al mas facil,
    tomando en cuenta cuantas veces lograron resolverlo.
    """
    datos_de_tableros = []

    for tablero in lista_tableros:

        intentos_de_este_tablero = []

        for intento in lista_intentos:
            if intento.id_sudoku == tablero.id_sudoku:
                intentos_de_este_tablero.append(intento)

        # Los tableros sin intentos no se pueden clasificar
        if len(intentos_de_este_tablero) == 0:
            continue

        tiempos = []
        porcentajes = []
        cantidad_resueltos = 0

        for intento in intentos_de_este_tablero:
            tiempos.append(intento.tiempo_segundos)
            porcentajes.append(intento.porcentaje_validez)

            if intento.resuelto_correctamente is True:
                cantidad_resueltos = cantidad_resueltos + 1

        cantidad_intentos = len(intentos_de_este_tablero)
        tasa = calcular_tasa_de_exito(cantidad_resueltos, cantidad_intentos)

        datos = {}
        datos["id_sudoku"] = tablero.id_sudoku
        datos["dificultad"] = tablero.dificultad
        datos["dificultad_real"] = clasificar_dificultad_real(tasa)
        datos["cantidad_intentos"] = cantidad_intentos
        datos["tasa_exito"] = tasa
        datos["validez_promedio"] = calcular_promedio(porcentajes)
        datos["tiempo_promedio"] = calcular_promedio(tiempos)

        datos_de_tableros.append(datos)

    ordenar_por_tasa_de_menor_a_mayor(datos_de_tableros)

    filas_html = ""

    for datos in datos_de_tableros:

        if datos["dificultad"] == datos["dificultad_real"]:
            comparacion = "Coincide"
        else:
            comparacion = "Difiere"

        filas_html = filas_html + "<tr>"
        filas_html = filas_html + "<td>" + str(datos["id_sudoku"]) + "</td>"
        filas_html = filas_html + "<td>" + datos["dificultad"] + "</td>"
        filas_html = filas_html + "<td>" + datos["dificultad_real"] + "</td>"
        filas_html = filas_html + "<td>" + comparacion + "</td>"
        filas_html = filas_html + "<td>" + str(datos["cantidad_intentos"]) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(datos["tasa_exito"]) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(datos["validez_promedio"])
        filas_html = filas_html + "</td>"
        filas_html = filas_html + "<td>" + convertir_a_minutos(datos["tiempo_promedio"])
        filas_html = filas_html + "</td>"
        filas_html = filas_html + "</tr>\n"

    if len(datos_de_tableros) == 0:
        contenido = "<p>No hay intentos para clasificar los tableros.</p>\n"
    else:
        titulos = ["Sudoku", "Declarada", "Real", "Comparacion", "Intentos",
                   "Tasa de exito", "Validez prom.", "Tiempo prom."]
        contenido = armar_encabezado_tabla(titulos) + filas_html + "</table>\n"

    documento = armar_documento_html(
        "Reporte 4: Sudokus mas dificiles",
        "Tableros ordenados de menor a mayor tasa de exito",
        contenido
    )

    return guardar_archivo_html(carpeta, "reporte_sudokus_dificiles.html", documento)


# REPORTE 5: Analisis por nivel de jugador

def reporte_analisis_nivel(lista_tableros, lista_jugadores, lista_intentos, carpeta):
    """
    Agrupa a los jugadores por su nivel de experiencia y compara
    como le fue a cada grupo.
    """
    niveles = ["Principiante", "Intermedio", "Experto"]

    filas_html = ""

    for nivel in niveles:

        # Primero juntamos los carnets de los jugadores de este nivel
        carnets_del_nivel = []

        for jugador in lista_jugadores:
            if jugador.nivel == nivel:
                carnets_del_nivel.append(jugador.carnet)

        # Ahora buscamos los intentos que hicieron esos jugadores
        intentos_del_nivel = []

        for intento in lista_intentos:
            if intento.carnet in carnets_del_nivel:
                intentos_del_nivel.append(intento)

        tiempos = []
        porcentajes = []
        cantidad_resueltos = 0

        for intento in intentos_del_nivel:
            tiempos.append(intento.tiempo_segundos)
            porcentajes.append(intento.porcentaje_validez)

            if intento.resuelto_correctamente is True:
                cantidad_resueltos = cantidad_resueltos + 1

        cantidad_intentos = len(intentos_del_nivel)
        validez_promedio = calcular_promedio(porcentajes)
        tiempo_promedio = calcular_promedio(tiempos)
        tasa = calcular_tasa_de_exito(cantidad_resueltos, cantidad_intentos)

        filas_html = filas_html + "<tr>"
        filas_html = filas_html + "<td>" + nivel + "</td>"
        filas_html = filas_html + "<td>" + str(len(carnets_del_nivel)) + "</td>"
        filas_html = filas_html + "<td>" + str(cantidad_intentos) + "</td>"
        filas_html = filas_html + "<td>" + str(cantidad_resueltos) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(validez_promedio) + "</td>"
        filas_html = filas_html + "<td>" + convertir_a_minutos(tiempo_promedio) + "</td>"
        filas_html = filas_html + "<td>" + formato_porcentaje(tasa) + "</td>"
        filas_html = filas_html + "</tr>\n"

    titulos = ["Nivel", "Jugadores", "Intentos", "Resueltos",
               "Validez prom.", "Tiempo prom.", "Tasa de exito"]
    contenido = armar_encabezado_tabla(titulos) + filas_html + "</table>\n"

    documento = armar_documento_html(
        "Reporte 5: Analisis por nivel de jugador",
        "Comparacion del desempeno segun la categoria de experiencia",
        contenido
    )

    return guardar_archivo_html(carpeta, "reporte_analisis_nivel.html", documento)
