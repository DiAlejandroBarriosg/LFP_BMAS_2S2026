"""

Programa principal del Torneo de Sudoku - Numerix Academy.

Este archivo muestra el menu y llama a las funciones de los otros
archivos segun la opcion que escoja el usuario.

"""

import os

import lectura
import reportes
import validacion

# ------------------------------Rutas de las carpetas---------------------------------

# __file__ es una variable que Python crea sola y guarda la ruta de
# este archivo. Con ella calculamos donde estan las carpetas del
# proyecto, sin importar desde donde se ejecute el programa.

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_ENTRADA = os.path.join(RUTA_BASE, "entrada")
CARPETA_REPORTES = os.path.join(RUTA_BASE, "reportes")


# --------------------------Funciones para mostrar cosas en pantalla--------------


def mostrar_titulo(texto):
    """Imprime un titulo entre lineas de signos igual."""
    print("")
    print("==========================================================")
    print(texto)
    print("==========================================================")


def mostrar_separador():
    print("----------------------------------------------------------")


def pausar():
    input("\nPresione ENTER para continuar...")


def pedir_ruta(nombre_archivo):
    """
    Le pide al usuario la ruta del archivo.
    Si solo presiona ENTER, se usa el archivo de la carpeta entrada.
    """
    ruta_por_defecto = os.path.join(CARPETA_ENTRADA, nombre_archivo)

    print("")
    print("Ruta por defecto: " + ruta_por_defecto)
    respuesta = input("Escriba la ruta del archivo (o ENTER para la ruta por defecto): ")
    respuesta = respuesta.strip()

    if respuesta == "":
        return ruta_por_defecto

    return respuesta


def mostrar_errores(lista_errores):
    """Muestra los errores encontrados durante la carga de un archivo."""
    if len(lista_errores) == 0:
        print("No se encontraron errores de formato.")
        return

    print("Registros descartados por formato incorrecto: " + str(len(lista_errores)))

    for mensaje in lista_errores:
        print("  - " + mensaje)


# Opcion 1: cargar el archivo de sudokus


def opcion_cargar_sudokus(lista_actual):
    """
    Carga el archivo de sudokus.
    Si algo sale mal, devuelve la lista que ya se tenia.
    """
    mostrar_titulo("CARGAR ARCHIVO DE SUDOKUS")

    ruta = pedir_ruta("sudokus.lfp")
    lista_tableros, lista_errores = lectura.cargar_sudokus(ruta)

    print("")
    print("Tableros cargados correctamente: " + str(len(lista_tableros)))
    mostrar_errores(lista_errores)

    if len(lista_tableros) == 0:
        return lista_actual

    mostrar_separador()
    print("Tableros disponibles:")

    for tablero in lista_tableros:
        print("  Sudoku #" + str(tablero.id_sudoku)
              + " (" + tablero.dificultad + ") - "
              + str(tablero.contar_pistas()) + " pistas")

    return lista_tableros


# Opcion 2: cargar el archivo de jugadores

def opcion_cargar_jugadores(lista_actual):
    mostrar_titulo("CARGAR ARCHIVO DE JUGADORES")

    ruta = pedir_ruta("jugadores.lfp")
    lista_jugadores, lista_errores = lectura.cargar_jugadores(ruta)

    print("")
    print("Jugadores cargados correctamente: " + str(len(lista_jugadores)))
    mostrar_errores(lista_errores)

    if len(lista_jugadores) == 0:
        return lista_actual

    return lista_jugadores


# Opcion 3: cargar el archivo de intentos

def opcion_cargar_intentos(lista_actual):
    mostrar_titulo("CARGAR ARCHIVO DE INTENTOS")

    ruta = pedir_ruta("intentos.lfp")
    lista_intentos, lista_errores = lectura.cargar_intentos(ruta)

    print("")
    print("Intentos cargados correctamente: " + str(len(lista_intentos)))
    mostrar_errores(lista_errores)

    if len(lista_intentos) == 0:
        return lista_actual

    return lista_intentos


# Opcion 4: validar y calificar los intentos

