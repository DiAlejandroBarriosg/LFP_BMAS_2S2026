Torneo de Sudoku — Numerix Academy

Sistema de consola que califica automáticamente los intentos de resolución de Sudoku enviados por los jugadores de un torneo. Lee los datos desde archivos de texto delimitados por comas, verifica cada intento contra las reglas del Sudoku, calcula métricas de desempeño y genera reportes en HTML.

**Práctica 1 · Lenguajes Formales y de Programación · 2S2026**  
Universidad de San Carlos de Guatemala · Facultad de Ingeniería  
Escuela de Ingeniería en Ciencias y Sistemas



Características

- Lectura y validación de tres archivos `.lfp` (tableros, jugadores e intentos)
- Validación matricial completa: 9 filas, 9 columnas y 9 cajas de 3×3 por intento
- Verificación de que el jugador no haya modificado las pistas originales del tablero
- Cálculo del porcentaje de validez sobre las 27 unidades evaluadas
- Cinco reportes en HTML, generables por separado o todos a la vez


Requisitos

- Python 3.8 o superior
- Un navegador web para ver los reportes

No se requiere instalar ninguna librería adicional.


Instalación y ejecución

```bash
git clone https://github.com/usuario/repositorio.git
cd repositorio/Practica1
python main.py
```

En Windows, si `python` no es reconocido, use `py main.py`.

> **Importante:** los cinco archivos `.py` deben permanecer en la misma carpeta. Si se separan, el programa falla con `ModuleNotFoundError: No module named 'lectura'`.



Estructura del proyecto

```
Practica1/
├── main.py           Menú de consola y control del flujo
├── clases.py         Clases Tablero, Jugador e Intento
├── lectura.py        Lectura de archivos .lfp y validación de formato
├── validacion.py     Validación matricial del Sudoku
├── reportes.py       Cálculo de estadísticas y generación de HTML
├── entrada/          Archivos .lfp de entrada
│   ├── sudokus.lfp
│   ├── jugadores.lfp
│   └── intentos.lfp
└── reportes/         Salida .html generada
```

Las dependencias apuntan en una sola dirección: `clases.py` no importa nada del proyecto, `validacion.py` trabaja solo con objetos ya construidos, y `main.py` es el único que conoce a todos los módulos. Esto evita importaciones circulares y permite modificar los reportes sin tocar la validación.



Formato de los archivos de entrada

Los tres archivos usan la coma como separador de campos, un registro por línea.

**`sudokus.lfp`** — 3 campos

```
id_sudoku,dificultad,tablero_81_digitos
```

- `dificultad`: `Facil`, `Media`, `Dificil` o `Experto`
- `tablero`: exactamente 81 dígitos, donde `0` representa una celda vacía

**`jugadores.lfp`** — 4 campos

```
carnet,nombre,apellido,nivel
```

- `nivel`: `Principiante`, `Intermedio` o `Experto`

**`intentos.lfp`** — 5 campos

```
carnet,id_sudoku,solucion_81_digitos,tiempo_segundos,fecha
```

- `fecha`: formato `DD-MM-AAAA`

Las líneas con formato inválido se reportan individualmente y se descartan, sin interrumpir la lectura del resto del archivo.



Uso

Al iniciar aparece el menú principal con un indicador de estado que muestra cuántos registros hay cargados y si ya se ejecutó la calificación.

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
```

**Orden recomendado:** `1` → `2` → `3` → `4` → `10`

Las opciones de reporte requieren que la calificación (opción 4) se haya ejecutado antes. Los archivos `.html` se guardan en la carpeta `reportes/` y se abren en cualquier navegador.



Cómo funciona la validación

Cada intento se reconstruye como una matriz de 9×9 a partir de la cadena de 81 dígitos, usando la correspondencia:

```
posicion = numero_fila * 9 + numero_columna
```

De la matriz se extraen **27 unidades**: 9 filas, 9 columnas y 9 cajas de 3×3. Una unidad es válida cuando contiene los dígitos del 1 al 9 exactamente una vez cada uno. El porcentaje de validez es la proporción de unidades correctas sobre esas 27.

Adicionalmente se verifica que las pistas originales del tablero no hayan sido alteradas. Un intento se considera resuelto correctamente solo si las 27 unidades son válidas y las pistas fueron respetadas.

Al calificar también se comprueba la integridad referencial: que cada intento apunte a un carnet y a un `id_sudoku` que existan realmente. Esta verificación solo puede hacerse en ese momento, porque cruza información entre los tres archivos.



Clases

| Clase | Responsabilidad |
|---|---|
| `Tablero` | Tablero publicado en el torneo. Guarda la cadena original, construye la matriz, cuenta pistas y se dibuja como texto. |
| `Jugador` | Datos del participante: carnet, nombre, apellido y nivel. |
| `Intento` | Combina los datos leídos con los resultados de la calificación: unidades válidas, porcentaje, pistas respetadas y veredicto final. |



Documentación

| Documento | Contenido |
|---|---|
| `MANUAL_TECNICO` | Arquitectura, clases, algoritmos de validación, lectura de archivos, métricas y ordenamientos |
| `MANUAL_USUARIO` | Guía paso a paso de instalación, ejecución y uso del menú |
| `DIAGRAMA_FLUJO` | Diagramas de flujo de los procesos principales |
| `INFORME_DESARROLLO` | Decisiones de diseño y proceso de desarrollo |



Detalles de implementación

- **Programación orientada a objetos** con tres clases y métodos de instancia convencionales
- **Ordenamiento** implementado manualmente mediante el método burbuja, sin funciones de librería
- **Manejo de errores** por acumulación: las funciones de carga devuelven la lista de objetos válidos junto con la lista de mensajes de error, en lugar de lanzar excepciones
- **Reportes HTML** construidos por concatenación de cadenas




Autor

Diego Alejandro Barrios  
Universidad de San Carlos de Guatemala
