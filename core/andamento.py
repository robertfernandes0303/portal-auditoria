"""Visitas em andamento (rascunhos ainda não enviados) de todos os formulários, para a tela Início.
Lê os rascunhos reais (planilha/Drive ou arquivo local) com o mesmo acesso de cada formulário. Puro Python."""
import importlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from core.forms_api import Ctx, PKG
from core.catalog import FORMS

TTL = 120                # lista pronta de cada pessoa
STALE = 86400            # além do TTL, devolve o último resultado na hora e atualiza por trás (nunca deixa a tela esperando)
TTL_UNIT = 120           # leitura de rascunho de cada unidade (todas as pessoas compartilham)
_CACHE = {}
_UNIT = {}               # unidade -> (instante, rascunho)
_LOCK = threading.Lock()
_EMVOO = set()


def limpar_cache():
    _CACHE.clear()
    _UNIT.clear()


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
    ler = getattr(mod.be, "carregar_rascunho_rapido", None) or mod.be.carregar_rascunho

    def _ler(unidade):
        _t = time.perf_counter()
        hit = _UNIT.get(unidade)
        if hit and time.time() - hit[0] < TTL_UNIT:
            return unidade, hit[1]
        try:
            b = ler(unidade)
        except Exception:
            b = mod.be.ERRO_VERIFICACAO_RASCUNHO
        finally:
            PROF.append((unidade[:14], round(time.perf_counter() - _t, 2)))
        if b == mod.be.ERRO_VERIFICACAO_RASCUNHO:       # falha/cota do Google: usa o último valor conhecido
            return unidade, (hit[1] if hit else None)
        _UNIT[unidade] = (time.time(), b)
        return unidade, b

    unidades = list(ctx.unit_names if ctx.is_global else ctx.allowed)
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(unidades)))) as ex:      # em paralelo (antes: uma a uma)
        lidos = list(ex.map(_ler, unidades))
    for unidade, b in lidos:
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


PROF = []                      # [(rótulo, segundos)] da última leitura: aparece em _t.prof para achar lentidão


def listar(store, mail, erros=None):
    user = store.user_by_mail(mail)
    if not user or not user.get("active", True):
        return []
    k = mail.strip().lower()
    hit = _CACHE.get(k)
    agora = time.time()
    if hit and agora - hit[0] < TTL:
        return hit[1]
    if hit and agora - hit[0] < STALE:          # lista antiga: entrega já e atualiza em segundo plano
        with _LOCK:
            novo = k not in _EMVOO
            if novo:
                _EMVOO.add(k)
        if novo:
            def _bg():
                try:
                    from core import gquota
                    gquota.modo_fundo()
                    _calcular(store, mail, user, k, None)
                except Exception:
                    pass
                finally:
                    with _LOCK:
                        _EMVOO.discard(k)
            threading.Thread(target=_bg, daemon=True).start()
        return hit[1]
    return _calcular(store, mail, user, k, erros)


def _calcular(store, mail, user, k, erros):
    ctx = Ctx(store, mail, user)
    out = []
    falhou = False
    del PROF[:]
    for key in ("aud", "enf", "sesmt", "v03", "upa"):
        if not FORMS.get(key, {}).get("ready"):
            continue
        _t = time.perf_counter()
        try:
            _aud(ctx, out) if key == "aud" else _vt(ctx, key, out)
        except Exception as e:
            falhou = True
            if erros is not None:
                erros.append(f"{key}: {str(e)[:80]}")
            continue
        finally:
            PROF.append((key, round(time.perf_counter() - _t, 2)))
    out.sort(key=lambda x: x["atualizado_em"][6:10] + x["atualizado_em"][3:5] + x["atualizado_em"][:2] + x["atualizado_em"][11:], reverse=True)
    if not falhou:  # nunca guardar em cache um resultado incompleto por falha de leitura
        _CACHE[k] = (time.time(), out)
    return out
