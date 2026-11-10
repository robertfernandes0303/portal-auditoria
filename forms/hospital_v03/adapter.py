"""Ponte entre o portal e a Visita Técnica · Hospital (ver core/forms_api.py)."""
import base64
import binascii
import threading
from core.api import Rejected
from core.forms_api import safe, fill_loc
from . import logic as lg, schema as sc, sheets_backend as be, evidencias as ev

MAX_B64 = 18 * 1024 * 1024  # ~13 MB binário (PDF até 10 MB; fotos já chegam reduzidas)


def _mapping(ctx):
    c = ctx.conn("v03").get("__consolidado__", {})
    return {"planilha_id": c.get("planilha", ""), "pasta_evidencias": c.get("pasta", ""), "nome_planilha": "Checklist_visita_tecnica_Hosp"}


def _visivel(ctx, hospital):
    return True   # sem filtro por unidade (hospitais em disputa de licitação)


def _resumo(r):
    return {"codigo": r["codigo"], "hospital": r["hospital"], "responsavel": r["responsavel"], "atualizado_em": r["atualizado_em"],
            "corrompido": r["corrompido"], "feitos": 0 if r["corrompido"] else lg.resumo_rascunho(r["dados"] or {})}


def aquecer(ctx):
    """Chamado ao subir o servidor (core/host.py): deixa a planilha e os rascunhos prontos em memória."""
    m = _mapping(ctx)
    be._carregar_mapeamento = lambda: m
    be.aquecer()


def handle(ctx, act, pl):
    m = _mapping(ctx)
    be._carregar_mapeamento = lambda: m
    base = {"form": "v03"}
    if act == "form_open":
        ab = be.listar_rascunhos_abertos()
        if ab == be.ERRO_VERIFICACAO_RASCUNHO:
            return {**base, "kind": "form_open", "ok": True, "estado": "erro_verificacao", "catalogo": lg.catalogo(), "config": lg.config()}
        return {**base, "kind": "form_open", "ok": True, "estado": "head", "catalogo": lg.catalogo(), "config": lg.config(),
                "abertas": [_resumo(r) for r in ab if r["corrompido"] or _visivel(ctx, r["hospital"])]}
    if act == "form_hospital":
        h = str(pl.get("hospital") or "").strip()
        ctx.require_unit(h, free=True)
        ach = be.listar_rascunhos_hospital(h)
        if ach == be.ERRO_VERIFICACAO_RASCUNHO:
            return {**base, "kind": "form_hospital", "ok": True, "estado": "erro"}
        if ach:
            return {**base, "kind": "form_hospital", "ok": True, "estado": "lista", "codigo": lg.novo_codigo(h), "lista": [_resumo(r) for r in ach]}
        return {**base, "kind": "form_hospital", "ok": True, "estado": "novo", "codigo": lg.novo_codigo(h)}
    if act == "form_load":
        r = be.carregar_rascunho_codigo(str(pl.get("codigo") or ""))
        if r == be.ERRO_VERIFICACAO_RASCUNHO:
            return {**base, "kind": "form_load", "ok": False, "msg": "Não foi possível consultar a visita agora. Tente de novo."}
        if not r or r["corrompido"] or not _visivel(ctx, r["hospital"]):
            return {**base, "kind": "form_load", "ok": False, "msg": "Visita não encontrada ou sem acesso."}
        return {**base, "kind": "form_load", "ok": True, "rascunho": {"atualizado_em": r["atualizado_em"], "dados": r["dados"]}}
    if act == "form_save":
        d = fill_loc(pl.get("dados") or {})
        if not d.get("codigo_visita"):
            raise Rejected("Visita sem código.")
        ctx.require_unit(str(d.get("hospital", "")).strip(), free=True)
        cod, hosp, resp, ver = d["codigo_visita"], d.get("hospital", ""), d.get("responsavel_visita", ""), int(pl.get("versao") or 0)
        threading.Thread(target=lambda: safe(be.salvar_rascunho, cod, hosp, resp, d, ver), daemon=True).start()
        est = be.estado_autosave(cod)
        out = {**base, "kind": "form_save", "ok": True}
        if est and not est["ok"]:
            out["autosave_erro"] = est["msg"]
        mesc = be.mesclado_pendente(cod)
        if mesc:
            out["mesclado"] = mesc
        return out
    if act == "form_upload":
        ctx.require_unit(str(pl.get("unit") or "").strip(), free=True)
        b64 = str(pl.get("b64") or "")
        if len(b64) > MAX_B64:
            return {**base, "kind": "form_upload", "ok": False, "num": pl.get("num"), "msg": "Arquivo muito grande."}
        try:
            dados = base64.b64decode(b64, validate=True)
        except (binascii.Error, ValueError):
            return {**base, "kind": "form_upload", "ok": False, "num": pl.get("num"), "msg": "Arquivo inválido."}
        num = int(pl.get("num"))
        if not 1 <= num <= sc.TOTAL_ITENS:
            raise Rejected("Item inválido.")
        sessao, pasta = be.drive_para_evidencias()
        try:
            info = ev.guardar_evidencia(sessao, pasta, str(pl.get("codigo")), num, str(pl.get("nome") or "arquivo"), dados)
        except ev.EvidenciaErro as exc:
            return {**base, "kind": "form_upload", "ok": False, "num": num, "msg": f"{pl.get('nome')}: {exc}"}
        return {**base, "kind": "form_upload", "ok": True, "num": num, "anexo": info}
    if act == "form_submit":
        d = fill_loc(pl.get("dados") or {})
        hosp = str(d.get("hospital", "")).strip()
        ctx.require_unit(hosp, free=True)
        if not hosp or not str(d.get("responsavel_visita", "")).strip() or not d.get("codigo_visita"):
            return {"kind": "form_submit", "ok": False, "msg": "Informe hospital e responsável."}
        try:
            visita, itens, evid, sint, pend = lg.montar_envio(d)
        except Exception:
            return {"kind": "form_submit", "ok": False, "msg": "Dados da visita inválidos."}
        if visita["Total Não Preenchido"] and not pl.get("forcado"):
            return {"kind": "form_submit", "ok": False, "msg": "Há itens sem resposta. Revise ou envie incompleta."}
        ok, modo, msg = be.salvar_auditoria(visita, itens, evid, sint, pend)
        if ok:
            safe(be.apagar_rascunho, visita["Código da Visita"])
        ctx.store.log(ctx.mail, f"Enviou v03 {visita['Código da Visita']} ({modo})")
        ctx.store.save()
        res = {k: visita[k] for k in ("Total OK", "Total Parcial", "Total Não", "Total N/A", "Total Não Preenchido", "Percentual de OK", "Total de Anexos", "Linhas do Quadro-Síntese", "Pendências Registradas")}
        return {"kind": "form_submit", "ok": ok, "modo": modo, "msg": msg, "codigo": visita["Código da Visita"],
                "status": visita["Status da Visita"], "resumo": res}
    raise Rejected("Ação desconhecida.")
