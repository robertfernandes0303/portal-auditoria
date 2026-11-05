"""Institucional: anexos (fotos/PDF) por item entram nos totais e nas linhas gravadas."""
from forms.institucional import logic as lg, schema as sc


def _primeiro_checklist():
    return [i["num"] for s in lg.catalogo() if s["tipo"] != "quantidade" for i in s["itens"]][0]


def test_anexos_contados_e_gravados():
    n = _primeiro_checklist()
    d = {"data_visita": "05/11/2026", "codigo_visita": "AUD-T-1",
         "anexos": {str(n): [{"nome": "a.jpg", "link": "https://x/a", "tamanho_kb": 3}, {"nome": "b.pdf", "link": "", "tamanho_kb": 9}]}}
    visita, itens, _res, _pend = lg.montar_registros("Unidade X", d)
    assert visita["Total de Anexos"] == 2
    linha = [i for i in itens if i["Nº do Item"] == n][0]
    assert linha["Qtde de Anexos"] == 2 and "a.jpg <https://x/a>" in linha["Links dos Anexos"]
    assert set(sc.COLUNAS_ITEM) >= {"Qtde de Anexos", "Links dos Anexos"} and "Total de Anexos" in sc.COLUNAS_VISITA


def test_anexo_em_item_de_quantidade_ignorado():
    d = {"data_visita": "05/11/2026", "codigo_visita": "AUD-T-2", "anexos": {"1": [{"nome": "x.jpg"}]}}
    visita, _i, _r, _p = lg.montar_registros("Unidade X", d)
    assert visita["Total de Anexos"] == 0
