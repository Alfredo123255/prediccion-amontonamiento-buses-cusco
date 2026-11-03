"""EDA del Entregable 1: headways por punto de control y figuras para el informe.
Uso: python eda_entregable1.py  (lee Dataset/*.csv, escribe figuras/*.png)"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figuras", exist_ok=True)
t = pd.read_csv("Dataset/Times.csv", dtype={"vehicle_id_id": str})
m = pd.read_csv("Dataset/Monitoring.csv", dtype={"vehicle_id_id": str})

# Times: una fila por vuelta con 18 puntos de control -> una fila por (vuelta, punto)
for c in ["start_time", "end_time", "difference_time"]:
    t[c] = t[c].str.strip("{}").str.split(",")
x = t.explode(["start_time", "end_time", "difference_time"]).reset_index(drop=True)
x["k"] = x.groupby("id").cumcount() + 1
x = x.rename(columns={"vehicle_id_id": "veh", "start_time": "prog", "end_time": "real", "difference_time": "delay"})
n_total = len(x)
x = x[x.real.str.match(r"^\d\d:\d\d")].copy()
n_valid = len(x)
for c in ["prog", "real"]:
    x[c] = pd.to_timedelta(x[c]).dt.total_seconds() / 60
x["delay"] = pd.to_numeric(x.delay, errors="coerce")

# headway real y programado con el bus anterior en el mismo punto y día
x = x.sort_values(["date", "k", "real"])
x["h"] = x.groupby(["date", "k"]).real.diff()
# ponytail: h_prog del mismo par de buses; si hubo adelantamiento sale <=0 y se descarta abajo
x["h_prog"] = x.groupby(["date", "k"]).prog.diff()
h = x.dropna(subset=["h", "h_prog"])
h = h[(h.h < 60) & (h.h_prog > 0)]  # ponytail: corte simple de outliers (>60 min = fin de servicio / datos rotos)
r = h.h / h.h_prog
h = h.assign(clase=np.select([r < 0.5, r > 1.5], ["amontonado", "hueco"], "regular"))

print("pasos totales", n_total, "validos", n_valid, "faltantes %", round(100 * (1 - n_valid / n_total), 1))
print("vueltas", len(t), "buses", t.vehicle_id_id.nunique(), "fechas", t.date.min(), t.date.max())
print("GPS", len(m), "buses", m.vehicle_id_id.nunique(), m.date.min(), m.date.max())
print("delay |x|>60 min:", int((x.delay.abs() > 60).sum()))
print("headway", h.h.describe().round(2).to_dict())
cv = h.h.std() / h.h.mean()
print("CV", round(cv, 2), "espera esperada", round(h.h.mean() / 2 * (1 + cv**2), 2), "ideal", round(h.h.mean() / 2, 2))
print("clases %", (h.clase.value_counts(normalize=True) * 100).round(1).to_dict())
dur = pd.to_timedelta(t.start_time.str[-1]) - pd.to_timedelta(t.start_time.str[0])
print("duracion vuelta programada (min, mediana)", dur.dt.total_seconds().median() / 60)

# ubicación de los puntos de control: GPS del mismo bus/día/vuelta más cercano en tiempo al paso real
m["tmin"] = pd.to_timedelta(m.time).dt.total_seconds() / 60
mm = m.rename(columns={"vehicle_id_id": "veh"}).sort_values("tmin")
xs = x.sample(min(20000, len(x)), random_state=0).sort_values("real")
j = pd.merge_asof(xs, mm[["date", "veh", "lap", "tmin", "latitude", "longitude"]],
                  left_on="real", right_on="tmin", by=["date", "veh", "lap"], tolerance=1.0, direction="nearest")
cp = j.groupby("k")[["latitude", "longitude"]].median()

# Fig 1: mapa de la ruta con los 18 puntos de control
s = m.sample(60000, random_state=0)
lo, hi = s[["latitude", "longitude"]].quantile(0.002), s[["latitude", "longitude"]].quantile(0.998)
s = s[s.latitude.between(lo.latitude, hi.latitude) & s.longitude.between(lo.longitude, hi.longitude)]  # quita saltos de GPS
fig, ax = plt.subplots(figsize=(3.4, 2.1), dpi=300)
sc = ax.scatter(s.longitude, s.latitude, c=s.speed.clip(0, 50), s=0.3, cmap="viridis", rasterized=True)
ax.scatter(cp.longitude, cp.latitude, c="red", s=12, edgecolor="white", linewidth=0.5, zorder=3)
for k, row in cp.iterrows():
    ax.annotate(str(k), (row.longitude, row.latitude), fontsize=5, xytext=(2, 2), textcoords="offset points")
ax.set_xlabel("Longitud", fontsize=6); ax.set_ylabel("Latitud", fontsize=6); ax.tick_params(labelsize=5)
ax.set_aspect("equal")
cb = fig.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.06, pad=0.25); cb.set_label("Velocidad (km/h)", fontsize=6); cb.ax.tick_params(labelsize=5)
fig.tight_layout(); fig.savefig("figuras/fig1_ruta.png"); plt.close(fig)

# Fig 2: dispersión del headway y % de amontonamiento por punto de control
g = h.groupby("k").agg(std=("h", "std"), bunch=("clase", lambda c: 100 * (c == "amontonado").mean()))
fig, ax = plt.subplots(figsize=(3.4, 2.0), dpi=300)
ax.plot(g.index, g["std"], "o-", ms=2.5, color="tab:blue", label="Desv. estándar del headway")
ax.set_xlabel("Punto de control k", fontsize=6); ax.set_ylabel("σ del headway (min)", fontsize=6, color="tab:blue")
ax2 = ax.twinx()
ax2.plot(g.index, g.bunch, "s--", ms=2.5, color="tab:red")
ax2.set_ylabel("% pasos amontonados", fontsize=6, color="tab:red")
for a in (ax, ax2): a.tick_params(labelsize=5)
ax.set_xticks(range(1, 19))
fig.tight_layout(); fig.savefig("figuras/fig2_headway.png"); plt.close(fig)
print(g.round(2).T.to_string())
