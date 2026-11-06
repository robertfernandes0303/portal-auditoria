from core import sessions, passwords


class Loja:
    def __init__(self):
        self.data = {"credentials": {"a@x.com": passwords.hash_senha("senha-12345")}, "users": [{"mail": "a@x.com", "active": True}]}

    def user_by_mail(self, m):
        return next((u for u in self.data["users"] if u["mail"] == (m or "").strip().lower()), None)


SEG = {"portal.session_secret": "chave-teste"}.get


def test_token_valido_volta_o_email():
    s = Loja(); t = sessions.emitir(s, "A@x.com", SEG)
    assert sessions.validar(s, t, SEG) == "a@x.com"


def test_expirado_adulterado_e_chave_trocada():
    s = Loja(); t = sessions.emitir(s, "a@x.com", SEG, agora=1000)
    assert sessions.validar(s, t, SEG, agora=1000 + 8 * 86400) is None
    assert sessions.validar(s, t, SEG, agora=1000 + 6 * 86400) == "a@x.com"
    b, sig = t.split(".")
    assert sessions.validar(s, b + "." + sig[:-2] + "xx", SEG) is None
    assert sessions.validar(s, "lixo", SEG) is None and sessions.validar(s, "", SEG) is None
    assert sessions.validar(s, t, {"portal.session_secret": "outra"}.get) is None


def test_senha_trocada_ou_usuario_desativado_invalida():
    s = Loja(); t = sessions.emitir(s, "a@x.com", SEG)
    s.data["credentials"]["a@x.com"] = passwords.hash_senha("nova-senha-1")
    assert sessions.validar(s, t, SEG) is None
    s2 = Loja(); t2 = sessions.emitir(s2, "a@x.com", SEG)
    s2.data["users"][0]["active"] = False
    assert sessions.validar(s2, t2, SEG) is None
    s3 = Loja(); t3 = sessions.emitir(s3, "a@x.com", SEG); del s3.data["credentials"]["a@x.com"]
    assert sessions.validar(s3, t3, SEG) is None


def test_token_de_um_usuario_nao_vale_para_outro():
    s = Loja(); s.data["credentials"]["b@x.com"] = passwords.hash_senha("outra-senha-1"); s.data["users"].append({"mail": "b@x.com", "active": True})
    t = sessions.emitir(s, "a@x.com", SEG)
    b, sig = t.split(".")
    import base64
    forjado = base64.urlsafe_b64encode(base64.urlsafe_b64decode(b + "==").replace(b"a@x.com", b"b@x.com")).decode().rstrip("=")
    assert sessions.validar(s, forjado + "." + sig, SEG) is None


# ---- troca de senha (própria e temporária)
from core.store import Store  # noqa: E402


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("PORTAL_DATA_DIR", str(tmp_path))
    s = Store()
    return s


def test_senha_temporaria_exige_troca_e_troca_propria_libera(tmp_path, monkeypatch):
    s = _store(tmp_path, monkeypatch)
    s.data["users"].append({"id": "u2", "name": "Pessoa", "mail": "p@x.com", "role": "admin", "scope": "all", "units": [], "ov": {}, "active": True})
    s.set_password("p@x.com", "Temporaria1", temporaria=True)
    assert s.must_change("P@x.com")
    ok, msg = s.trocar_senha("p@x.com", "errada-123", "NovaSenha1")
    assert not ok and "atual" in msg and s.must_change("p@x.com")
    assert s.trocar_senha("p@x.com", "Temporaria1", "curta")[0] is False
    assert s.trocar_senha("p@x.com", "Temporaria1", "Temporaria1")[0] is False
    assert s.trocar_senha("p@x.com", "Temporaria1", "p@x.com")[0] is False
    ok, _ = s.trocar_senha("p@x.com", "Temporaria1", "NovaSenha1")
    assert ok and not s.must_change("p@x.com")
    assert s.check_password("p@x.com", "NovaSenha1") and not s.check_password("p@x.com", "Temporaria1")


def test_troca_invalida_sessoes_antigas(tmp_path, monkeypatch):
    s = _store(tmp_path, monkeypatch)
    s.data["users"].append({"id": "u2", "name": "P", "mail": "p@x.com", "role": "admin", "scope": "all", "units": [], "ov": {}, "active": True})
    s.set_password("p@x.com", "SenhaAntiga1")
    t = sessions.emitir(s, "p@x.com", SEG)
    assert sessions.validar(s, t, SEG) == "p@x.com"
    s.trocar_senha("p@x.com", "SenhaAntiga1", "SenhaNova123")
    assert sessions.validar(s, t, SEG) is None
