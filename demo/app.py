"""Demo en vivo: streamlit run demo/app.py (antes: python demo/entrenar.py)."""
import socket
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

from nucleo import posiciones, predecir

ART = Path(__file__).resolve().parent / "artefactos" / "demo.joblib"


# joblib = pickle: solo se cargan artefactos generados localmente por entrenar.py
@st.cache_resource
def cargar():
    return joblib.load(ART)


# ponytail: prueba la red del servidor, no la del navegador; en la expo son la misma laptop
@st.cache_data(ttl=30)
def hay_internet():
    try:
        socket.create_connection(("basemaps.cartocdn.com", 443), timeout=1).close()
        return True
    except OSError:
        return False


@st.cache_data
def traza_ruta(_gps):
    """Huella de la ruta: GPS de los días de prueba en una grilla de ~50 m (unos 2000 puntos)."""
    return ((_gps[["lat", "lon"]] * 2000).round() / 2000).drop_duplicates()


def hhmm(minutos):
    return "" if pd.isna(minutos) else f"{int(minutos // 60):02d}:{int(minutos % 60):02d}"


st.set_page_config(page_title="ETA buses Cusco", layout="wide")
st.title("Predicción en vivo del tiempo de llegada")
if not ART.exists():
    st.error("Faltan los artefactos: corre primero `python demo/entrenar.py`.")
    st.stop()
art = cargar()
pasos = art["pasos"]
res = art["resumen"]
cifras = ("No había datos de clima para comparar." if res["mae_val_con_clima"] is None else
          f"MAE en validación: {res['mae_val_sin_clima']:.2f} min sin clima, {res['mae_val_con_clima']:.2f} min con clima.")
if res["usa_clima"]:
    st.info("Modelo: Gradient Boosting **con clima**: en validación mejoró el error, aunque el reanálisis ERA5 "
            "no existe en tiempo real. " + cifras)
else:
    st.info("Modelo: Gradient Boosting **sin clima**, a diferencia del modelo del paper: el clima viene del "
            "reanálisis ERA5, que no existe en tiempo real, y en la ablación del paper empeoró el error. " + cifras)

# día por defecto: el día laborable de prueba con más pasos registrados
n_pasos = pasos.drop_duplicates(["trip", "k"]).groupby("date").size()
laborables = n_pasos[pd.to_datetime(n_pasos.index).dayofweek < 5]
dias = sorted(n_pasos.index)
# al cambiar de día el reloj vuelve a la hora inicial de ese día (cada día tiene otro rango)
dia = st.selectbox("Día de prueba", dias, index=dias.index(laborables.idxmax()),
                   on_change=lambda: st.session_state.pop("instante", None))
pasos_dia = pasos[pasos.date == dia]
gps_dia = art["gps"][art["gps"].date == dia]
buses = sorted(set(pasos_dia.veh) | set(gps_dia.veh), key=lambda v: (len(v), v))

ini, fin = int(pasos_dia.a.min()), int(pasos_dia.a.max()) + 1
st.session_state.setdefault("instante", min(ini + 180, fin))  # 3 h después del primer paso
st.session_state.setdefault("play", False)
st.session_state.setdefault("version_mapa", 0)
st.session_state.setdefault("ultimo_tick", 0.0)


def play_pausa():
    st.session_state.play = not st.session_state.play
    if st.session_state.play and st.session_state.instante >= fin:
        st.session_state.instante = ini  # ▶ al final del día vuelve a empezar


def elegir_desde_mapa():
    objs = st.session_state[f"mapa_{st.session_state.version_mapa}"].selection.objects.get("buses")
    if objs:
        st.session_state.bus = objs[0]["veh"]
    # La selección de Streamlit va por índice y atenúa lo demás; con el reloj andando ese índice pasa a otro bus.
    # Una key nueva descarta la selección: el resaltado lo da el color naranja, que sigue al bus.
    st.session_state.version_mapa += 1


st.button("⏸ Pausa" if st.session_state.play else "▶ Reproducir x60", on_click=play_pausa)
fondo = {"map_style": None} if hay_internet() else {"map_provider": None}  # sin internet: sin calles, todo lo demás igual
traza = traza_ruta(art["gps"])
vista = pdk.data_utils.compute_view(traza[["lon", "lat"]], view_proportion=0.98)
vista.zoom = 11.4  # la ruta completa cabe en media pantalla
puntos = art["puntos"].assign(texto=art["puntos"].k.astype(str))