def opcion_calificar(lista_tableros, lista_jugadores, lista_intentos):
    """
    Califica todos los intentos y devuelve la lista de los que si
    se pudieron calificar.

    Un intento no se puede calificar si apunta a un carnet o a un
    id de sudoku que no existe en los otros archivos.
    """
    mostrar_titulo("VALIDAR Y CALIFICAR INTENTOS")

    if len(lista_tableros) == 0 or len(lista_jugadores) == 0 or len(lista_intentos) == 0:
        print("")
        print("AVISO: primero debe cargar los tres archivos.")
        print("  Sudokus: " + str(len(lista_tableros))
              + " | Jugadores: " + str(len(lista_jugadores))
              + " | Intentos: " + str(len(lista_intentos)))
        return []

    intentos_calificados = []
    intentos_sin_referencia = []

    for intento in lista_intentos:

        tablero = validacion.buscar_tablero(lista_tableros, intento.id_sudoku)
        jugador = validacion.buscar_jugador(lista_jugadores, intento.carnet)

        if tablero is None:
            intentos_sin_referencia.append(
                "Carnet " + str(intento.carnet)
                + ": no existe el sudoku " + str(intento.id_sudoku)
            )
            continue

        if jugador is None:
            intentos_sin_referencia.append(
                "Sudoku " + str(intento.id_sudoku)
                + ": no existe el carnet " + str(intento.carnet)
            )
            continue

        validacion.calificar_intento(tablero, intento)
        intentos_calificados.append(intento)

    # Contamos cuantos quedaron resueltos
    cantidad_resueltos = 0

    for intento in intentos_calificados:
        if intento.resuelto_correctamente is True:
            cantidad_resueltos = cantidad_resueltos + 1

    cantidad_con_error = len(intentos_calificados) - cantidad_resueltos

    print("")
    print("Intentos calificados: " + str(len(intentos_calificados)))
    print("Resueltos correctamente (100% de validez): " + str(cantidad_resueltos))
    print("Con al menos un error: " + str(cantidad_con_error))

    if len(intentos_sin_referencia) > 0:
        print("")
        print("Intentos descartados porque el carnet o el sudoku no existen: "
              + str(len(intentos_sin_referencia)))

        for mensaje in intentos_sin_referencia:
            print("  - " + mensaje)

    mostrar_separador()
    print("CARNET     SUDOKU  VALIDEZ   TIEMPO   RESULTADO")
    mostrar_separador()

    for intento in intentos_calificados:

        texto_carnet = str(intento.carnet)
        texto_sudoku = str(intento.id_sudoku)
        texto_validez = reportes.formato_porcentaje(intento.porcentaje_validez)
        texto_tiempo = str(intento.tiempo_segundos) + "s"

        # Rellenamos con espacios para que las columnas queden alineadas
        while len(texto_carnet) < 11:
            texto_carnet = texto_carnet + " "
        while len(texto_sudoku) < 8:
            texto_sudoku = texto_sudoku + " "
        while len(texto_validez) < 10:
            texto_validez = texto_validez + " "
        while len(texto_tiempo) < 9:
            texto_tiempo = texto_tiempo + " "

        print(texto_carnet + texto_sudoku + texto_validez
              + texto_tiempo + intento.observacion)

    return intentos_calificados


# Opciones 5 a 10: generar los reportes


def opcion_generar_reporte(numero_reporte, lista_tableros, lista_jugadores,
                           intentos_calificados):
    """
    Genera el reporte que corresponda al numero recibido.
    Antes revisa que ya se hayan calificado los intentos.
    """
    if len(intentos_calificados) == 0:
        print("")
        print("AVISO: primero debe ejecutar la opcion 4 para calificar los intentos.")
        return

    if numero_reporte == 1:
        mostrar_titulo("REPORTE 1: RESUMEN POR SUDOKU")
        ruta = reportes.reporte_resumen_sudokus(
            lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES)

    elif numero_reporte == 2:
        mostrar_titulo("REPORTE 2: RENDIMIENTO POR JUGADOR")
        ruta = reportes.reporte_rendimiento_jugadores(
            lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES)

    elif numero_reporte == 3:
        mostrar_titulo("REPORTE 3: TOP 10 MEJORES TIEMPOS")
        ruta = reportes.reporte_top_tiempos(
            lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES)

    elif numero_reporte == 4:
        mostrar_titulo("REPORTE 4: SUDOKUS MAS DIFICILES")
        ruta = reportes.reporte_sudokus_dificiles(
            lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES)

    else:
        mostrar_titulo("REPORTE 5: ANALISIS POR NIVEL")
        ruta = reportes.reporte_analisis_nivel(
            lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES)

    print("")
    print("Reporte generado correctamente:")
    print("  " + ruta)


