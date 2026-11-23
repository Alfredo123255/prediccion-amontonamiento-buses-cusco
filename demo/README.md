# Demo: predicción en vivo del tiempo de llegada

Repite un día del conjunto de prueba (27-ene al 1-feb de 2025) como si fuera en vivo. El mapa muestra la ruta, los 18 puntos de control y los buses. Para el bus elegido, una tabla da su llegada estimada (P50) a cada punto siguiente, con el rango P10–P90, la hora programada y la real. Arriba se ven el MAE acumulado del día del modelo y el del horario.

## Preparar y lanzar (desde la raíz del repo)

1. Copiar `Times.csv` y `Monitoring.csv` (provistos por los docentes) en `Dataset/`.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Entrenar la demo (unos minutos; no necesita el notebook): `python demo/entrenar.py`
4. Lanzar: `streamlit run demo/app.py` y abrir http://localhost:8501

## En la expo

- **▶ Reproducir x60**: 1 s real = 1 min del día. **⏸** pausa; el slider salta a cualquier hora.
- Elegir el bus en la lista o haciendo clic en el mapa (mejor en pausa). Las filas en verde son llegadas reales que cayeron dentro del rango.
- Hora punta recomendada: 07:00–09:00 o 17:00–19:00.
- Sin internet el mapa sigue funcionando, aunque sin fondo de calles.
- Si falla la laptop o el proyector: GIF de respaldo (ver abajo).

## Pruebas

```
python demo/test_nucleo.py
```

## GIF de respaldo

`demo/respaldo/demo_respaldo.gif` (5,6 MB) y `demo_respaldo.mp4` (0,8 MB): 50 s del 30-ene desde las 07:39 con el bus 21, que llega al punto 18 dentro del rango, y el MAE acumulado avanzando. No se versionan (pesan): se suben a la carpeta compartida del grupo.
