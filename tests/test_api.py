import copy, pytest
from core import api
from core.store import Store


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("PORTAL_DATA_DIR", str(tmp_path))
    import importlib
    from core import settings
    importlib.reload(settings)
    return Store()


def payload(store):
    b = api.build_boot(store, "admin.inicial@portal.local", 1, {})
    return {"profiles": b["profiles"], "users": b["users"], "units": b["units"],
            "connections": b["connections"]}


ADM = "admin.inicial@portal.local"


def test_boot_modes(store):
    assert api.build_boot(store, None, 1, {})["mode"] == "login"
    assert api.build_boot(store, "x@y.com", 1, {})["mode"] == "denied"
    b = api.build_boot(store, ADM, 1, {})
    assert b["mode"] == "app" and "conn" in b["me"]["screens"]


def test_add_user_and_scope(store):
    p = payload(store)
    p["users"].append({"id": "n", "name": "Ana", "mail": "ana@isssl.com.br", "role": "gestor", "scope": "sel", "units": ["Juína"], "ov": {}})
    assert api.save_config(store, ADM, p) == "Salvo."
    assert store.user_by_mail("ana@isssl.com.br")["units"] == ["juina"]


def test_gestor_boot_is_scoped(store):
    p = payload(store)
    p["users"].append({"id": "n", "name": "Ana", "mail": "ana@isssl.com.br", "role": "gestor", "scope": "sel", "units": ["Juína"], "ov": {}})
    api.save_config(store, ADM, p)
    b = api.build_boot(store, "ana@isssl.com.br", 1, {})
    assert b["me"]["units"] == ["Juína"] and b["users"] == [] and len(b["units"]) == 1 and b["connections"] == {}


def test_invariants(store):
    p = payload(store)
    q = copy.deepcopy(p); q["users"] = []
    with pytest.raises(api.Rejected): api.save_config(store, ADM, q)
    q = copy.deepcopy(p); q["users"].append({"id": "n", "name": "Ana", "mail": "ADMIN.inicial@portal.local", "role": "gestor", "scope": "all", "units": [], "ov": {}})
    with pytest.raises(api.Rejected): api.save_config(store, ADM, q)
    q = copy.deepcopy(p); q["units"] = [dict(u, ativo=False) for u in q["units"]]
    with pytest.raises(api.Rejected): api.save_config(store, ADM, q)
    q = copy.deepcopy(p); q["profiles"].pop("gestor")
    with pytest.raises(api.Rejected): api.save_config(store, ADM, q)


def test_non_admin_cannot_touch_admin_or_units(store):
    p = payload(store)
    p["users"].append({"id": "n", "name": "Ana", "mail": "ana@isssl.com.br", "role": "gestor", "scope": "all", "units": [],
                       "ov": {"perm": True}})
    api.save_config(store, ADM, p)
    q = payload(store)
    q["users"][0]["role"] = "resp"
    ana_p = api.build_boot(store, "ana@isssl.com.br", 1, {})
    assert "perm" in ana_p["me"]["screens"] and "conn" not in ana_p["me"]["screens"]
    q = {"profiles": ana_p["profiles"], "users": ana_p["users"], "units": ana_p["units"], "connections": {}}
    q["users"].append({"id": "m", "name": "Mau", "mail": "mau@isssl.com.br", "role": "admin", "scope": "all", "units": [], "ov": {}})
    with pytest.raises(api.Rejected): api.save_config(store, "ana@isssl.com.br", q)


def test_connections_validate_and_map(store):
    p = payload(store)
    p["connections"] = {"aud|Juína": {"planilha": "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUv/edit", "pasta": ""}}
    api.save_config(store, ADM, p)
    assert "aud|juina" in store.data["connections"]
    assert api.build_boot(store, ADM, 2, {})["connections"].keys() == {"aud|Juína"}
    p["connections"]["aud|Juína"]["pasta"] = "lixo"
    with pytest.raises(api.Rejected): api.save_config(store, ADM, p)


