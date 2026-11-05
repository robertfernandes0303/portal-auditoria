"""Sessão persistente: ao atualizar a página o navegador reapresenta um token assinado (HMAC) e a pessoa continua logada.
Sem estado no servidor: o token carrega e-mail + validade e uma impressão da senha atual — trocar/remover a senha, desativar
o usuário ou mudar a chave invalida tudo. Puro Python."""
import base64
import hashlib
import hmac
import time

DIAS = 7


def _chave(secret_fn):
    s = ""
    for caminho in ("portal.session_secret", "portal.admin_password"):
        s = secret_fn(caminho) or ""
        if s:
            break
    if not s:
        s = secret_fn("gcp_service_account.private_key") or "portal-dev-local"
    return hashlib.sha256(("sessao|" + str(s)).encode()).digest()


def _impressao(store, mail):
    h = store.data.get("credentials", {}).get(mail, "")
    return hashlib.sha256(h.encode()).hexdigest()[:16]


def _assinar(chave, corpo):
    return base64.urlsafe_b64encode(hmac.new(chave, corpo.encode(), hashlib.sha256).digest()).decode().rstrip("=")


def emitir(store, mail, secret_fn, agora=None):
    mail = (mail or "").strip().lower()
    exp = int((agora or time.time()) + DIAS * 86400)
    corpo = f"{mail}|{exp}|{_impressao(store, mail)}"
    b = base64.urlsafe_b64encode(corpo.encode()).decode().rstrip("=")
    return b + "." + _assinar(_chave(secret_fn), corpo)


def validar(store, token, secret_fn, agora=None):
    """Devolve o e-mail se o token for válido e o usuário ainda puder entrar; senão None."""
    try:
        b, sig = str(token or "").split(".", 1)
        corpo = base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode()
        if not hmac.compare_digest(sig, _assinar(_chave(secret_fn), corpo)):
            return None
        mail, exp, imp = corpo.split("|")
        if int(exp) < (agora or time.time()):
            return None
        u = store.user_by_mail(mail)
        if not u or not u.get("active", True) or not store.data.get("credentials", {}).get(mail):
            return None
        if not hmac.compare_digest(imp, _impressao(store, mail)):
            return None
        return mail
    except Exception:
        return None
