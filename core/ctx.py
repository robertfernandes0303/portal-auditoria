import streamlit as st
from core import auth
from core.store import Store


@st.cache_resource(show_spinner=False)
def _make_store():
    return Store()


def get_store():
    """Store em cache do processo. Depois de uma atualização do código o cache pode guardar uma instância da classe antiga
    (sem os métodos novos); nesse caso descarta e recria, em vez de quebrar a tela."""
    s = _make_store()
    if type(s) is not Store or not all(hasattr(s, m) for m in ("must_change", "trocar_senha", "admins_active")):
        _make_store.clear()
        s = _make_store()
    return s


def ctx():
    store = get_store()
    user = store.user_by_mail(auth.current_mail())
    return store, user
