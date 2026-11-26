"""Demo en vivo: streamlit run demo/app.py (antes: python demo/entrenar.py). Pensada para 1920×1080."""
import socket
import time
from datetime import time as Hora, timedelta
from pathlib import Path

import altair as alt
import joblib
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

from nucleo import cuantiles, marcador, paradero, posiciones

ART = Path(__file__).resolve().parent / "artefactos" / "demo.joblib"
# Contraste WCAG AA sobre el fondo #F5F7F8: GRIS y NARANJA_TXT ≥ 4,5:1 (texto); NARANJA ≥ 3:1 (marcas gráficas)
NARANJA, NARANJA_SUAVE, NARANJA_TXT, GRIS, TINTA = "#E8711A", "#F7C9A0", "#B85309", "#66737C", "#1E2A33"
IDA, VUELTA, ACIERTO, FALLO = "#1C7C7D", "#6B4C9A", "#2F9E5B", "#D1453B"
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
HHMM = "timeFormat(datetime(2000, 0, 1, 0, datum.value), '%H:%M')"  # minutos desde medianoche -> HH:MM

CSS = f"""<style>
header[data-testid="stHeader"], footer {{display: none}}
.block-container {{padding: 1.2rem 2.2rem 1rem; max-width: none}}
.titulo {{font-size: 2rem; font-weight: 700; margin: 0; line-height: 1.2}}
.titulo small {{display: block; font-size: 1rem; font-weight: 400; color: {GRIS}}}
.reloj {{font-size: 4.2rem; font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums;
         letter-spacing: -0.02em}}
.senal {{display: flex; align-items: center; gap: 0.9rem}}
.senal .num {{background: var(--c); color: white; font-weight: 800; font-size: 2.1rem; min-width: 3.6rem;
              text-align: center; border-radius: 0.6rem; padding: 0.2rem 0.6rem}}
.senal h2 {{font-size: 1.5rem; margin: 0; padding: 0; line-height: 1.2}}
.senal span.sub {{color: {GRIS}; font-size: 1rem}}
.marcador {{display: grid; grid-template-columns: 1fr 1fr 1.1fr; gap: 1.4rem; margin: 0.6rem 0 0.4rem;
            padding: 0.9rem 0 1rem; border-top: 2px solid #DDE3E6; border-bottom: 2px solid #DDE3E6}}
.marcador .cifra {{font-size: 2.3rem; font-weight: 800; line-height: 1.1; font-variant-numeric: tabular-nums}}
.marcador .txt {{font-size: 0.98rem; color: #4B5A64}}
.leyenda {{color: #4B5A64; font-size: 0.95rem}}
.leyenda b {{font-weight: 600; color: {TINTA}}}
.dot {{display: inline-block; width: 0.8em; height: 0.8em; border-radius: 50%; vertical-align: -0.05em;
       margin: 0 0.25em 0 0.9em}}
.estado {{display: inline-block; font-size: 0.9rem; font-weight: 700; padding: 0.1rem 0.6rem; border-radius: 1rem;
          margin-top: 0.35rem; white-space: nowrap}}
.estado.vivo {{background: {NARANJA_TXT}; color: white}}
.estado.pausa {{background: #DDE3E6; color: {TINTA}}}
.fecha {{font-size: 1rem; color: {GRIS}; font-weight: 600}}
.marcador > div[title] {{cursor: help}}
.vacio {{color: #4B5A64; font-size: 1rem; padding: 0.4rem 0}}
</style>"""


# joblib = pickle: solo se cargan artefactos generados localmente por entrenar.py
@st.cache_resource(show_spinner="Cargando los modelos y el día de prueba…")
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


@st.cache_data
def etiquetas(_puntos, umbral=0.005):
    """Una etiqueta por grupo de puntos encimados en el mapa (ida y vuelta pasan por la misma vía): "3/17"."""
    grupos = []  # ponytail: agrupación voraz, basta para 18 puntos
    for r in _puntos.itertuples():
        g = next((g for g in grupos if abs(g["lat"] - r.lat) + abs(g["lon"] - r.lon) < umbral), None)
        if g:
            g["k"].append(r.k)
        else:
            grupos.append({"lat": r.lat, "lon": r.lon, "k": [r.k]})
    return pd.DataFrame([{**g, "texto": "/".join(map(str, g["k"]))} for g in grupos])


