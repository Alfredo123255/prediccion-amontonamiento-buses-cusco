"""Entrenamiento rápido de la demo (minutos, no horas).

Reconstruye el dataset de modelado con la misma lógica que `Experimentacion.ipynb` (secciones 1–3),
decide en validación si se usa el clima (sin clima, salvo que quitarlo empeore el MAE), entrena Gradient Boosting
(profundidad 6, tasa 0,1): P50 con entrenamiento + validación; P10 y P90 con
entrenamiento, calibrados con CQR en validación para cubrir el 80 %. Guarda en `demo/artefactos/demo.joblib`
los modelos, la corrección CQR, un resumen y, de los días de prueba, los pasos y el GPS limpio
(más las coordenadas de los 18 puntos). Nada de eso se versiona.

Correr desde cualquier carpeta: python demo/entrenar.py
"""
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from nucleo import calibrar

warnings.filterwarnings("ignore", category=UserWarning)
T0 = time.perf_counter()
ROOT = Path(__file__).resolve().parent.parent
DATA, EXT = ROOT / "Dataset", ROOT / "datos_externos"
OUT = ROOT / "demo" / "artefactos"

SEED = 42
DELTAS = list(range(1, 18))
TRAIN_END, VAL_END = "2025-01-22", "2025-01-26"
MAX_DELAY = 60  # |retraso| > 60 min se considera error de registro
MAX_H = 60      # headways > 60 min = fin de servicio / error
MAX_AGE = 60    # un bus que terminó el tramo hace > 60 min ya no informa del tráfico actual
SLOW = 5        # km/h: "detenido o casi detenido"

# --- 1. Times.csv: pasos por punto de control, limpieza e Isolation Forest (ajustado con entrenamiento)
t = pd.read_csv(DATA / "Times.csv", dtype={"vehicle_id_id": str})
arr = ["start_time", "end_time", "difference_time"]
for c in arr:
    t[c] = t[c].str.strip("{}").str.split(",")
p = t.explode(arr).reset_index(drop=True)
p["k"] = p.groupby("id").cumcount() + 1
p = p.rename(columns={"id": "trip", "vehicle_id_id": "veh"})
p["s"] = pd.to_timedelta(p.start_time).dt.total_seconds() / 60
p["a"] = pd.to_timedelta(p.end_time).dt.total_seconds() / 60
p = p[["trip", "date", "veh", "lap", "k", "s", "a"]].sort_values(["trip", "k"]).reset_index(drop=True)
p.loc[p.a == 0, "a"] = np.nan
p["delay"] = p.a - p.s
p.loc[p.delay.abs() > MAX_DELAY, ["a", "delay"]] = np.nan
prev_max = p.groupby("trip").a.cummax().groupby(p.trip).shift().groupby(p.trip).ffill()
p.loc[p.a < prev_max, ["a", "delay"]] = np.nan
p["ddelay"] = p.delay - p.groupby("trip").delay.shift()
ok = p[["delay", "ddelay"]].notna().all(axis=1)
iso_p = IsolationForest(contamination=0.001, random_state=SEED).fit(p.loc[ok & (p.date <= TRAIN_END), ["delay", "ddelay"]])
bad = pd.Series(False, index=p.index)
bad[ok] = iso_p.predict(p.loc[ok, ["delay", "ddelay"]]) == -1
p.loc[bad, ["a", "delay"]] = np.nan
print(f"pasos válidos: {p.a.notna().sum()}")

# imputación (solo para headways) y headway con el bus de adelante
p["delay_i"] = p.groupby("trip").delay.transform(lambda d: d.interpolate(limit=2, limit_area="inside"))
p["a_i"] = p.s + p.delay_i
q = p[p.a_i.notna()].sort_values(["date", "k", "a_i"])
g = q.groupby(["date", "k"])
q["h"] = q.a_i - g.a_i.shift()
q["hp"] = q.s - g.s.shift()
q.loc[~(q.h.between(0, MAX_H) & q.hp.between(0, MAX_H, inclusive="right")), "h"] = np.nan
p = p.merge(q[["trip", "k", "h"]], on=["trip", "k"], how="left")

# --- 2. Monitoring.csv: GPS limpio y variables por tramo
m = pd.read_csv(DATA / "Monitoring.csv", dtype={"vehicle_id_id": str},
                usecols=["date", "time", "latitude", "longitude", "speed", "vehicle_id_id"])
m = m.rename(columns={"vehicle_id_id": "veh"}).drop_duplicates(["veh", "date", "time"])
m["t"] = pd.to_timedelta(m.time).dt.total_seconds() / 60
iso_g = IsolationForest(contamination=0.005, random_state=SEED, n_jobs=-1)
iso_g.fit(m.loc[m.date <= TRAIN_END, ["latitude", "longitude", "speed"]])
m = m[iso_g.predict(m[["latitude", "longitude", "speed"]]) != -1].reset_index(drop=True)

