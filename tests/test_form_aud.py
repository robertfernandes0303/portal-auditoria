import pytest
from core import api, forms_api
from core.api import Rejected
from core.store import Store
from forms.institucional import logic

ADM = "admin.inicial@portal.local"


@pytest.fixture
def store():
    return Store()


def test_totals_and_percent():
    cat = logic.catalogo()
    resp = {}
    nums = [i["num"] for s in cat if s["tipo"] == "checklist" for i in s["itens"]]
    for n in nums[:3]:
        resp[n] = {"resposta": "Conforme", "observacao": ""}
    resp[nums[3]] = {"resposta": "Não Conforme", "observacao": "x"}
    resp[nums[4]] = {"resposta": "Não se Aplica", "observacao": ""}
    d = {"data_visita": "30/10/2026", "responsavel_visita": "A", "respostas_checklist": resp, "valores_quantidade": {"1": "10"}}
    v, itens, r, pend = logic.montar_registros("Juína", d)
    assert (r["conforme"], r["nao_conforme"], r["nao_aplica"]) == (3, 1, 1)
    assert r["nao_preenchido"] == 241 - 5 and v["Percentual de Conformidade"] == "75.0%" and v["Status da Visita"] == "Incompleta"
    assert len(itens) == 251 and pend


def test_quantity_validation():
    s = logic.catalogo()[0]
    assert logic.validar_quantidade(s, {9: "101"}) and logic.validar_quantidade(s, {1: "-2"}) and logic.validar_quantidade(s, {1: "abc"})
    assert not logic.validar_quantidade(s, {1: "10", 9: "87,5", 10: "texto"})


def test_open_save_submit_flow(store):
    r = forms_api.handle(store, ADM, "form_open", {"form": "aud", "unit": "Juína"})
    assert r["estado"] == "novo" and len(r["catalogo"]) == 26
    d = {"codigo_visita": r["codigo"], "data_visita": "30/10/2026", "responsavel_visita": "Ana", "respostas_checklist": {"11": {"resposta": "Conforme"}}}
    bad = forms_api.handle(store, ADM, "form_submit", {"form": "aud", "unit": "Juína", "dados": d})
    assert not bad["ok"]  # pendentes sem 'forcado'
    ok = forms_api.handle(store, ADM, "form_submit", {"form": "aud", "unit": "Juína", "dados": d, "forcado": True})
    assert ok["ok"] and ok["resumo"]["percentual"] == "100.0%"


def test_scope_enforced(store):
    p = api.build_boot(store, ADM, 1, {})
    pl = {"profiles": p["profiles"], "users": p["users"] + [{"id": "n", "name": "Ana", "mail": "ana@isssl.com.br", "role": "resp", "scope": "sel", "units": ["Juína"], "ov": {}}],
          "units": p["units"], "connections": {}}
    api.save_config(store, ADM, pl)
    with pytest.raises(Rejected):
        forms_api.handle(store, "ana@isssl.com.br", "form_open", {"form": "aud", "unit": "Campo Verde"})
    assert forms_api.handle(store, "ana@isssl.com.br", "form_open", {"form": "aud", "unit": "Juína"})["ok"]
    with pytest.raises(Rejected):
        forms_api.handle(store, "x@y.com", "form_open", {"form": "aud", "unit": "Juína"})


def test_mapping_from_portal_connections(store):
    p = api.build_boot(store, ADM, 1, {})
    ref = "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUv/edit"
    p["connections"] = {"aud|Juína": {"planilha": ref, "pasta": ""}, "aud|__consolidado__": {"planilha": "1ZzCdEfGhIjKlMnOpQrStUv", "pasta": "1PastaPastaPastaPasta"}}
    api.save_config(store, ADM, {"profiles": p["profiles"], "users": p["users"], "units": p["units"], "connections": p["connections"]})
    m = __import__('forms.institucional.adapter',fromlist=['x'])._mapping(forms_api.Ctx(store, ADM, store.user_by_mail(ADM)))
    assert m["unidades"]["Juína"] == "1AbCdEfGhIjKlMnOpQrStUv" and m["consolidado"] == "1ZzCdEfGhIjKlMnOpQrStUv" and m["pasta_visita_unidade"] == "1PastaPastaPastaPasta"
