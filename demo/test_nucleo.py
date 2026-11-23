"""Pruebas del núcleo de predicción con un mini-dataset sintético (2 buses, 3 puntos).

Correr: python demo/test_nucleo.py  (o pytest demo/test_nucleo.py)
"""
import numpy as np
import pandas as pd

from nucleo import calibrar, marcador, paradero, posiciones


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
    r = paradero(pasos_sinteticos(), modelos(m), FEATURES, instante=605, destino=3)
    assert sum(len(X) for X in m.vistos) == 1  # solo la fila (k=1 -> 3) del bus 1
    assert list(r.k) == [1] and list(r.p50) == [620]  # a(1) + sp


def test_usa_la_prediccion_mas_reciente_de_la_vuelta():
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=615, destino=3)
    assert list(r.k) == [2] and list(r.p50) == [620]  # desde k=2 (a=610), no desde k=1


def test_hora_real_solo_si_ya_ocurrio():
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=609, destino=2)
    assert list(r.veh) == ["1"] and np.isnan(r.real[0])  # llega en el 610, todavía no
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=610, destino=2)
    assert r.real[0] == 610  # llegó justo en el instante


def test_los_que_llegaron_se_quedan_solo_la_ventana():
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=630, destino=3)
    assert list(r.veh) == ["1"] and r.real[0] == 625  # el bus 2 todavía no pasa por ningún punto
    assert paradero(pasos_sinteticos(), modelos(), FEATURES, instante=641, destino=3).empty  # 625 + 15 < 641
    assert paradero(pasos_sinteticos(), modelos(), FEATURES, instante=500, destino=3).empty


def test_bus_al_que_le_falta_la_llegada():
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=720, destino=2)
    assert list(r.veh) == ["2"] and r.p50[0] == 709 and np.isnan(r.real[0])  # se predice sin hora real
    # sin llegada registrada se descarta 15 min después de su P90 (700 + 9 + 3 = 712)
    assert paradero(pasos_sinteticos(), modelos(), FEATURES, instante=730, destino=2).empty


def test_rango_calibrado_y_marca_de_acierto():
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=722, destino=3, q=1)
    assert (r.veh[0], r.p10[0], r.p90[0]) == ("2", 700 + 20 - 2 - 1, 700 + 20 + 3 + 1)
    assert r.dentro[0]  # real 722 en [717, 724]
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=722, destino=3, q=-3)
    assert not r.dentro[0]  # q < 0 cruza los extremos: el rango colapsa en p50 = 720
    r = paradero(pasos_sinteticos(), modelos(), FEATURES, instante=705, destino=3)
    assert not r.dentro[0]  # todavía sin hora real


def test_orden_de_cuantiles_aunque_los_modelos_crucen():
    r = paradero(pasos_sinteticos(), modelos(d10=5, d90=-5), FEATURES, instante=722, destino=3, q=1)
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


def test_marcador_solo_con_llegadas_ya_ocurridas():
    d = pasos_sinteticos().assign(p50=lambda x: x.a_t + 1, p10=lambda x: x.a_t, p90=lambda x: x.a_t + 2)
    # en el min 615 solo llegó el bus 1 al k=2 (610): la llegada al k=3 (625) aún no cuenta
    assert marcador(d, instante=615) == (1, 1, 1, 1)  # horario: |609 - 610|
    # en el 625 entran las dos predicciones del k=3 (desde k=1 y k=2): horario |620 - 625| = 5
    assert marcador(d, instante=625) == (1, (1 + 5 + 5) / 3, 1, 3)
    m, h, c, n = marcador(d, instante=599)
    assert n == 0 and np.isnan(m) and np.isnan(h) and np.isnan(c)


def test_marcador_cobertura():
    d = pasos_sinteticos().assign(p50=lambda x: x.a_t, p10=lambda x: x.a_t - 1, p90=lambda x: x.a_t + 1)
    d.loc[0, ["p10", "p90"]] = [700, 701]  # una de las cuatro llegadas cae fuera del rango
    m, h, c, n = marcador(d, instante=800)
    assert m == 0 and h > 0 and n == 4 and c == 0.75  # la fila sin llegada real no cuenta


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("ok", nombre)
