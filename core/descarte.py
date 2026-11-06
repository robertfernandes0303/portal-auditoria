"""Descarte de uma visita em andamento (rascunho de teste ou zerado). Só Administrador.
Remove apenas a linha do rascunho; visitas já enviadas e o resto da planilha não são tocados.
Antes de remover, o resumo do rascunho vai para o registro de auditoria do portal."""
import importlib
from core import andamento
from core.api import Rejected
from core.forms_api import Ctx, PKG


def descartar(store, mail, form, codigo, unidade):
    u = store.user_by_mail(mail)
    if not u or not u.get("active", True) or u.get("role") != "admin":
        raise Rejected("Só o Administrador descarta visitas em andamento.")
    if form not in PKG:
        raise Rejected("Formulário inválido.")
    codigo = str(codigo or "").strip()
    unidade = str(unidade or "").strip()
    if not codigo:
        raise Rejected("Visita não informada.")
    ctx = Ctx(store, mail, u)
    mod = importlib.import_module(f"forms.{PKG[form]}.adapter")
    be = mod.be
    m = mod._mapping(ctx)
    be._carregar_mapeamento = lambda: m
    if form == "aud":
        if not unidade:
            raise Rejected("Informe a unidade da auditoria.")
        b = be.carregar_rascunho(unidade)
        if not isinstance(b, dict):
            raise Rejected("Rascunho não encontrado (ou não foi possível verificar). Nada foi alterado.")
        d = b.get("dados") or {}
        if str(d.get("codigo_visita") or "") != codigo:
            raise Rejected("O rascunho atual da unidade não é o informado. Nada foi alterado.")
        resumo = f"auditoria {unidade} {codigo}, responsável {d.get('responsavel_visita') or '-'}, {len(d.get('respostas_checklist') or {})} resposta(s)"
        be.apagar_rascunho(unidade)
    else:
        r = be.carregar_rascunho_codigo(codigo)
        if not isinstance(r, dict):
            raise Rejected("Rascunho não encontrado (ou não foi possível verificar). Nada foi alterado.")
        resumo = f"{form} {r.get('hospital') or '-'} {codigo}, responsável {r.get('responsavel') or '-'}, {len((r.get('dados') or {}).get('respostas') or {})} resposta(s)"
        be.apagar_rascunho(codigo)
    store.log(mail, "Descartou visita em andamento: " + resumo)
    store.save()
    andamento.limpar_cache()
    return {"kind": "visit_discard", "ok": True, "form": form, "codigo": codigo, "msg": "Visita descartada."}
