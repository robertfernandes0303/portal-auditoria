import base64, io
from core.store import Store
from core import forms_api
from forms.enfermagem import logic


def test_catalogo():
    assert len(logic.catalogo()) == 8 and logic.config()["total"] == 74
    assert [len(g["itens"]) for g in logic.catalogo()] == [10, 10, 11, 10, 8, 10, 5, 10]
    nums = [i["num"] for g in logic.catalogo() for i in g["itens"]]
    assert nums == list(range(1, 75))
    assert logic.config()["rotulos"]["Parcial"] == "Parcialmente conforme" and "CME" in logic.config()["modulos"]


def test_montar_envio_totais():
    cat = logic.catalogo()
    nums = [i["num"] for g in cat for i in g["itens"]]
    d = {"codigo_visita": "ENF-X-20260101-ab12", "hospital": "H", "responsavel_visita": "R", "data_visita": "2026-01-01",
         "respostas": {nums[0]: {"situacao": "OK"}, nums[1]: {"situacao": "Não"}, nums[2]: {"situacao": "N/A"}},
         "anexos": {}, "previsto_informado": {}}
    visita = logic.montar_envio(d)[0]
    assert visita["Total OK"] == 1 and visita["Total Não"] == 1
    assert visita["Total Não Preenchido"] == 71
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


def test_novos_campos_e_obs_obrigatoria():
    from forms.enfermagem import schema as sc
    d = {"codigo_visita": "ENF-X-20261110-ab12", "hospital": "H", "responsavel_visita": "R", "data_visita": "2026-11-10",
         "rt_enfermagem": "Ana", "gestor_unidade": "Beto", "perfil_unidade": "UPA 24h", "horario": "09:30",
         "modulos": ["CME", "UTI", "Inexistente"],
         "respostas": {1: {"situacao": "Parcial"}, 2: {"situacao": "Não", "observacao": "sem registro"}, 3: {"situacao": "OK"}},
         "anexos": {}}
    assert logic.itens_sem_observacao(d) == ["1"]
    d["respostas"][1]["observacao"] = "escala incompleta"
    assert logic.itens_sem_observacao(d) == []
    visita, itens, _ = logic.montar_envio(d)
    assert set(visita) == set(sc.COLUNAS_VISITA) and set(itens[0]) == set(sc.COLUNAS_ITEM)
    assert visita["RT de Enfermagem"] == "Ana" and visita["Gestor da Unidade"] == "Beto" and visita["Perfil da Unidade"] == "UPA 24h"
    assert visita["Horário"] == "09:30" and visita["Módulos Específicos Aplicáveis"] == "CME, UTI"
    # PC conta como NC: OK=1, Parcial=1, Não=1 -> 1/3
    assert visita["Total Parcial"] == 1 and str(visita["Percentual de OK"]).startswith("33")
    assert itens[0]["Ref."] == "1" and itens[73]["Ref."] == "74"
