# Spec: rediseño de la demo en vivo (panel de paradero)

Status: ready-for-agent

Continúa `.scratch/demo-prediccion-en-vivo/`. Decisiones tomadas en el grill del 23-nov-2026, para la expo del viernes 27-nov.

## Problema

La demo funciona pero cuesta explicarla: todo va apilado en columna (el mapa queda bajo el borde del proyector), el slider dice "476 min" mientras el reloj dice 07:56, la tabla del bus a veces tiene una fila, hay jerga (MAE, P50, P10–P90, CQR) y en el mapa se enciman los números de los puntos de ida y vuelta.

## Mensaje central

"El modelo predice cuándo llega el bus con ~1,5 min de error, contra ~8 min del horario oficial, y además dice cuánto confiar." Lo que no apoya esa frase va al desplegable "Detalles del modelo".

## Decisiones

1. **Tecnología**: se queda Streamlit; se rehace layout, textos y tema (`.streamlit/config.toml` + CSS).
2. **Vista por paradero** (como un panel de paradero): "¿cuándo llegan los buses al punto X?". Se elimina la vista por bus; clic en un bus del mapa solo resalta su fila.
3. **Una sola pantalla sin scroll en 1920×1080**: barra superior con reloj grande, ▶/⏸, saltos a 07:30 y 17:30 y slider en HH:MM; mapa a la izquierda (~60 %), panel a la derecha.
4. **Lenguaje**: "Error promedio" (no MAE), "llegada estimada" (no P50), "rango probable, 8 de cada 10" (no P10–P90), "N× más preciso que el horario". Lo técnico solo en el desplegable.
5. **Tiempo**: un solo reloj; x60 fijo; arranca en pausa a las 07:30 del día laborable con más pasos.
6. **Paradero por defecto**: punto 10 (extremo de la ruta). Se cambia con clic en el mapa o con la lista.
7. **Mapa**: ida (1–10) y vuelta (11–18) en dos colores; puntos encimados con una sola etiqueta ("3 / 17"); paradero elegido resaltado; buses que van al paradero en naranja, el resto en gris.
8. **Panel**: línea de tiempo (Altair) con una fila por bus: barra = rango probable, punto = llegada estimada, raya gris = horario, línea = ahora; al llegar, rombo verde (dentro del rango) o rojo. Rótulo "en 7 min" / "llegó en el rango". Los que llegaron se quedan 15 min simulados.
9. **Marcador del día**: error promedio del modelo vs horario, "N× más preciso" y "% de llegadas dentro del rango (se espera 8 de cada 10)".
10. **Detalles del modelo**: desplegable cerrado al pie (Gradient Boosting cuantílico, por qué sin clima, CQR con coberturas, partición temporal).
11. **Guion** de ~2 min en el README de la demo; se regraba el video de respaldo.

## Núcleo

- `paradero(pasos, modelos, features, instante, destino, q, ventana=15)` reemplaza a `predecir`: buses que vienen al destino (predicción desde su último paso) y los que llegaron en los últimos `ventana` min (predicción desde su último paso antes de llegar).
- `marcador` reemplaza a `mae_acumulado` y agrega la fracción de llegadas dentro del rango.
- Pruebas en `demo/test_nucleo.py` (mismos invariantes: nada del futuro, P10 ≤ P50 ≤ P90, hora real solo si ya ocurrió).
