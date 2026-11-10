from forms.sesmt import logic, schema as sc


def test_catalogo():
    assert len(logic.catalogo()) == 18 and logic.config()["total"] == 156


def test_montar_envio_totais():
    cat = logic.catalogo()
    nums = [i["num"] for g in cat for i in g["itens"]]
    d = {"codigo_visita": "SES-X-20260101-ab12", "hospital": "Juína", "responsavel_visita": "R",
         "data_visita": "2026-01-01",
         "respostas": {nums[0]: {"situacao": "OK"}, nums[1]: {"situacao": "Não"}, nums[2]: {"situacao": "N/A"}},
         "anexos": {}}
    res = logic.montar_envio(d)
    visita = res[0]
    assert visita["Total Conforme"] == 1 and visita["Total Não Conforme"] == 1
    assert visita["Total Não se Aplica"] == 1 and visita["Total Não Preenchido"] == 153
    assert str(visita["Percentual de Conformidade"]).startswith("50")
    assert set(visita) == set(sc.COLUNAS_VISITA)
    assert all(set(i) == set(sc.COLUNAS_ITEM) for i in res[1])
