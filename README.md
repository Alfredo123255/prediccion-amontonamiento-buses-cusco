# Predicción del tiempo de llegada de buses en Cusco

Proyecto final del curso **Aprendizaje de Máquina (1INF02, PUCP, 2026-2)**.

En un corredor de transporte público de Cusco los buses siguen un horario de paso por 18 puntos de control, pero el tiempo real de cada tramo cambia con la hora, el tráfico y la demanda. Este proyecto predice, **cuando un bus pasa por un punto de control A, cuántos minutos tardará en llegar a cualquier punto posterior B** (ETA de A a B), a partir de los registros de puntos de control y del GPS de los buses.

- **Regresión:** tiempo hasta el punto k+Δ, con Δ = 1…17, en **un solo modelo** (Δ es una variable de entrada).
- **Referencias:** el horario, el promedio histórico del trayecto A→B a esa hora y el tiempo del último bus que recorrió el mismo trayecto.
- **Modelos:** Ridge, KNN, árbol de decisión, SVM, Random Forest, AdaBoost, Gradient Boosting y MLP, más regresión cuantílica (P10–P90) con Gradient Boosting.
- **Métricas:** MAE (principal), RMSE, WAPE, % de predicciones dentro de ±2 min, P90 del error y cobertura del intervalo. No se usan R² ni MAPE (ver notebook).
- **Apoyo:** Isolation Forest para la limpieza y PCA como experimento de reducción de dimensionalidad. Las técnicas de clustering quedaron fuera del alcance.
- **Datos externos:** clima horario (reanálisis ERA5) y altitud de Open-Meteo en las coordenadas de cada punto de control.

## Estructura

```
├── Experimentacion.ipynb   # preprocesamiento + experimentos E1–E7
├── eda_entregable1.py      # mapa de la ruta y puntos de control (Fig. 1 del paper)
├── paper/paper_E2.tex      # paper del Entregable 2 (IEEE); usa las figuras de figuras/
├── Dataset/README.md       # descripción de Times.csv y Monitoring.csv (los CSV no se versionan)
├── datos_externos/         # clima y altitud de Open-Meteo (caché para correr sin internet)
├── figuras/                # figuras del paper y de los experimentos
├── resultados/             # tablas de resultados (CSV) y entorno de ejecución
├── modelos/                # modelos entrenados (.joblib, no se versionan; los genera el notebook)
└── demo/                   # demostración interactiva (en construcción)
```

## Cómo ejecutar

1. Copiar `Times.csv` y `Monitoring.csv` (provistos por los docentes) en `Dataset/`.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Abrir y ejecutar `Experimentacion.ipynb` con Jupyter desde la raíz del repositorio (~2 h; Random Forest toma más de 1 h).

La semilla está fija (`SEED = 42`) y la partición es temporal por días: entrenamiento del 06 al 22 de enero de 2025, validación del 23 al 26 y prueba del 27 de enero al 1 de febrero.

Para compilar el paper, subir `paper/paper_E2.tex` y la carpeta `figuras/` a Overleaf (o compilar localmente con `pdflatex` desde `paper/`).

## Integrantes

- Divano Estefano Perez Nina
- Angel Freddy Cerdán Cigüeñas
- Alfredo Ernesto Sanchez Tuesta
- Renzo Kei Shimabukuro Kohatsu
