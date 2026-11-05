"""Fig. 1 del paper: mapa de la ruta con la ubicación estimada de los 18 puntos de control.
Uso: python eda_entregable1.py  (lee Dataset/*.csv, escribe figuras/fig1_ruta.png)"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figuras", exist_ok=True)
t = pd.read_csv("Dataset/Times.csv", dtype={"vehicle_id_id": str})
m = pd.read_csv("Dataset/Monitoring.csv", dtype={"vehicle_id_id": str})

# Times: una fila por vuelta con 18 puntos de control -> una fila por (vuelta, punto)
for c in ["start_time", "end_time"]:
    t[c] = t[c].str.strip("{}").str.split(",")
x = t.explode(["start_time", "end_time"]).reset_index(drop=True)
x["k"] = x.groupby("id").cumcount() + 1
x = x.rename(columns={"vehicle_id_id": "veh"})
x["real"] = pd.to_timedelta(x.end_time).dt.total_seconds() / 60
x = x[x.real > 0]   # 00:00:00 = paso no registrado

# ubicación de los puntos de control: GPS del mismo bus/día/vuelta más cercano en tiempo al paso real
m["tmin"] = pd.to_timedelta(m.time).dt.total_seconds() / 60
mm = m.rename(columns={"vehicle_id_id": "veh"}).sort_values("tmin")
xs = x.sample(min(20000, len(x)), random_state=0).sort_values("real")
j = pd.merge_asof(xs, mm[["date", "veh", "lap", "tmin", "latitude", "longitude"]],
                  left_on="real", right_on="tmin", by=["date", "veh", "lap"], tolerance=1.0, direction="nearest")
cp = j.groupby("k")[["latitude", "longitude"]].median()

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
cp.to_csv("resultados/puntos_control.csv")   # también lo usará la demo
print(cp.round(5))
