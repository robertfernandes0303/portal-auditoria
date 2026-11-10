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
    assert v["unit"] == "Juína" and v["date"] == "2026-10-30" and len(v["items"]) == 74
    assert v["items"][0]["s"] == "NC" and v["items"][0]["ev"] == 2 and v["items"][1]["s"] == "NA"


def test_df_planilha_antiga_com_municipio_e_aba_ausente():
    """Auditoria_Consolidado antigo: cabeçalho tem 'Município', as linhas não -> valores devem cair nas colunas certas."""
    cab = ["Código da Visita", "Unidade", "Município", "Data da Visita", "Responsável pela Visita", "Nome de Quem Acompanhou",
           "Início do Preenchimento", "Fim do Preenchimento (Envio)", "Status da Visita", "Total de Itens Aplicáveis",
           "Total Conforme", "Total Não Conforme", "Total Não se Aplica", "Total Não Preenchido", "Percentual de Conformidade"]
    lin = ["AUD-X", "Aripuanã", "22/09/2026", "Litana", "Dayane", "22/09/2026 14:12:54", "25/09/2026 12:24:50", "Completa", "226", "169", "57", "15", "0", "74.8%"]
    df = readers._df([cab, lin], "aud", "Visitas")
    r = df.iloc[0]
    assert r["Data da Visita"] == "22/09/2026" and r["Responsável pela Visita"] == "Litana" and r["Percentual de Conformidade"] == "74.8%"
    assert r["Total Conforme"] == "169" and r["Total Não Conforme"] == "57"
    assert readers._df([], "aud", "Visitas").empty


def test_load_visita_tecnica_livre_so_global(monkeypatch):
    import pandas as pd
    from core import readers as rd
    vis = pd.DataFrame([{"Código da Visita": "VT-1", "Hospital": "Hospital Júlio", "Data da Visita": "13/10/2026", "Responsável pela Visita": "Natasha"}])
    class U:  # store mínimo
        def __init__(s, role): s.role = role
    class St:
        def __init__(s, role): s.role = role; s.data = {"units": [], "connections": {}}
        def user_by_mail(s, m): return {"role": s.role, "active": True, "scope": "all" if s.role in ("admin", "resp") else "sel", "units": []}
        def units(s, only_active=True): return []
    monkeypatch.setattr(rd, "_fontes", lambda store, form, problems: [(vis, pd.DataFrame())] if form == "v03" else [])
    monkeypatch.setattr(rd.perms, "allowed_unit_ids", lambda store, user: []) if hasattr(rd, "perms") else None
    assert [v["unit"] for v in rd.load(St("admin"), "a@b")["visits"]] == ["Hospital Júlio"]
    assert rd.load(St("gestor"), "a@b")["visits"] == []


def test_visita_enf_antiga_le_com_catalogo_legado():
    """Visita gravada com o checklist de 43 itens continua legivel depois do padrao de 74 itens."""
    import pandas as pd
    from forms.enfermagem import catalogo_legado as lg
    cat = readers._catalogo("enf")
    vis = pd.DataFrame([{"Código da Visita": "ENF-VELHA", "Hospital": "Juína", "Data da Visita": "30/10/2026", "Responsável pela Visita": "R"},
                        {"Código da Visita": "ENF-NOVA", "Hospital": "Juína", "Data da Visita": "10/11/2026", "Responsável pela Visita": "R"}])
    velho = lg.GRUPOS[0]["itens"][0]
    novo = cat[0][1][0]
    itens = pd.DataFrame([
        {"Código da Visita": "ENF-VELHA", "Nº do Item": "1", "Item a Verificar": velho["texto"], "Situação": "Não", "Qtde de Anexos": "0"},
        {"Código da Visita": "ENF-NOVA", "Nº do Item": "1", "Item a Verificar": novo[1], "Situação": "OK", "Qtde de Anexos": "0"}])
    a, b = readers._visitas_de("enf", vis, itens, cat)
    assert len(a["items"]) == 43 and a["items"][0]["name"] == velho["texto"] and a["items"][0]["s"] == "NC"
    assert len(b["items"]) == 74 and b["items"][0]["name"] == novo[1] and b["items"][0]["s"] == "C"
