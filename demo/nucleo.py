"""Núcleo de predicción de la demo (sin Streamlit).

`pasos`: una fila por (paso real del bus por el punto k, destino kt > k) con las variables del notebook,
calculadas solo con información disponible en el instante del paso `a`. Tiempos en minutos desde medianoche.
"""
import numpy as np
import pandas as pd

COLUMNAS = ["veh", "trip", "k", "a", "kt", "p10", "p50", "p90", "programada", "real", "dentro"]


def calibrar(lo, hi, y, cobertura=0.8):
    """Corrección CQR (Romano et al., 2019): el intervalo [lo - q, hi + q] cubre `cobertura` en la muestra
    de calibración. q < 0 estrecha un intervalo demasiado ancho."""
    e = np.maximum(np.asarray(lo) - y, np.asarray(y) - hi)
    n = len(e)
    return float(np.quantile(e, min(1.0, np.ceil((n + 1) * cobertura) / n), method="higher"))


def predecir(pasos, modelos, features, instante, q=0.0):
    """Para cada bus, desde su último paso con a <= instante: llegada estimada (P50) a cada punto posterior,
    rango P10–P90 calibrado con la corrección CQR `q`, hora programada, hora real (solo si ya ocurrió) y si
    cayó dentro del rango. `modelos`: {"p10", "p50", "p90"}. Garantiza P10 ≤ P50 ≤ P90.
    Al llegar al último punto de la vuelta la tabla se mantiene, con su hora real, hasta el primer paso de la siguiente."""
    vis = pasos[pasos.a <= instante]
    if vis.empty:
        return pd.DataFrame(columns=COLUMNAS)
    ult = vis.loc[vis.groupby("veh").a.idxmax(), ["veh", "trip", "k"]]
    d = vis.merge(ult, on=["veh", "trip", "k"]).sort_values(["veh", "kt"]).reset_index(drop=True)
    X = d[features]
    d["p50"] = d.a + modelos["p50"].predict(X)
    d["p10"] = np.minimum(d.a + modelos["p10"].predict(X) - q, d.p50)
    d["p90"] = np.maximum(d.a + modelos["p90"].predict(X) + q, d.p50)
    d["programada"] = d.s_t
    d["real"] = d.a_t.where(d.a_t <= instante)
    d["dentro"] = d.real.between(d.p10, d.p90)
    return d[COLUMNAS]


def posiciones(gps, instante, max_edad=5):
    """Último ping GPS de cada bus con instante - max_edad <= t <= instante (`gps`: veh, t, lat, lon).
    Un bus sin ping en los últimos `max_edad` minutos no se dibuja (fuera de servicio o sin señal)."""
    vis = gps[gps.t.between(instante - max_edad, instante)]
    return vis.loc[vis.groupby("veh").t.idxmax()].reset_index(drop=True)


def mae_acumulado(pasos, instante):
    """MAE del modelo y del horario hasta `instante`, sobre las predicciones hechas en pasos ya ocurridos
    (a <= instante) cuya llegada real también ya ocurrió (a_t <= instante). `pasos` trae `p50`: la llegada
    estimada en minutos desde medianoche. Devuelve (mae_modelo, mae_horario, n); sin filas, MAE = NaN."""
    d = pasos[(pasos.a <= instante) & (pasos.a_t <= instante)]
    return (d.p50 - d.a_t).abs().mean(), (d.s_t - d.a_t).abs().mean(), len(d)
