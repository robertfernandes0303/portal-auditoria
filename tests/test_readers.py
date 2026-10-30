import pytest
from core import readers
from core.store import Store


def _store():
    return Store.__new__(Store) if False else None


def test_estado_e_data():
    assert readers._estado("aud", "Não Conforme") == "NC"
    assert readers._estado("enf", "OK") == "C" and readers._estado("enf", "Parcial") == readers.PARCIAL_COMO
    assert readers._estado("enf", "Não preenchido") is None
    assert readers._data("30/10/2026") == "2026-10-30" and readers._data("2026-10-30") == "2026-10-30"


def test_visitas_enf():
    import pandas as pd
    cat = readers._catalogo("enf")
    n0 = cat[0][1][0][0]
    vis = pd.DataFrame([{"Código da Visita": "ENF-1", "Hospital": "Juína", "Data da Visita": "30/10/2026", "Responsável pela Visita": "R"}])
    itens = pd.DataFrame([{"Código da Visita": "ENF-1", "Nº do Item": str(n0), "Situação": "Não", "Qtde de Anexos": "2"}])
    v = readers._visitas_de("enf", vis, itens, cat)[0]
    assert v["unit"] == "Juína" and v["date"] == "2026-10-30" and len(v["items"]) == 43
    assert v["items"][0]["s"] == "NC" and v["items"][0]["ev"] == 2 and v["items"][1]["s"] == "NA"
