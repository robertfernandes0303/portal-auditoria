"""Senhas do login por e-mail e senha: hash scrypt com sal (nunca guardamos a senha). Puro Python."""
import base64
import hashlib
import hmac
import os


def hash_senha(senha):
    sal = os.urandom(16)
    h = hashlib.scrypt(senha.encode(), salt=sal, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(sal).decode() + "$" + base64.b64encode(h).decode()


def confere(senha, guardado):
    try:
        _, s, h = guardado.split("$")
        novo = hashlib.scrypt(senha.encode(), salt=base64.b64decode(s), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(novo, base64.b64decode(h))
    except Exception:
        return False
