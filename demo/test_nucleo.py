"""Pruebas del núcleo de predicción con un mini-dataset sintético (2 buses, 3 puntos).

Correr: python demo/test_nucleo.py  (o pytest demo/test_nucleo.py)
"""
import numpy as np
import pandas as pd

from nucleo import predecir


class ModeloEspia:
    """Predice y = sp (tiempo programado) y guarda las filas que recibió."""

    def __init__(self):
        self.vistos = []

    def predict(self, X):
        self.vistos.append(X.copy())
        return X.sp.to_numpy()


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
    r = predecir(pasos_sinteticos(), m, FEATURES, instante=605)
    assert sum(len(X) for X in m.vistos) == 2  # solo las filas del paso k=1 del bus 1
    assert set(r.k) == {1}
    assert list(r.kt) == [2, 3]
    assert list(r.p50) == [609, 620]  # a(1) + sp


def test_hora_real_solo_si_ya_ocurrio():
    r = predecir(pasos_sinteticos(), ModeloEspia(), FEATURES, instante=609).set_index(["veh", "kt"])
    assert np.isnan(r.loc[("1", 2), "real"])  # llega en el 610, todavía no
    r = predecir(pasos_sinteticos(), ModeloEspia(), FEATURES, instante=722).set_index(["veh", "kt"])
    assert r.loc[("2", 3), "real"] == 722  # llegó justo en el instante


def test_bus_sin_pasos_no_aparece():
    r = predecir(pasos_sinteticos(), ModeloEspia(), FEATURES, instante=650)
    assert set(r.veh) == {"1"}
    assert len(predecir(pasos_sinteticos(), ModeloEspia(), FEATURES, instante=500)) == 0


def test_bus_al_que_le_falta_un_paso():
    r = predecir(pasos_sinteticos(), ModeloEspia(), FEATURES, instante=730).set_index(["veh", "kt"])
    assert r.loc[("2", 2), "p50"] == 709  # se predice aunque no haya hora real
    assert np.isnan(r.loc[("2", 2), "real"])
    assert r.loc[("2", 3), "real"] == 722


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("ok", nombre)
