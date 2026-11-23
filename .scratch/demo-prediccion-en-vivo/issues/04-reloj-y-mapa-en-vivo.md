# 04: Reloj ▶ x60 y mapa en vivo

**What to build:** El expositor pulsa ▶ y el reloj del día avanza a x60 (1 s real = 1 min simulado). Puede pausarlo o saltar de hora con el slider. Un mapa muestra la ruta, los 18 puntos de control numerados y la posición GPS de cada bus en el minuto actual. El bus se puede elegir desde la lista o desde el mapa, y su tabla se actualiza sola cuando pasa por un nuevo punto.

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** ready-for-agent

- [x] El script guarda, por cada día de prueba, las posiciones GPS ya limpias y las coordenadas de los 18 puntos.
- [x] Botón ▶/⏸ que avanza el reloj a x60 sin recargar toda la página. El slider fija la hora.
- [x] La hora simulada se ve en grande.
- [x] El mapa muestra la ruta, los 18 puntos numerados y un marcador por bus en el minuto actual, usando solo componentes de Streamlit.
- [x] El bus elegido se resalta en el mapa y su tabla se recalcula en cada avance del reloj.
- [x] Sin internet, el mapa sigue mostrando la ruta y los buses, aunque sin fondo de calles.
- [x] El avance del reloj es fluido en la laptop de la expo.

## Comments

- 2026-11-23, implementado en `demo/entrenar.py` (guarda el GPS limpio de los días de prueba y los 18 puntos), `demo/nucleo.py` (`posiciones`, con prueba) y `demo/app.py`. Probado en Chromium: ▶ avanza ~1 min por segundo, ⏸ detiene, clic en un bus del mapa lo elige (naranja) y cambia la tabla; un rerun completo tarda ~0,2 s.
- La "ruta" es la huella del GPS de prueba en una grilla de ~50 m (≈1900 puntos grises), no una línea: muestra el trazado real de las calles sin datos extra.
- Mapa con `st.pydeck_chart` (pydeck viene con Streamlit). Sin internet se usa `map_provider=None`: no hay fondo de calles y las capas se dibujan igual (verificado leyendo el frontend de Streamlit y con AppTest, no desconectando la red).
- Tras cada clic en el mapa se cambia la key del gráfico para descartar la selección de Streamlit (va por índice y, con el reloj andando, apuntaba a otro bus). Efecto: el zoom manual se reinicia con cada clic.
- A x60 los buses se mueven cada segundo; para elegir uno con clic conviene pausar.
