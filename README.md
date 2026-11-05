# Predicción del tiempo de llegada de buses en Cusco

Proyecto final del curso **Aprendizaje de Máquina (1INF02, PUCP, 2026-2)**.

En un corredor de transporte público de Cusco los buses siguen un horario de paso por 18 puntos de control, pero el tiempo real de cada tramo cambia con la hora, el tráfico y la demanda. Este proyecto predice, **cuando un bus pasa por un punto de control, cuántos minutos tardará en llegar al siguiente** (ETA), a partir de los registros de puntos de control y del GPS de los buses.

- **Regresión:** tiempo hasta el punto k+Δ. El problema principal es Δ = 1; también se analizan Δ = 3 y Δ = 5.
- **Referencias:** el horario, el promedio histórico del tramo a esa hora y el tiempo del último bus que recorrió el tramo.
- **Modelos:** Ridge, KNN, árbol de decisión, SVM, Random Forest, AdaBoost, Gradient Boosting y MLP.
- **Apoyo no supervisado:** Isolation Forest para la limpieza, DBSCAN para ubicar los paraderos reales a partir del GPS, y PCA.

## Estructura

```
├── Experimentacion.ipynb   # preprocesamiento + experimentos E1–E6
├── eda_entregable1.py      # mapa de la ruta y puntos de control (Fig. 1 del paper)
├── Dataset/README.md       # descripción de Times.csv y Monitoring.csv (los CSV no se versionan)
├── figuras/                # figuras del paper y de los experimentos
├── resultados/             # tablas de resultados (CSV)
├── modelos/                # modelos entrenados (.joblib, no se versionan; los genera el notebook)
└── demo/                   # demostración interactiva (en construcción)
```

## Cómo ejecutar

1. Copiar `Times.csv` y `Monitoring.csv` (provistos por los docentes) en `Dataset/`.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Abrir y ejecutar `Experimentacion.ipynb` con Jupyter desde la raíz del repositorio (~20 min).

La semilla está fija (`SEED = 42`) y la partición es temporal por días: entrenamiento del 06 al 22 de enero de 2025, validación del 23 al 26 y prueba del 27 de enero al 1 de febrero.

## Integrantes

- [Integrante 1 (responsable)]
- [Integrante 2]
- [Integrante 3]
- [Integrante 4]