passes = p.loc[p.a_i.notna(), ["veh", "date", "a_i", "trip", "k"]].sort_values("a_i")
mg = pd.merge_asof(m.sort_values("t"), passes, left_on="t", right_on="a_i", by=["veh", "date"],
                   direction="forward", tolerance=60).dropna(subset=["trip"])
mg["stop"] = mg.speed <= SLOW
seg = mg.groupby(["trip", "k"]).agg(v=("speed", "mean"), stop=("stop", "mean")).reset_index()
seg["trip"] = seg.trip.astype(p.trip.dtype)
seg["k"] = seg.k.astype(int)

# altitud y clima de Open-Meteo (ya descargados por el notebook en datos_externos/). La altitud
# (puntos_control_clima.csv) es fija y siempre hace falta; el clima horario solo si se compara.
# ponytail: sin clima_open_meteo.csv no se compara y el modelo va sin clima, sin avisar más que en el resumen.
cp = pd.read_csv(EXT / "puntos_control_clima.csv", index_col="k")
HAY_CLIMA = (EXT / "clima_open_meteo.csv").exists()
if HAY_CLIMA:
    cl = pd.read_csv(EXT / "clima_open_meteo.csv").sort_values(["k", "time"])
    cl["date"], cl["hora_c"] = cl.time.str[:10], cl.time.str[11:13].astype(int)
    cl["precip_3h"] = cl.groupby("k").precipitation.transform(lambda x: x.rolling(3, min_periods=1).sum())
    cl = cl.rename(columns={"temperature_2m": "temp", "relative_humidity_2m": "hum", "precipitation": "precip",
                            "cloud_cover": "nubes", "wind_speed_10m": "viento"})
    cl = cl[["k", "date", "hora_c", "temp", "hum", "precip", "precip_3h", "nubes", "viento"]]

# --- 3. Dataset de modelado: una fila por (paso real por k, destino kt = k + Δ)
key = ["trip", "k"]
p = p.merge(seg, on=key, how="left").sort_values(key).reset_index(drop=True)
gt = p.groupby("trip")
p["T_prev"] = p.a - gt.a.shift()
p["ddelay_k"] = p.delay_i - gt.delay_i.shift()
p = p.rename(columns={"delay": "delay_k", "h": "h_k", "v": "v_i", "stop": "stop_i"})
segj = seg.rename(columns={"trip": "trip_c", "k": "kc", "v": "v_last", "stop": "stop_last"})
segj["trip_c"] = segj.trip_c.astype(float)

rows = []
for D in DELTAS:
    b = p[p.a.notna() & (p.k + D <= 18)].copy()
    b["delta"], b["kt"] = D, b.k + D
    nxt = p[["trip", "k", "a", "s"]].rename(columns={"k": "kt", "a": "a_t", "s": "s_t"})
    # ponytail: a diferencia del notebook, se conservan los destinos sin llegada real (a_t NaN) para que la
    # demo prediga también ahí; el entrenamiento y `comp` los descartan, así que el dataset de modelado es el mismo.
    b = b.merge(nxt, on=["trip", "kt"], how="left")
    b["y"], b["sp"] = b.a_t - b.a, b.s_t - b.s
    comp = b.loc[b.a_t.notna(), ["date", "k", "a_t", "y", "trip"]].rename(
        columns={"a_t": "c", "y": "T_last", "trip": "trip_c"})
    comp = comp.sort_values("c")
    comp["T_roll3"] = comp.groupby(["date", "k"]).T_last.transform(lambda x: x.rolling(3, min_periods=1).mean())
    b = pd.merge_asof(b.sort_values("a"), comp, left_on="a", right_on="c", by=["date", "k"],
                      direction="backward", allow_exact_matches=False)
    b["age_last"] = b.a - b.c
    b.loc[b.age_last > MAX_AGE, ["T_last", "T_roll3", "age_last", "trip_c"]] = np.nan
    b["kc"] = b.k + 1
    b = b.merge(segj[["trip_c", "kc", "v_last", "stop_last"]], on=["trip_c", "kc"], how="left")
    rows.append(b)
