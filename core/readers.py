"""Leitura dos dados que os formulários gravaram, para os painéis do portal (Painel, Visitas, Evolução, Plano de ação).

Fonte: as planilhas cadastradas em Configurações → Unidades e conexões (Google). Sem credenciais do Google (ambiente de
teste), lê os arquivos locais que os formulários gravam no modo de contingência. Tudo é filtrado no servidor pelo acesso
da pessoa. Puro Python (sem Streamlit).

Regras de conversão para o painel (ajustáveis nas constantes abaixo):
  Institucional : Conforme = C · Não Conforme = NC · Não se Aplica = NA (seções de quantidade não pontuam)
  Enfermagem/Hospital: OK = C · Parcial = PARCIAL_COMO · Não = NC · N/A = NA · Não preenchido = fora da conta
  UPA/PAM       : levantamento sem conformidade → entra em Visitas/Histórico, sem pontuação
"""
import os
import time
from datetime import datetime

from core import drive, settings
from core.catalog import FORMS
from core.forms_api import Ctx

PARCIAL_COMO = "NC"      # Parcial conta como não conforme (entra no plano de ação). Mude para "NA" para ignorar.
TTL = 180                # segundos de cache por planilha (a cota do Google é de ~60 leituras/min)

_CACHE = {}


def _cached(key, fn):
    t = time.time()
    hit = _CACHE.get(key)
    if hit and t - hit[0] < TTL:
        return hit[1]
    try:
        val = fn()
    except Exception:
        if hit:                         # o Google falhou agora: mostra o último dado bom em vez de esvaziar o painel
            return hit[1]
        raise
    _CACHE[key] = (t, val)
    return val


def limpar_cache():
    _CACHE.clear()


# ---------------------------------------------------------------- catálogo por formulário
def _catalogo(form):
    """[(nome do grupo, [(num, texto), ...])] só com o que pontua/aparece nos painéis."""
    if form == "aud":
        from forms.institucional import logic
        return [(s["nome"], [(i["num"], i["texto"]) for i in s["itens"]]) for s in logic.catalogo() if s["tipo"] == "checklist"]
    pkg = {"enf": "enfermagem", "v03": "hospital_v03", "upa": "upa"}[form]
    import importlib
    logic = importlib.import_module(f"forms.{pkg}.logic")
    return [(g["nome"], [(i["num"], i["texto"]) for i in g["itens"]]) for g in logic.catalogo()]


def grupos(form):
    """Formato do protótipo: [[nome do grupo, item1, item2, ...], ...]"""
    return [[n] + [t for _, t in its] for n, its in _catalogo(form)]


# ---------------------------------------------------------------- fontes
def _arquivo_local(form):
    import importlib
    pkg = {"aud": "institucional", "enf": "enfermagem", "v03": "hospital_v03", "upa": "upa"}[form]
    be = importlib.import_module(f"forms.{pkg}.sheets_backend")
    if form == "aud":
        return os.path.join(be.LOCAL_DIR, "Auditoria_Consolidado.xlsx")
    return be.ARQUIVO_LOCAL


def _ler_local(form):
    import pandas as pd
    p = _arquivo_local(form)
    if not os.path.exists(p):
        return []
    tabs = FORMS[form]["tabs"]
    vis = pd.read_excel(p, sheet_name=tabs["visitas"], dtype=str).fillna("")
    try:
        itens = pd.read_excel(p, sheet_name=tabs["itens"], dtype=str).fillna("")
    except ValueError:
        itens = pd.DataFrame()
    return [(vis, itens)]


def _df(valores, form=None, tab=""):
    """Tabela a partir de get_all_values (posicional). Planilhas antigas do Institucional têm 'Município' no cabeçalho de
    Visitas, mas as linhas nunca tiveram essa coluna: remove-a do cabeçalho para os valores caírem nas colunas certas."""
    import pandas as pd
    if not valores:
        return pd.DataFrame()
    cab = [str(c).strip() for c in valores[0]]
    if form == "aud" and tab == "Visitas" and "Município" in cab:
        cab.remove("Município")
    linhas = []
    for r in valores[1:]:
        r = list(r) + [""] * (len(cab) - len(r))
        linhas.append(r[:len(cab)])
    return pd.DataFrame(linhas, columns=cab).astype(str)


def _ler_google(form, ref):
    import pandas as pd
    tabs = FORMS[form]["tabs"]

    def aba(planilha, nome):
        try:
            return _df(planilha.worksheet(nome).get_all_values(), form, nome)
        except Exception as e:
            if e.__class__.__name__ == "WorksheetNotFound":
                return pd.DataFrame()       # formulário ainda não gravou nenhuma visita: vazio, não é erro
            raise

    def go():
        sid = drive.extract_id(ref)
        try:        # uma única chamada traz as duas abas (antes eram ~5 leituras por planilha)
            r = drive.client().http_client.values_batch_get(sid, ["'%s'" % tabs["visitas"], "'%s'" % tabs["itens"]])
            vr = r.get("valueRanges", [])
            return (_df(vr[0].get("values", []), form, tabs["visitas"]), _df(vr[1].get("values", []), form, tabs["itens"]))
        except Exception as e:
            if getattr(getattr(e, "response", None), "status_code", 0) != 400:
                raise                   # 429/403/rede: não esconde o problema
        pl = drive.open_spreadsheet(ref)    # aba inexistente (400): caminho antigo, que trata "sem aba" como vazio
        return aba(pl, tabs["visitas"]), aba(pl, tabs["itens"])
    return _cached((form, ref), go)


