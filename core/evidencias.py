"""Fotos e documentos de evidência de uma visita, para o detalhe da visita no painel.

Os arquivos ficam no Drive em modo PRIVADO (dono + conta de serviço): o link direto não abre para quem usa o portal.
Por isso o servidor baixa o arquivo com a conta de serviço e entrega ao painel, **depois de conferir que a pessoa
pode ver aquela visita** (mesmo filtro de unidade do painel). Só ids que constam nas evidências da própria visita
são aceitos: o painel não consegue pedir um arquivo qualquer do Drive."""
import base64
import io
import os
import re

from core import drive, readers, settings
from core.catalog import FORMS

ABA_EVID = {"enf": "Evidencias", "sesmt": "Evidencias", "v03": "VT_Evidencias", "upa": "UPA_Evidencias"}
_ID = re.compile(r"(?:/d/|[?&]id=)([A-Za-z0-9_-]{15,})")
MAX_PX = 1400            # lado maior da imagem entregue ao painel
MAX_PDF = 6 * 1024 * 1024
MAX_IMG_ORIG = 25 * 1024 * 1024


class Negado(Exception):
    pass


def _visita(store, mail, form, codigo):
    """A visita só é devolvida se a pessoa a enxerga no painel (mesmo filtro do readers.load)."""
    if form not in FORMS or not FORMS[form].get("ready"):
        raise Negado("Formulário inválido.")
    codigo = str(codigo or "").strip()
    for v in readers.load(store, mail).get("visits", []):
        if v["mod"] == form and v["id"] == codigo:
            return v
    raise Negado("Visita não encontrada para o seu perfil.")


def _ref(store, form, unit):
    if form == "aud":
        for u in store.units(only_active=False):
            if u["nome"] == unit:
                return drive.extract_id(store.conn("aud", u["id"]).get("planilha", ""))
        return None
    return drive.extract_id(store.conn(form, "__consolidado__").get("planilha", ""))


def _tabela_google(form, ref, aba):
    def go():
        r = drive.client().http_client.values_get(ref, "'%s'" % aba)
        return r.get("values", [])
    return readers._cached(("ev", form, ref), go)


def _linhas_evid(form, ref):
    """Linhas (dict) da aba de evidências dos formulários de visita técnica."""
    if not settings.google_configured():
        import pandas as pd
        p = readers._arquivo_local(form)
        if not os.path.exists(p):
            return []
        try:
            df = pd.read_excel(p, sheet_name=ABA_EVID[form], dtype=str).fillna("")
        except ValueError:
            return []
        return df.to_dict("records")
    vals = _tabela_google(form, ref, ABA_EVID[form])
    if not vals:
        return []
    cab = [str(c).strip() for c in vals[0]]
    return [dict(zip(cab, list(r) + [""] * (len(cab) - len(r)))) for r in vals[1:]]


def _tipo(nome, tipo):
    t = str(tipo or "").lower()
    ext = os.path.splitext(str(nome or ""))[1].lower()
    if t.startswith("imag") or ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"):
        return "imagem"
    if t == "pdf" or ext == ".pdf":
        return "pdf"
    return "arquivo"


def _de_item_aud(form, ref, codigo, unit):
    """Auditoria Institucional: os links ficam na coluna 'Links dos Anexos' da aba Itens (um ou vários por item)."""
    if not settings.google_configured():
        par = readers._ler_local(form)
        itens = par[0][1] if par else None
    else:
        itens = readers._ler_google(form, ref)[1] if ref else None
    out = []
    if itens is None or itens.empty or "Links dos Anexos" not in itens or "Código da Visita" not in itens:
        return out
    ncol = "Nº do Item" if "Nº do Item" in itens else ("Nº" if "Nº" in itens else None)
    for _, r in itens[itens["Código da Visita"].astype(str).str.strip() == codigo].iterrows():
        try:
            n = int(float(r[ncol])) if ncol else 0
        except (TypeError, ValueError):
            continue
        for i, m in enumerate(_ID.finditer(str(r.get("Links dos Anexos", "")))):
            out.append({"n": n, "id": m.group(1), "nome": "Anexo %d do item %d" % (i + 1, n), "tipo": "imagem"})
    return out


