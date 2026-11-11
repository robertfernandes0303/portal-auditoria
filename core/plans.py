"""Plano de ação: cada ação nasce de uma não conformidade (item + unidade + formulário). O que é editável aqui —
ação corretiva, responsável, prazo, situação e observação — fica no cadastro do portal (store.data['plans']).
Quem pode editar (conferido no servidor): Administrador/CDQ e Responsável pela visita (o auditor, todas as unidades), e quem acompanha
a unidade — Gestor e Integrante da unidade (e perfis personalizados com a tela Plano de ação) — somente nas unidades do seu acesso."""
import base64
import binascii
import importlib
import os
import re
from datetime import datetime, timedelta, timezone

from core.api import Rejected
from core import perms

STATUS = ("Aberto", "Em andamento", "Concluído")
LIM = {"acao": 600, "resp": 120, "obs": 600}
MAX_ANEXOS = 6
MAX_B64 = 18 * 1024 * 1024


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
    ant = store.data.get("plans", {}).get(key) or {}
    if ant.get("anexos"):
        rec["anexos"] = ant["anexos"]           # salvar o texto nunca apaga as evidências já anexadas
    store.data.setdefault("plans", {})[key] = rec
    store.log(mail, f"Plano de ação editado: {unit} · {name[:60]}")
    store.save()
    return {"key": key, "plan": rec}


# ---------------------------------------------------------------- evidência de conclusão (opcional)
def _chave(pl):
    unit, mod = str(pl.get("unit") or "").strip(), str(pl.get("mod") or "").strip()
    gn, name = str(pl.get("gn") or "").strip(), str(pl.get("name") or "").strip()
    if not (unit and mod and name):
        raise Rejected("Ação inválida.")
    return unit, mod, f"{unit}|{mod}|{gn}|{name}"


def _autorizar_edicao(store, mail, unit):
    user = store.user_by_mail(mail)
    ed = _quem_edita(store, user)
    if ed is not None and unit not in ed:
        raise Rejected("Você não tem permissão para editar o plano de ação desta unidade.")
    vis = _visiveis(store, user)
    if vis is not None and unit not in vis:
        raise Rejected("Unidade fora do seu acesso.")
    return user


def _codigo_pasta(unit, mod):
    return "PLANO-" + re.sub(r"[^A-Za-z0-9]+", "-", unit).strip("-").upper()[:40] + "-" + mod.upper()


def _destino(store, mail, mod):
    """(módulo do formulário, destino de upload, pasta) com o mesmo mapeamento de conexões que o formulário usa."""
    from core.forms_api import PKG, Ctx
    if mod not in PKG:
        raise Rejected("Formulário inválido.")
    user = store.user_by_mail(mail)
    ctx = Ctx(store, mail, user)
    adapter = importlib.import_module(f"forms.{PKG[mod]}.adapter")
    ev = importlib.import_module(f"forms.{PKG[mod]}.evidencias")
    m = adapter._mapping(ctx)
    adapter.be._carregar_mapeamento = lambda: m
    sessao, pasta = adapter.be.drive_para_evidencias()
    return ev, sessao, pasta


def anexar(store, mail, pl):
    unit, mod, key = _chave(pl)
    user = _autorizar_edicao(store, mail, unit)
    rec = store.data.setdefault("plans", {}).get(key)
    n_atual = len((rec or {}).get("anexos") or [])
    if n_atual >= MAX_ANEXOS:
        raise Rejected(f"Limite de {MAX_ANEXOS} evidências por ação. Remova uma para anexar outra.")
    b64 = str(pl.get("b64") or "")
    if len(b64) > MAX_B64:
        raise Rejected("Arquivo muito grande.")
    try:
        dados = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise Rejected("Arquivo inválido.")
    ev, sessao, pasta = _destino(store, mail, mod)
    try:
        info = ev.guardar_evidencia(sessao, pasta, _codigo_pasta(unit, mod), "acao", str(pl.get("nome") or "arquivo"), dados)
    except ev.EvidenciaErro as e:
        raise Rejected(str(e))
    fid = info["id_arquivo"] or ("local:" + os.path.basename(info["link"]))
    agora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    rec = store.data["plans"].get(key)
    if rec is None:      # primeira edição da ação é o próprio anexo: cria o registro mínimo, sem inventar status
        rec = {"unit": unit, "mod": mod, "gn": str(pl.get("gn") or "").strip(), "name": str(pl.get("name") or "").strip(),
               "status": "Aberto", "prazo": "", "acao": "", "resp": "", "obs": ""}
        store.data["plans"][key] = rec
    rec.setdefault("anexos", []).append({"id": fid, "nome": info["nome"], "tipo": info["tipo"], "kb": info["tamanho_kb"],
                                          "por": user["name"], "em": agora})
    rec["by"], rec["at"] = user["name"], agora
    store.log(mail, f"Evidência anexada ao plano de ação: {unit} · {rec['name'][:60]}")
    store.save()
    return {"key": key, "plan": rec}


def remover_anexo(store, mail, pl):
    unit, mod, key = _chave(pl)
    user = _autorizar_edicao(store, mail, unit)
    rec = store.data.get("plans", {}).get(key)
    fid = str(pl.get("id") or "")
    if not rec or not any(a["id"] == fid for a in rec.get("anexos") or []):
        raise Rejected("Evidência não encontrada.")
    rec["anexos"] = [a for a in rec["anexos"] if a["id"] != fid]
    agora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    rec["by"], rec["at"] = user["name"], agora
    store.log(mail, f"Evidência retirada do plano de ação (o arquivo permanece no Drive): {unit} · {rec['name'][:60]}")
    store.save()
    return {"key": key, "plan": rec}


def obter_anexo(store, mail, pl):
    """Imagem/PDF de uma evidência do plano, para quem enxerga a unidade (não só quem edita)."""
    from core import evidencias
    user = store.user_by_mail(mail)
    if not user or not user.get("active", True):
        raise evidencias.Negado("Sessão inválida.")
    unit, mod, key = _chave(pl)
    vis = _visiveis(store, user)
    if vis is not None and unit not in vis:
        raise evidencias.Negado("Unidade fora do seu acesso.")
    rec = store.data.get("plans", {}).get(key) or {}
    fid = str(pl.get("id") or "")
    achado = next((a for a in rec.get("anexos") or [] if a["id"] == fid), None)
    if not achado:
        raise evidencias.Negado("Evidência não encontrada.")
    pasta_local = None
    if fid.startswith("local:"):
        pasta_local = os.path.join(evidencias._local_dir(mod), _codigo_pasta(unit, mod))
    mime, out = evidencias._preparar(achado["tipo"], evidencias.baixar(fid, pasta_local))
    return {"kind": "plan_evid_get", "ok": True, "fid": fid, "key": key, "nome": achado["nome"], "tipo": achado["tipo"],
            "mime": mime, "b64": base64.b64encode(out).decode("ascii")}
