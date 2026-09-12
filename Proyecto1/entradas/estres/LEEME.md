# Archivos de estres

Estos archivos **no** son los casos de prueba del proyecto. Los casos de
prueba estan en `entradas/` y documentados en `docs/CASOS_DE_PRUEBA.md`.

Estos diez son entradas deliberadamente hostiles, escritas para verificar que
el programa **no se cae** ante archivos que un usuario real podria producir
por error. Ninguno lanza una excepcion: todos terminan el analisis y generan
los cuatro reportes.

| Archivo | Que prueba |
|---|---|
| `e01_vacio.hor` | Archivo de 0 bytes. |
| `e02_solo_espacios.hor` | Solo espacios, tabulaciones y saltos de linea. |
| `e03_solo_comentarios.hor` | Solo comentarios, con simbolos fuera del alfabeto adentro. |
| `e04_sin_bloques.hor` | Un elemento suelto, sin ningun bloque que lo contenga. |
| `e05_orden_invertido.hor` | Los cuatro bloques en orden inverso, con un aula sin guion (`MAGNA`). |
| `e06_bloques_vacios.hor` | Los cuatro bloques declarados y vacios. |
| `e07_unicode.hor` | Tildes, enie y `& < >` dentro de comillas; seccion `"Ñ"`. |
| `e08_una_linea.hor` | Archivo completo en una sola linea, sin salto final. |
| `e09_extremos.hor` | Nombre vacio, nombre de 130 caracteres, capacidad 999999, creditos 0. |
| `e10_destrozado.hor` | Llaves desbalanceadas, `:` faltantes, relaciones ausentes, `DOMINGO`, `seccion: 1`. |

Para correrlos todos:

```bash
python pruebas_reportes.py entradas/estres/e10_destrozado.hor
```
