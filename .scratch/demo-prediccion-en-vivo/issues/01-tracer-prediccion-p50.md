# 01: Tracer bullet: predicción P50 de un bus en Streamlit

**What to build:** El expositor corre un script de entrenamiento rápido y luego la app. En la app elige un día de prueba, mueve un slider de hora y elige un bus. Una tabla le muestra, para cada punto de control posterior al último por el que pasó ese bus, la llegada estimada (P50), la hora programada y la hora real, esta última solo si el reloj ya la alcanzó. Para lograrlo, la construcción del dataset de modelado se saca del notebook a la demo con la misma lógica, y el núcleo de predicción queda separado de la interfaz.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] El script de entrenamiento reconstruye el dataset de modelado con la misma lógica que el notebook. Los conteos por Δ y partición coinciden con la tabla de salida del notebook (por ejemplo, Δ=1: 43 815 en entrenamiento, 10 050 en validación y 16 875 en prueba).
- [x] Entrena Gradient Boosting (profundidad 6, tasa 0,1) con entrenamiento y validación, y guarda el modelo y los datos por paso de cada día de prueba. Ningún artefacto se versiona.
- [x] El script termina en pocos minutos, no en horas.
- [x] El núcleo de predicción recibe un día y un instante y devuelve, por bus, la tabla de puntos posteriores con P50, hora programada y hora real.
- [x] Prueba: el núcleo nunca usa pasos posteriores al instante.
- [x] Prueba: la hora real aparece solo si es anterior o igual al instante.
- [x] Prueba: un bus que todavía no pasó por ningún punto no aparece.
- [x] La app carga los artefactos una sola vez y tiene selector de día (por defecto, el día laborable de prueba con más pasos), slider de hora, selector de bus y la tabla.
- [x] La app no se cae con buses a los que les falta un paso.

## Comments

- 2026-11-23, implementado en `demo/` (`entrenar.py`, `nucleo.py`, `app.py`, `test_nucleo.py`). `entrenar.py` tarda ~2,2 min; los conteos por Δ y partición coinciden con el notebook y el MAE en prueba es 1,912 (notebook: 1,919). Pruebas: `python demo/test_nucleo.py`.
- Comportamiento: la tabla muestra los puntos posteriores al último paso, así que la hora real casi solo aparece al llegar al punto 18; el bus mantiene esa tabla hasta su siguiente vuelta. Para marcar aciertos durante el recorrido (02/05) habría que comparar con predicciones de pasos anteriores.
- Heredado del notebook: `h_k` usa pasos interpolados del bus de adelante, que pueden depender de pasos posteriores (efecto leve).