def listar(store, mail, form, codigo):
    """{'ok': True, 'itens': {n: [{id, nome, tipo}]}} — sem baixar nenhum arquivo."""
    v = _visita(store, mail, form, codigo)
    codigo = v["id"]
    ref = _ref(store, form, v["unit"]) if settings.google_configured() else ""
    por_item = {}
    if form == "aud":
        lista = _de_item_aud(form, ref, codigo, v["unit"])
    else:
        lista = []
        for r in _linhas_evid(form, ref):
            if str(r.get("Código da Visita", "")).strip() != codigo:
                continue
            link = str(r.get("Link / Caminho", "") or "")
            m = _ID.search(link)
            fid = m.group(1) if m else ""
            if not fid and not settings.google_configured() and link:
                fid = "local:" + os.path.basename(link)
            if not fid:
                continue
            try:
                n = int(float(r.get("Nº do Item", "")))
            except (TypeError, ValueError):
                continue
            lista.append({"n": n, "id": fid, "nome": str(r.get("Arquivo", "") or "arquivo"), "tipo": _tipo(r.get("Arquivo"), r.get("Tipo")),
                          "_caminho": link})
    for e in lista:
        e.pop("_caminho", None)
        por_item.setdefault(str(e["n"]), []).append({"id": e["id"], "nome": e["nome"], "tipo": e["tipo"]})
    return {"kind": "evid_list", "ok": True, "form": form, "codigo": codigo, "itens": por_item}


def _reduzir(dados):
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(dados))
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail((MAX_PX, MAX_PX))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=72, optimize=True)
    return b.getvalue()


def _baixar_google(fid):
    from core import gquota
    gquota.aplicar()
    s = drive.client().http_client.session
    r = s.get("https://www.googleapis.com/drive/v3/files/%s" % fid, params={"alt": "media", "supportsAllDrives": "true"}, timeout=60)
    if r.status_code != 200:
        raise Negado("O Drive não entregou o arquivo (código %s)." % r.status_code)
    return r.content


def obter(store, mail, form, codigo, fid):
    """Entrega um arquivo da visita (imagem reduzida, ou PDF) em base64. Só aceita ids listados na própria visita."""
    lst = listar(store, mail, form, codigo)
    achado = None
    for itens in lst["itens"].values():
        for e in itens:
            if e["id"] == fid:
                achado = e
    if not achado:
        raise Negado("Arquivo não pertence a esta visita.")
    if fid.startswith("local:"):
        import importlib
        from core.forms_api import PKG
        pasta = os.path.join(importlib.import_module("forms.%s.evidencias" % PKG[form]).LOCAL_EVID_DIR, lst["codigo"])
        pasta = os.path.realpath(pasta)
        p = os.path.realpath(os.path.join(pasta, fid[6:]))
        if not p.startswith(pasta + os.sep) or not os.path.exists(p):
            raise Negado("Arquivo local não encontrado.")
        dados = open(p, "rb").read()
    else:
        dados = _baixar_google(fid)
    if achado["tipo"] == "pdf":
        if len(dados) > MAX_PDF:
            raise Negado("PDF grande demais para exibir aqui (%.1f MB). Peça o arquivo ao responsável pela visita." % (len(dados) / 1048576))
        mime, out = "application/pdf", dados
    else:
        if len(dados) > MAX_IMG_ORIG:
            raise Negado("Imagem grande demais para exibir aqui.")
        try:
            mime, out = "image/jpeg", _reduzir(dados)
        except Exception:
            raise Negado("Não foi possível abrir este arquivo como imagem.")
    return {"kind": "evid_get", "ok": True, "fid": fid, "nome": achado["nome"], "tipo": achado["tipo"], "mime": mime,
            "b64": base64.b64encode(out).decode("ascii")}
