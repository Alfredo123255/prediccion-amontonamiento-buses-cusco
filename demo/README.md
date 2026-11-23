# Demo: predicción en vivo del tiempo de llegada

Repite un día del conjunto de prueba (27-ene al 1-feb de 2025) como si fuera en vivo, como un panel de paradero: para el punto de control elegido, cada bus que viene tiene su llegada estimada, su rango probable (8 de cada 10 llegadas caen ahí) y la hora del horario oficial. Al llegar, se marca si cayó dentro del rango. Arriba, el marcador del día compara el error del modelo con el del horario. Pensada para 1920×1080.

## Preparar y lanzar (desde la raíz del repo)

1. Copiar `Times.csv` y `Monitoring.csv` (provistos por los docentes) en `Dataset/`.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Entrenar la demo (unos minutos; no necesita el notebook): `python demo/entrenar.py`
4. Lanzar: `streamlit run demo/app.py` y abrir http://localhost:8501

## En la expo

Abre en pausa a las 07:30 del jueves 30-ene, en el punto 10 (extremo de la ruta). Guion de ~2 min:

1. **El mapa**: la ruta es un circuito, ida del 1 al 10 (verde azulado) y vuelta del 11 al 18 (morado) por la misma vía. Los buses naranjas van hacia el punto elegido.
2. **El panel**: "estos buses vienen al punto 10. El bus 29 llega en 5 min; la barra es el rango donde caen 8 de cada 10 llegadas; la raya gris es lo que dice el horario".
3. **▶ Reproducir** (1 s = 1 min): la cuenta baja, las barras se ajustan cada vez que el bus pasa un punto y, al llegar, aparece el rombo verde (dentro del rango) o rojo. ⏸ para explicar.
4. **El marcador**: error promedio del modelo (~1,5 min) contra el del horario, y el % de llegadas dentro del rango, que debe rondar el 80 %.
5. Si hay preguntas: **Ir a 17:30**, clic en otro punto del mapa o **Detalles del modelo** (al pie: modelo, por qué no usa clima, calibración CQR y partición temporal).

- Clic en un bus del mapa lo marca con ▸ en el panel.
- Sin internet el mapa sigue funcionando, aunque sin fondo de calles.
- Si falla la laptop o el proyector: video de respaldo (ver abajo).

## Pruebas

```
python demo/test_nucleo.py
```

## Video de respaldo

`demo/respaldo/demo_respaldo.mp4`: el guion de arriba grabado en 1920×1080 (jueves 30-ene desde las 07:30, punto 10, luego el punto 16).
