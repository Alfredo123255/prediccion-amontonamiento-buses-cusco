# Guía de uso: ¿Cuándo llega el bus?

Esta aplicación muestra cómo el modelo del proyecto predice **cuándo llegará cada bus a un punto de control** de una ruta urbana de Cusco. Repite un día real de operación (de la semana de prueba, que el modelo nunca vio al entrenar) como si estuviera ocurriendo en vivo, y compara las predicciones con lo que dice el horario oficial.

---

## 1. Antes de empezar

| Requisito | Detalle |
|---|---|
| Python | Probado con Python 3.14 y las dependencias de `requirements.txt` |
| Datos | `Times.csv` y `Monitoring.csv` (los entregan los docentes) en la carpeta `Dataset/` |
| Pantalla | Pensada para 1920 × 1080 en pantalla completa; en pantallas más chicas puede requerir desplazarse |
| Internet | Opcional: solo se usa para el fondo de calles del mapa |

Desde la raíz del repositorio:

```bash
pip install -r requirements.txt
python demo/entrenar.py          # una sola vez, ~5 min: genera demo/artefactos/demo.joblib
python -m streamlit run demo/app.py
```

La aplicación se abre en http://localhost:8501. Si el comando `streamlit` no se reconoce en Windows, usa `python -m streamlit` como arriba.

---

## 2. La pantalla

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ① ¿Cuándo llega el bus?                       ⑦ Día que se repite  ⑧ ¿Cómo se usa? │
│ ② 07:30  [▶ Reproducir] [Punta mañana] [Punta tarde]  ③ ───●──────────────── │
│   jue 30 ene 2025  ⏸ EN PAUSA                                                 │
├───────────────────────────────────────────┬──────────────────────────────────┤
│                                           │ ⑤ [10] Llegadas al punto 10  [Ver otro punto ▾] │
│                                           │ ⑥ 1,5 min    9,1 min     79 %                 │
│            ④ MAPA DE LA RUTA              │   modelo     horario     dentro del rango     │
│                                           │ ─────────────────────────────────            │
│                                           │   Bus 27  ●═══   ✓ llegó dentro del rango    │
│                                           │   Bus 28    ●══  llegando                    │
│                                           │   Bus 29      ═●═   en 5 min                 │
│ leyenda del mapa                          │   leyenda del panel                          │
├───────────────────────────────────────────┴──────────────────────────────────┤
│ ⑨ Detalles del modelo (desplegable)                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

| # | Zona | Para qué sirve |
|---|---|---|
| ① | Título | Recuerda qué muestra la aplicación. |
| ② | Reloj y controles | Hora simulada, fecha y **estado**: `⏸ EN PAUSA` o `● EN VIVO ×60` (1 segundo real = 1 minuto del día). |
| ③ | Barra de hora | Arrástrala para ir a cualquier momento del día de servicio. |
| ④ | Mapa | La ruta, los 18 puntos de control y la posición de los buses en ese minuto. |
| ⑤ | Punto elegido | El punto de control cuyas llegadas se muestran (por defecto, el 10). |
| ⑥ | Marcador del día | Cuánto se equivocan el modelo y el horario en lo que va del día. |
| ⑦ | Día | Cambia entre los 6 días de prueba (27-ene al 1-feb de 2025). |
| ⑧ | Ayuda | Resumen de uso en 5 pasos, sin salir de la aplicación. |
| ⑨ | Detalles del modelo | Información técnica: modelo, clima, calibración del rango y partición de los datos. |

---

## 3. Cómo leer el panel de llegadas

Cada fila es un bus que viene hacia el punto elegido, ordenado por hora de llegada estimada. Solo se muestran los 6 más próximos; debajo se indica cuántos más vienen en camino.

| Elemento | Qué significa |
|---|---|
| **Punto naranja** | Llegada estimada por el modelo. |
| **Barra naranja clara** | Rango probable: 8 de cada 10 llegadas reales caen dentro de él. |
| **Raya gris vertical** | Hora de llegada según el horario oficial. |
| **Línea punteada** | El momento actual de la simulación. |
| **Rombo verde con ✓** | El bus ya llegó y lo hizo dentro del rango. |
| **Rombo rojo con ✗** | El bus ya llegó, pero fuera del rango. |
| **"en 7 min" / "llegando"** | Cuánto le falta al bus según la estimación. |
| **▸ Bus 29** | El bus que marcaste haciendo clic en el mapa. |