D_all = pd.concat(rows, ignore_index=True)
D_all["hour"] = D_all.s / 60
D_all["dow"] = pd.to_datetime(D_all.date).dt.dayofweek
D_all["hora_c"] = (D_all.a // 60).astype(int)
if HAY_CLIMA:
    D_all = D_all.merge(cl, on=["k", "date", "hora_c"], how="left")
D_all["alt"] = D_all.k.map(cp.alt)
D_all["desnivel"] = D_all.kt.map(cp.alt) - D_all.alt
D_all["split"] = np.where(D_all.date <= TRAIN_END, "train", np.where(D_all.date <= VAL_END, "val", "test"))

G_I = ["delay_k", "ddelay_k", "T_prev", "h_k", "lap"]
G_REC = ["T_last", "T_roll3", "age_last"]
G_GPS = ["v_i", "stop_i", "v_last", "stop_last"]
G_CLIMA = ["temp", "hum", "precip", "precip_3h", "nubes", "viento"]
G_ALT = ["alt", "desnivel"]
G_CTX = ["k", "delta", "hour", "dow", "sp"]
CAT = ["veh"]
NUM_CLIMA = G_I + G_REC + G_GPS + G_CLIMA + G_ALT + G_CTX  # orden del notebook
NUM_SIN_CLIMA = [c for c in NUM_CLIMA if c not in G_CLIMA]

d = D_all[D_all.y.notna()]
print("filas por Δ y partición (deben coincidir con el notebook):")
print(d.groupby(["delta", "split"]).size().unstack())

# --- 4. Gradient Boosting con los hiperparámetros del notebook
def gb(num, **kw):
    ct = ColumnTransformer([("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
                            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])
    return Pipeline([("prep", ct), ("model", HistGradientBoostingRegressor(
        learning_rate=0.1, max_depth=6, max_iter=1000, early_stopping=True, random_state=SEED, **kw))])


tr, va, te = (d[d.split == s] for s in ("train", "val", "test"))
trva = d[d.split != "test"]

# Clima: ERA5/Open-Meteo es reanálisis y no existe en tiempo real. Se compara en validación entrenando solo con
# entrenamiento, y se queda sin clima salvo que eso empeore el MAE.
def mae_validacion(num):
    return mean_absolute_error(va.y, gb(num).fit(tr[num + CAT], tr.y).predict(va[num + CAT]))


mae_val = {"sin": mae_validacion(NUM_SIN_CLIMA)}
if HAY_CLIMA:
    mae_val["con"] = mae_validacion(NUM_CLIMA)
usa_clima = HAY_CLIMA and mae_val["sin"] > mae_val["con"]
NUM = NUM_CLIMA if usa_clima else NUM_SIN_CLIMA
print("MAE validación: " + ", ".join(f"{k} clima {v:.3f}" for k, v in mae_val.items())
      + f" → modelo {'con' if usa_clima else 'sin'} clima")

X = NUM + CAT
modelos = {"p50": gb(NUM).fit(trva[X], trva.y)}
mae = mean_absolute_error(te.y, modelos["p50"].predict(te[X]))
print(f"MAE en prueba: {mae:.3f} min (notebook, GB con clima: 1.919)")

# P10 y P90 solo con entrenamiento: validación queda libre para la calibración CQR
for nombre, alfa in (("p10", 0.1), ("p90", 0.9)):
    modelos[nombre] = gb(NUM, loss="quantile", quantile=alfa).fit(tr[X], tr.y)
lo_va, hi_va = modelos["p10"].predict(va[X]), modelos["p90"].predict(va[X])
lo_te, hi_te = modelos["p10"].predict(te[X]), modelos["p90"].predict(te[X])
q = calibrar(lo_va, hi_va, va.y.to_numpy())


def cob(lo, hi, y):
    # ponytail: mide [lo - q, hi + q] sin el recorte contra P50 de `nucleo.cuantiles`, que solo ensancha: la app cubre ≥ esto
    return float(((y >= lo) & (y <= hi)).mean())


resumen = {"mae_test": mae, "q_cqr": q, "usa_clima": usa_clima, "mae_val_sin_clima": mae_val["sin"],
           "mae_val_con_clima": mae_val.get("con"),
           "cob_val_antes": cob(lo_va, hi_va, va.y), "cob_val_despues": cob(lo_va - q, hi_va + q, va.y),
           "cob_test_antes": cob(lo_te, hi_te, te.y), "cob_test_despues": cob(lo_te - q, hi_te + q, te.y)}
print(f"CQR: corrección {q:+.3f} min")
print(f"cobertura P10–P90  validación: {resumen['cob_val_antes']:.1%} → {resumen['cob_val_despues']:.1%}"
      f"  |  prueba: {resumen['cob_test_antes']:.1%} → {resumen['cob_test_despues']:.1%}")

OUT.mkdir(exist_ok=True)
cols = list(dict.fromkeys(["date", "veh", "trip", "k", "a", "kt", "s_t", "a_t"] + NUM))
pasos = D_all[D_all.split == "test"][cols].reset_index(drop=True)
# GPS ya limpio (Isolation Forest) de los días de prueba y coordenadas de los 18 puntos, para el mapa
LATLON = {"latitude": "lat", "longitude": "lon"}
gps = m.loc[m.date > VAL_END, ["date", "veh", "t", "latitude", "longitude"]].rename(columns=LATLON).astype(
    {"t": "float32", "lat": "float32", "lon": "float32"})
puntos = cp[["latitude", "longitude"]].rename(columns=LATLON).reset_index()
joblib.dump({"modelos": modelos, "q": q, "resumen": resumen, "features": X, "pasos": pasos,
             "gps": gps.reset_index(drop=True), "puntos": puntos}, OUT / "demo.joblib")
print(f"guardado {OUT / 'demo.joblib'} en {(time.perf_counter() - T0) / 60:.1f} min")
