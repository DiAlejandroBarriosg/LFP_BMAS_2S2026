"""

revisar si un intento cumple las reglas del Sudoku.

Las reglas dicen que en cada FILA, en cada COLUMNA y en cada CAJA de 3x3
tienen que aparecer los numeros del 1 al 9, y ninguno se puede repetir.

Como hay 9 filas, 9 columnas y 9 cajas, en total se revisan 27 cosas.
A cada una de esas 27 cosas le llamamos UNIDAD.

El porcentaje de validez sale de:

    porcentaje = (unidades correctas / 27) * 100
"""


# Sacar una fila, una columna o una caja de la matriz

def obtener_fila(matriz, numero_fila):
    """
    Devuelve una lista con los 9 numeros de la fila indicada.
    numero_fila va de 0 a 8.
    """
    fila = []

    for numero_columna in range(9):
        valor = matriz[numero_fila][numero_columna]
        fila.append(valor)

    return fila


def obtener_columna(matriz, numero_columna):
    """
    Devuelve una lista con los 9 numeros de la columna indicada.
    numero_columna va de 0 a 8.

    Aqui la columna se queda fija y lo que cambia es la fila.
    """
    columna = []

    for numero_fila in range(9):
        valor = matriz[numero_fila][numero_columna]
        columna.append(valor)

    return columna


def obtener_caja(matriz, numero_caja):
    """
    Devuelve una lista con los 9 numeros de una caja de 3x3.

    Para saber donde empieza cada caja hacemos dos cuentas:

        fila_inicial    = (numero_caja // 3) * 3
        columna_inicial = (numero_caja % 3) * 3

    El simbolo // es division entera.
    El simbolo % es el residuo de la division.

        fila_inicial    = (5 // 3) * 3 = 1 * 3 = 3
        columna_inicial = (5 %  3) * 3 = 2 * 3 = 6
    Entonces la caja 5 empieza en la fila 3, columna 6.
    """
    fila_inicial = (numero_caja // 3) * 3
    columna_inicial = (numero_caja % 3) * 3

    caja = []

    for numero_fila in range(fila_inicial, fila_inicial + 3):
        for numero_columna in range(columna_inicial, columna_inicial + 3):
            valor = matriz[numero_fila][numero_columna]
            caja.append(valor)

    return caja


# Revisar si una unidad cumple la regla

def unidad_es_valida(valores):
    """
    Recibe una lista de 9 numeros (una fila, una columna o una caja)
    y dice si cumple la regla del Sudoku.

    La forma de revisarlo es por cada numero del 1 al 9,
    contamos cuantas veces aparece en la lista.
    Si alguno no aparece exactamente 1 vez, la unidad esta mala.

    """
    for numero_buscado in range(1, 10):

        veces_que_aparece = 0

        for valor in valores:
            if valor == numero_buscado:
                veces_que_aparece = veces_que_aparece + 1

        if veces_que_aparece != 1:
            return False

    return True


# Revisar que el jugador no haya cambiado las pistas

def buscar_pistas_modificadas(tablero, intento):
    """
    Devuelve una lista con las celdas donde el jugador cambio una pista.

    Cada celda encontrada se guarda como una lista de dos numeros:
    [numero_fila, numero_columna]
    """
    celdas_modificadas = []

    for numero_fila in range(9):
        for numero_columna in range(9):

            valor_original = tablero.matriz[numero_fila][numero_columna]
            valor_del_jugador = intento.matriz[numero_fila][numero_columna]

            # Solo revisamos las celdas que traian pista (distintas de 0)
            if valor_original != 0:
                if valor_del_jugador != valor_original:
                    celdas_modificadas.append([numero_fila, numero_columna])

    return celdas_modificadas


# Calificar un intento completo

def calificar_intento(tablero, intento):
    """
    Revisa un intento y guarda los resultados dentro del mismo objeto Intento.

    Pasos:
      1. Contar cuantas filas estan buenas
      2. Contar cuantas columnas estan buenas
      3. Contar cuantas cajas estan buenas
      4. Revisar si cambio alguna pista
      5. Calcular el porcentaje
      6. Decidir si el intento cuenta como resuelto
    """

    # --- Paso 1: revisar las 9 filas ---
    filas_buenas = 0

    for numero in range(9):
        fila = obtener_fila(intento.matriz, numero)
        if unidad_es_valida(fila) is True:
            filas_buenas = filas_buenas + 1

    # --- Paso 2: revisar las 9 columnas ---
    columnas_buenas = 0

    for numero in range(9):
        columna = obtener_columna(intento.matriz, numero)
        if unidad_es_valida(columna) is True:
            columnas_buenas = columnas_buenas + 1

    # --- Paso 3: revisar las 9 cajas ---
    cajas_buenas = 0

    for numero in range(9):
        caja = obtener_caja(intento.matriz, numero)
        if unidad_es_valida(caja) is True:
            cajas_buenas = cajas_buenas + 1

    # --- Paso 4: revisar las pistas del tablero original ---
    celdas_modificadas = buscar_pistas_modificadas(tablero, intento)

    if len(celdas_modificadas) == 0:
        pistas_respetadas = True
    else:
        pistas_respetadas = False

    # --- Paso 5: calcular el porcentaje de validez ---
    unidades_buenas = filas_buenas + columnas_buenas + cajas_buenas
    porcentaje = (unidades_buenas / 27) * 100

    # --- Paso 6: decidir si cuenta como resuelto ---
    # Tienen que cumplirse LAS DOS cosas:
    #   que el porcentaje sea 100 y que no haya tocado ninguna pista
    if porcentaje == 100 and pistas_respetadas is True:
        resuelto = True
    else:
        resuelto = False

    # --- Guardar todo dentro del objeto intento ---
    intento.filas_validas = filas_buenas
    intento.columnas_validas = columnas_buenas
    intento.cajas_validas = cajas_buenas
    intento.porcentaje_validez = porcentaje
    intento.celdas_modificadas = celdas_modificadas
    intento.pistas_respetadas = pistas_respetadas
    intento.resuelto_correctamente = resuelto
    intento.observacion = escribir_observacion(intento)


def escribir_observacion(intento):
    """
    Devuelve un texto corto que explica como le fue al intento.
    """
    if intento.resuelto_correctamente is True:
        return "Resuelto correctamente"

    if intento.pistas_respetadas is False:
        cantidad = len(intento.celdas_modificadas)
        return "Cambio " + str(cantidad) + " pista(s) del tablero original"

    if intento.porcentaje_validez == 100:
        return "Tablero valido pero no es el tablero que le tocaba"

    unidades_malas = 27 - intento.contar_unidades_validas()
    return "Incompleto: " + str(unidades_malas) + " de 27 unidades con error"


# Funciones para buscar dentro de las listas

def buscar_tablero(lista_tableros, id_sudoku):
    """
    Recorre la lista de tableros y devuelve el que tenga ese id.
    Si no lo encuentra devuelve None.
    """
    for tablero in lista_tableros:
        if tablero.id_sudoku == id_sudoku:
            return tablero

    return None


def buscar_jugador(lista_jugadores, carnet):
    """
    Recorre la lista de jugadores y devuelve el que tenga ese carnet.
    Si no lo encuentra devuelve None.
    """
    for jugador in lista_jugadores:
        if jugador.carnet == carnet:
            return jugador

    return None
