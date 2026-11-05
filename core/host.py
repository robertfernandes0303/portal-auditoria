"""Ponte Streamlit <-> interface. Só este arquivo conhece o Streamlit; o resto (core/api.py, store, perms) roda em qualquer host."""
import os
import streamlit as st
import streamlit.components.v1 as components
from core import settings, api, auth, drive
from core.ctx import get_store

_UI = os.path.join(os.path.dirname(os.path.dirname(__file__)), "portal_ui")
_comp = components.declare_component("portal", path=_UI)

CSS = """
<style>
header[data-testid="stHeader"],footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],#MainMenu{display:none!important}
[data-testid="stAppViewContainer"],[data-testid="stMain"],.main,.block-container{padding:0!important;margin:0!important;max-width:none!important}
[data-stale="true"],[data-stale="true"] *,.stale-element,[data-testid="stElementContainer"],[data-testid="stCustomComponentV1"],[data-testid="stMain"] *{opacity:1!important;transition:none!important;filter:none!important}
[data-testid="stStatusWidget"],[data-testid="stAppDeployButton"]{display:none!important}
iframe[title="portal.portal"],iframe[title*="portal"]{position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;border:0;z-index:999990;background:#fff}
</style>"""


def _flags(store):
    return {"dev": not settings.auth_configured() and not settings.password_login_enabled(), "ms": settings.auth_configured(),
            "password": settings.password_login_enabled(), "google": settings.google_configured(), "sa_email": drive.service_account_email()}