def _fontes(store, form, problems):
    if not settings.google_configured():
        return _ler_local(form)
    out = []
    if form == "aud":
        refs = []
        for u in store.units(only_active=False):
            r = drive.extract_id(store.conn("aud", u["id"]).get("planilha", ""))
            if r:
                refs.append((u["nome"], r))
    else:
        r = drive.extract_id(store.conn(form, "__consolidado__").get("planilha", ""))
        refs = [("", r)] if r else []
    for nome, ref in refs:
        try:
            out.append(_ler_google(form, ref))
        except Exception as e:
            problems.append({"form": form, "onde": nome or "planilha única", "erro": str(e)[:120]})
    return out


# ---------------------------------------------------------------- conversão
def _data(txt):
    txt = str(txt or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(txt[:19] if "%H" in fmt else txt[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _estado(form, bruto):
    b = str(bruto or "").strip()
    if form == "aud":
        return {"Conforme": "C", "Não Conforme": "NC", "Não se Aplica": "NA"}.get(b)
    return {"OK": "C", "Parcial": PARCIAL_COMO, "Não": "NC", "N/A": "NA"}.get(b)


COLS = {  # coluna da unidade, do responsável e do nº do item/estado em cada formulário
    "aud": ("Unidade", "Responsável pela Visita", "Nº do Item", "Resposta"),
    "enf": ("Hospital", "Responsável pela Visita", "Nº do Item", "Situação"),
    "v03": ("Hospital", "Responsável pela Visita", "Nº do Item", "Situação"),
    "upa": ("Unidade", "Visitantes", "ID", None),
}


def _visitas_de(form, vis, itens, cat):
    ucol, rcol, ncol, scol = COLS[form]
    out = []
    if vis is None or vis.empty or "Código da Visita" not in vis:
        return out
    por_cod = {}
    if scol and not itens.empty and ncol in itens and scol in itens:
        for cod, grp in itens.groupby("Código da Visita"):
            m = {}
            for _, r in grp.iterrows():
                try:
                    n = int(float(r[ncol]))
                except (TypeError, ValueError):
                    continue
                m[n] = (_estado(form, r[scol]), r.get("Qtde de Anexos", "0"))
            por_cod[cod] = m
    for _, v in vis.iterrows():
        cod = str(v["Código da Visita"]).strip()
        d = _data(v.get("Data da Visita"))
        if not cod or not d:
            continue
        resp = por_cod.get(cod, {})
        its = []
        if scol:
            for gi, (gn, itm) in enumerate(cat):
                for n, nome in itm:
                    s, ev = resp.get(n, (None, "0"))
                    try:
                        ev = int(float(ev or 0))
                    except ValueError:
                        ev = 0
                    its.append({"g": gi, "gn": gn, "name": nome, "s": s or "NA", "ev": ev})
        out.append({"id": cod, "mod": form, "unit": str(v.get(ucol, "")).strip(), "date": d,
                    "resp": str(v.get(rcol, "")).strip(), "items": its})
    return out


def load(store, mail):
    """{'visits': [...], 'groups': {form: [[grupo, itens...]]}, 'problems': [...]} já filtrado pelo acesso de `mail`."""
    user = store.user_by_mail(mail)
    if not user or not user.get("active", True):
        return {"visits": [], "groups": {}, "problems": []}
    ctx = Ctx(store, mail, user)
    nomes = {u["nome"] for u in store.units(only_active=False)}
    problems, visits = [], []

    def _um(form):                      # cada formulário lê suas próprias planilhas; roda em paralelo
        prob, out = [], []
        cat = _catalogo(form)
        for vis, itens in _fontes(store, form, prob):
            out += _visitas_de(form, vis, itens, cat)
        return prob, out

    prontos = [f for f in FORMS if FORMS[f].get("ready")]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, len(prontos))) as ex:
        for prob, out in ex.map(_um, prontos):   # ex.map preserva a ordem dos formulários
            problems += prob
            visits += out
    vistos, final = set(), []
    for v in visits:
        k = (v["mod"], v["id"])
        if k in vistos:
            continue
        if FORMS[v["mod"]].get("free"):          # hospital/UPA em licitação: sem cadastro, só perfis globais
            if not ctx.is_global:
                continue
        elif v["unit"] not in nomes or (not ctx.is_global and v["unit"] not in ctx.allowed):
            continue
        vistos.add(k)
        final.append(v)
    final.sort(key=lambda x: x["date"])
    return {"visits": final, "groups": {f: grupos(f) for f in FORMS if FORMS[f].get("ready")}, "problems": problems}
