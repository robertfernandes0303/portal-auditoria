"""Leitura de configuração (segredos do host ou variáveis de ambiente). Sem valores no código."""
import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("PORTAL_DATA_DIR", os.path.join(BASE_DIR, "data"))
META_CONFORMIDADE = 0.85


def secret(path, default=None):
    """secret('portal.admin_email') -> st.secrets['portal']['admin_email'] ou env PORTAL_ADMIN_EMAIL."""
    try:
        cur = st.secrets
        for p in path.split("."):
            cur = cur[p]
        return cur
    except Exception:
        return os.environ.get(path.replace(".", "_").upper(), default)


def auth_configured():
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def google_configured():
    try:
        return "gcp_service_account" in st.secrets and bool(st.secrets["gcp_service_account"].get("client_email"))
    except Exception:
        return False


def password_login_enabled():
    """Login por e-mail e senha (logins criados pelo administrador em Permissionamento). Ligado por padrão enquanto o
    login Microsoft não é obrigatório; desligue com portal.password_login = "0" (secrets) ou PORTAL_PASSWORD_LOGIN=0."""
    v = secret("portal.password_login", None)
    if v is None:
        return True
    return str(v).strip().lower() in ("1", "true", "sim", "yes")
