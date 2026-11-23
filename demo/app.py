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

# día por defecto: el día laborable de prueba con más pasos registrados
n_pasos = pasos.drop_duplicates(["trip", "k"]).groupby("date").size()
laborables = n_pasos[pd.to_datetime(n_pasos.index).dayofweek < 5]
dias = sorted(n_pasos.index)
dia = st.selectbox("Día de prueba", dias, index=dias.index(laborables.idxmax()))
pasos_dia = pasos[pasos.date == dia]

ini, fin = int(pasos_dia.a.min()), int(pasos_dia.a.max()) + 1
instante = st.slider("Hora", ini, fin, value=min(ini + 180, fin), format="%d min", step=1)
st.subheader(f"🕒 {hhmm(instante)}")

r = predecir(pasos_dia, art["modelo"], art["features"], instante)
if r.empty:
    st.info("Ningún bus ha pasado todavía por un punto de control.")
    st.stop()

bus = st.selectbox("Bus", sorted(r.veh.unique(), key=lambda v: (len(v), v)))
rb = r[r.veh == bus]
st.write(f"Último punto de control: **{int(rb.k.iloc[0])}** a las **{hhmm(rb.a.iloc[0])}**")
st.dataframe(pd.DataFrame({
    "Punto": rb.kt.astype(int),
    "Estimada (P50)": rb.p50.map(hhmm),
    "Programada": rb.programada.map(hhmm),
    "Real": rb.real.map(hhmm),
}), hide_index=True)
