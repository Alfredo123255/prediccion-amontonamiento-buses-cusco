# Spec: demo de predicción en vivo del tiempo de llegada (ETA A→B)

Status: ready-for-agent

## Problem Statement

Para la exposición final del curso (viernes 27-nov-2026) los docentes pidieron una interfaz que haga una predicción en vivo. Hoy el proyecto solo tiene un notebook que tarda ~2 h, tablas de resultados y un paper. No hay nada que se pueda mostrar en pantalla mientras "pasa" un día de operación. Además, en esta laptop no están los modelos entrenados ni los datos, y el notebook completo es demasiado lento para regenerarlos antes de la expo.

Dos debilidades de la revisión del Entregable 2 afectan directamente a una demo en vivo:
- El rango P10–P90 cubre solo el 73,5 % de los casos: en vivo, el valor real caería fuera del rango 1 de cada 4 veces.
- El modelo usa clima de reanálisis ERA5, que no existe en tiempo real.

## Solution

Una app Streamlit que corre en local y reproduce un día de la semana de prueba como si ocurriera en vivo:
- Un reloj avanza a x60 y se puede saltar a cualquier hora con un slider.
- Un mapa muestra la ruta, los 18 puntos de control y la posición GPS de cada bus en ese minuto.
- Al elegir un bus, una tabla muestra su llegada estimada (P50) a cada punto posterior, con el rango P10–P90 calibrado, la hora programada y la hora real cuando ya se cumplió.
- El modelo se ejecuta en el instante en que el bus pasa por un punto de control, usando solo información disponible en ese instante.
- Un contador muestra el MAE acumulado del día, modelo frente al horario.

Un script de entrenamiento rápido (minutos, no horas) prepara todo lo que necesita la app a partir de los CSV originales.

## User Stories

1. Como expositor, quiero arrancar la demo con un solo comando, para no perder tiempo frente al jurado.
2. Como expositor, quiero que la demo funcione sin internet, salvo el fondo del mapa, para no depender de la red del aula.
3. Como expositor, quiero que por defecto se cargue el día laborable de prueba con más pasos registrados, para mostrar el caso más representativo.
4. Como expositor, quiero un selector para cambiar de día de prueba, para responder si el jurado pide otro día.
5. Como expositor, quiero un botón ▶ que avance el reloj a x60, para que el jurado vea pasar los buses en tiempo comprimido.
6. Como expositor, quiero pausar el reloj, para detenerme a explicar una predicción.
7. Como expositor, quiero un slider de hora, para saltar directo a la hora punta.
8. Como espectador, quiero ver la hora simulada actual en grande, para entender en qué momento del día estamos.
9. Como espectador, quiero ver la ruta y los 18 puntos de control numerados en un mapa, para ubicar el corredor en Cusco.
10. Como espectador, quiero ver la posición de cada bus en el mapa en el minuto actual, para sentir que es operación en vivo.
11. Como expositor, quiero elegir un bus (en una lista o al hacer clic), para mostrar sus predicciones.
12. Como espectador, quiero ver, para el bus elegido, el último punto por el que pasó y a qué hora, para entender desde dónde se predice.
13. Como espectador, quiero ver la llegada estimada (P50) a cada punto posterior, para saber cuándo llegará a cualquier destino.
14. Como espectador, quiero ver el rango P10–P90 de cada llegada, para saber cuánto confiar en la predicción.
15. Como espectador, quiero ver la hora programada junto a la estimada, para comparar el modelo con el horario.
16. Como espectador, quiero que la hora real aparezca solo cuando el reloj la alcanza, para que no se revele el futuro.
17. Como espectador, quiero que la fila se marque cuando la llegada real cae dentro del rango, para ver que el modelo acierta.
18. Como espectador, quiero que las predicciones se actualicen cada vez que el bus pasa por un nuevo punto, para ver cómo el modelo corrige con información nueva.
19. Como espectador, quiero ver el MAE acumulado del día del modelo y del horario, para tener evidencia cuantitativa en vivo.
20. Como jurado, quiero leer en la interfaz que el modelo de la demo no usa clima y por qué, para no confundirlo con el modelo del paper.
21. Como jurado, quiero ver qué modelo se usa (Gradient Boosting cuantílico calibrado) y su cobertura en validación, para evaluar el rigor.
22. Como integrante del grupo, quiero regenerar modelos y datos de la demo con un script de pocos minutos, para no depender del notebook de 2 h.
23. Como integrante del grupo, quiero que el script decida en validación (no en prueba) si se quita el clima, para no seleccionar variables con los datos de prueba.
24. Como integrante del grupo, quiero que el script reporte la cobertura P10–P90 antes y después de calibrar, para justificar la calibración en la expo.
25. Como integrante del grupo, quiero que los datos de los docentes y los artefactos generados no se versionen, para respetar la confidencialidad de los datos.
26. Como integrante del grupo, quiero un README de la demo con los pasos para correrla, para que cualquiera del grupo pueda presentarla.
27. Como expositor, quiero un GIF o video de respaldo de la demo, para mostrarla aunque falle la laptop o el proyector.
28. Como expositor, quiero que la app no se caiga si un bus no tiene GPS o le falta un paso, para que la demo no se interrumpa.
29. Como expositor, quiero que la app arranque rápido, cargando los artefactos una sola vez, para que el avance del reloj sea fluido.