def opcion_generar_todos(lista_tableros, lista_jugadores, intentos_calificados):
    """Genera los cinco reportes, uno tras otro."""
    mostrar_titulo("GENERAR TODOS LOS REPORTES")

    if len(intentos_calificados) == 0:
        print("")
        print("AVISO: primero debe ejecutar la opcion 4 para calificar los intentos.")
        return

    rutas = []

    rutas.append(reportes.reporte_resumen_sudokus(
        lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES))
    rutas.append(reportes.reporte_rendimiento_jugadores(
        lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES))
    rutas.append(reportes.reporte_top_tiempos(
        lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES))
    rutas.append(reportes.reporte_sudokus_dificiles(
        lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES))
    rutas.append(reportes.reporte_analisis_nivel(
        lista_tableros, lista_jugadores, intentos_calificados, CARPETA_REPORTES))

    print("")
    print("Se generaron " + str(len(rutas)) + " reportes:")

    for ruta in rutas:
        print("  - " + ruta)


# Opcion 11: ver el detalle de un intento

def opcion_ver_detalle(lista_tableros, lista_jugadores, intentos_calificados):
    """Muestra toda la informacion de un intento en particular."""
    mostrar_titulo("DETALLE DE UN INTENTO")

    if len(intentos_calificados) == 0:
        print("")
        print("AVISO: primero debe ejecutar la opcion 4 para calificar los intentos.")
        return

    numero = 0

    for intento in intentos_calificados:
        numero = numero + 1
        jugador = validacion.buscar_jugador(lista_jugadores, intento.carnet)

        print("  " + str(numero) + ". " + jugador.obtener_nombre_completo()
              + " - Sudoku #" + str(intento.id_sudoku)
              + " (" + reportes.formato_porcentaje(intento.porcentaje_validez) + ")")

    print("")
    respuesta = input("Numero del intento que quiere revisar (0 para regresar): ")
    respuesta = respuesta.strip()

    if respuesta.isdigit() is False:
        print("")
        print("AVISO: debe escribir un numero.")
        return

    elegido = int(respuesta)

    if elegido == 0:
        return

    if elegido < 1 or elegido > len(intentos_calificados):
        print("")
        print("AVISO: ese numero no esta en la lista.")
        return

    # Restamos 1 porque las listas empiezan en la posicion 0
    intento = intentos_calificados[elegido - 1]
    tablero = validacion.buscar_tablero(lista_tableros, intento.id_sudoku)
    jugador = validacion.buscar_jugador(lista_jugadores, intento.carnet)

    mostrar_separador()
    print("Jugador : " + jugador.obtener_nombre_completo()
          + " (" + jugador.nivel + ") - " + str(jugador.carnet))
    print("Tablero : #" + str(tablero.id_sudoku) + " - " + tablero.dificultad
          + " - " + str(tablero.contar_pistas()) + " pistas")
    print("Fecha   : " + intento.fecha + "    Tiempo: "
          + str(intento.tiempo_segundos) + " s")
    mostrar_separador()
    print("Filas validas    : " + str(intento.filas_validas) + "/9")
    print("Columnas validas : " + str(intento.columnas_validas) + "/9")
    print("Cajas validas    : " + str(intento.cajas_validas) + "/9")
    print("Validez total    : "
          + reportes.formato_porcentaje(intento.porcentaje_validez)
          + " (" + str(intento.contar_unidades_validas()) + " de 27 unidades)")

    if intento.pistas_respetadas is True:
        print("Pistas respetadas: Si")
    else:
        print("Pistas respetadas: No")

        texto_celdas = ""

        for celda in intento.celdas_modificadas:
            numero_fila = celda[0]
            numero_columna = celda[1]

            # Le sumamos 1 a cada uno para que el usuario vea
            # las filas y columnas numeradas del 1 al 9
            if texto_celdas != "":
                texto_celdas = texto_celdas + ", "

            texto_celdas = (texto_celdas + "(" + str(numero_fila + 1)
                            + "," + str(numero_columna + 1) + ")")

        print("Celdas cambiadas : " + texto_celdas)

    print("Resultado        : " + intento.observacion)
    mostrar_separador()
    print("Tablero original:")
    print(tablero.dibujar())