def test_new_unit_gets_id_and_cannot_delete(store):
    p = payload(store)
    p["units"].append({"id": "", "nome": "Sinop - Hospital", "ativo": True})
    api.save_config(store, ADM, p)
    assert any(u["id"] == "sinop-hospital" for u in store.data["units"])
    p["units"] = p["units"][:-1]
    with pytest.raises(api.Rejected): api.save_config(store, ADM, p)


def test_planilha_nao_pode_repetir_entre_formularios():
    import pytest
    from core import api
    from core.store import Store
    st = Store.load() if hasattr(Store, "load") else None
    units = [{"id": "u1", "nome": "Juína", "ativo": True}]
    ok = {"enf|__consolidado__": {"planilha": "1" * 30, "pasta": "P" * 30}, "v03|__consolidado__": {"planilha": "2" * 30, "pasta": "Q" * 30}}
    api._conferir_separacao(ok, units)
    dup = {"enf|__consolidado__": {"planilha": "1" * 30, "pasta": ""}, "v03|__consolidado__": {"planilha": "1" * 30, "pasta": ""}}
    with pytest.raises(api.Rejected):
        api._conferir_separacao(dup, units)
    pasta = {"enf|__consolidado__": {"planilha": "", "pasta": "P" * 30}, "v03|__consolidado__": {"planilha": "", "pasta": "P" * 30}}
    with pytest.raises(api.Rejected):
        api._conferir_separacao(pasta, units)


def test_login_por_senha():
    from core.store import Store
    st = Store()
    st.data["users"].append({"id": "u-x", "name": "X", "mail": "x@isssl.com.br", "role": "admin", "scope": "all", "units": [], "ov": {}, "active": True})
    st.set_password("X@isssl.com.br", "SenhaBoa123")
    assert st.check_password("x@isssl.com.br", "SenhaBoa123")
    assert not st.check_password("x@isssl.com.br", "errada")
    assert not st.check_password("nao@existe.com", "SenhaBoa123")
    assert "SenhaBoa123" not in str(st.data)


def test_visita_tecnica_sem_filtro_por_unidade(store):
    """Hospitais em disputa de licitação não são unidades do cadastro: qualquer perfil que registra visitas pode usar."""
    from core.forms_api import Ctx
    store.data["users"].append({"id": "u-g", "name": "Gestor", "mail": "g@isssl.com.br", "role": "gestor", "scope": "unit",
                                "units": [], "ov": {}, "active": True})
    c = Ctx(store, "g@isssl.com.br", store.user_by_mail("g@isssl.com.br"))
    c.require_unit("Hospital Concorrente XYZ", free=True)          # visita técnica: livre
    with pytest.raises(api.Rejected):
        c.require_unit("Hospital Concorrente XYZ")                  # auditoria institucional: continua restrita à unidade
    from forms.enfermagem.adapter import _visivel
    assert _visivel(c, "qualquer hospital")


def test_sqlite_ida_e_volta_e_migracao(tmp_path, monkeypatch):
    import json, importlib
    from core import settings
    monkeypatch.setenv("PORTAL_DATA_DIR", str(tmp_path))
    importlib.reload(settings)
    import core.store as cs
    importlib.reload(cs)
    # config antiga em JSON é importada na primeira leitura
    j = cs.JsonBackend(str(tmp_path / "portal_config.json"))
    s0 = cs.Store.__new__(cs.Store)
    base = cs._defaults()
    base["users"].append({"id": "u1", "name": "Ana", "mail": "Ana@isssl.com.br", "role": "gestor", "scope": "sel", "units": ["juina"], "ov": {}, "active": True})
    base["credentials"]["ana@isssl.com.br"] = "scrypt$x$y"
    base["plans"]["k"] = {"unit": "Juína", "acao": "a"}
    base["connections"]["aud|juina"] = {"planilha": "P", "pasta": "F"}
    j.save(base)
    st = cs.Store()
    assert st.kind == "sqlite" and (tmp_path / "portal.db").exists()
    assert st.user_by_mail("ana@isssl.com.br")["units"] == ["juina"]
    assert st.data["credentials"]["ana@isssl.com.br"] == "scrypt$x$y" and st.data["plans"]["k"]["acao"] == "a"
    st.log("x", "teste"); st.data["users"][-1]["active"] = False; st.save()
    st2 = cs.Store()
    assert st2.data["audit"][0]["what"] == "teste" and st2.user_by_mail("ana@isssl.com.br")["active"] is False
    assert [u["id"] for u in st2.data["units"]] == [u["id"] for u in base["units"]]       # ordem preservada
    assert st2.data["connections"]["aud|juina"]["pasta"] == "F"


