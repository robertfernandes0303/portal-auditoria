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


_WARM = {"feito": False}


def _aquecer(store):
    """Ao subir o servidor, já lê as planilhas em segundo plano: a primeira pessoa a entrar não espera a leitura fria."""
    try:
        from core import readers, andamento
        mail = next((u["mail"] for u in store.users() if u.get("active", True) and (u.get("role") == "admin" or u.get("scope") == "all")), None)
        if mail:
            readers.load(store, mail)
            andamento.listar(store, mail)
            _aquecer_formularios(store, mail)
    except Exception:
        pass


def _aquecer_formularios(store, mail):
    """Visitas técnicas (Enfermagem, Hospital, UPA/PAM): cliente Google, planilha e lista de rascunhos já em memória."""
    import importlib
    from core import forms_api
    from core.catalog import FORMS
    u = store.user_by_mail(mail)
    for chave, pkg in forms_api.PKG.items():
        if FORMS.get(chave, {}).get("kind") != "vt":
            continue
        try:
            importlib.import_module(f"forms.{pkg}.adapter").aquecer(forms_api.Ctx(store, mail, u))
        except Exception:
            pass


def run():
    st.set_page_config(page_title="Portal de Auditoria · São Lucas", page_icon=":material/fact_check:", layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    store = get_store()
    if not _WARM["feito"]:
        _WARM["feito"] = True
        import threading
        threading.Thread(target=_aquecer, args=(store,), daemon=True).start()
    ss = st.session_state
    ss.setdefault("ver", 1)
    reply = None
    req = ss.get("portal")
    if isinstance(req, dict) and req.get("id") and req["id"] != ss.get("last_rpc"):
        ss["last_rpc"] = req["id"]
        import time as _tm
        from core import gquota as _gq
        _t0, _s0 = _tm.perf_counter(), _gq.snapshot()
        act, pl = req.get("action"), req.get("payload") or {}
        mail = auth.current_mail()
        if mail and settings.password_login_enabled() and store.must_change(mail) and act not in ("change_password", "logout", "pw_login", "pw_resume", "login", "save_noop"):
            reply = {"kind": act, "ok": False, "must_change": True, "msg": "Defina uma nova senha para continuar."}
        elif act == "login":
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
                from core import sessions
                reply = {"kind": "pw_login", "ok": True, "token": sessions.emitir(store, ss["pw_mail"], settings.secret)}
            else:
                ss["pw_fails"] = fails + [time.time()]
                reply = {"kind": "pw_login", "ok": False, "msg": "E-mail ou senha incorretos."}
        elif act == "pw_resume" and settings.password_login_enabled():
            from core import sessions
            m = sessions.validar(store, pl.get("token"), settings.secret)
            if m:
                ss["pw_mail"] = m
                ss["ver"] += 1
                reply = {"kind": "pw_resume", "ok": True, "token": sessions.emitir(store, m, settings.secret)}
            else:
                reply = {"kind": "pw_resume", "ok": False}
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
                reply = {"kind": "ongoing_load", "ok": True, "ongoing": _on, "ongoing_err": bool(_err), "prof": list(andamento.PROF)}
            except Exception as e:
                reply = {"kind": "ongoing_load", "ok": False, "msg": str(e)[:160]}
        elif act == "visit_discard":
            from core import descarte
            try:
                reply = descarte.descartar(store, mail, pl.get("form"), pl.get("codigo"), pl.get("unit"))
            except api.Rejected as e:
                reply = {"kind": "visit_discard", "ok": False, "msg": str(e)}
            except Exception as e:
                reply = {"kind": "visit_discard", "ok": False, "msg": "Não foi possível descartar: " + str(e)[:120]}
        elif act == "change_password" and settings.password_login_enabled():
            import time
            from core import sessions
            fails = [t for t in ss.get("pw_fails", []) if time.time() - t < 300]
            if not mail:
                reply = {"kind": act, "ok": False, "msg": "Entre novamente para alterar a senha."}
            elif len(fails) >= 5:
                reply = {"kind": act, "ok": False, "msg": "Muitas tentativas. Aguarde alguns minutos."}
            else:
                ok, msg = store.trocar_senha(mail, str(pl.get("current") or ""), str(pl.get("new") or ""))
                if ok:
                    store.log(mail, "Alterou a própria senha")
                    store.save()
                    ss["pw_fails"] = []
                    ss["ver"] += 1
                    reply = {"kind": act, "ok": True, "msg": msg, "token": sessions.emitir(store, mail.strip().lower(), settings.secret)}
                else:
                    ss["pw_fails"] = fails + [time.time()]
                    reply = {"kind": act, "ok": False, "msg": msg}
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
                    propria = alvo == (mail or "").strip().lower()
                    store.set_password(alvo, senha, temporaria=not propria)
                    store.log(mail, f"Definiu senha de acesso de {alvo}" + ("" if propria else " (temporária: troca obrigatória no próximo acesso)"))
                    store.save()
                    ss["ver"] += 1
                    reply = {"kind": act, "ok": True, "mail": alvo, "msg": "Senha definida."}
            else:
                store.data["credentials"].pop(alvo, None)
                store.data["must_change"] = [x for x in store.data.get("must_change", []) if x != alvo]
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
        _s1 = _gq.snapshot()
        reply["_t"] = {"ms": round((_tm.perf_counter() - _t0) * 1000), "calls": _s1["calls"] - _s0["calls"],
                       "wait": round(_s1["wait"] - _s0["wait"], 1), "r429": _s1["r429"] - _s0["r429"],
                       "http": round(_s1["http"] - _s0["http"], 2)}
        reply["id"] = req["id"]
    mail = auth.current_mail()
    boot = api.build_boot(store, mail, ss["ver"], _flags(store))
    _comp(boot=boot, reply=reply or ss.get("last_reply"), key="portal", default=None)
    if reply:
        ss["last_reply"] = reply
