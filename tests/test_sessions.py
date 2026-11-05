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
