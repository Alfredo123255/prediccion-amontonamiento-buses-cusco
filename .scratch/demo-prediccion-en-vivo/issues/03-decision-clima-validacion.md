# 03: Decisión del clima en validación

**What to build:** El script decide, usando validación y no prueba, si el modelo de la demo usa variables de clima. En la interfaz, el jurado ve una nota que dice qué variante se usa y por qué: el reanálisis ERA5 no existe en tiempo real y en la ablación el clima empeoró el error.

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** ready-for-agent

- [x] El script compara el MAE en validación de Gradient Boosting con y sin clima, entrenando solo con entrenamiento.
- [x] Se queda sin clima salvo que eso empeore el MAE de validación, y guarda la decisión y ambas cifras en el resumen.
- [x] El modelo final, incluidos los cuantiles si el 02 ya está hecho, usa la variante elegida.
- [x] La interfaz muestra la nota con la variante usada y las cifras de validación.
- [x] Si se quita el clima, la demo ya no necesita los archivos de Open-Meteo.

## Comments

- 2026-11-23, implementado en `demo/entrenar.py` y `demo/app.py`. MAE en validación (entrenando solo con entrenamiento): sin clima 2,330, con clima 2,369 → modelo sin clima. Con eso, MAE P50 en prueba 1,844 (antes 1,912); CQR q = +0,433 min; cobertura P10–P90: validación 72,5 % → 80,0 %, prueba 73,8 % → 82,1 %. El script tarda ~7 min.
- "No necesita los archivos de Open-Meteo": se puede borrar `clima_open_meteo.csv` (el script va sin clima y no compara; esa rama no se ejecutó, se revisó leyendo el código). `puntos_control_clima.csv` sigue haciendo falta porque trae la altitud.
