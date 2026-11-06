import time
import pytest
from core import forms_api, descarte
from core.api import Rejected
from core.store import Store

ADM = "admin.inicial@portal.local"


@pytest.fixture
def store():
    return Store()


def test_descarta_auditoria_e_registra(store):
    r = forms_api.handle(store, ADM, "form_open", {"form": "aud", "unit": "Juína"})
    d = {"codigo_visita": r["codigo"], "data_visita": "30/10/2026", "responsavel_visita": "Ana", "respostas_checklist": {}}
    forms_api.handle(store, ADM, "form_save", {"form": "aud", "unit": "Juína", "dados": d})
    time.sleep(0.6)
    ab = forms_api.handle(store, ADM, "form_open", {"form": "aud", "unit": "Juína"})
    assert ab["estado"] != "novo"
    out = descarte.descartar(store, ADM, "aud", r["codigo"], "Juína")
    assert out["ok"]
    assert forms_api.handle(store, ADM, "form_open", {"form": "aud", "unit": "Juína"})["estado"] == "novo"
    assert "Descartou visita" in store.data["audit"][0]["what"]


def test_codigo_diferente_nao_apaga(store):
    r = forms_api.handle(store, ADM, "form_open", {"form": "aud", "unit": "Juína"})
    d = {"codigo_visita": r["codigo"], "data_visita": "30/10/2026", "responsavel_visita": "Ana", "respostas_checklist": {}}
    forms_api.handle(store, ADM, "form_save", {"form": "aud", "unit": "Juína", "dados": d})
    time.sleep(0.6)
    with pytest.raises(Rejected):
        descarte.descartar(store, ADM, "aud", "OUTRO-CODIGO", "Juína")
    assert forms_api.handle(store, ADM, "form_open", {"form": "aud", "unit": "Juína"})["estado"] != "novo"


def test_so_admin(store):
    with pytest.raises(Rejected):
        descarte.descartar(store, "x@y.com", "aud", "C", "Juína")
