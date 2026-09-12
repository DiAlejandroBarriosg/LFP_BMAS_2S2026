"""
Aqui se definen las tres clases del programa: Tablero, Jugador e Intento.

Tambien esta la funcion que convierte una cadena de 81 caracteres en una
matriz de 9 filas por 9 columnas.
"""


def convertir_cadena_a_matriz(cadena):
    """
    Recibe una cadena de 81 digitos y devuelve una matriz de 9x9.

    Una matriz es una lista que contiene otras listas. Cada lista de adentro
    es una fila del tablero.

    La cadena viene asi:  "307026050040310269..."
    y se lee de izquierda a derecha, fila por fila.

    Para saber que caracter le toca a cada celda usamos esta cuenta:
        posicion = numero_fila * 9 + numero_columna

    Por ejemplo, la celda de la fila 2, columna 3:
        posicion = 2 * 9 + 3 = 21   ->  el caracter 21 de la cadena
    """
    matriz = []

    for numero_fila in range(9):
        fila = []

        for numero_columna in range(9):
            posicion = numero_fila * 9 + numero_columna
            caracter = cadena[posicion]
            numero = int(caracter)
            fila.append(numero)

        matriz.append(fila)

    return matriz


class Tablero:
    """
    Representa un tablero de Sudoku

    Las celdas que ya vienen con un numero se llaman PISTAS.
    Las celdas vacias se guardan como 0.
    """

    def __init__(self, id_sudoku, dificultad, cadena):
        """
        self significa "este objeto". Cada tablero que creemos tendra
        su propio id_sudoku, su propia dificultad y su propia matriz.
        """
        self.id_sudoku = id_sudoku
        self.dificultad = dificultad
        self.cadena = cadena
        self.matriz = convertir_cadena_a_matriz(cadena)

    def contar_pistas(self):
        """
        Cuenta cuantas celdas del tablero ya traen un numero.
        Recorre las 81 celdas una por una y suma 1 cada vez que
        encuentra una celda distinta de 0.
        """
        contador = 0

        for numero_fila in range(9):
            for numero_columna in range(9):
                valor = self.matriz[numero_fila][numero_columna]
                if valor != 0:
                    contador = contador + 1

        return contador

    def dibujar(self):
        """
        Devuelve el tablero como texto, para mostrarlo en la consola.
        Las celdas vacias se dibujan con un punto.
        """
        texto = ""

        for numero_fila in range(9):

            # Cada 3 filas se dibuja una linea horizontal
            if numero_fila == 0 or numero_fila == 3 or numero_fila == 6:
                texto = texto + "+-------+-------+-------+\n"

            for numero_columna in range(9):

                # Cada 3 columnas se dibuja una barra vertical
                if numero_columna == 0 or numero_columna == 3 or numero_columna == 6:
                    texto = texto + "| "

                valor = self.matriz[numero_fila][numero_columna]

                if valor == 0:
                    texto = texto + ". "
                else:
                    texto = texto + str(valor) + " "

            texto = texto + "|\n"

        texto = texto + "+-------+-------+-------+"
        return texto


class Jugador:
    """Representa a un estudiante inscrito en el torneo."""

    def __init__(self, carnet, nombre, apellido, nivel):
        self.carnet = carnet
        self.nombre = nombre
        self.apellido = apellido
        self.nivel = nivel

    def obtener_nombre_completo(self):
        """Une el nombre y el apellido con un espacio en medio."""
        return self.nombre + " " + self.apellido


class Intento:
    """
    Representa la solucion que un jugador envio para un tablero.

    Este objeto guarda dos tipos de datos:
      1. Los datos que venian en el archivo (carnet, solucion, tiempo...)
      2. Los resultados de la calificacion, que empiezan vacios y se llenan
         cuando el programa ejecuta la validacion.
    """

    def __init__(self, carnet, id_sudoku, solucion, tiempo_segundos, fecha):
        # --- Datos que vienen del archivo ---
        self.carnet = carnet
        self.id_sudoku = id_sudoku
        self.solucion = solucion
        self.tiempo_segundos = tiempo_segundos
        self.fecha = fecha
        self.matriz = convertir_cadena_a_matriz(solucion)

        # --- Resultados de la calificacion (todavia vacios) ---
        self.filas_validas = 0
        self.columnas_validas = 0
        self.cajas_validas = 0
        self.porcentaje_validez = 0.0
        self.pistas_respetadas = True
        self.celdas_modificadas = []
        self.resuelto_correctamente = False
        self.observacion = "Sin calificar"

    def contar_unidades_validas(self):
        """Suma las filas, columnas y cajas que quedaron correctas."""
        return self.filas_validas + self.columnas_validas + self.cajas_validas
