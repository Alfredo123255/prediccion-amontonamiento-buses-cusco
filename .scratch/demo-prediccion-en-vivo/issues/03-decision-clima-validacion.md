# 03: Decisión del clima en validación

**What to build:** El script decide, usando validación y no prueba, si el modelo de la demo usa variables de clima. En la interfaz, el jurado ve una nota que dice qué variante se usa y por qué: el reanálisis ERA5 no existe en tiempo real y en la ablación el clima empeoró el error.

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** ready-for-agent

- [ ] El script compara el MAE en validación de Gradient Boosting con y sin clima, entrenando solo con entrenamiento.
- [ ] Se queda sin clima salvo que eso empeore el MAE de validación, y guarda la decisión y ambas cifras en el resumen.
- [ ] El modelo final, incluidos los cuantiles si el 02 ya está hecho, usa la variante elegida.
- [ ] La interfaz muestra la nota con la variante usada y las cifras de validación.
- [ ] Si se quita el clima, la demo ya no necesita los archivos de Open-Meteo.
