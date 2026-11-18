# Demo (en construcción)

Aplicación interactiva para la presentación final (Streamlit + mapa). Planificada:

1. **En vivo:** repite un día del conjunto de prueba sobre el mapa. Al pasar cada bus por un punto de control se muestra su hora estimada de llegada a los puntos siguientes, con su rango P10–P90, junto con la programada y la real.
2. **Planificar viaje:** el usuario elige origen A, destino B, día y hora, y obtiene el tiempo estimado de A a B con su rango.
3. **Comparación:** error del modelo frente al horario en el día que se está reproduciendo.

Usará los artefactos que genera `Experimentacion.ipynb`: `modelos/eta_*_AaB.joblib` (incluidos los cuantiles P10, P50 y P90), `resultados/dataset_modelo.pkl` y `resultados/puntos_control.csv`.
