# -*- coding: utf-8 -*-
"""
estilos.py
CSS embebido en cada reporte HTML.

Se embebe en lugar de enlazar un archivo externo por dos razones:
  1. El enunciado lo exige ("CSS embebido").
  2. Cada reporte debe abrirse en cualquier navegador como archivo suelto,
     sin depender de rutas relativas ni de conexion a internet. Por eso no se
     usan fuentes web: solo tipografias del sistema.
"""

# Umbrales de carga docente. Son los sugeridos por el enunciado; se dejan como
# constantes para poder ajustarlos con justificacion en el manual tecnico.
CARGA_BAJA_MAX = 4
CARGA_NORMAL_MAX = 10
CARGA_ALTA_MAX = 15

# Minutos disponibles a la semana: 6 dias x 15 horas institucionales (06:00-21:00)
MINUTOS_DIA_INSTITUCIONAL = 900
DIAS_HABILES = 6
MINUTOS_SEMANA = MINUTOS_DIA_INSTITUCIONAL * DIAS_HABILES

UMBRAL_OCUPACION_ALTA = 80.0

CSS = """
:root {
    --tinta:    #16202a;
    --pizarra:  #4a5b6c;
    --papel:    #ffffff;
    --fondo:    #eef1f4;
    --regla:    #d3dae1;

    --ok-texto: #1f7a3f;
    --ok-fondo: #e3f4e8;
    --mal-texto: #a32626;
    --mal-fondo: #fbe6e6;
    --baja-texto: #1f5f9e;
    --baja-fondo: #e6eff8;
    --alta-texto: #b5651d;
    --alta-fondo: #fdeedd;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 32px 20px 64px;
    background: var(--fondo);
    color: var(--tinta);
    font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 15px;
    line-height: 1.5;
}

.hoja {
    max-width: 1180px;
    margin: 0 auto;
    background: var(--papel);
    border: 1px solid var(--regla);
    padding: 36px 40px 44px;
}

.encabezado {
    border-bottom: 3px solid var(--tinta);
    padding-bottom: 18px;
    margin-bottom: 30px;
}

.encabezado h1 {
    margin: 0 0 6px;
    font-size: 27px;
    font-weight: 600;
    letter-spacing: -0.01em;
}

.encabezado p {
    margin: 0;
    color: var(--pizarra);
    font-size: 14px;
}

h2 {
    margin: 38px 0 14px;
    font-size: 19px;
    font-weight: 600;
    padding-bottom: 7px;
    border-bottom: 1px solid var(--regla);
}

h3 {
    margin: 26px 0 10px;
    font-size: 16px;
    font-weight: 600;
    color: var(--pizarra);
}

p.nota {
    color: var(--pizarra);
    font-size: 13.5px;
    margin: 0 0 18px;
    max-width: 74ch;
}

.leyenda { margin: 0 0 22px; }
.leyenda div { margin-bottom: 6px; color: var(--pizarra); font-size: 13.5px; }
.leyenda .etiqueta { margin-right: 8px; }

/* ---------- tablas ---------- */

table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 8px;
    font-size: 14px;
}

thead th {
    background: var(--tinta);
    color: var(--papel);
    text-align: left;
    font-weight: 600;
    padding: 9px 11px;
    border-right: 1px solid rgba(255,255,255,0.14);
}

thead th:last-child { border-right: none; }

tbody td, tbody th {
    padding: 9px 11px;
    border-bottom: 1px solid var(--regla);
    border-right: 1px solid var(--regla);
    vertical-align: top;
}

tbody td:last-child, tbody th:last-child { border-right: none; }

tbody th { text-align: left; font-weight: 600; background: #f2f5f8; }

tbody tr:nth-child(even) td { background: #f7f9fb; }

.numero {
    font-variant-numeric: tabular-nums;
    text-align: right;
    white-space: nowrap;
}

/* ---------- rejilla semanal ---------- */

.rejilla { table-layout: fixed; }

.rejilla thead th { text-align: center; }

.rejilla .hora {
    width: 104px;
    background: #f2f5f8;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    text-align: center;
    white-space: nowrap;
    color: var(--pizarra);
}

.rejilla td {
    height: 74px;
    font-size: 13px;
    padding: 7px 8px;
    background: var(--papel);
}

.rejilla tbody tr:nth-child(even) td { background: var(--papel); }

.bloque { border-left: 4px solid transparent; padding-left: 7px; }
.bloque + .bloque { margin-top: 7px; border-top: 1px dashed var(--regla); padding-top: 6px; }

.bloque .curso { font-weight: 600; display: block; }
.bloque .detalle { color: var(--pizarra); display: block; font-size: 12.5px; }

.confirmado { background: var(--ok-fondo) !important; }
.confirmado .bloque { border-left-color: var(--ok-texto); }

.choque { background: var(--mal-fondo) !important; }
.choque .bloque { border-left-color: var(--mal-texto); }

.marca {
    display: inline-block;
    margin-top: 4px;
    color: var(--mal-texto);
    font-weight: 600;
    font-size: 11.5px;
}

.revisar { background: var(--alta-fondo) !important; }
.revisar .bloque { border-left-color: var(--alta-texto); }
.revisar .marca { color: var(--alta-texto); }

.vacia { background: #fbfcfd !important; }

/* ---------- etiquetas de estado ---------- */

.etiqueta {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 2px;
    font-size: 12.5px;
    font-weight: 600;
    white-space: nowrap;
}

.e-ok      { background: var(--ok-fondo);   color: var(--ok-texto); }
.e-mal     { background: var(--mal-fondo);  color: var(--mal-texto); }
.e-baja    { background: var(--baja-fondo); color: var(--baja-texto); }
.e-normal  { background: var(--ok-fondo);   color: var(--ok-texto); }
.e-alta    { background: var(--alta-fondo); color: var(--alta-texto); }
.e-saturada{ background: var(--mal-fondo);  color: var(--mal-texto); }

/* ---------- indicadores ---------- */

.indicadores {
    display: -webkit-box;
    display: -webkit-flex;
    display: flex;
    -webkit-flex-wrap: wrap;
    flex-wrap: wrap;
    background: var(--regla);
    border: 1px solid var(--regla);
    margin-bottom: 10px;
}

.indicador {
    -webkit-flex: 1 1 184px;
    flex: 1 1 184px;
    min-width: 184px;
    background: var(--papel);
    padding: 15px 17px;
    border-right: 1px solid var(--regla);
    border-bottom: 1px solid var(--regla);
}

.indicador .valor {
    display: block;
    font-size: 30px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    line-height: 1.15;
}

.indicador .rotulo {
    display: block;
    color: var(--pizarra);
    font-size: 13px;
    margin-top: 2px;
}

.indicador.alerta .valor { color: var(--mal-texto); }

/* ---------- barra de ocupacion ---------- */

.barra {
    position: relative;
    height: 19px;
    background: #e8edf2;
    border: 1px solid var(--regla);
    min-width: 150px;
}

.barra span {
    display: block;
    height: 100%;
    background: var(--ok-texto);
}

.barra.saturada span { background: var(--mal-texto); }

/* ---------- listas de apoyo ---------- */

ul.lista { margin: 0 0 18px; padding-left: 21px; }
ul.lista li { margin-bottom: 5px; }

.sugerencia { font-variant-numeric: tabular-nums; }

.pie {
    margin-top: 42px;
    padding-top: 14px;
    border-top: 1px solid var(--regla);
    color: var(--pizarra);
    font-size: 12.5px;
}

.limpio {
    background: var(--ok-fondo);
    border-left: 4px solid var(--ok-texto);
    padding: 13px 16px;
    color: var(--ok-texto);
    margin-bottom: 18px;
}

/* ---------- responsive y impresion ---------- */

@media (max-width: 760px) {
    body { padding: 14px 8px 40px; }
    .hoja { padding: 20px 16px 28px; }
    table, .rejilla { font-size: 12px; }
    .rejilla .hora { width: 66px; }
}

@media print {
    body { background: var(--papel); padding: 0; }
    .hoja { border: none; max-width: none; padding: 0; }
    thead th { background: #333333 !important; -webkit-print-color-adjust: exact; }
    .confirmado, .choque, .etiqueta, .barra span {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}
"""
