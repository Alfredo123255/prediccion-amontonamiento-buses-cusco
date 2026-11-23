# 02: Rango P10–P90 calibrado con CQR

**What to build:** En la tabla del bus elegido, cada llegada estimada muestra su rango P10–P90, y la fila se marca cuando la llegada real cae dentro. El rango está calibrado con validación para cubrir cerca del 80 % de los casos (el modelo del paper cubría 73,5 %).

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** done

- [x] El script entrena los modelos de cuantiles P10 y P90 con entrenamiento y calcula la corrección CQR con validación.
- [x] El resumen de entrenamiento informa la cobertura P10–P90 en validación y en prueba, antes y después de calibrar.
- [x] El núcleo devuelve P10, P50 y P90 calibrados y garantiza que P10 ≤ P50 ≤ P90.
- [x] Prueba sintética: con datos de cobertura conocida, después de calibrar la cobertura queda en 80 % ± 2 pp.
- [x] Prueba: el orden P10 ≤ P50 ≤ P90 se cumple aunque los modelos crucen sus cuantiles.
- [x] La tabla muestra el rango y marca las filas donde la llegada real cae dentro.

## Comments

- 2026-11-23, implementado en `demo/`. `entrenar.py` entrena P10 y P90 (pérdida cuantílica) solo con entrenamiento y calcula la corrección CQR (`nucleo.calibrar`) con validación: q = +0,538 min. Cobertura P10–P90: validación 71,0 % → 80,0 %; prueba 71,1 % → 81,3 %. MAE P50 en prueba 1,912. El script ahora tarda ~5,4 min.
- `nucleo.predecir` recibe `{"p10", "p50", "p90"}` y `q`; recorta P10/P90 contra P50 para garantizar el orden (si los cuantiles se cruzan, el rango colapsa en P50) y devuelve `dentro`. La tabla muestra el rango, una columna ✅ y fondo verde en las filas acertadas.
- Pendiente de decidir: P50 sigue entrenado con entrenamiento + validación (como en el ticket 01), aunque la spec dice "P10, P50 y P90 con entrenamiento". No afecta la CQR, que solo usa P10/P90. La cobertura reportada no incluye el recorte contra P50, que solo ensancha el rango.
