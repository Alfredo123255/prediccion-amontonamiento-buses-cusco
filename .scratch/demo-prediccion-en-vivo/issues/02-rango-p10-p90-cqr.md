# 02: Rango P10–P90 calibrado con CQR

**What to build:** En la tabla del bus elegido, cada llegada estimada muestra su rango P10–P90, y la fila se marca cuando la llegada real cae dentro. El rango está calibrado con validación para cubrir cerca del 80 % de los casos (el modelo del paper cubría 73,5 %).

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** ready-for-agent

- [ ] El script entrena los modelos de cuantiles P10 y P90 con entrenamiento y calcula la corrección CQR con validación.
- [ ] El resumen de entrenamiento informa la cobertura P10–P90 en validación y en prueba, antes y después de calibrar.
- [ ] El núcleo devuelve P10, P50 y P90 calibrados y garantiza que P10 ≤ P50 ≤ P90.
- [ ] Prueba sintética: con datos de cobertura conocida, después de calibrar la cobertura queda en 80 % ± 2 pp.
- [ ] Prueba: el orden P10 ≤ P50 ≤ P90 se cumple aunque los modelos crucen sus cuantiles.
- [ ] La tabla muestra el rango y marca las filas donde la llegada real cae dentro.
