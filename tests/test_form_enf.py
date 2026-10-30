import base64, io
from core.store import Store
from core import forms_api
from forms.enfermagem import logic


def test_catalogo():
    assert len(logic.catalogo()) == 11 and logic.config()["total"] == 43


def test_montar_envio_totais():
    cat = logic.catalogo()
    nums = [i["num"] for g in cat for i in g["itens"]]
    d = {"codigo_visita": "ENF-X-20260101-ab12", "hospital": "H", "responsavel_visita": "R", "data_visita": "2026-01-01",
         "respostas": {nums[0]: {"situacao": "OK"}, nums[1]: {"situacao": "Não"}, nums[2]: {"situacao": "N/A"}},
         "anexos": {}, "previsto_informado": {}}
    visita = logic.montar_envio(d)[0]
    assert visita["Total OK"] == 1 and visita["Total Não"] == 1
    assert visita["Total Não Preenchido"] == 40
    assert str(visita["Percentual de OK"]).startswith("50")


def test_v03_envio():
    from forms.hospital_v03 import logic as lv, schema as sv
    assert sv.TOTAL_ITENS == 77 and len(lv.catalogo()) == 24
    n = lv.catalogo()[0]["itens"][0]["num"]
    d = {"codigo_visita": "V03-X-1", "hospital": "H", "responsavel_visita": "R", "data_visita": "2026-01-01",
         "respostas": {n: {"situacao": "OK", "achado": "a", "evidencia": "e", "impacto": "i"}},
         "sintese": [{"setor": "UTI", "referencia": "", "situacao": "", "risco": "", "custo": "", "acao": ""}, {"setor": ""}],
         "pendencias": ["doc X", " "], "obs_finais": "fim"}
    visita, itens, evid, sint, pend = lv.montar_envio(d)
    assert visita["Total OK"] == 1 and visita["Total Não Preenchido"] == 76
    assert len(sint) == 1 and len(pend) == 1 and visita["Observações Finais"] == "fim"
    assert itens[0]["Achado / quantidade / GAP"] == "a" and set(itens[0]) == set(sv.COLUNAS_ITEM)
    assert set(visita) == set(sv.COLUNAS_VISITA)


def test_upa_envio():
    from forms.upa import logic as lu, schema as su
    assert su.TOTAL_ITENS == 107 and len(lu.catalogo()) == 11
    ess = next(i for g in lu.catalogo() for i in g["itens"] if i["foco"] == "E")
    d = {"codigo_visita": "UPA-X-1", "hospital": "UPA Sul", "responsavel_visita": "R", "data_visita": "2026-01-01",
         "respostas": {ess["num"]: {"resposta": "120", "fonte": "Observado"}, 2: {"fonte": "Não se aplica"}, 3: {"fonte": "Não verificado"}},
         "impactos": {0: "texto", 1: " "}, "horario": "09:30"}
    visita, itens, evid, secoes = lu.montar_envio(d)
    assert visita["Total Verificados"] == 1 and visita["Total Não se Aplica"] == 1 and visita["Total Não Verificados"] == 1
    assert visita["Total Não Preenchido"] == 104 and visita["Horário"] == "09:30" and len(secoes) == 1
    assert set(visita) == set(su.COLUNAS_VISITA) and set(itens[0]) == set(su.COLUNAS_ITEM)
