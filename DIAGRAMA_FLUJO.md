# Diagrama de Flujo del Sistema

**Torneo de Sudoku — Numerix Academy**
Práctica 1 · Lenguajes Formales y de Programación · 2S2026

> Los diagramas están en formato Mermaid, que GitHub renderiza automáticamente
> al abrir este archivo. Para exportarlos como imagen puede usar
> [mermaid.live](https://mermaid.live) pegando el código de cada bloque.

---

## 1. Flujo general del programa

```mermaid
flowchart TD
    A([Inicio]) --> B[Crear las cuatro listas vacías:<br/>tableros, jugadores, intentos, calificados]
    B --> C[Mostrar menú con<br/>el indicador de estado]
    C --> D[/Leer la opción del usuario/]
    D --> E{Opción}

    E -->|1, 2, 3| F[Pedir la ruta del archivo]
    F --> G[Leer y validar el archivo]
    G --> H[Mostrar cargados<br/>y errores descartados]
    H --> I[Borrar la calificación anterior]
    I --> C

    E -->|4| J{¿Están cargadas<br/>las tres listas?}
    J -->|No| K[Mostrar aviso]
    K --> C
    J -->|Sí| L[Calificar cada intento]
    L --> M[Mostrar tabla de resultados]
    M --> C

    E -->|5 a 10| N{¿Ya se calificó?}
    N -->|No| O[Mostrar aviso]
    O --> C
    N -->|Sí| P[Calcular métricas]
    P --> Q[Escribir archivos HTML]
    Q --> R[Mostrar rutas generadas]
    R --> C

    E -->|11| S[Mostrar detalle<br/>de un intento]
    S --> C

    E -->|0| T([Fin])
    E -->|Otra| U[Opción no válida]
    U --> C
```

---

## 2. Lectura y procesamiento de un archivo `.lfp`

```mermaid
flowchart TD
    A([Inicio: ruta del archivo]) --> B[lista_objetos ← vacía<br/>lista_errores ← vacía]
    B --> C{¿Existe la ruta?}
    C -->|No| D[Agregar error<br/>'No se encontro el archivo']
    D --> Z([Retornar las dos listas])

    C -->|Sí| E[Abrir con with open<br/>y leer con readlines]
    E --> F{¿Quedan líneas<br/>por revisar?}

    F -->|No| Z

    F -->|Sí| G[Tomar la siguiente línea<br/>y quitarle los espacios]
    G --> H{¿La línea<br/>está vacía?}
    H -->|Sí| F
    H -->|No| I[partes ← texto.split de coma]
    I --> J{¿Cantidad de<br/>campos correcta?}
    J -->|No| K[Agregar mensaje<br/>a lista_errores]
    K --> F
    J -->|Sí| L{¿Los tipos de dato<br/>son válidos?}
    L -->|No| K
    L -->|Sí| M{¿La dificultad o<br/>el nivel son válidos?}
    M -->|No| K
    M -->|Sí| N{¿La cadena tiene<br/>81 dígitos?}
    N -->|No| K
    N -->|Sí| O{¿El identificador<br/>está repetido?}
    O -->|Sí| K
    O -->|No| P[Crear el objeto<br/>y agregarlo a lista_objetos]
    P --> F
```

---

## 3. Validación matricial de un intento

```mermaid
flowchart TD
    A([Inicio: tablero + intento]) --> B[filas ← 0<br/>columnas ← 0<br/>cajas ← 0]

    B --> C[numero ← 0]
    C --> D{numero < 9?}
    D -->|Sí| E[Sacar la fila número<br/>con obtener_fila]
    E --> F{¿unidad_es_valida?}
    F -->|Sí| G[filas ← filas + 1]
    F -->|No| H[numero ← numero + 1]
    G --> H
    H --> D
    D -->|No| I[Repetir lo mismo<br/>para las 9 columnas]
    I --> J[Repetir lo mismo<br/>para las 9 cajas]

    J --> K[Recorrer las 81 celdas<br/>buscando pistas modificadas]
    K --> L{¿La lista de celdas<br/>modificadas está vacía?}
    L -->|Sí| M[pistas_respetadas ← Verdadero]
    L -->|No| N[pistas_respetadas ← Falso]

    M --> O[unidades ← filas + columnas + cajas<br/>porcentaje ← unidades / 27 × 100]
    N --> O
    O --> P{¿porcentaje = 100<br/>Y pistas respetadas?}
    P -->|Sí| Q[resuelto ← Verdadero]
    P -->|No| R[resuelto ← Falso]
    Q --> S[Guardar los resultados<br/>dentro del objeto Intento]
    R --> S
    S --> T([Fin])
```

---

## 4. Verificación de una unidad (fila, columna o caja)

```mermaid
flowchart TD
    A([Inicio: lista de 9 valores]) --> B[numero_buscado ← 1]
    B --> C{numero_buscado<br/>menor o igual a 9?}

    C -->|No| D([Retornar Verdadero:<br/>la unidad es válida])

    C -->|Sí| E[veces_que_aparece ← 0]
    E --> F[Recorrer los 9 valores<br/>de la lista]
    F --> G{¿El valor es igual a<br/>numero_buscado?}
    G -->|Sí| H[veces ← veces + 1]
    G -->|No| I{¿Quedan valores<br/>por revisar?}
    H --> I
    I -->|Sí| F
    I -->|No| J{¿veces es<br/>exactamente 1?}
    J -->|No| K([Retornar Falso:<br/>repetido, faltante o cero])
    J -->|Sí| L[numero_buscado ← numero_buscado + 1]
    L --> C
```

---

## 5. Cálculo de métricas y generación de un reporte

```mermaid
flowchart TD
    A([Inicio: opción de reporte]) --> B{¿La lista de intentos<br/>calificados está vacía?}
    B -->|Sí| C[Mostrar aviso<br/>y regresar al menú]
    C --> Z([Fin])

    B -->|No| D[Agrupar los intentos<br/>según el reporte pedido]
    D --> E[Juntar tiempos y porcentajes<br/>en listas aparte]
    E --> F[Contar cuántos intentos<br/>quedaron resueltos]
    F --> G{¿La lista<br/>está vacía?}
    G -->|Sí| H[Promedio ← 0<br/>evitar división entre cero]
    G -->|No| I[Promedio ← suma / cantidad<br/>Tasa ← resueltos / total × 100]
    H --> J[Ordenar los datos<br/>con el método de la burbuja]
    I --> J
    J --> K[Armar las filas de la tabla<br/>concatenando etiquetas HTML]
    K --> L[Envolver en la estructura<br/>basica de una pagina HTML]
    L --> M{¿Existe la<br/>carpeta reportes?}
    M -->|No| N[Crearla con makedirs]
    M -->|Sí| O[Escribir el archivo .html<br/>en UTF-8]
    N --> O
    O --> P[Mostrar la ruta<br/>al usuario]
    P --> Y([Fin])
```

---

## 6. Método de ordenamiento burbuja

```mermaid
flowchart TD
    A([Inicio: lista de datos]) --> B[cantidad ← largo de la lista]
    B --> C[vuelta ← 0]
    C --> D{vuelta < cantidad?}

    D -->|No| K([Fin: lista ordenada])

    D -->|Sí| E[posicion ← 0]
    E --> F{posicion menor que<br/>cantidad - 1 - vuelta?}

    F -->|No| G[vuelta ← vuelta + 1]
    G --> D

    F -->|Sí| H[actual ← lista posicion<br/>siguiente ← lista posicion+1]
    H --> I{¿Están en el<br/>orden equivocado?}
    I -->|Sí| J[Intercambiar los dos<br/>elementos de lugar]
    I -->|No| L[posicion ← posicion + 1]
    J --> L
    L --> F
```

---

## 7. Simbología utilizada

| Símbolo | Significado |
|---|---|
| Óvalo | Inicio o fin del proceso |
| Rectángulo | Proceso o acción |
| Rombo | Decisión (bifurcación condicional) |
| Paralelogramo | Entrada o salida de datos |
| Flecha | Sentido del flujo |
