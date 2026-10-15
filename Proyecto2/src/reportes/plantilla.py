# -*- coding: utf-8 -*-
"""
plantilla.py
Partes comunes de los reportes HTML: escape de caracteres, CSS embebido y
el esqueleto de la pagina. Cada reporte es un archivo HTML independiente
con su CSS adentro, asi que se abre en cualquier navegador sin nada mas.
"""

import os

# Paleta y medidas compartidas por los tres reportes.
CSS = """
:root {
  --fondo: #f6f7f9;
  --hoja: #ffffff;
  --texto: #1f2328;
  --suave: #57606a;
  --borde: #d8dee4;
  --acento: #2e75b6;
  --codigo-fondo: #eff1f3;
  --bloque-fondo: #0f1419;
  --bloque-texto: #e6edf3;
  --ok-fondo: #e6f4ea;
  --ok-texto: #1a7f37;
  --error-fondo: #fdecea;
  --error-texto: #b3261e;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--fondo);
  color: var(--texto);
  font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  line-height: 1.6;
}
.hoja {
  max-width: 820px;
  margin: 32px auto;
  padding: 40px 48px;
  background: var(--hoja);
  border: 1px solid var(--borde);
  border-radius: 10px;
}
.estado {
  display: inline-block;
  margin-bottom: 24px;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 13px;
  background: var(--ok-fondo);
  color: var(--ok-texto);
}
.estado.con-errores {
  background: var(--error-fondo);
  color: var(--error-texto);
}
.subtitulo { color: var(--suave); font-size: 14px; margin-top: -8px; }
h1, h2, h3, h4, h5, h6 { line-height: 1.25; margin: 28px 0 12px; }
h1 {
  font-size: 2em;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--borde);
}
h2 {
  font-size: 1.5em;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--borde);
}
h3 { font-size: 1.25em; }
h4 { font-size: 1.1em; }
h5 { font-size: 1em; }
h6 { font-size: 0.9em; color: var(--suave); }
p { margin: 0 0 14px; }
ul, ol { margin: 0 0 14px; padding-left: 28px; }
li > ul, li > ol { margin: 4px 0; }
li.tarea { list-style: none; margin-left: -22px; }
li.tarea input { margin: 0 6px 0 0; vertical-align: middle; }
del { color: var(--suave); }
a { color: var(--acento); }
img { max-width: 100%; }
blockquote {
  margin: 0 0 14px;
  padding: 2px 16px;
  color: var(--suave);
  border-left: 4px solid var(--borde);
}
blockquote blockquote { margin-top: 8px; }
code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.9em;
  padding: 2px 6px;
  background: var(--codigo-fondo);
  border-radius: 4px;
}
pre {
  margin: 0 0 16px;
  padding: 16px 20px;
  overflow-x: auto;
  background: var(--bloque-fondo);
  color: var(--bloque-texto);
  border-radius: 8px;
}
pre code { padding: 0; background: none; color: inherit; font-size: 0.9em; }
hr { border: 0; border-top: 1px solid var(--borde); margin: 28px 0; }
table { width: 100%; border-collapse: collapse; margin: 0 0 20px; }
th, td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--borde);
}
th { color: var(--suave); font-weight: 600; font-size: 13px; }
/* Reporte 1: tablas del documento (alcance opcional) */
.tabla-md { width: auto; min-width: 50%; }
.tabla-md th, .tabla-md td { border: 1px solid var(--borde); }
.tabla-md th {
  color: var(--texto);
  font-size: 1em;
  background: var(--fondo);
}
.pie { margin-top: 36px; color: var(--suave); font-size: 12px; }

/* Reporte 2: tarjetas, barras y pares de valores */
.seccion {
  margin: 32px 0 12px;
  padding-bottom: 6px;
  font-size: 1.05em;
  border-bottom: 1px solid var(--borde);
}
.tarjetas {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.tarjeta {
  padding: 14px 16px;
  background: var(--fondo);
  border: 1px solid var(--borde);
  border-radius: 8px;
}
.tarjeta .numero { font-size: 26px; font-weight: 700; color: var(--acento); }
.tarjeta .rotulo { font-size: 12px; color: var(--suave); }
.barra-fila {
  display: grid;
  grid-template-columns: 32px 1fr 32px;
  gap: 10px;
  align-items: center;
  margin: 6px 0;
  font-size: 13px;
}
.barra-fondo {
  height: 10px;
  background: var(--codigo-fondo);
  border-radius: 5px;
}
.barra { height: 10px; background: var(--acento); border-radius: 5px; }
.par {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid var(--borde);
  border-radius: 8px;
}
.pares { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.par .valor { font-size: 20px; font-weight: 700; }

/* Reporte 3: indice */
.indice {
  padding: 16px 20px;
  background: var(--fondo);
  border: 1px solid var(--borde);
  border-radius: 8px;
}
.entrada { padding: 6px 0; border-bottom: 1px dashed var(--borde); }
.entrada:last-child { border-bottom: 0; }
.entrada a { color: var(--acento); text-decoration: none; }
.entrada a:hover { text-decoration: underline; }
.nivel {
  display: inline-block;
  min-width: 26px;
  margin-right: 8px;
  padding: 1px 5px;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  color: #ffffff;
  background: var(--acento);
  border-radius: 4px;
}
.nota { color: var(--suave); font-size: 13px; font-style: italic; }

/* Tabla de errores */
.tabla-errores { font-size: 13px; }
.tabla-errores td.descripcion { min-width: 300px; }
.tabla-errores td.tipo { white-space: nowrap; }
/* La pagina de errores es mas ancha para que la tabla quepa. */
.hoja:has(.tabla-errores) { max-width: 1120px; }
@media (max-width: 600px) {
  .pares { grid-template-columns: 1fr; }
  .hoja { margin: 0; padding: 24px 16px; border-radius: 0; border: 0; }
}
"""


def escapar(texto):
    """
    Convierte los caracteres que tienen significado en HTML para que se
    muestren tal cual. Sin esto, un texto como '<b>' se volveria negrita
    en el reporte en vez de verse escrito.
    """
    resultado = ''
    i = 0
    while i < len(texto):
        c = texto[i]
        if c == '&':
            resultado = resultado + '&amp;'
        elif c == '<':
            resultado = resultado + '&lt;'
        elif c == '>':
            resultado = resultado + '&gt;'
        elif c == '"':
            resultado = resultado + '&quot;'
        else:
            resultado = resultado + c
        i = i + 1
    return resultado


def pagina(titulo, cuerpo, nombre_archivo, cabecera_extra=''):
    """
    Documento HTML completo: cabecera, CSS embebido, cuerpo y pie.
    'cabecera_extra' es lo que un reporte quiera agregar al <head>; el
    Reporte 1 lo usa para el resaltado de sintaxis (D-36).
    """
    return ('<!DOCTYPE html>\n'
            '<html lang="es">\n'
            '<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1">\n'
            '<title>' + escapar(titulo) + '</title>\n'
            '<style>' + CSS + '</style>\n' +
            cabecera_extra +
            '</head>\n'
            '<body>\n'
            '<main class="hoja">\n' +
            cuerpo +
            '<div class="pie">Generado por MarkdownCheck a partir de ' +
            escapar(nombre_archivo) + '.</div>\n'
            '</main>\n'
            '</body>\n'
            '</html>\n')


def guardar(carpeta, nombre, contenido):
    """Escribe 'contenido' en carpeta/nombre (UTF-8) y devuelve la ruta."""
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    ruta = os.path.join(carpeta, nombre)
    archivo = open(ruta, 'w', encoding='utf-8')
    archivo.write(contenido)
    archivo.close()
    return ruta
