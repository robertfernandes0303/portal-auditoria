"""Identificação do usuário: login Microsoft (OIDC nativo do Streamlit) quando configurado; senão modo de teste."""
import streamlit as st
from core import settings


def current_mail():
    pm = st.session_state.get("pw_mail")
    if pm:
        return pm
    if settings.auth_configured():
        if getattr(st.user, "is_logged_in", False):
            return (st.user.get("email") or st.user.get("preferred_username") or "").lower()
        return None
    return st.session_state.get("dev_mail")


def login_screen(store):
    from core.ui import login_header
    login_header()
    if settings.auth_configured():
        st.button("Entrar com conta Microsoft", type="primary", on_click=st.login, args=("microsoft",), use_container_width=True)
        st.caption("Use a conta institucional. Se não tiver acesso, procure o administrador do portal.")
        return
    st.warning("Modo de teste: login Microsoft ainda não configurado. Escolha um usuário para entrar.", icon=":material/science:")
    users = [u for u in store.users() if u.get("active", True)]
    labels = {u["mail"]: f'{u["name"]} · {store.data["profiles"][u["role"]]["label"]}' for u in users}
    mail = st.selectbox("Entrar como", list(labels), format_func=lambda m: labels[m])
    if st.button("Entrar", type="primary", use_container_width=True):
        st.session_state["dev_mail"] = mail
        st.rerun()


def logout():
    st.session_state.pop("pw_mail", None)
    if settings.auth_configured():
        st.logout()
    else:
        st.session_state.pop("dev_mail", None)
        st.rerun()
