# 05: MAE acumulado del día

**What to build:** Mientras avanza el reloj, la interfaz muestra el MAE acumulado del día del modelo frente al del horario programado, calculado solo con las llegadas reales que ya ocurrieron. Es la evidencia cuantitativa en vivo de que el modelo supera al horario.

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** ready-for-agent

- [ ] El núcleo calcula el MAE acumulado del modelo y del horario hasta el instante dado, sobre las predicciones hechas en los pasos ya ocurridos cuya llegada real también ya ocurrió.
- [ ] Prueba: las llegadas reales posteriores al instante no entran en el cálculo.
- [ ] Prueba: con un modelo perfecto sintético, el MAE del modelo es 0.
- [ ] La interfaz muestra ambos valores y la mejora en %, y se actualizan con el reloj.
