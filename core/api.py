"""Regras do portal no servidor (puro Python, sem Streamlit): monta o que a interface recebe e valida tudo
o que ela envia. A interface nunca é fonte de verdade: permissões e invariantes são conferidas aqui."""
import copy, re
from core import perms, drive
from core.catalog import SCREENS, FORMS
from core.store import slug

SCREEN_IDS = [s for s, _ in SCREENS]
MAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _names(store, ids):
    m = {u["id"]: u["nome"] for u in store.data["units"]}
    return [m[i] for i in ids if i in m]


def build_boot(store, mail, version, flags, mode_hint=None):
    user = store.user_by_mail(mail) if mail else None
    prof = store.data["profiles"]
    boot = {"v": version, "flags": flags, "mail": mail or "",
            "forms": [{"key": k, "name": f["name"], "ready": bool(f.get("ready")), "kind": f.get("kind", "q"), "variant": f.get("variant", ""), "free": bool(f.get("free")), "medido": f.get("medido", True), "conn_mode": f.get("conn_mode", "por_unidade")} for k, f in FORMS.items()]}
    if not mail:
        boot["mode"] = "login"
    elif not user or not user.get("active", True):
        boot["mode"] = "denied"
    else:
        boot["mode"] = "app"
    if flags.get("dev"):
        boot["devUsers"] = [{"mail": u["mail"], "name": u["name"], "label": prof[u["role"]]["label"]}
                            for u in store.users() if u.get("active", True)]
    if boot["mode"] != "app":
        boot.update(profiles={}, users=[], units=[], connections={})
        return boot
    scr = sorted(perms.effective_screens(store, user), key=SCREEN_IDS.index)
    allowed = perms.allowed_unit_ids(store, user)
    p = prof[user["role"]]
    boot["me"] = {"name": user["name"], "mail": user["mail"], "role": user["role"], "label": p["label"], "desc": p.get("desc", ""),
                  "scope": "all" if user["role"] == "admin" or user.get("scope") == "all" else "sel",
                  "units": _names(store, allowed), "screens": scr}
    admin_view = "perm" in scr or "conn" in scr
    boot["units"] = [dict(u) for u in store.data["units"]] if "conn" in scr else \
        [dict(u) for u in store.data["units"] if u["id"] in allowed]
    if admin_view:
        boot["profiles"] = copy.deepcopy(prof)
        boot["users"] = [{"id": u["id"], "name": u["name"], "mail": u["mail"], "role": u["role"], "scope": u["scope"],
                          "units": _names(store, u.get("units") or []), "ov": u.get("ov") or {}, "fict": bool(u.get("fict"))}
                         for u in store.users()]
        boot["pw_users"] = sorted(m for m in store.data.get("credentials", {}))
    else:
        boot["profiles"] = {user["role"]: copy.deepcopy(p)}
        boot["users"] = []
    conns = {}
    if "conn" in scr:
        nm = {u["id"]: u["nome"] for u in store.data["units"]}
        for k, v in store.data["connections"].items():
            form, uid = k.split("|", 1)
            conns[f"{form}|{nm.get(uid, uid)}"] = v
    boot["connections"] = conns
    return boot


class Rejected(Exception):
    pass


def _conferir_separacao(conns, units):
    """Cada formulário (e cada unidade, no Institucional) grava na SUA planilha: a mesma planilha em dois lugares
    misturaria abas de mesmo nome (Visitas, Itens, Rascunho) com colunas diferentes. A mesma pasta de evidências
    também não pode ser usada por formulários diferentes."""
    nomes = {u["id"]: u["nome"] for u in units}
    plan, pasta = {}, {}
    for k, v in conns.items():
        form, _, uid = k.partition("|")
        onde = f"{FORMS[form]['name']} · " + ("planilha única" if uid == "__consolidado__" else nomes.get(uid, uid))
        pid, fid = drive.extract_id(v.get("planilha", "")), drive.extract_id(v.get("pasta", ""))
        if pid:
            if pid in plan:
                raise Rejected(f"A mesma planilha foi informada em dois lugares: {plan[pid]} e {onde}. Cada formulário usa uma planilha própria.")
            plan[pid] = onde
        if fid:
            if fid in pasta and pasta[fid][0] != form:
                raise Rejected(f"A mesma pasta foi informada em formulários diferentes: {pasta[fid][1]} e {onde}. Use uma pasta por formulário.")
            pasta.setdefault(fid, (form, onde))