Los buses que ya llegaron se quedan 15 minutos simulados en el panel para que se vea si la predicción acertó. Cada vez que un bus pasa por un punto de control, su predicción se actualiza con la información nueva y la barra se mueve.

### El marcador del día

| Cifra | Qué mide |
|---|---|
| **Error promedio del modelo** (naranja) | Diferencia media, en minutos, entre la llegada estimada y la real. |
| **Error del horario oficial** (gris) | Lo mismo, usando la hora del horario. Debajo se indica cuántas veces más preciso es el modelo. |
| **% dentro del rango** | Porcentaje de llegadas reales que cayeron en el rango probable. Si el rango está bien calibrado, ronda el 80 %. |

Las cifras se calculan solo con buses que ya llegaron, desde el inicio del día hasta la hora del reloj. Al pasar el cursor sobre cada cifra aparece una explicación. Al inicio del día, antes de la primera llegada, el marcador muestra un aviso en lugar de cifras.

---

## 4. Tareas frecuentes

**Ver cuándo llegan los buses a un punto**
1. Haz clic en el círculo del punto en el mapa, o elígelo en **Ver otro punto**.
2. El panel de la derecha cambia a ese punto.

> El punto 1 es la salida de la ruta: ningún bus "llega" a él, así que no se puede elegir. Si haces clic en él, un aviso lo explica.

**Ver la simulación en movimiento**
1. Pulsa **▶ Reproducir**. El indicador cambia a `● EN VIVO ×60`.
2. Pulsa **⏸ Pausar** para detenerla y explicar algo.
3. Al llegar al final del día la reproducción se detiene sola; ▶ vuelve a empezar desde la primera hora.

**Ir a una hora concreta**
- **Punta mañana** salta a las 07:30 y **Punta tarde** a las 17:30.
- Para cualquier otra hora, arrastra la barra de hora.

**Seguir a un bus**
1. Haz clic en el bus en el mapa. Un aviso confirma que quedó marcado y su fila aparece con ▸ en el panel.
2. Si en ese momento no va al punto elegido, el pie del panel lo indica.
3. **Quitar marca** deja de resaltarlo.

**Cambiar de día**
- Elige otro día en **Día que se repite**. El reloj vuelve a las 07:30 de ese día.

---

## 5. Colores del mapa

| Color | Significado |
|---|---|
| Verde azulado | Puntos de control de la **ida** (1 a 10). |
| Morado | Puntos de control de la **vuelta** (11 a 18). |
| Naranja | Buses que **van hacia el punto elegido**. |
| Gris | Otros buses en servicio. |
| Borde naranja grande | El punto elegido. |

La ida y la vuelta pasan por las mismas calles, por eso algunos puntos comparten etiqueta (por ejemplo, "3/17"). Además del color, cada estado se indica con texto o símbolo (✓, ✗, ▸, "en 5 min"), para que la aplicación pueda usarse sin distinguir colores.

---

## 6. Problemas frecuentes

| Problema | Solución |
|---|---|
| "Todavía no se entrenó la demo" | Ejecuta `python demo/entrenar.py` desde la raíz del repositorio y recarga la página. |
| El mapa se ve sin calles | No hay conexión a internet. Todo lo demás funciona igual. |
| "Ahora ningún bus viene hacia el punto X" | A esa hora no hay buses en camino a ese punto: pulsa ▶, avanza la hora o elige otro punto. |
| El marcador muestra un aviso en lugar de cifras | Todavía no llegó ningún bus en el día; avanza la hora. |
| La página quedó con errores tras editar el código | Detén Streamlit (Ctrl + C) y vuelve a lanzarlo: el estado de la sesión no sobrevive a algunos cambios del archivo. |
| `streamlit` no se reconoce como comando | Usa `python -m streamlit run demo/app.py`. |

---

## 7. Qué hay detrás (resumen)

- **Modelo**: Gradient Boosting con pérdida cuantílica. Un modelo da la llegada estimada y otros dos los extremos del rango.
- **Rango probable**: calibrado con CQR para que contenga 8 de cada 10 llegadas en los días de validación.
- **Datos**: entrenamiento del 6 al 22 de enero de 2025, validación del 23 al 26 y prueba (lo que muestra la aplicación) del 27 de enero al 1 de febrero.
- **Sin trampas**: cada predicción usa solo información disponible en el instante en que el bus pasó por su último punto de control.

Más detalle en el desplegable **Detalles del modelo** de la aplicación y en el paper del proyecto (`paper/paper_E2.tex`).
