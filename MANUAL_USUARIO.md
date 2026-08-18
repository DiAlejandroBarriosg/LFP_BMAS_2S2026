# Manual de Usuario

**Torneo de Sudoku — Numerix Academy**
Práctica 1 · Lenguajes Formales y de Programación · 2S2026

---

## 1. ¿Qué hace este programa?

Es un sistema de consola que califica automáticamente los intentos de resolución
de Sudoku enviados por los jugadores de un torneo. El programa:

- Lee los tableros, los jugadores y los intentos desde archivos de texto
- Revisa si cada intento cumple las reglas del Sudoku
- Calcula estadísticas de desempeño
- Genera reportes en HTML que se abren en cualquier navegador

---

## 2. Requisitos previos

- **Python 3.8 o superior** instalado. Para verificarlo, abra una terminal y
  escriba `python --version`. Si el sistema no reconoce el comando, descargue
  Python desde [python.org](https://www.python.org/downloads/) y durante la
  instalación marque la casilla **"Add Python to PATH"**.
- Un navegador web para ver los reportes.
- No se requiere instalar ninguna librería adicional.

---

## 3. Instalación

1. Descargue o clone el repositorio.
2. Descomprima el proyecto en la carpeta que prefiera.
3. Verifique que la estructura sea la siguiente, con los cinco archivos `.py`
   juntos en la carpeta principal:

```
Practica1/
├── main.py
├── clases.py
├── lectura.py
├── validacion.py
├── reportes.py
├── entrada/
│   ├── sudokus.lfp
│   ├── jugadores.lfp
│   └── intentos.lfp
└── reportes/
```

> **Importante:** los cinco archivos `.py` deben estar en la misma carpeta. Si
> los separa, el programa mostrará un error del tipo
> `ModuleNotFoundError: No module named 'lectura'`.

---

## 4. Cómo ejecutar el programa

Abra una terminal, ubíquese en la carpeta del proyecto y ejecute:

```bash
cd Practica1
python main.py
```

En Windows, si `python` no funciona, pruebe con `py main.py`.

Desde Visual Studio Code: `Archivo > Abrir carpeta...`, seleccione la carpeta
**`Practica1`**, abra la terminal integrada con `` Ctrl + ` `` y ejecute el
mismo comando.

---

## 5. El menú principal

Al iniciar aparece la pantalla principal:

```
==========================================================
           TORNEO DE SUDOKU - NUMERIX ACADEMY
==========================================================
Sudokus: 0 | Jugadores: 0 | Intentos: 0 | Calificados: No
==========================================================
 1. Cargar archivo de sudokus
 2. Cargar archivo de jugadores
 3. Cargar archivo de intentos
 4. Validar y calificar intentos
 5. Generar Reporte: Resumen por Sudoku
 6. Generar Reporte: Rendimiento por Jugador
 7. Generar Reporte: Top 10 Mejores Tiempos
 8. Generar Reporte: Sudokus mas dificiles
 9. Generar Reporte: Analisis por nivel
10. Generar todos los reportes
11. Ver detalle de un intento
 0. Salir
==========================================================
Seleccione una opcion:
```

La línea debajo del título es el **indicador de estado**: muestra en todo momento
cuántos registros hay cargados y si ya se ejecutó la calificación. Sirve para
saber en qué punto del proceso se encuentra.

Para elegir una opción, escriba el número y presione **ENTER**.

> **Orden recomendado:** 1 → 2 → 3 → 4 → 10

---

## 6. Paso a paso

### Paso 1 · Cargar el archivo de sudokus

Seleccione la opción **1**. El programa le propone una ruta por defecto:

```
==========================================================
CARGAR ARCHIVO DE SUDOKUS
==========================================================

Ruta por defecto: C:\...\Practica1\entrada\sudokus.lfp
Escriba la ruta del archivo (o ENTER para la ruta por defecto):
```

Presione **ENTER** para usar el archivo incluido, o escriba otra ruta si sus
archivos están en un lugar distinto. Resultado:

```
Tableros cargados correctamente: 8
No se encontraron errores de formato.
----------------------------------------------------------
Tableros disponibles:
  Sudoku #1 (Facil) - 41 pistas
  Sudoku #2 (Facil) - 39 pistas
  Sudoku #3 (Media) - 33 pistas
  Sudoku #4 (Media) - 31 pistas
  Sudoku #5 (Dificil) - 27 pistas
  Sudoku #6 (Dificil) - 25 pistas
  Sudoku #7 (Experto) - 23 pistas
  Sudoku #8 (Experto) - 21 pistas
```

Las **pistas** son las casillas que el tablero ya trae resueltas. Entre menos
pistas, más difícil es el tablero.

### Paso 2 · Cargar el archivo de jugadores

Seleccione la opción **2** y repita el procedimiento. Si algún registro tiene un
error, el programa lo informa sin detener la carga:

```
Jugadores cargados correctamente: 10
Registros descartados por formato incorrecto: 2
  - Linea 11: el carnet '20201XXXX' no es un numero entero
  - Linea 12: el nivel 'Avanzado' no es valido
```

Los registros correctos sí se cargan; solo se descartan las líneas defectuosas.

### Paso 3 · Cargar el archivo de intentos

Seleccione la opción **3**:

```
Intentos cargados correctamente: 55
Registros descartados por formato incorrecto: 3
  - Linea 56: la solucion debe tener 81 digitos y tiene 5
  - Linea 57: el tiempo 'abc' no es un numero entero
  - Linea 58: la fecha '2026-03-16' no tiene el formato DD-MM-AAAA
```

### Paso 4 · Validar y calificar los intentos

Seleccione la opción **4**. Este es el paso central: aquí se aplican las reglas
del Sudoku a cada intento.

```
==========================================================
VALIDAR Y CALIFICAR INTENTOS
==========================================================

Intentos calificados: 53
Resueltos correctamente (100% de validez): 17
Con al menos un error: 36

Intentos descartados porque el carnet o el sudoku no existen: 2
  - Sudoku 3: no existe el carnet 202099999
  - Carnet 202011234: no existe el sudoku 99
----------------------------------------------------------
CARNET     SUDOKU  VALIDEZ   TIEMPO   RESULTADO
----------------------------------------------------------
202011234  1       100.00%   213s     Resuelto correctamente
202017890  1       88.89%    245s     Cambio 1 pista(s) del tablero original
202014567  1       100.00%   216s     Resuelto correctamente
202017890  2       66.67%    184s     Incompleto: 9 de 27 unidades con error
202012345  5       77.78%    478s     Incompleto: 6 de 27 unidades con error
```

**Cómo leer la columna VALIDEZ.** El programa revisa 27 unidades por tablero:
9 filas, 9 columnas y 9 cajas de 3×3. El porcentaje indica cuántas de esas 27
unidades quedaron correctas. Un intento con 100% tiene todo el tablero bien
resuelto.

**Cómo leer la columna RESULTADO:**

| Mensaje | Significado |
|---|---|
| `Resuelto correctamente` | El tablero está perfecto y se respetaron las pistas originales |
| `Cambio N pista(s) del tablero original` | El jugador modificó casillas que ya venían resueltas, así que el intento no es válido aunque el porcentaje sea alto |
| `Incompleto: N de 27 unidades con error` | Hay filas, columnas o cajas con números repetidos o faltantes |
| `Tablero valido pero no es el tablero que le tocaba` | El Sudoku está bien resuelto, pero no corresponde al tablero asignado |

> Si intenta calificar sin haber cargado los tres archivos, el programa se lo
> advierte y regresa al menú.

### Paso 5 · Generar los reportes

Puede generar los reportes uno por uno (opciones 5 a 9) o todos de una vez con
la opción **10**:

```
==========================================================
GENERAR TODOS LOS REPORTES
==========================================================

Se generaron 5 reportes:
  - C:\...\Practica1\reportes\reporte_resumen_sudokus.html
  - C:\...\Practica1\reportes\reporte_rendimiento_jugadores.html
  - C:\...\Practica1\reportes\reporte_top_tiempos.html
  - C:\...\Practica1\reportes\reporte_sudokus_dificiles.html
  - C:\...\Practica1\reportes\reporte_analisis_nivel.html
```

Para verlos, abra la carpeta `reportes` y haga doble clic sobre cualquier
archivo `.html`; se abrirá en su navegador.

> Los reportes solo se pueden generar después de ejecutar la opción 4. Si lo
> intenta antes, el programa se lo indica.

### Paso 6 · Salir

Seleccione la opción **0**.

---

## 7. Consultar el detalle de un intento (opción 11)

Esta opción permite revisar a fondo un intento específico. Primero muestra la
lista numerada de todos los intentos calificados:

```
  1. Diego Fuentes - Sudoku #1 (100.00%)
  2. Jorge Castillo - Sudoku #1 (88.89%)
  3. Maria Lopez - Sudoku #1 (100.00%)
  ...

Numero del intento que quiere revisar (0 para regresar):
```

Al escribir un número obtiene el desglose completo:

```
----------------------------------------------------------
Jugador : Jorge Castillo (Intermedio) - 202017890
Tablero : #1 - Facil - 41 pistas
Fecha   : 14-03-2026    Tiempo: 245 s
----------------------------------------------------------
Filas validas    : 8/9
Columnas validas : 8/9
Cajas validas    : 8/9
Validez total    : 88.89% (24 de 27 unidades)
Pistas respetadas: No
Celdas cambiadas : (1,1)
Resultado        : Cambio 1 pista(s) del tablero original
----------------------------------------------------------
Tablero original:
+-------+-------+-------+
| 3 . 7 | . 2 6 | . 5 . |
| . 4 . | 3 1 . | 2 6 9 |
| 9 2 6 | 8 4 5 | 1 7 3 |
+-------+-------+-------+
| . 6 3 | . 5 . | . 8 1 |
| . 5 9 | . 7 8 | . . 2 |
| . . . | 2 . . | . 9 . |
+-------+-------+-------+
| . 8 4 | 6 . . | . 2 . |
| . . . | . . 2 | . . 7 |
| . . . | . 8 4 | . . 6 |
+-------+-------+-------+
```

En el tablero, los puntos (`.`) son las casillas vacías que el jugador debía
completar. Las **celdas cambiadas** se muestran como pares (fila, columna)
contando desde 1, así que `(1,1)` es la esquina superior izquierda.

Escriba `0` para regresar al menú.

---

## 8. Los reportes generados

### Reporte 1 · Resumen por Sudoku

Una fila por tablero con: dificultad declarada, dificultad real observada,
cantidad de pistas, intentos recibidos, cuántos se resolvieron, tiempo promedio,
validez promedio y tasa de éxito.

La **dificultad real** la calcula el sistema según qué tan seguido lograron
resolverlo los jugadores, y puede no coincidir con la declarada por la
plataforma.

### Reporte 2 · Rendimiento por Jugador

Una fila por jugador, ordenada de mejor a peor desempeño: nombre, carnet, nivel,
tableros intentados, validez promedio, tiempo promedio y tableros resueltos
perfectamente.

### Reporte 3 · Top 10 Mejores Tiempos

Los diez tiempos más rápidos entre los intentos **resueltos al 100%**. Un tiempo
muy bajo con errores no aparece aquí: solo compiten los intentos correctos.

### Reporte 4 · Sudokus más difíciles

Los tableros ordenados de menor a mayor tasa de éxito, con una columna que
indica si la dificultad declarada coincide con la observada.

### Reporte 5 · Análisis por nivel

Compara el desempeño de los jugadores agrupados por categoría (Principiante,
Intermedio, Experto).

---

## 9. Formato de los archivos de entrada

Si desea usar sus propios archivos, deben respetar estos formatos. Cada línea es
un registro y los campos se separan con comas.

**`sudokus.lfp`**

```
id_sudoku,dificultad,tablero
```

Ejemplo:

```
1,Facil,307026050040310269926845173063050081059078002000200090084600020000002007000084006
```

- `dificultad`: `Facil`, `Media`, `Dificil` o `Experto`
- `tablero`: 81 dígitos leídos fila por fila; el `0` marca casilla vacía

**`jugadores.lfp`**

```
carnet,nombre,apellido,nivel
```

Ejemplo:

```
202011234,Diego,Fuentes,Intermedio
```

- `nivel`: `Principiante`, `Intermedio` o `Experto`

**`intentos.lfp`**

```
carnet,id_sudoku,solucion,tiempo_segundos,fecha
```

Ejemplo:

```
202011234,1,317926458845317269926845173263459781459178632178263594784631925631592847592784316,213,20-03-2026
```

- `solucion`: 81 dígitos del 1 al 9, en el mismo orden que el tablero
- `fecha`: formato `DD-MM-AAAA`

---

## 10. Solución de problemas frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'lectura'` | Los archivos `.py` no están en la misma carpeta | Descomprima el proyecto conservando la estructura original |
| `python no se reconoce como comando` | Python no está en el PATH | Reinstale Python marcando "Add Python to PATH", o use `py main.py` |
| `No se encontro el archivo` | La ruta escrita no existe | Presione ENTER para usar la ruta por defecto, o revise el nombre del archivo |
| `AVISO: primero debe cargar los tres archivos` | Falta cargar alguno de los archivos | Ejecute las opciones 1, 2 y 3 antes de la 4 |
| `AVISO: primero debe ejecutar la opcion 4` | Se pidió un reporte sin calificar | Ejecute la opción 4 y vuelva a intentarlo |
| Se descartan muchos registros | Los archivos tienen otro formato | Revise el número de campos y el formato de fecha según la sección 9 |
| Los reportes no se actualizan | Se generaron antes de recargar los datos | Vuelva a ejecutar la opción 4 y luego la 10 |
| El indicador dice `Calificados: No` después de cargar | Al cargar un archivo se borra la calificación anterior | Es el comportamiento esperado: vuelva a ejecutar la opción 4 |
