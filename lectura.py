"""
lectura.py
----------
Aqui se leen los tres archivos .lfp y se convierten en objetos.

Cada funcion de carga devuelve DOS listas:
  - una lista con los objetos que se pudieron crear
  - una lista con mensajes de error de las lineas que estaban mal escritas

De esa forma una linea mala no arruina todo el archivo: se descarta esa
linea y las demas si se cargan.
"""

import os

from clases import Intento, Jugador, Tablero


# ---------------------------------------------------------------------
# Funciones de apoyo para validar los datos
# ---------------------------------------------------------------------

def es_numero_entero(texto):
    """
    Devuelve True si el texto contiene solo digitos.
    El metodo isdigit() de las cadenas hace esa revision.
    """
    if texto == "":
        return False
    return texto.isdigit()


def dificultad_es_valida(dificultad):
    """Revisa que la dificultad sea una de las cuatro permitidas."""
    if dificultad == "Facil":
        return True
    if dificultad == "Media":
        return True
    if dificultad == "Dificil":
        return True
    if dificultad == "Experto":
        return True
    return False


def nivel_es_valido(nivel):
    """Revisa que el nivel sea uno de los tres permitidos."""
    if nivel == "Principiante":
        return True
    if nivel == "Intermedio":
        return True
    if nivel == "Experto":
        return True
    return False


def cadena_de_81_digitos(cadena):
    """
    Revisa que la cadena tenga exactamente 81 caracteres
    y que todos sean digitos.
    """
    if len(cadena) != 81:
        return False

    for caracter in cadena:
        if caracter.isdigit() is False:
            return False

    return True


def fecha_es_valida(fecha):
    """
    Revisa que la fecha tenga el formato DD-MM-AAAA.
    Ejemplo valido: 15-03-2026
    """
    partes = fecha.split("-")

    if len(partes) != 3:
        return False

    dia = partes[0]
    mes = partes[1]
    anio = partes[2]

    if es_numero_entero(dia) is False:
        return False
    if es_numero_entero(mes) is False:
        return False
    if es_numero_entero(anio) is False:
        return False

    if len(dia) != 2:
        return False
    if len(mes) != 2:
        return False
    if len(anio) != 4:
        return False

    numero_dia = int(dia)
    numero_mes = int(mes)

    if numero_dia < 1 or numero_dia > 31:
        return False
    if numero_mes < 1 or numero_mes > 12:
        return False

    return True


def existe_tablero_con_id(lista_tableros, id_sudoku):
    """Recorre la lista buscando un tablero con ese id."""
    for tablero in lista_tableros:
        if tablero.id_sudoku == id_sudoku:
            return True
    return False


def existe_jugador_con_carnet(lista_jugadores, carnet):
    """Recorre la lista buscando un jugador con ese carnet."""
    for jugador in lista_jugadores:
        if jugador.carnet == carnet:
            return True
    return False


def leer_lineas_del_archivo(ruta):
    """
    Abre el archivo y devuelve una lista con sus lineas.
    Si el archivo no existe, devuelve None.

    Se usa 'with open(...)' porque asi Python cierra el archivo
    automaticamente cuando termina de leerlo.
    """
    if os.path.exists(ruta) is False:
        return None

    with open(ruta, "r", encoding="utf-8") as archivo:
        lineas = archivo.readlines()

    return lineas


# ---------------------------------------------------------------------
# Carga del archivo de sudokus
# ---------------------------------------------------------------------

def cargar_sudokus(ruta):
    """
    Lee el archivo sudokus.lfp
    Formato de cada linea:  id_sudoku,dificultad,tablero
    """
    lista_tableros = []
    lista_errores = []

    lineas = leer_lineas_del_archivo(ruta)

    if lineas is None:
        lista_errores.append("No se encontro el archivo: " + ruta)
        return lista_tableros, lista_errores

    numero_linea = 0

    for linea in lineas:
        numero_linea = numero_linea + 1

        # strip() quita los espacios y el salto de linea del final
        texto = linea.strip()

        # Las lineas vacias se saltan
        if texto == "":
            continue

        # split(",") corta el texto cada vez que encuentra una coma
        # y devuelve una lista con los pedazos
        partes = texto.split(",")

        if len(partes) != 3:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": se esperaban 3 campos y hay "
                + str(len(partes))
            )
            continue

        texto_id = partes[0].strip()
        dificultad = partes[1].strip()
        cadena_tablero = partes[2].strip()

        if es_numero_entero(texto_id) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el id '" + texto_id
                + "' no es un numero entero"
            )
            continue

        id_sudoku = int(texto_id)

        if dificultad_es_valida(dificultad) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": la dificultad '" + dificultad
                + "' no es valida"
            )
            continue

        if cadena_de_81_digitos(cadena_tablero) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el tablero debe tener 81 digitos y tiene "
                + str(len(cadena_tablero))
            )
            continue

        if existe_tablero_con_id(lista_tableros, id_sudoku) is True:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el id " + str(id_sudoku)
                + " esta repetido"
            )
            continue

        # Si llegamos hasta aqui, la linea esta bien y creamos el objeto
        tablero = Tablero(id_sudoku, dificultad, cadena_tablero)
        lista_tableros.append(tablero)

    return lista_tableros, lista_errores



