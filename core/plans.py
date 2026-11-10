"""Plano de ação: cada ação nasce de uma não conformidade (item + unidade + formulário). O que é editável aqui —
ação corretiva, responsável, prazo, situação e observação — fica no cadastro do portal (store.data['plans']).
Quem pode editar (conferido no servidor): Administrador/CDQ e Responsável pela visita (o auditor, todas as unidades), e quem acompanha
a unidade — Gestor e Integrante da unidade (e perfis personalizados com a tela Plano de ação) — somente nas unidades do seu acesso."""
import re
from datetime import datetime, timedelta, timezone

from core.api import Rejected
from core import perms

STATUS = ("Aberto", "Em andamento", "Concluído")
LIM = {"acao": 600, "resp": 120, "obs": 600}


def _quem_edita(store, user):
    """None = todas as unidades; lista de nomes = só estas; [] = ninguém."""
    if not user or not user.get("active", True) or not perms.can(store, user, "plano"):
        return []
    if user["role"] in ("admin", "resp"):
        return None
    names = {u["id"]: u["nome"] for u in store.units(only_active=False)}
    return [names[i] for i in perms.allowed_unit_ids(store, user) if i in names]


def _visiveis(store, user):
    names = {u["id"]: u["nome"] for u in store.units(only_active=False)}
    if user["role"] == "admin" or user.get("scope") == "all":
        return None
    return {names[i] for i in perms.allowed_unit_ids(store, user) if i in names}


def visible(store, mail):
    user = store.user_by_mail(mail)
    if not user or not user.get("active", True):
        return {"plans": {}, "plan_edit": []}
    vis = _visiveis(store, user)
    ed = _quem_edita(store, user)
    plans = {k: v for k, v in store.data.get("plans", {}).items() if vis is None or v.get("unit") in vis}
    return {"plans": plans, "plan_edit": "all" if ed is None else ed}


def save(store, mail, pl):
    user = store.user_by_mail(mail)
    unit, mod = str(pl.get("unit") or "").strip(), str(pl.get("mod") or "").strip()
    gn, name = str(pl.get("gn") or "").strip(), str(pl.get("name") or "").strip()
    if not (unit and mod and name):
        raise Rejected("Ação inválida.")
    ed = _quem_edita(store, user)
    if ed is not None and unit not in ed:
        raise Rejected("Você não tem permissão para editar o plano de ação desta unidade.")
    vis = _visiveis(store, user)
    if vis is not None and unit not in vis:
        raise Rejected("Unidade fora do seu acesso.")
    status = str(pl.get("status") or "Aberto")
    if status not in STATUS:
        raise Rejected("Situação inválida.")
    prazo = str(pl.get("prazo") or "").strip()
    if prazo and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", prazo):
        raise Rejected("Prazo inválido.")
    if prazo:
        try:
            datetime.strptime(prazo, "%Y-%m-%d")
        except ValueError:
            raise Rejected("Prazo inválido.")
    rec = {"unit": unit, "mod": mod, "gn": gn, "name": name, "status": status, "prazo": prazo}
    for k, n in LIM.items():
        rec[k] = str(pl.get(k) or "").strip()[:n]
    agora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    rec["by"], rec["at"] = user["name"], agora
    key = f"{unit}|{mod}|{gn}|{name}"
    store.data.setdefault("plans", {})[key] = rec
    store.log(mail, f"Plano de ação editado: {unit} · {name[:60]}")
    store.save()
    return {"key": key, "plan": rec}