## Implementation Decisions

- **Ubicación**: todo en la carpeta de la demo, en la rama `demo`. No se toca el notebook ni el paper.
- **Módulo de entrenamiento** (script):
  - Reconstruye el dataset de modelado con la misma lógica que el notebook: limpieza, Isolation Forest ajustado con entrenamiento, headways, variables GPS, buses recientes, altitud, y clima solo si se mantiene.
  - Respeta la partición temporal del proyecto: entrenamiento del 06 al 22 de enero, validación del 23 al 26, prueba del 27 de enero al 1 de febrero.
  - Entrena Gradient Boosting (HistGradientBoosting) con los hiperparámetros elegidos en el notebook (profundidad 6, tasa 0,1).
  - **Decisión sobre el clima**: compara en validación el MAE con y sin clima, y se queda sin clima salvo que empeore.
  - **Modelos de cuantiles**: P10, P50 y P90, entrenados con datos de entrenamiento.
  - **Calibración CQR**: usa validación para calcular la corrección que lleva la cobertura P10–P90 al 80 %, y la aplica a los cuantiles extremos.
  - Guarda los modelos, la corrección CQR, la lista de variables, un resumen de validación (MAE, cobertura antes y después) y, por cada día de prueba, las variables por paso y las posiciones GPS.
- **Módulo de predicción (núcleo, sin Streamlit)**:
  - Entrada: el día y un instante del reloj.
  - Salida: para cada bus que ya pasó por al menos un punto de control, la tabla de puntos posteriores con P10, P50 y P90 calibrados, la hora programada y la hora real (solo si es anterior o igual al instante).
  - Para cada bus usa el último paso registrado antes del instante; las variables de ese paso solo contienen información disponible en ese momento.
  - Garantiza P10 ≤ P50 ≤ P90.
  - Calcula también el MAE acumulado del modelo y del horario sobre las llegadas reales ya cumplidas.
- **Módulo de interfaz** (Streamlit):
  - Solo presentación: carga los artefactos una vez con caché y llama al núcleo en cada avance del reloj.
  - El reloj avanza con un fragmento que se refresca periódicamente; el slider fija la hora.
  - Mapa con los componentes nativos de Streamlit, sin dependencias nuevas salvo Streamlit.
- **Modelo**: Gradient Boosting en lugar de Random Forest; empatan en MAE (1,92 contra 1,90, sin significancia) y Gradient Boosting entrena ~70 veces más rápido y admite pérdida cuantílica.
- **Ejecución**: solo en local con `streamlit run`; no se despliega en ningún servicio porque los datos son de los docentes.
- **Dependencias**: se agrega Streamlit a los requisitos; nada más.

## Testing Decisions

- **Criterio**: una buena prueba ejercita el comportamiento externo del módulo (entradas → salidas) con datos sintéticos pequeños y no depende de detalles internos ni de los CSV reales.
- **Seam principal, el núcleo de predicción.** Con un mini-dataset sintético (2 buses, 3 puntos) y un modelo trivial, se verifica que:
  - nunca use pasos posteriores al instante;
  - P10 ≤ P50 ≤ P90;
  - la hora real aparezca solo cuando ya se cumplió;
  - un bus que todavía no pasó por ningún punto no aparezca;
  - el MAE acumulado solo considere llegadas reales ya ocurridas.
- **Seam secundario, la calibración CQR.** Con datos sintéticos de cobertura conocida, después de calibrar la cobertura en validación queda en 80 % ± 2 pp.
- **Interfaz**: sin prueba automática; se revisa a mano y con el GIF de respaldo.
- **Prior art**: el repo no tiene pruebas. Estas son las primeras: un solo archivo de pruebas, sin frameworks extra más allá de pytest o asserts.

## Out of Scope

- Pestaña de formulario A→B con hora elegida por el usuario. Solo si sobra tiempo el jueves, en una spec aparte.
- Modo de comparación separado: el MAE acumulado dentro de la repetición lo cubre.
- Random Forest en la demo.
- Despliegue en Streamlit Cloud u otro servicio.
- Cambios al notebook, a los resultados o al paper (las correcciones de la revisión, como la prueba de Wilcoxon por bloques independientes, van aparte).
- Predicción desde cualquier posición GPS; solo desde puntos de control.
- Pronóstico de clima en tiempo real.

## Further Notes

- **Bloqueante**: `Times.csv` y `Monitoring.csv` deben copiarse en la carpeta de datos del repo. No se versionan ni se suben a ningún servicio.
- El fondo del mapa necesita internet. Sin red se ve la ruta GPS sobre fondo liso.
- **Expo**: viernes 27-nov-2026. Orden de trabajo sugerido:
  1. Script de entrenamiento.
  2. Núcleo de predicción y sus pruebas.
  3. Interfaz.
  4. README.
  5. GIF de respaldo.