# Solo este fragmento se refresca cada segundo (1 s real = 1 min simulado); el resto de la página no se recarga.
@st.fragment(run_every=1 if st.session_state.play else None)
def en_vivo():
    # solo los ticks del temporizador avanzan el reloj, no las recargas por el slider, la lista o el mapa
    # ponytail: se distinguen por el tiempo desde el último avance; un clic justo al segundo también avanza 1 min
    if st.session_state.play and time.monotonic() - st.session_state.ultimo_tick >= 0.9:
        if st.session_state.instante >= fin:
            st.session_state.play = False
            st.rerun()  # recarga completa para apagar el refresco
        st.session_state.instante += 1
        st.session_state.ultimo_tick = time.monotonic()
    instante = st.slider("Hora", ini, fin, key="instante", format="%d min", step=1)
    st.markdown(f"<p style='font-size:4rem;font-weight:700;margin:0'>🕒 {hhmm(instante)}</p>", unsafe_allow_html=True)

    if st.session_state.get("bus") not in buses:
        st.session_state.bus = buses[0]
    pos = posiciones(gps_dia, instante)
    elegido = (pos.veh == st.session_state.bus).to_numpy()
    pos["color"] = np.where(elegido[:, None], [255, 140, 0, 255], [30, 100, 220, 220]).tolist()
    pos["radio"] = np.where(elegido, 140, 70)

    col_mapa, col_tabla = st.columns(2)
    with col_mapa:
        capas = [
            pdk.Layer("ScatterplotLayer", traza, get_position=["lon", "lat"],
                      get_radius=12, radius_min_pixels=1, get_fill_color=[120, 120, 120, 120]),
            pdk.Layer("ScatterplotLayer", puntos, get_position=["lon", "lat"], get_radius=90, radius_min_pixels=8,
                      get_fill_color=[255, 255, 255], stroked=True, get_line_color=[40, 40, 40], line_width_min_pixels=2),
            pdk.Layer("TextLayer", puntos, get_position=["lon", "lat"], get_text="texto", get_size=14,
                      get_color=[0, 0, 0]),
            pdk.Layer("ScatterplotLayer", pos, id="buses", pickable=True, get_position=["lon", "lat"],
                      get_radius="radio", radius_min_pixels=6, get_fill_color="color", stroked=True,
                      get_line_color=[255, 255, 255], line_width_min_pixels=1),
        ]
        st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=vista, tooltip={"text": "Bus {veh}"}, **fondo),
                        key=f"mapa_{st.session_state.version_mapa}", on_select=elegir_desde_mapa,
                        selection_mode="single-object", height=520)
        st.caption("Puntos blancos: los 18 puntos de control. Azul: buses en este minuto; naranja: el bus elegido "
                   "(clic en el mapa para elegirlo).")

    with col_tabla:
        bus = st.selectbox("Bus", buses, key="bus")
        rb = predecir(pasos_dia[pasos_dia.veh == bus], art["modelos"], art["features"], instante, art["q"])
        if rb.empty:
            st.info(f"El bus {bus} todavía no ha pasado por ningún punto de control.")
            return
        st.write(f"Último punto de control: **{int(rb.k.iloc[0])}** a las **{hhmm(rb.a.iloc[0])}**")
        st.dataframe(pd.DataFrame({
            "Punto": rb.kt.astype(int),
            "Estimada (P50)": rb.p50.map(hhmm),
            "Rango P10–P90": rb.p10.map(hhmm) + "–" + rb.p90.map(hhmm),
            "Programada": rb.programada.map(hhmm),
            "Real": rb.real.map(hhmm),
            "En rango": rb.dentro.map({True: "✅", False: ""}),
        }).style.apply(lambda fila: ["background-color: rgba(46, 160, 67, 0.2)" if rb.dentro[fila.name] else ""]
                       * len(fila), axis=1), hide_index=True)


en_vivo()
st.caption(f"Rango P10–P90 calibrado con CQR en validación: cubre {res['cob_val_despues']:.0%} en validación "
           f"(sin calibrar, {res['cob_val_antes']:.0%}) y {res['cob_test_despues']:.0%} en prueba.")
