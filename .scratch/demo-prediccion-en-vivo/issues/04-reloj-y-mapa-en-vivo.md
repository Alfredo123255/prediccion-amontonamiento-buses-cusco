# 04: Reloj ▶ x60 y mapa en vivo

**What to build:** El expositor pulsa ▶ y el reloj del día avanza a x60 (1 s real = 1 min simulado). Puede pausarlo o saltar de hora con el slider. Un mapa muestra la ruta, los 18 puntos de control numerados y la posición GPS de cada bus en el minuto actual. El bus se puede elegir desde la lista o desde el mapa, y su tabla se actualiza sola cuando pasa por un nuevo punto.

**Blocked by:** 01 (Tracer bullet: predicción P50 de un bus en Streamlit)

**Status:** ready-for-agent

- [ ] El script guarda, por cada día de prueba, las posiciones GPS ya limpias y las coordenadas de los 18 puntos.
- [ ] Botón ▶/⏸ que avanza el reloj a x60 sin recargar toda la página. El slider fija la hora.
- [ ] La hora simulada se ve en grande.
- [ ] El mapa muestra la ruta, los 18 puntos numerados y un marcador por bus en el minuto actual, usando solo componentes de Streamlit.
- [ ] El bus elegido se resalta en el mapa y su tabla se recalcula en cada avance del reloj.
- [ ] Sin internet, el mapa sigue mostrando la ruta y los buses, aunque sin fondo de calles.
- [ ] El avance del reloj es fluido en la laptop de la expo.