def run():
    st.set_page_config(page_title="Portal de Auditoria · São Lucas", page_icon=":material/fact_check:", layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    store = get_store()
    ss = st.session_state
    ss.setdefault("ver", 1)
    reply = None
    req = ss.get("portal")
    if isinstance(req, dict) and req.get("id") and req["id"] != ss.get("last_rpc"):
        ss["last_rpc"] = req["id"]
        act, pl = req.get("action"), req.get("payload") or {}
        mail = auth.current_mail()
        if act == "login":
            if settings.auth_configured():
                st.login("microsoft")
            else:
                reply = {"kind": "login", "ok": False, "msg": "Login Microsoft ainda não está configurado neste ambiente."}
        elif act == "dev_login" and not settings.auth_configured() and not settings.password_login_enabled():
            u = store.user_by_mail(pl.get("mail"))
            if u and u.get("active", True):
                ss["dev_mail"] = u["mail"]
                ss["ver"] += 1
            reply = {"kind": "dev_login", "ok": bool(u), "msg": "" if u else "Usuário não encontrado."}
        elif act == "pw_login" and settings.password_login_enabled():
            import time
            fails = [t for t in ss.get("pw_fails", []) if time.time() - t < 300]
            if len(fails) >= 5:
                reply = {"kind": "pw_login", "ok": False, "msg": "Muitas tentativas. Aguarde alguns minutos."}
            elif store.check_password(str(pl.get("mail", "")), str(pl.get("password", ""))):
                ss["pw_mail"] = str(pl["mail"]).strip().lower()
                ss["pw_fails"] = []
                ss["ver"] += 1
                reply = {"kind": "pw_login", "ok": True}
            else:
                ss["pw_fails"] = fails + [time.time()]
                reply = {"kind": "pw_login", "ok": False, "msg": "E-mail ou senha incorretos."}
        elif act == "logout":
            if settings.auth_configured():
                st.logout()
            ss.pop("dev_mail", None)
            ss.pop("pw_mail", None)
            ss["ver"] += 1
        elif act == "save":
            try:
                msg = api.save_config(store, mail, pl)
                reply = {"kind": "save", "ok": True, "msg": msg}
            except api.Rejected as e:
                reply = {"kind": "save", "ok": False, "msg": str(e)}
            ss["ver"] += 1
        elif act and act.startswith("form_"):
            from core import forms_api
            try:
                reply = forms_api.handle(store, mail, act, pl)
            except api.Rejected as e:
                reply = {"kind": act, "ok": False, "msg": str(e)}
        elif act == "data_load":
            from core import readers, plans
            try:
                if pl.get("fresh"):
                    readers.limpar_cache()
                reply = {"kind": "data_load", "ok": True, **readers.load(store, mail), **plans.visible(store, mail)}
            except Exception as e:
                reply = {"kind": "data_load", "ok": False, "msg": str(e)[:160]}
        elif act == "ongoing_load":          # separado: o Painel não espera a leitura dos rascunhos
            from core import andamento
            try:
                if pl.get("fresh"):
                    andamento.limpar_cache()
                _err = []
                _on = andamento.listar(store, mail, _err)
                reply = {"kind": "ongoing_load", "ok": True, "ongoing": _on, "ongoing_err": bool(_err)}
            except Exception as e:
                reply = {"kind": "ongoing_load", "ok": False, "msg": str(e)[:160]}
        elif act in ("set_password", "remove_password"):
            who = store.user_by_mail(mail)
            alvo = str(pl.get("mail") or "").strip().lower()
            if not who or who["role"] != "admin" or not who.get("active", True):
                reply = {"kind": act, "ok": False, "msg": "Só o Administrador define senhas."}
            elif not store.user_by_mail(alvo):
                reply = {"kind": act, "ok": False, "msg": "Usuário não encontrado. Salve o usuário antes de definir a senha."}
            elif act == "set_password":
                senha = str(pl.get("password") or "")
                if len(senha) < 8:
                    reply = {"kind": act, "ok": False, "msg": "A senha precisa ter pelo menos 8 caracteres."}
                else:
                    store.set_password(alvo, senha)
                    store.log(mail, f"Definiu senha de acesso de {alvo}")
                    store.save()
                    ss["ver"] += 1
                    reply = {"kind": act, "ok": True, "mail": alvo, "msg": "Senha definida."}
            else:
                store.data["credentials"].pop(alvo, None)
                store.log(mail, f"Removeu a senha de acesso de {alvo}")
                store.save()
                ss["ver"] += 1
                reply = {"kind": act, "ok": True, "mail": alvo, "msg": "Senha removida."}
        elif act == "plan_save":
            from core import plans
            try:
                reply = {"kind": "plan_save", "ok": True, **plans.save(store, mail, pl)}
            except api.Rejected as e:
                reply = {"kind": "plan_save", "ok": False, "msg": str(e)}
        elif act in ("conn_discover", "conn_create"):
            from core import perms, drive
            who = store.user_by_mail(mail)
            if not who or not perms.can(store, who, "conn"):
                reply = {"kind": act, "ok": False, "msg": "Sem permissão."}
            elif not settings.google_configured():
                reply = {"kind": act, "ok": False, "msg": "Credenciais do Google não configuradas."}
            else:
                try:
                    if act == "conn_discover":
                        reply = {"kind": act, "ok": True, **drive.discover(True)}
                    else:
                        titulo = str(pl.get("title") or "").strip()[:100]
                        if not titulo:
                            reply = {"kind": act, "ok": False, "msg": "Informe um nome para a planilha."}
                        else:
                            sid, url = drive.create_spreadsheet(titulo, str(pl.get("folder") or ""))
                            store.log(mail, f"Criou a planilha {titulo}")
                            store.save()
                            reply = {"kind": act, "ok": True, "k": pl.get("k"), "url": url}
                except Exception as e:
                    reply = {"kind": act, "ok": False, "k": pl.get("k"), "msg": "Não foi possível: " + str(e)[:140]}
        elif act == "test":
            try:
                reply = {"kind": "test", "results": api.run_tests(store, mail, pl.get("conn"))}
            except api.Rejected as e:
                reply = {"kind": "test", "results": {}}
        if reply is None:
            reply = {"kind": act, "ok": True}
        reply["id"] = req["id"]
    mail = auth.current_mail()
    boot = api.build_boot(store, mail, ss["ver"], _flags(store))
    _comp(boot=boot, reply=reply or ss.get("last_reply"), key="portal", default=None)
    if reply:
        ss["last_reply"] = reply
