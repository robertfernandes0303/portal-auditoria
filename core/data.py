"""Leitura dos dados gravados pelos formulários (abas de visitas) via conexões cadastradas."""
import pandas as pd
import streamlit as st
from core import drive, settings
from core.catalog import FORMS


@st.cache_data(ttl=120, show_spinner=False)
def _read(ref, tab):
    return drive.read_tab(ref, tab)


def load_visits(store, allowed_unit_ids):
    """DataFrame normalizado: form, unidade_id, unidade, data, pct, codigo. Só o que tem dado (sem conexão/aba vazia = ausente)."""
    frames, problems = [], []
    if not settings.google_configured():
        return pd.DataFrame(columns=["form", "unidade_id", "unidade", "data", "pct", "codigo"]), problems
    for fkey, f in FORMS.items():
        for u in store.units():
            if u["id"] not in allowed_unit_ids:
                continue
            ref = store.conn(fkey, u["id"]).get("planilha")
            if not ref:
                continue
            try:
                df = _read(ref, f["tabs"]["visitas"])
            except Exception as e:
                problems.append((fkey, u["nome"], str(e)[:80]))
                continue
            if df.empty:
                continue
            out = pd.DataFrame({
                "form": fkey, "unidade_id": u["id"], "unidade": u["nome"],
                "data": pd.to_datetime(df.get(f["date_col"]), errors="coerce"),
                "codigo": df.get("Código da Visita"),
            })
            if f["pct_col"] and f["pct_col"] in df:
                p = pd.to_numeric(df[f["pct_col"]].astype(str).str.replace("%", "").str.replace(",", "."), errors="coerce")
                out["pct"] = p.where(p <= 1, p / 100)
            else:
                out["pct"] = None
            frames.append(out)
    if not frames:
        return pd.DataFrame(columns=["form", "unidade_id", "unidade", "data", "pct", "codigo"]), problems
    return pd.concat(frames, ignore_index=True), problems