# Menu principal

def mostrar_menu(lista_tableros, lista_jugadores, lista_intentos, intentos_calificados):
    """Imprime el menu junto con el estado actual de los datos."""

    if len(intentos_calificados) > 0:
        texto_calificado = "Si"
    else:
        texto_calificado = "No"

    print("")
    print("==========================================================")
    print("           TORNEO DE SUDOKU - NUMERIX ACADEMY")
    print("==========================================================")
    print("Sudokus: " + str(len(lista_tableros))
          + " | Jugadores: " + str(len(lista_jugadores))
          + " | Intentos: " + str(len(lista_intentos))
          + " | Calificados: " + texto_calificado)
    print("==========================================================")
    print(" 1. Cargar archivo de sudokus")
    print(" 2. Cargar archivo de jugadores")
    print(" 3. Cargar archivo de intentos")
    print(" 4. Validar y calificar intentos")
    print(" 5. Generar Reporte: Resumen por Sudoku")
    print(" 6. Generar Reporte: Rendimiento por Jugador")
    print(" 7. Generar Reporte: Top 10 Mejores Tiempos")
    print(" 8. Generar Reporte: Sudokus mas dificiles")
    print(" 9. Generar Reporte: Analisis por nivel")
    print("10. Generar todos los reportes")
    print("11. Ver detalle de un intento")
    print(" 0. Salir")
    print("==========================================================")


def main():
    """
    Funcion principal. Aqui se guardan las cuatro listas del programa
    se repite el menu hasta que el usuario escoge salir.
    """
    lista_tableros = []
    lista_jugadores = []
    lista_intentos = []
    intentos_calificados = []

    while True:

        mostrar_menu(lista_tableros, lista_jugadores, lista_intentos, intentos_calificados)
        opcion = input("Seleccione una opcion: ")
        opcion = opcion.strip()

        if opcion == "1":
            lista_tableros = opcion_cargar_sudokus(lista_tableros)
            intentos_calificados = []

        elif opcion == "2":
            lista_jugadores = opcion_cargar_jugadores(lista_jugadores)
            intentos_calificados = []

        elif opcion == "3":
            lista_intentos = opcion_cargar_intentos(lista_intentos)
            intentos_calificados = []

        elif opcion == "4":
            intentos_calificados = opcion_calificar(
                lista_tableros, lista_jugadores, lista_intentos)

        elif opcion == "5":
            opcion_generar_reporte(1, lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "6":
            opcion_generar_reporte(2, lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "7":
            opcion_generar_reporte(3, lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "8":
            opcion_generar_reporte(4, lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "9":
            opcion_generar_reporte(5, lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "10":
            opcion_generar_todos(lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "11":
            opcion_ver_detalle(lista_tableros, lista_jugadores, intentos_calificados)

        elif opcion == "0":
            mostrar_titulo("GRACIAS POR USAR EL SISTEMA")
            print("Programa finalizado.")
            break

        else:
            print("")
            print("AVISO: esa opcion no existe. Escriba un numero del menu.")

        if opcion != "0":
            pausar()


# Esta linea hace que main() se ejecute solo cuando corremos

if __name__ == "__main__":
    main()