# Cuantiles de todo el día una sola vez (~1 s); el marcador solo filtra en cada tick
@st.cache_data(show_spinner="Calculando las predicciones del día…")
def estimados_dia(dia):
    return cuantiles(pasos[pasos.date == dia], art["modelos"], art["features"], art["q"])


def hhmm(minutos):
    return f"{int(minutos // 60):02d}:{int(minutos % 60):02d}"


def a_min(h):
    return h.hour * 60 + h.minute


def a_hora(m):
    return Hora(int(m) // 60, int(m) % 60)


def num(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def sentido(k):
    return "ida" if k <= 10 else "vuelta"


def nombre_punto(k):
    extra = {10: " · extremo", 18: " · fin"}.get(k, "")
    return f"Punto {k} · {sentido(k)}{extra}"


def nombre_dia(d):
    t = pd.Timestamp(d)
    return f"{DIAS[t.dayofweek]} {t.day} {MESES[t.month - 1]} {t.year}"


st.set_page_config(page_title="¿Cuándo llega el bus? · Cusco", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
if not ART.exists():
    st.error("**Todavía no se entrenó la demo.** Desde la raíz del repositorio:\n\n"
             "1. Copia `Times.csv` y `Monitoring.csv` en `Dataset/`.\n"
             "2. Ejecuta `python demo/entrenar.py` (unos 5 minutos).\n"
             "3. Recarga esta página.\n\nMás detalles en `demo/GUIA_DE_USO.md`.")
    st.stop()
art = cargar()
pasos, res = art["pasos"], art["resumen"]

# día por defecto: el día laborable de prueba con más pasos registrados
n_pasos = pasos.drop_duplicates(["trip", "k"]).groupby("date").size()
laborables = n_pasos[pd.to_datetime(n_pasos.index).dayofweek < 5]
dias = sorted(n_pasos.index)

c_tit, c_dia, c_ayuda = st.columns([4.6, 1.1, 0.75], vertical_alignment="bottom")
c_tit.markdown("<div class='titulo'>¿Cuándo llega el bus?<small>Un día real de operación en Cusco, "
               "repetido como si fuera en vivo: el modelo predice la llegada a cada punto de control.</small></div>",
               unsafe_allow_html=True)
# al cambiar de día el reloj vuelve a las 07:30 de ese día
dia = c_dia.selectbox("Día que se repite", dias, index=dias.index(laborables.idxmax()), format_func=nombre_dia,
                      on_change=lambda: st.session_state.pop("hora", None),
                      help="Uno de los 6 días de prueba (27-ene al 1-feb de 2025), que el modelo nunca vio al entrenar.")
with c_ayuda.popover("¿Cómo se usa?", width="stretch"):
    st.markdown(
        "1. **Elige un punto de control**: haz clic en un círculo del mapa o usa *Ver otro punto*.\n"
        "2. **Pulsa ▶ Reproducir**: el día avanza 1 minuto por segundo. ⏸ lo detiene; la barra de hora "
        "salta a cualquier momento.\n"
        "3. **Lee el panel**: cada fila es un bus que viene. El **punto naranja** es la llegada estimada, la "
        "**barra** es el rango donde caen 8 de cada 10 llegadas y la **raya gris** es la hora del horario.\n"
        "4. **Al llegar el bus** aparece un rombo: ✓ verde si cayó dentro del rango, ✗ rojo si no.\n"
        "5. **El marcador** compara el error del modelo con el del horario en lo que va del día.\n\n"
        "Clic en un bus del mapa lo marca con ▸ en el panel. Guía completa: `demo/GUIA_DE_USO.md`.")
pasos_dia = pasos[pasos.date == dia]
gps_dia = art["gps"][art["gps"].date == dia]

ini, fin = int(pasos_dia.a.min()), min(int(pasos_dia.a.max()) + 1, 23 * 60 + 59)


def iniciar_estado():
    """Valores por defecto. También se llama al inicio de cada tick: Streamlit puede descartar el estado de un
    widget (hora, destino) entre ejecuciones y el fragmento corre sin pasar por el resto del script."""
    st.session_state.setdefault("hora", a_hora(min(max(7 * 60 + 30, ini), fin)))
    st.session_state.setdefault("play", False)
    st.session_state.setdefault("destino", 10)
    st.session_state.setdefault("bus", None)
    st.session_state.setdefault("version_mapa", 0)
    st.session_state.setdefault("ultimo_tick", 0.0)


iniciar_estado()


def saltar(m):
    st.session_state.hora = a_hora(min(max(m, ini), fin))


def clic_mapa():
    mapa = st.session_state.get(f"mapa_{st.session_state.get('version_mapa', 0)}")
    if mapa is None:  # clic de un mapa que ya se reemplazó: se ignora
        return
    sel = mapa.selection.objects
    k = (sel.get("paraderos") or [{}])[0].get("k")
    if k == 1:  # el punto 1 es la salida: ningún bus "llega" a él
        st.session_state.aviso = "El punto 1 es la salida de la ruta: ningún bus llega ahí. Elige otro punto."
    elif k:
        st.session_state.destino = k
    if sel.get("buses"):
        st.session_state.bus = sel["buses"][0]["veh"]
        st.session_state.aviso = f"Bus {st.session_state.bus} marcado con ▸ en el panel."
    # La selección de Streamlit va por índice y atenúa lo demás; con el reloj andando ese índice pasa a otro bus.
    # Una key nueva descarta la selección: el resaltado lo dan los colores, que siguen al bus y al punto.
    st.session_state.version_mapa += 1


fondo = {"map_style": None} if hay_internet() else {"map_provider": None}  # sin internet: sin calles, todo lo demás igual
traza = traza_ruta(art["gps"])
pp = art["puntos"]
vista = pdk.ViewState(latitude=(pp.lat.min() + pp.lat.max()) / 2 - 0.004,  # deja aire abajo para las etiquetas
                      longitude=(pp.lon.min() + pp.lon.max()) / 2, zoom=12.2)  # los 18 puntos en ~1100 px
etiq = etiquetas(art["puntos"])


def grafico(r, instante):
    """Línea de tiempo del paradero: una fila por bus, en orden de llegada."""
    resaltado = r.veh == st.session_state.bus
    r = r.assign(
        fila=np.where(resaltado, "▸ Bus ", "Bus ") + r.veh.astype(str),
        acierto=np.where(r.dentro, "sí", "no"),
        # ✓/✗ además del color del rombo: el acierto no depende solo de distinguir verde y rojo
        nota=np.where(r.real.notna(), np.where(r.dentro, "✓ llegó dentro del rango", "✗ llegó fuera del rango"),
                      np.where(r.p50 - instante < 0.5, "llegando",
                               "en " + (r.p50 - instante).round().astype(int).astype(str) + " min")),
        x_nota=np.fmax(np.fmax(r.p90, r.programada), r.real.fillna(-1)),
    )
    lo, hi = min(instante - 15, r.p10.min() - 2, r.real.min() - 2), max(r.x_nota.max() + 14, instante + 20)
    eje_x = alt.X("p10:Q", scale=alt.Scale(domain=[lo, hi], clamp=True), title=None,
                  axis=alt.Axis(labelExpr=HHMM, tickCount=8, grid=True, gridColor="#E4EAED", labelFontSize=15))
    base = alt.Chart(r).encode(y=alt.Y("fila:N", sort=None, title=None,
                                       axis=alt.Axis(labelFontSize=18, labelFontWeight=600, ticks=False,
                                                     domain=False, labelPadding=10, labelColor=TINTA)))
    capas = [
        base.mark_bar(height=16, cornerRadius=8, color=NARANJA_SUAVE).encode(x=eje_x, x2="p90:Q"),
        alt.Chart(pd.DataFrame({"t": [instante]})).mark_rule(color=TINTA, strokeDash=[5, 4], size=2).encode(x="t:Q"),
        base.mark_tick(thickness=3, size=30, color=GRIS).encode(x="programada:Q"),
        base.mark_point(filled=True, size=260, color=NARANJA, opacity=1).encode(x="p50:Q"),
        base.transform_filter("isValid(datum.real)").mark_point(shape="diamond", filled=True, size=320, opacity=1)
        .encode(x="real:Q", color=alt.Color("acierto:N", scale=alt.Scale(domain=["sí", "no"],
                                                                            range=[ACIERTO, FALLO]), legend=None)),
        base.mark_text(align="left", dx=16, fontSize=16, color="#4B5A64").encode(x="x_nota:Q", text="nota:N"),
    ]
    return alt.layer(*capas).properties(height=max(150, 44 * len(r))).configure_view(stroke=None)


# Solo este fragmento se refresca cada segundo (1 s real = 1 min simulado); el resto de la página no se recarga.
@st.fragment(run_every=1 if st.session_state.play else None)
def en_vivo():
    iniciar_estado()
    # solo los ticks del temporizador avanzan el reloj, no las recargas por el slider, la lista o el mapa
    # ponytail: se distinguen por el tiempo desde el último avance; un clic justo al segundo también avanza 1 min
    if st.session_state.play and time.monotonic() - st.session_state.ultimo_tick >= 0.9:
        if a_min(st.session_state.hora) >= fin:
            st.session_state.play = False
            st.rerun()  # recarga completa para apagar el refresco
        saltar(a_min(st.session_state.hora) + 1)
        st.session_state.ultimo_tick = time.monotonic()
    if aviso := st.session_state.pop("aviso", None):
        st.toast(aviso, icon=":material/info:")

    c_reloj, c_play, c_man, c_tar, c_slider = st.columns([1.35, 0.85, 0.95, 0.95, 4.9], vertical_alignment="center")
    if c_play.button("⏸ Pausar" if st.session_state.play else "▶ Reproducir", type="primary",
                     key="boton_play", width="stretch",
                     help="Pausa la simulación" if st.session_state.play else
                     "Avanza el día 1 minuto por cada segundo real"):
        st.session_state.play = not st.session_state.play
        if st.session_state.play and a_min(st.session_state.hora) >= fin:
            saltar(ini)  # ▶ al final del día vuelve a empezar
        st.rerun()  # recarga completa: el temporizador del fragmento se fija al cargar la página
    c_man.button("Punta mañana", on_click=saltar, args=(7 * 60 + 30,), width="stretch",
                 help="Salta a las 07:30, hora punta de la mañana")
    c_tar.button("Punta tarde", on_click=saltar, args=(17 * 60 + 30,), width="stretch",
                 help="Salta a las 17:30, hora punta de la tarde")
    c_slider.slider("Hora del día", a_hora(ini), a_hora(fin), key="hora", step=timedelta(minutes=1),
                    format="HH:mm", label_visibility="collapsed",
                    help="Arrastra para ir a cualquier hora del día de servicio")
    instante = a_min(st.session_state.hora)
    estado = ("<span class='estado vivo'>● EN VIVO ×60</span>" if st.session_state.play
              else "<span class='estado pausa'>⏸ EN PAUSA</span>")
    c_reloj.markdown(f"<div class='reloj'>{hhmm(instante)}</div><span class='fecha'>{nombre_dia(dia)}</span> "
                     f"{estado}", unsafe_allow_html=True)

    destino = st.session_state.destino
    r = paradero(pasos_dia, art["modelos"], art["features"], instante, destino, art["q"])
    vienen = set(r.veh[r.real.isna()])
    mas = max(len(vienen) - 6, 0)
    r = pd.concat([r[r.real.notna()], r[r.real.isna()].head(6)])  # en el panel, solo los 6 más próximos

    col_mapa, col_panel = st.columns([1.45, 1], gap="large")
    with col_mapa:
        pos = posiciones(gps_dia, instante)
        pos["color"] = [list(int(NARANJA[i:i + 2], 16) for i in (1, 3, 5)) + [255] if v in vienen
                        else [110, 125, 135, 200] for v in pos.veh]
        pos["radio"] = np.where(pos.veh == st.session_state.bus, 190, 95)
        pos["tip"] = "Bus " + pos.veh.astype(str)
        pts = art["puntos"].assign(
            color=[[28, 124, 125] if k <= 10 else [107, 76, 154] for k in art["puntos"].k],
            radio=np.where(art["puntos"].k == destino, 210, 85),
            borde=[[232, 113, 26] if k == destino else [255, 255, 255] for k in art["puntos"].k],
            tip=[f"Punto {k} ({sentido(k)}): clic para ver sus llegadas" for k in art["puntos"].k])
        capas = [
            pdk.Layer("ScatterplotLayer", traza, get_position=["lon", "lat"], get_radius=14, radius_min_pixels=1.5,
                      get_fill_color=[150, 160, 168, 140]),
            pdk.Layer("ScatterplotLayer", pts, id="paraderos", pickable=True, get_position=["lon", "lat"],
                      get_radius="radio", radius_min_pixels=7, get_fill_color="color", stroked=True,
                      get_line_color="borde", line_width_min_pixels=3),
            pdk.Layer("TextLayer", etiq, get_position=["lon", "lat"], get_text="texto", get_size=17,
                      get_color=[30, 42, 51], get_pixel_offset=[0, -24], font_weight=700, background=True,
                      get_background_color=[255, 255, 255, 230], background_padding=[5, 2]),
            pdk.Layer("ScatterplotLayer", pos, id="buses", pickable=True, get_position=["lon", "lat"],
                      get_radius="radio", radius_min_pixels=6, get_fill_color="color", stroked=True,
                      get_line_color=[255, 255, 255], line_width_min_pixels=2),
        ]
        st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=vista, tooltip={"text": "{tip}"}, **fondo),
                        key=f"mapa_{st.session_state.version_mapa}", on_select=clic_mapa,
                        selection_mode="single-object", height=700)
        st.markdown(
            f"<div class='leyenda'>Puntos de control: <span class='dot' style='background:{IDA}'></span><b>ida</b> "
            f"(1 a 10) <span class='dot' style='background:{VUELTA}'></span><b>vuelta</b> (11 a 18). Buses: "
            f"<span class='dot' style='background:{NARANJA}'></span><b>van a tu punto</b>"
            f"<span class='dot' style='background:#6E7D87'></span><b>otros</b>. "
            f"Clic en un punto: ver sus llegadas. Clic en un bus: marcarlo en el panel.</div>", unsafe_allow_html=True)

    with col_panel:
        c_senal, c_lista = st.columns([2.3, 1.2], vertical_alignment="center")
        c_senal.markdown(
            f"<div class='senal'><span class='num' style='--c:{IDA if destino <= 10 else VUELTA}'>{destino}</span>"
            f"<div><h2>Llegadas al punto {destino}</h2><span class='sub'>Punto de control de la "
            f"{sentido(destino)}{', extremo de la ruta' if destino == 10 else ''}</span></div></div>",
            unsafe_allow_html=True)
        c_lista.selectbox("Ver otro punto", range(2, 19), key="destino", format_func=nombre_punto,
                          help="También puedes hacer clic en un punto del mapa. El punto 1 es la salida.")

        mae_m, mae_h, cob, n = marcador(estimados_dia(dia), instante)
        if n > 0 and mae_m > 0:
            st.markdown(
                f"<div class='marcador'>"
                f"<div title='Diferencia promedio entre la llegada estimada y la real, en todas las predicciones "
                f"del día cuya llegada ya ocurrió.'><div class='cifra' style='color:{NARANJA_TXT}'>"
                f"{num(mae_m)} min</div><div class='txt'>error promedio del modelo hoy</div></div>"
                f"<div title='Diferencia promedio entre la hora del horario oficial y la llegada real, sobre las "
                f"mismas llegadas.'><div class='cifra' style='color:{GRIS}'>{num(mae_h)} min</div>"
                f"<div class='txt'>error del horario oficial: el modelo es "
                f"<b>{num(mae_h / mae_m)} veces más preciso</b></div></div>"
                f"<div title='Si el rango está bien calibrado, debería contener a 8 de cada 10 llegadas reales.'>"
                f"<div class='cifra'>{cob * 100:.0f} %</div>"
                f"<div class='txt'>de las llegadas cayó dentro del rango probable (se espera 80 %)</div></div>"
                f"</div><div class='leyenda'>Acumulado del día sobre {f'{n:,}'.replace(',', ' ')} predicciones "
                f"cuya llegada ya ocurrió. Pasa el cursor sobre una cifra para ver qué mide.</div>",
                unsafe_allow_html=True)
        else:
            st.markdown("<div class='marcador'><div class='vacio' style='grid-column: 1 / -1'>El marcador se llena "
                        "cuando llegan los primeros buses del día. Pulsa ▶ Reproducir o avanza la hora.</div></div>",
                        unsafe_allow_html=True)

        if r.empty:
            st.info(f"Ahora ningún bus viene hacia el punto {destino}. Pulsa ▶ Reproducir, avanza la hora o "
                    f"elige otro punto en el mapa.")
        else:
            st.altair_chart(grafico(r, instante), width="stretch")
            st.markdown(
                f"<div class='leyenda'><span class='dot' style='background:{NARANJA};margin-left:0'></span>"
                f"<b>llegada estimada</b><span class='dot' style='background:{NARANJA_SUAVE};border-radius:3px;"
                f"width:1.6em'></span><b>rango probable</b> (8 de cada 10)"
                f"<span class='dot' style='background:{GRIS};border-radius:1px;width:0.25em'></span><b>horario</b>"
                f"<span class='dot' style='border-left:2px dashed {TINTA};border-radius:0;width:0'></span><b>ahora</b>"
                f"<span class='dot' style='background:{ACIERTO};border-radius:2px;transform:rotate(45deg)'></span>"
                f"<b>✓ llegó en el rango</b>"
                f"<span class='dot' style='background:{FALLO};border-radius:2px;transform:rotate(45deg)'></span>"
                f"<b>✗ fuera</b></div>", unsafe_allow_html=True)

        # una sola línea al pie del panel: buses que no caben y bus marcado (no empuja la pantalla hacia abajo)
        bus = st.session_state.bus
        pie = [f"y {mas} buses más en camino."] if mas else []
        if bus is not None:
            pie.append(f"▸ Bus {bus} marcado{'' if bus in set(r.veh) else f' (ahora no va al punto {destino})'}.")
        if pie:
            c_pie, c_quitar = st.columns([3, 1], vertical_alignment="center")
            c_pie.markdown(f"<div class='leyenda'>{' '.join(pie)}</div>", unsafe_allow_html=True)
            if bus is not None and c_quitar.button("Quitar marca", key="quitar_bus", width="stretch",
                                                   help=f"Deja de resaltar el bus {bus}"):
                st.session_state.bus = None
                st.rerun(scope="fragment")


en_vivo()

with st.expander("Detalles del modelo"):
    clima = ("No había datos de clima para comparar." if res["mae_val_con_clima"] is None else
             f"En validación, el error fue {num(res['mae_val_sin_clima'], 2)} min sin clima y "
             f"{num(res['mae_val_con_clima'], 2)} min con clima.")
    st.markdown(f"""
- **Modelo**: Gradient Boosting (HistGradientBoosting, profundidad 6, tasa 0,1) con pérdida cuantílica: un modelo
  para la llegada estimada (P50) y dos para los extremos del rango (P10 y P90). Error promedio en prueba:
  {num(res['mae_test'], 2)} min.
- **Clima**: {"se usa, porque en validación mejoró el error, aunque el reanálisis ERA5 no existe en tiempo real."
  if res["usa_clima"] else "no se usa, a diferencia del modelo del paper: viene del reanálisis ERA5, que no "
  "existe en tiempo real, y en la ablación del paper empeoró el error."} {clima}
- **Rango probable**: calibrado con CQR (Romano et al., 2019) en validación. Cubre {res['cob_val_despues']:.0%} en
  validación (sin calibrar, {res['cob_val_antes']:.0%}) y {res['cob_test_despues']:.0%} en prueba.
- **Partición temporal**: entrenamiento del 6 al 22 de enero de 2025, validación del 23 al 26 y prueba (lo que se
  ve aquí) del 27 de enero al 1 de febrero. El modelo solo usa información disponible en el instante en que el bus
  pasa por un punto de control.
""")
