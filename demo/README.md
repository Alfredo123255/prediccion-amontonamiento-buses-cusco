# Demo (en construcción)

Aplicación interactiva para la presentación final (Streamlit + mapa). Planificada:

1. **Repetición de un día** del conjunto de prueba sobre el mapa, con los buses coloreados según el riesgo de amontonamiento que predice el modelo.
2. **Detalle de un bus:** headways predichos y reales en los puntos de control siguientes.
3. **Recomendación de despacho:** para la siguiente salida del terminal, prueba desplazamientos de −2 a +5 min y recomienda el que deja los headways previstos más cercanos a los programados.

Usará los artefactos que genera `Experimentacion.ipynb`: `modelos/*.joblib`, `resultados/dataset_modelo.pkl` y `resultados/paraderos_dbscan.csv`.
