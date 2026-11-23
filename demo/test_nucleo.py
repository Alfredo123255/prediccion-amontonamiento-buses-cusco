"""Pruebas del núcleo de predicción con un mini-dataset sintético (2 buses, 3 puntos).

Correr: python demo/test_nucleo.py  (o pytest demo/test_nucleo.py)
"""
import numpy as np
import pandas as pd

from nucleo import calibrar, mae_acumulado, posiciones, predecir


class ModeloEspia:
    """Predice y = sp (tiempo programado) + desfase y guarda las filas que recibió."""

    def __init__(self, desfase=0):
        self.desfase, self.vistos = desfase, []

    def predict(self, X):
        self.vistos.append(X.copy())
        return X.sp.to_numpy() + self.desfase


def modelos(p50=None, d10=-2, d90=3):
    return {"p10": ModeloEspia(d10), "p50": p50 or ModeloEspia(), "p90": ModeloEspia(d90)}


def pasos_sinteticos():
    """Bus 1 pasa por k=1 (min 600) y k=2 (min 610); al k=3 llega en el min 625.
    Bus 2 pasa por k=1 recién en el min 700. Una fila por (paso k, destino kt)."""
    filas = [  # veh, trip, k, a, kt, s_t, a_t
        ("1", 10, 1, 600, 2, 609, 610),
        ("1", 10, 1, 600, 3, 620, 625),
        ("1", 10, 2, 610, 3, 620, 625),
        ("2", 20, 1, 700, 2, 709, np.nan),  # le falta el paso por k=2
        ("2", 20, 1, 700, 3, 720, 722),
    ]
    d = pd.DataFrame(filas, columns=["veh", "trip", "k", "a", "kt", "s_t", "a_t"])
    d["s"] = d.a  # bus puntual al pasar por A
    d["sp"] = d.s_t - d.s
    return d


FEATURES = ["sp", "veh"]


def test_nunca_usa_pasos_posteriores_al_instante():
    m = ModeloEspia()
    r = predecir(pasos_sinteticos(), modelos(m), FEATURES, instante=605)
    assert sum(len(X) for X in m.vistos) == 2  # solo las filas del paso k=1 del bus 1
    assert set(r.k) == {1}
    assert list(r.kt) == [2, 3]
    assert list(r.p50) == [609, 620]  # a(1) + sp


def test_hora_real_solo_si_ya_ocurrio():
    r = predecir(pasos_sinteticos(), modelos(), FEATURES, instante=609).set_index(["veh", "kt"])
    assert np.isnan(r.loc[("1", 2), "real"])  # llega en el 610, todavía no
    r = predecir(pasos_sinteticos(), modelos(), FEATURES, instante=722).set_index(["veh", "kt"])
    assert r.loc[("2", 3), "real"] == 722  # llegó justo en el instante


def test_bus_sin_pasos_no_aparece():
    r = predecir(pasos_sinteticos(), modelos(), FEATURES, instante=650)
    assert set(r.veh) == {"1"}
    assert len(predecir(pasos_sinteticos(), modelos(), FEATURES, instante=500)) == 0


def test_bus_al_que_le_falta_un_paso():
    r = predecir(pasos_sinteticos(), modelos(), FEATURES, instante=730).set_index(["veh", "kt"])
    assert r.loc[("2", 2), "p50"] == 709  # se predice aunque no haya hora real
    assert np.isnan(r.loc[("2", 2), "real"])
    assert r.loc[("2", 3), "real"] == 722


def test_rango_calibrado_y_marca_de_acierto():
    r = predecir(pasos_sinteticos(), modelos(), FEATURES, instante=730, q=1).set_index(["veh", "kt"])
    assert r.loc[("2", 3), "p10"] == 700 + 20 - 2 - 1
    assert r.loc[("2", 3), "p90"] == 700 + 20 + 3 + 1
    assert r.loc[("2", 3), "dentro"]  # real 722 en [717, 724]
    assert not r.loc[("2", 2), "dentro"]  # sin hora real
    r = predecir(pasos_sinteticos(), modelos(), FEATURES, instante=730, q=-3).set_index(["veh", "kt"])
    assert not r.loc[("2", 3), "dentro"]  # q < 0 cruza los extremos: el rango colapsa en p50 = 720


def test_orden_de_cuantiles_aunque_los_modelos_crucen():
    r = predecir(pasos_sinteticos(), modelos(d10=5, d90=-5), FEATURES, instante=730, q=1)
    assert (r.p10 <= r.p50).all() and (r.p50 <= r.p90).all()
    assert (r.p10 == r.p50).all() and (r.p90 == r.p50).all()  # cruzados: el rango colapsa en p50


def test_cqr_lleva_la_cobertura_al_80():
    """Intervalo fijo [-0,5; 0,5] sobre y ~ N(0, 1): cubre ~38 %. Calibrado en una muestra, evaluado en otra."""
    rng = np.random.default_rng(0)
    y_val, y_te = rng.normal(size=5000), rng.normal(size=5000)
    lo, hi = np.full(5000, -0.5), np.full(5000, 0.5)
    assert abs(((y_te >= lo) & (y_te <= hi)).mean() - 0.38) < 0.03
    q = calibrar(lo, hi, y_val)
    cob = ((y_te >= lo - q) & (y_te <= hi + q)).mean()
    assert abs(cob - 0.80) <= 0.02, cob
    # intervalo demasiado ancho: la corrección es negativa y lo estrecha
    q = calibrar(lo * 6, hi * 6, y_val)
    assert q < 0 and abs(((y_te >= -3 - q) & (y_te <= 3 + q)).mean() - 0.80) <= 0.02


def test_posicion_gps_en_el_minuto_actual():
    gps = pd.DataFrame({"veh": ["1", "1", "1", "2", "3"], "t": [600, 604.5, 611, 590, 600],
                        "lat": [1, 2, 3, 9, 7], "lon": [1, 2, 3, 9, 7]})
    r = posiciones(gps, instante=605).set_index("veh")
    assert r.loc["1", "lat"] == 2  # último ping antes del instante, nunca el del minuto 611
    assert "2" not in r.index  # su último ping es de hace 15 min: ya no se dibuja
    assert r.loc["3", "lat"] == 7  # justo 5 min: todavía se dibuja
    assert len(posiciones(gps, instante=500)) == 0


def test_mae_acumulado_solo_con_llegadas_ya_ocurridas():
    d = pasos_sinteticos().assign(p50=lambda x: x.a_t + 1)  # el modelo se equivoca 1 min siempre
    # en el min 615 solo llegó el bus 1 al k=2 (610): la llegada al k=3 (625) aún no cuenta
    assert mae_acumulado(d, instante=615) == (1, 1, 1)  # horario: |609 - 610|
    # en el 625 entran las dos predicciones del k=3 (desde k=1 y k=2): horario |620 - 625| = 5
    assert mae_acumulado(d, instante=625) == (1, (1 + 5 + 5) / 3, 3)
    m, h, n = mae_acumulado(d, instante=599)
    assert n == 0 and np.isnan(m) and np.isnan(h)


def test_mae_acumulado_modelo_perfecto():
    d = pasos_sinteticos().assign(p50=lambda x: x.a_t)
    m, h, n = mae_acumulado(d, instante=800)
    assert m == 0 and h > 0 and n == 4  # la fila sin llegada real no cuenta


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("ok", nombre)