#  ---------------------------------- Carga del archivo de jugadores ----------------------------------


def cargar_jugadores(ruta):
    """
    Lee el archivo jugadores.lfp
    Formato de cada linea:  carnet,nombre,apellido,nivel
    """
    lista_jugadores = []
    lista_errores = []

    lineas = leer_lineas_del_archivo(ruta)

    if lineas is None:
        lista_errores.append("No se encontro el archivo: " + ruta)
        return lista_jugadores, lista_errores

    numero_linea = 0

    for linea in lineas:
        numero_linea = numero_linea + 1
        texto = linea.strip()

        if texto == "":
            continue

        partes = texto.split(",")

        if len(partes) != 4:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": se esperaban 4 campos y hay "
                + str(len(partes))
            )
            continue

        texto_carnet = partes[0].strip()
        nombre = partes[1].strip()
        apellido = partes[2].strip()
        nivel = partes[3].strip()

        if es_numero_entero(texto_carnet) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el carnet '" + texto_carnet
                + "' no es un numero entero"
            )
            continue

        carnet = int(texto_carnet)

        if nombre == "" or apellido == "":
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el nombre o el apellido estan vacios"
            )
            continue

        if nivel_es_valido(nivel) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el nivel '" + nivel + "' no es valido"
            )
            continue

        if existe_jugador_con_carnet(lista_jugadores, carnet) is True:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el carnet " + str(carnet)
                + " esta repetido"
            )
            continue

        jugador = Jugador(carnet, nombre, apellido, nivel)
        lista_jugadores.append(jugador)

    return lista_jugadores, lista_errores


# -------------------------------Carga del archivo de intentos--------------------------------------


def cargar_intentos(ruta):
    """
    Lee el archivo intentos.lfp
    Formato:  carnet,id_sudoku,solucion,tiempo_segundos,fecha
    """
    lista_intentos = []
    lista_errores = []

    lineas = leer_lineas_del_archivo(ruta)

    if lineas is None:
        lista_errores.append("No se encontro el archivo: " + ruta)
        return lista_intentos, lista_errores

    numero_linea = 0

    for linea in lineas:
        numero_linea = numero_linea + 1
        texto = linea.strip()

        if texto == "":
            continue

        partes = texto.split(",")

        if len(partes) != 5:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": se esperaban 5 campos y hay "
                + str(len(partes))
            )
            continue

        texto_carnet = partes[0].strip()
        texto_id = partes[1].strip()
        solucion = partes[2].strip()
        texto_tiempo = partes[3].strip()
        fecha = partes[4].strip()

        if es_numero_entero(texto_carnet) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el carnet '" + texto_carnet
                + "' no es un numero entero"
            )
            continue

        if es_numero_entero(texto_id) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el id de sudoku '" + texto_id
                + "' no es un numero entero"
            )
            continue

        if cadena_de_81_digitos(solucion) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": la solucion debe tener 81 digitos y tiene "
                + str(len(solucion))
            )
            continue

        if es_numero_entero(texto_tiempo) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": el tiempo '" + texto_tiempo
                + "' no es un numero entero"
            )
            continue

        if fecha_es_valida(fecha) is False:
            lista_errores.append(
                "Linea " + str(numero_linea) + ": la fecha '" + fecha
                + "' no tiene el formato DD-MM-AAAA"
            )
            continue

        carnet = int(texto_carnet)
        id_sudoku = int(texto_id)
        tiempo = int(texto_tiempo)

        intento = Intento(carnet, id_sudoku, solucion, tiempo, fecha)
        lista_intentos.append(intento)

    return lista_intentos, lista_errores