def _user(store, mail, role, scope, units):
    store.data["users"].append({"id": "u-" + mail[:4], "name": mail, "mail": mail, "role": role, "scope": scope, "units": units, "ov": {}, "active": True})


def test_plano_quem_edita(store):
    from core import plans
    _user(store, "g@x.com", "gestor", "sel", ["juina"])
    _user(store, "m@x.com", "membro", "sel", ["juina"])
    _user(store, "r@x.com", "resp", "all", [])
    base = {"unit": "Juína", "mod": "aud", "gn": "G", "name": "Item", "status": "Em andamento", "prazo": "2026-12-01", "acao": "a", "resp": "Maria"}
    assert plans.save(store, "g@x.com", base)["plan"]["by"]                      # gestor da própria unidade
    assert plans.save(store, "r@x.com", {**base, "acao": "b"})["plan"]["acao"] == "b"   # responsável pela visita (global)
    assert plans.save(store, ADM, base)                                           # administrador
    assert plans.save(store, "m@x.com", {**base, "acao": "c"})["plan"]["acao"] == "c"   # integrante (quem acompanha a unidade) também preenche
    with pytest.raises(api.Rejected):
        plans.save(store, "m@x.com", {**base, "unit": "Aripuanã"})                # integrante só na própria unidade
    with pytest.raises(api.Rejected):
        plans.save(store, "g@x.com", {**base, "unit": "Aripuanã"})                # gestor de outra unidade
    with pytest.raises(api.Rejected):
        plans.save(store, "g@x.com", {**base, "status": "Qualquer"})
    with pytest.raises(api.Rejected):
        plans.save(store, "g@x.com", {**base, "prazo": "31/12/2026"})
    assert plans.visible(store, "m@x.com")["plan_edit"] == ["Juína"]
    assert plans.visible(store, "g@x.com")["plan_edit"] == ["Juína"]
    assert plans.visible(store, "r@x.com")["plan_edit"] == "all"


def test_admin_inicial_pela_senha_do_secret(tmp_path, monkeypatch):
    import importlib
    from core import settings
    monkeypatch.setenv("PORTAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PORTAL_ADMIN_EMAIL", "robert@isssl.com.br")
    monkeypatch.setenv("PORTAL_ADMIN_PASSWORD", "SenhaInicial1")
    importlib.reload(settings)
    import core.store as cs
    importlib.reload(cs)
    st = cs.Store()
    assert st.check_password("robert@isssl.com.br", "SenhaInicial1") and not st.check_password("robert@isssl.com.br", "outra")


def test_visitas_em_aberto_so_o_responsavel_conduz(store):
    """Gestor e Integrante só consultam as visitas em andamento: nenhuma ação dos formulários é aceita (mesmo com a tela Nova visita liberada
    por ajuste pessoal). Responsável pela visita e Administrador conduzem."""
    from core import forms_api, perms
    _user(store, "g@x.com", "gestor", "sel", ["juina"])
    _user(store, "m@x.com", "membro", "sel", ["juina"])
    _user(store, "r@x.com", "resp", "all", [])
    for mail in ("g@x.com", "m@x.com"):
        store.user_by_mail(mail)["ov"] = {"nova": True}
        for act in ("form_open", "form_load", "form_save", "form_upload", "form_submit"):
            with pytest.raises(api.Rejected, match="Responsável pela visita"):
                forms_api.handle(store, mail, act, {"form": "enf", "codigo": "X"})
        assert not perms.can_conduct_visit(store, store.user_by_mail(mail))
    assert perms.can_conduct_visit(store, store.user_by_mail("r@x.com"))
    assert perms.can_conduct_visit(store, store.user_by_mail(ADM))
