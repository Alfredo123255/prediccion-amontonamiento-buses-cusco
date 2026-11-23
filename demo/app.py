"""Demo en vivo: streamlit run demo/app.py (antes: python demo/entrenar.py)."""
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from nucleo import predecir

ART = Path(__file__).resolve().parent / "artefactos" / "demo.joblib"


# joblib = pickle: solo se cargan artefactos generados localmente por entrenar.py
@st.cache_resource
def cargar():
    return joblib.load(ART)


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
dia = st.selectbox("Día de prueba", dias, index=dias.index(laborables.idxmax()))
pasos_dia = pasos[pasos.date == dia]

ini, fin = int(pasos_dia.a.min()), int(pasos_dia.a.max()) + 1
instante = st.slider("Hora", ini, fin, value=min(ini + 180, fin), format="%d min", step=1)
st.subheader(f"🕒 {hhmm(instante)}")

r = predecir(pasos_dia, art["modelos"], art["features"], instante, art["q"])
if r.empty:
    st.info("Ningún bus ha pasado todavía por un punto de control.")
    st.stop()

bus = st.selectbox("Bus", sorted(r.veh.unique(), key=lambda v: (len(v), v)))
rb = r[r.veh == bus]
st.write(f"Último punto de control: **{int(rb.k.iloc[0])}** a las **{hhmm(rb.a.iloc[0])}**")
st.dataframe(pd.DataFrame({
    "Punto": rb.kt.astype(int),
    "Estimada (P50)": rb.p50.map(hhmm),
    "Rango P10–P90": rb.p10.map(hhmm) + "–" + rb.p90.map(hhmm),
    "Programada": rb.programada.map(hhmm),
    "Real": rb.real.map(hhmm),
    "En rango": rb.dentro.map({True: "✅", False: ""}),
}).style.apply(lambda fila: ["background-color: rgba(46, 160, 67, 0.2)" if rb.dentro[fila.name] else ""] * len(fila), axis=1),
    hide_index=True)
st.caption(f"Rango P10–P90 calibrado con CQR en validación: cubre {res['cob_val_despues']:.0%} en validación "
           f"(sin calibrar, {res['cob_val_antes']:.0%}) y {res['cob_test_despues']:.0%} en prueba.")
