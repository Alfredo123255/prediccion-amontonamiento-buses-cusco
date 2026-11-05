# Demo (en construcción)

Aplicación interactiva para la presentación final (Streamlit + mapa). Planificada:

1. **Repetición de un día** del conjunto de prueba sobre el mapa. Al pasar cada bus por un punto de control se muestra su hora estimada de llegada al siguiente punto, junto con la programada y la real.
2. **Panel de paradero:** al elegir un punto de control se listan los próximos buses con su tiempo estimado de llegada.
3. **Comparación:** error del modelo frente al horario en el día que se está reproduciendo.

Usará los artefactos que genera `Experimentacion.ipynb`: `modelos/eta_*.joblib`, `resultados/dataset_modelo.pkl` y `resultados/paraderos_dbscan.csv`.
