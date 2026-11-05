"""Visitas em andamento (rascunhos ainda não enviados) de todos os formulários, para a tela Início.
Lê os rascunhos reais (planilha/Drive ou arquivo local) com o mesmo acesso de cada formulário. Puro Python."""
import importlib
import time

from core.forms_api import Ctx, PKG
from core.catalog import FORMS

TTL = 60
_CACHE = {}


def limpar_cache():
    _CACHE.clear()


def _vt(ctx, key, out):
    mod = importlib.import_module(f"forms.{PKG[key]}.adapter")
    lg = importlib.import_module(f"forms.{PKG[key]}.logic")
    m = mod._mapping(ctx)
    mod.be._carregar_mapeamento = lambda: m
    ab = mod.be.listar_rascunhos_abertos()
    if not isinstance(ab, list):
        return
    total = lg.config()["total"]
    for r in ab:
        if r.get("corrompido"):
            continue
        feitos = lg.resumo_rascunho(r.get("dados") or {})
        out.append({"form": key, "codigo": r["codigo"], "unit": r["hospital"], "resp": r["responsavel"],
                    "atualizado_em": r["atualizado_em"], "feitos": feitos, "total": total,
                    "pct": min(100, round(100 * feitos / total)) if total else 0})


def _aud(ctx, out):
    mod = importlib.import_module("forms.institucional.adapter")
    lg = mod.lg
    m = mod._mapping(ctx)
    mod.be._carregar_mapeamento = lambda: m
    total = sum(1 for s in lg.SECOES if s["tipo"] != "quantidade" for _ in s["itens"])
    for unidade in (ctx.unit_names if ctx.is_global else ctx.allowed):
        try:
            b = (getattr(mod.be, "carregar_rascunho_rapido", None) or mod.be.carregar_rascunho)(unidade)
        except Exception:
            continue
        if not isinstance(b, dict):
            continue
        d = b.get("dados") or {}
        if not (d.get("codigo_visita") or d.get("respostas_checklist") or d.get("valores_quantidade")):
            continue
        resp, vals = lg.limpar(d)
        feitos = sum(1 for v in resp.values() if v.get("resposta"))
        out.append({"form": "aud", "codigo": d.get("codigo_visita", ""), "unit": unidade, "resp": d.get("responsavel_visita", ""),
                    "atualizado_em": b.get("atualizado_em", ""), "feitos": feitos, "total": total,
                    "pct": min(100, round(100 * feitos / total)) if total else 0})


def listar(store, mail, erros=None):
    user = store.user_by_mail(mail)
    if not user or not user.get("active", True):
        return []
    k = mail.strip().lower()
    hit = _CACHE.get(k)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    ctx = Ctx(store, mail, user)
    out = []
    falhou = False
    for key in ("aud", "enf", "v03", "upa"):
        if not FORMS.get(key, {}).get("ready"):
            continue
        try:
            _aud(ctx, out) if key == "aud" else _vt(ctx, key, out)
        except Exception as e:
            falhou = True
            if erros is not None:
                erros.append(f"{key}: {str(e)[:80]}")
            continue
    out.sort(key=lambda x: x["atualizado_em"][6:10] + x["atualizado_em"][3:5] + x["atualizado_em"][:2] + x["atualizado_em"][11:], reverse=True)
    if not falhou:  # nunca guardar em cache um resultado incompleto por falha de leitura
        _CACHE[k] = (time.time(), out)
    return out
