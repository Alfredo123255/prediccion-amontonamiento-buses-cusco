# 01: Tracer bullet: predicción P50 de un bus en Streamlit

**What to build:** El expositor corre un script de entrenamiento rápido y luego la app. En la app elige un día de prueba, mueve un slider de hora y elige un bus. Una tabla le muestra, para cada punto de control posterior al último por el que pasó ese bus, la llegada estimada (P50), la hora programada y la hora real, esta última solo si el reloj ya la alcanzó. Para lograrlo, la construcción del dataset de modelado se saca del notebook a la demo con la misma lógica, y el núcleo de predicción queda separado de la interfaz.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] El script de entrenamiento reconstruye el dataset de modelado con la misma lógica que el notebook. Los conteos por Δ y partición coinciden con la tabla de salida del notebook (por ejemplo, Δ=1: 43 815 en entrenamiento, 10 050 en validación y 16 875 en prueba).
- [ ] Entrena Gradient Boosting (profundidad 6, tasa 0,1) con entrenamiento y validación, y guarda el modelo y los datos por paso de cada día de prueba. Ningún artefacto se versiona.
- [ ] El script termina en pocos minutos, no en horas.
- [ ] El núcleo de predicción recibe un día y un instante y devuelve, por bus, la tabla de puntos posteriores con P50, hora programada y hora real.
- [ ] Prueba: el núcleo nunca usa pasos posteriores al instante.
- [ ] Prueba: la hora real aparece solo si es anterior o igual al instante.
- [ ] Prueba: un bus que todavía no pasó por ningún punto no aparece.
- [ ] La app carga los artefactos una sola vez y tiene selector de día (por defecto, el día laborable de prueba con más pasos), slider de hora, selector de bus y la tabla.
- [ ] La app no se cae con buses a los que les falta un paso.
