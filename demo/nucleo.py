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


def cuantiles(d, modelos, features, q=0.0):
    """Agrega p10, p50 y p90 (llegada en minutos desde medianoche) con la corrección CQR `q`.
    Garantiza P10 ≤ P50 ≤ P90. `modelos`: {"p10", "p50", "p90"}."""
    X = d[features]
    p50 = d.a + modelos["p50"].predict(X)
    return d.assign(p50=p50, p10=np.minimum(d.a + modelos["p10"].predict(X) - q, p50),
                    p90=np.maximum(d.a + modelos["p90"].predict(X) + q, p50))


def paradero(pasos, modelos, features, instante, destino, q=0.0, ventana=15):
    """Panel de paradero para el punto `destino` en `instante`, ordenado por llegada.
    - Vienen: buses cuya vuelta actual todavía no llega al destino; se predice desde su último paso.
      Si su llegada real falta en los datos, la fila se descarta `ventana` min después de su P90.
    - Llegaron: vueltas cuya llegada real fue en los últimos `ventana` min, con la predicción hecha
      desde su último paso antes de llegar. `real` solo se llena si ya ocurrió."""
    vis = pasos[pasos.a <= instante]
    d = vis[vis.kt == destino]
    if d.empty:
        return pd.DataFrame(columns=COLUMNAS)
    d = d.loc[d.groupby(["veh", "trip"]).a.idxmax()]  # predicción más reciente de cada vuelta
    actual = d.a.to_numpy() == vis.groupby("veh").a.max().reindex(d.veh).to_numpy()
    llego = d.a_t <= instante
    d = d[(llego & (d.a_t > instante - ventana)) | (~llego & actual)]
    if d.empty:
        return pd.DataFrame(columns=COLUMNAS)
    d = cuantiles(d, modelos, features, q)
    d = d[d.a_t.notna() | (d.p90 > instante - ventana)]
    d = d.assign(programada=d.s_t, real=d.a_t.where(d.a_t <= instante))
    d["dentro"] = d.real.between(d.p10, d.p90)
    return d.sort_values(["p50"]).reset_index(drop=True)[COLUMNAS]


def posiciones(gps, instante, max_edad=5):
    """Último ping GPS de cada bus con instante - max_edad <= t <= instante (`gps`: veh, t, lat, lon).
    Un bus sin ping en los últimos `max_edad` minutos no se dibuja (fuera de servicio o sin señal)."""
    vis = gps[gps.t.between(instante - max_edad, instante)]
    return vis.loc[vis.groupby("veh").t.idxmax()].reset_index(drop=True)


def marcador(pasos, instante):
    """Marcador del día hasta `instante`, sobre las predicciones hechas en pasos ya ocurridos (a <= instante)
    cuya llegada real también ya ocurrió (a_t <= instante). `pasos` trae p10, p50 y p90.
    Devuelve (error medio del modelo, error medio del horario, fracción dentro del rango, n); sin filas, NaN."""
    d = pasos[(pasos.a <= instante) & (pasos.a_t <= instante)]
    return ((d.p50 - d.a_t).abs().mean(), (d.s_t - d.a_t).abs().mean(),
            d.a_t.between(d.p10, d.p90).mean(), len(d))
