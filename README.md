# Predicción del amontonamiento de buses en Cusco

Proyecto final del curso **Aprendizaje de Máquina (1INF02, PUCP, 2026-2)**.

En un corredor de transporte público de Cusco los buses salen del terminal bien espaciados, pero se van desordenando a lo largo de la ruta: algunos pasan casi juntos (*bus bunching*) y otros dejan huecos largos. Este proyecto predice, con varios puntos de control de anticipación, el **headway** (tiempo con el bus de adelante) de cada bus. A partir de esa predicción detecta el amontonamiento y recomienda la hora de salida del siguiente bus.

- **Regresión:** headway en el punto k+Δ (Δ = 1, 3 y 5).
- **Clasificación:** amontonado (< 0,5 del headway programado), regular o hueco (> 1,5 del programado).
- **Modelos:** Ridge/logística, KNN, árbol de decisión, SVM, Random Forest, AdaBoost, Gradient Boosting y MLP, comparados con referencias de horario y de persistencia.
- **Apoyo no supervisado:** Isolation Forest (limpieza), DBSCAN (paraderos reales a partir del GPS) y PCA.

## Estructura

```
├── Experimentacion.ipynb   # preprocesamiento + experimentos E1–E6 (Entregable 2)
├── eda_entregable1.py      # análisis exploratorio y figuras del Entregable 1
├── Dataset/README.md       # descripción de Times.csv y Monitoring.csv (los CSV no se versionan)
├── figuras/                # figuras del paper y de los experimentos
├── resultados/             # tablas de resultados (CSV)
├── modelos/                # modelos entrenados (.joblib, no se versionan; los genera el notebook)
└── demo/                   # demostración interactiva (en construcción)
```

## Cómo ejecutar

1. Copiar `Times.csv` y `Monitoring.csv` (provistos por los docentes) en `Dataset/`.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Abrir y ejecutar `Experimentacion.ipynb` con Jupyter desde la raíz del repositorio (~40 min).

La semilla está fija (`SEED = 42`) y la partición es temporal por días: entrenamiento del 06 al 22 de enero de 2025, validación del 23 al 26 y prueba del 27 de enero al 1 de febrero.

## Integrantes

- [Integrante 1 (responsable)]
- [Integrante 2]
- [Integrante 3]
- [Integrante 4]
