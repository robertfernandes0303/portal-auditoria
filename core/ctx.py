import streamlit as st
from core import auth
from core.store import Store


@st.cache_resource(show_spinner=False)
def get_store():
    return Store()


def ctx():
    store = get_store()
    user = store.user_by_mail(auth.current_mail())
    return store, user
