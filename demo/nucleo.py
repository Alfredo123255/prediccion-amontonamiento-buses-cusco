"""Núcleo de predicción de la demo (sin Streamlit).

`pasos`: una fila por (paso real del bus por el punto k, destino kt > k) con las variables del notebook,
calculadas solo con información disponible en el instante del paso `a`. Tiempos en minutos desde medianoche.
"""
import pandas as pd

COLUMNAS = ["veh", "trip", "k", "a", "kt", "p50", "programada", "real"]


def predecir(pasos, modelo, features, instante):
    """Para cada bus, desde su último paso con a <= instante: llegada estimada (P50) a cada punto posterior,
    hora programada y hora real (solo si ya ocurrió).
    Al llegar al último punto de la vuelta la tabla se mantiene, con su hora real, hasta el primer paso de la siguiente."""
    vis = pasos[pasos.a <= instante]
    if vis.empty:
        return pd.DataFrame(columns=COLUMNAS)
    ult = vis.loc[vis.groupby("veh").a.idxmax(), ["veh", "trip", "k"]]
    d = vis.merge(ult, on=["veh", "trip", "k"]).sort_values(["veh", "kt"]).reset_index(drop=True)
    d["p50"] = d.a + modelo.predict(d[features])
    d["programada"] = d.s_t
    d["real"] = d.a_t.where(d.a_t <= instante)
    return d[COLUMNAS]