def save_config(store, actor_mail, payload):
    """Valida e grava. Levanta Rejected com mensagem amigável. Retorna texto de sucesso."""
    store.reload()
    actor = store.user_by_mail(actor_mail)
    if not actor or not actor.get("active", True):
        raise Rejected("Sessão sem acesso.")
    d = copy.deepcopy(store.data)
    can_perm, can_conn = perms.can(store, actor, "perm"), perms.can(store, actor, "conn")
    is_admin = actor["role"] == "admin"

    # ---- unidades (só quem tem 'conn')
    units_in = payload.get("units")
    if units_in is not None:
        cur = {u["id"]: u for u in d["units"]}
        new, seen = [], set()
        for u in units_in:
            nome = str(u.get("nome", "")).strip()[:80]
            if not nome:
                raise Rejected("Unidade sem nome.")
            if nome.lower() in seen:
                raise Rejected(f"Unidade repetida: {nome}.")
            seen.add(nome.lower())
            uid = u.get("id") or ""
            if uid and uid in cur:
                new.append({"id": uid, "nome": cur[uid]["nome"], "ativo": bool(u.get("ativo", True))})
            else:
                base, i, uid = slug(nome), 2, slug(nome)
                while uid in cur or any(x["id"] == uid for x in new):
                    uid, i = f"{base}-{i}", i + 1
                new.append({"id": uid, "nome": nome, "ativo": bool(u.get("ativo", True))})
        if set(cur) - {u["id"] for u in new}:
            raise Rejected("Unidades não podem ser excluídas; desative.")
        if not any(u["ativo"] for u in new):
            raise Rejected("Mantenha ao menos uma unidade ativa.")
        if new != d["units"]:
            if not can_conn:
                raise Rejected("Sem permissão para alterar unidades.")
            d["units"] = new
    name2id = {u["nome"]: u["id"] for u in d["units"]}

    # ---- conexões
    conns_in = payload.get("connections")
    if conns_in is not None and can_conn:
        newc = {}
        for k, v in conns_in.items():
            form, _, un = k.partition("|")
            if form not in FORMS or (un not in name2id and un != "__consolidado__"):
                raise Rejected("Conexão para formulário ou unidade desconhecidos.")
            pl, pa = str(v.get("planilha", "")).strip()[:400], str(v.get("pasta", "")).strip()[:400]
            for ref, lab in ((pl, "planilha"), (pa, "pasta")):
                if ref and not drive.extract_id(ref):
                    raise Rejected(f"Endereço de {lab} inválido em {un}.")
            if pl or pa:
                newc[f"{form}|{name2id.get(un, un)}"] = {"planilha": pl, "pasta": pa}
        _conferir_separacao(newc, d["units"])
        if newc != d["connections"]:
            d["connections"] = newc

    # ---- perfis e usuários (só quem tem 'perm')
    profs_in, users_in = payload.get("profiles"), payload.get("users")
    if profs_in is not None and users_in is not None and can_perm:
        profs = {}
        labels = set()
        for k, p in profs_in.items():
            old = d["profiles"].get(k)
            lab = str(p.get("label", "")).strip()[:60]
            scr = [s for s in p.get("screens", []) if s in SCREEN_IDS]
            if old and old.get("builtin") and k == "admin":
                profs[k] = old
                labels.add(old["label"].lower())
                continue
            if not lab or lab.lower() in labels:
                raise Rejected("Nome de perfil vazio ou repetido.")
            labels.add(lab.lower())
            if not scr:
                raise Rejected("Libere ao menos uma tela por perfil.")
            if p.get("scope") not in ("all", "sel"):
                raise Rejected("Escopo de perfil inválido.")
            if old and old.get("builtin"):
                profs[k] = {**old, "label": lab, "desc": str(p.get("desc", ""))[:200], "scope": p["scope"], "screens": scr}
            else:
                key = k if (old or re.fullmatch(r"p\d+", k)) else "p" + slug(lab)
                if not old and key in d["profiles"]:
                    key = "p" + slug(lab) + "x"
                profs[key] = {"label": lab, "desc": str(p.get("desc", ""))[:200] or "Perfil personalizado.",
                              "scope": p["scope"], "builtin": False, "screens": scr}
        for k, old in d["profiles"].items():
            if k not in profs:
                if old.get("builtin"):
                    raise Rejected("Perfis padrão não podem ser excluídos.")
        users, mails = [], set()
        old_users = {u["id"]: u for u in d["users"]}
        for u in users_in:
            mail = str(u.get("mail", "")).strip().lower()
            name = str(u.get("name", "")).strip()[:80]
            if not name or not MAIL_RE.match(mail):
                raise Rejected("Nome ou e-mail de usuário inválido.")
            if mail in mails:
                raise Rejected(f"E-mail repetido: {mail}.")
            mails.add(mail)
            role = u.get("role")
            if role not in profs:
                raise Rejected(f"Perfil inexistente para {name}.")
            if u.get("scope") not in ("all", "sel"):
                raise Rejected("Escopo inválido.")
            ids = []
            for n in u.get("units", []):
                if n not in name2id:
                    raise Rejected(f"Unidade desconhecida: {n}.")
                ids.append(name2id[n])
            if u["scope"] == "sel" and not ids and role != "admin":
                raise Rejected(f"Selecione ao menos uma unidade para {name}.")
            ov = {s: bool(v) for s, v in (u.get("ov") or {}).items() if s in SCREEN_IDS}
            old = old_users.get(u.get("id"))
            row = {"id": old["id"] if old else "u-" + slug(mail), "name": name, "mail": mail, "role": role,
                   "scope": u["scope"], "units": ids if u["scope"] == "sel" else [], "ov": ov,
                   "active": True, "fict": bool(old and old.get("fict"))}
            if old and old.get("fict"):
                row["role"], row["mail"] = old["role"], old["mail"]
            users.append(row)
        kept = {u["id"] for u in users}
        for oid, old in old_users.items():
            if oid not in kept and old.get("fict"):
                raise Rejected("A conta inicial não pode ser removida.")
        if not [u for u in users if u["role"] == "admin"]:
            raise Rejected("Mantenha ao menos um Administrador.")
        me = next((u for u in users if u["mail"] == actor["mail"].lower()), None)
        if not me:
            raise Rejected("Você não pode remover o próprio acesso.")
        if me["role"] != actor["role"]:
            raise Rejected("Você não pode alterar o próprio perfil.")
        # só Administrador mexe em administradores / concede perfil admin
        old_by_id = old_users
        for u in users:
            o = old_by_id.get(u["id"])
            changed = (o is None) or any(o.get(f) != u[f] for f in ("role", "scope", "units", "ov", "name", "mail"))
            if changed and not is_admin and (u["role"] == "admin" or (o and o["role"] == "admin")):
                raise Rejected("Só o Administrador altera administradores.")
        for oid, o in old_by_id.items():
            if oid not in kept and o["role"] == "admin" and not is_admin:
                raise Rejected("Só o Administrador remove administradores.")
        if profs != d["profiles"] and not is_admin and any(profs.get(k) != d["profiles"].get(k) for k in ("admin",)):
            raise Rejected("Perfil Administrador é fixo.")
        if any(u["role"] not in profs for u in users):
            raise Rejected("Perfil em uso não pode ser excluído.")
        if profs != d["profiles"] or users != d["users"]:
            d["profiles"], d["users"] = profs, users
            keep = {u["mail"].strip().lower() for u in users}
            d["credentials"] = {m: h for m, h in d.get("credentials", {}).items() if m in keep}
    if d == store.data:
        return "Nada para salvar."
    d["audit"] = store.data["audit"]
    store.data = d
    store.log(actor["mail"], "Atualizou configurações")
    store.save()
    return "Salvo."


def run_tests(store, actor_mail, conns):
    actor = store.user_by_mail(actor_mail)
    if not perms.can(store, actor, "conn"):
        raise Rejected("Sem permissão.")
    out = {}
    for k, v in (conns or {}).items():
        res = {}
        for kind in ("planilha", "pasta"):
            ok, msg = drive.test_connection(v.get(kind, ""), kind)
            if ok is not None or v.get(kind):
                res[kind] = {"ok": ok, "msg": msg}
        out[k] = res
    return out
