"""Ponte entre o portal e o formulário Institucional (ver core/forms_api.py)."""
import base64
import binascii
import threading
from datetime import datetime
from core.api import Rejected
from core.forms_api import safe
from . import logic as lg, schema as sc, sheets_backend as be, evidencias as ev

MAX_B64 = 18 * 1024 * 1024  # ~13 MB binário (PDF até 10 MB; fotos já chegam reduzidas)


def _mapping(ctx):
    c = ctx.conn("aud")
    m = {"unidades": {}, "consolidado": "", "pasta_visita_unidade": "", "pasta_visita_consolidado": ""}
    for nome, v in c.items():
        if nome == "__consolidado__":
            m["consolidado"] = v["planilha"]
            m["pasta_visita_unidade"] = m["pasta_visita_consolidado"] = v["pasta"]
        elif v["planilha"]:
            m["unidades"][nome] = v["planilha"]
    return m


def handle(ctx, act, pl):
    unidade = str(pl.get("unit") or "")
    ctx.require_unit(unidade)
    m = _mapping(ctx)
    be._carregar_mapeamento = lambda: m  # o backend original lê o cadastro do portal, não um JSON em disco
    if act == "form_open":
        bruto = be.carregar_rascunho(unidade)
        base = {"kind": "form_open", "ok": True, "form": "aud", "unit": unidade, "catalogo": lg.catalogo(), "config": lg.config()}
        if bruto == be.ERRO_VERIFICACAO_RASCUNHO:
            return {**base, "estado": "erro_verificacao"}
        d = (bruto or {}).get("dados") or {}
        if d.get("codigo_visita") or d.get("secoes_visitadas") or d.get("respostas_checklist") or d.get("valores_quantidade"):
            return {**base, "estado": "retomar", "rascunho": bruto}
        return {**base, "estado": "novo", "codigo": lg.novo_codigo(unidade)}
    if act == "form_save":
        dados = pl.get("dados") or {}
        threading.Thread(target=lambda: safe(be.salvar_rascunho, unidade, dados), daemon=True).start()
        return {"kind": "form_save", "ok": True}
    if act == "form_upload":
        b64 = str(pl.get("b64") or "")
        if len(b64) > MAX_B64:
            return {"kind": "form_upload", "form": "aud", "ok": False, "num": pl.get("num"), "msg": "Arquivo muito grande."}
        try:
            dados_b = base64.b64decode(b64, validate=True)
        except (binascii.Error, ValueError):
            return {"kind": "form_upload", "form": "aud", "ok": False, "num": pl.get("num"), "msg": "Arquivo inválido."}
        num = int(pl.get("num"))
        itens_ok = {i["num"] for s in lg.catalogo() if s["tipo"] != "quantidade" for i in s["itens"]}
        if num not in itens_ok:
            raise Rejected("Item inválido.")
        sessao, pasta = be.drive_para_evidencias()
        try:
            info = ev.guardar_evidencia(sessao, pasta, str(pl.get("codigo")), num, str(pl.get("nome") or "arquivo"), dados_b)
        except ev.EvidenciaErro as exc:
            return {"kind": "form_upload", "form": "aud", "ok": False, "num": num, "msg": f"{pl.get('nome')}: {exc}"}
        return {"kind": "form_upload", "form": "aud", "ok": True, "num": num, "anexo": info}
    if act == "form_submit":
        dados = pl.get("dados") or {}
        try:
            datetime.strptime(str(dados.get("data_visita")), "%d/%m/%Y")
        except ValueError:
            return {"kind": "form_submit", "ok": False, "msg": "Data da visita inválida."}
        if not str(dados.get("responsavel_visita", "")).strip():
            return {"kind": "form_submit", "ok": False, "msg": "Informe o responsável pela visita."}
        resp, vals = lg.limpar(dados)
        for s in lg.catalogo():
            if s["tipo"] == "quantidade":
                erros = lg.validar_quantidade({"itens": s["itens"]}, vals)
                if erros:
                    return {"kind": "form_submit", "ok": False, "msg": "; ".join(erros)}
        visita, itens, resumo, pend = lg.montar_registros(unidade, dados)
        if pend and not pl.get("forcado"):
            return {"kind": "form_submit", "ok": False, "msg": "Há seções pendentes. Revise ou envie incompleta."}
        ok, modo, msg = be.salvar_auditoria(visita, itens)
        if ok:
            safe(be.apagar_rascunho, unidade)
        ctx.store.log(ctx.mail, f"Enviou aud {visita['Código da Visita']} ({modo})")
        ctx.store.save()
        return {"kind": "form_submit", "ok": ok, "modo": modo, "msg": msg, "codigo": visita["Código da Visita"], "resumo": resumo}
    raise Rejected("Ação desconhecida.")
