"""Conexão com o Google Drive/Sheets tratada como uma 'API' cadastrável: o administrador informa a URL (ou só o
trecho/ID) da planilha ou pasta de cada unidade e o portal resolve e acessa. Sem credenciais, funciona em modo local."""
import re
import streamlit as st
from core import settings

_ID_PATTERNS = [r"/spreadsheets/d/([A-Za-z0-9_-]{15,})", r"/folders/([A-Za-z0-9_-]{15,})", r"/d/([A-Za-z0-9_-]{15,})",
                r"[?&]id=([A-Za-z0-9_-]{15,})"]


def extract_id(ref):
    """Aceita URL completa, trecho da URL ou o ID puro. Retorna o ID ou None."""
    if not ref:
        return None
    ref = ref.strip()
    for p in _ID_PATTERNS:
        m = re.search(p, ref)
        if m:
            return m.group(1)
    return ref if re.fullmatch(r"[A-Za-z0-9_-]{15,}", ref) else None


@st.cache_resource(show_spinner=False)
def _client():
    import gspread
    from core import gquota
    gquota.aplicar()
    info = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(info)


def client():
    return _client()


def open_spreadsheet(ref):
    sid = extract_id(ref)
    if not sid:
        raise ValueError("Endereço da planilha inválido.")
    return _client().open_by_key(sid)


def service_account_email():
    try:
        return st.secrets["gcp_service_account"].get("client_email", "")
    except Exception:
        return ""


def test_connection(ref, kind="planilha"):
    """Retorna (ok, mensagem). Para planilha, lista as abas; para pasta, só valida o ID."""
    sid = extract_id(ref)
    if not ref:
        return None, "Não cadastrado"
    if not sid:
        return False, "Endereço inválido (use a URL ou o ID)"
    if not settings.google_configured():
        return None, "ID reconhecido · credenciais do Google não configuradas (modo local)"
    try:
        if kind == "planilha":
            sh = _client().open_by_key(sid)
            tabs = ", ".join(ws.title for ws in sh.worksheets())
            return True, f"Conectado · abas: {tabs}"
        _client().http_client  # valida credencial; pasta é verificada na primeira gravação
        return True, "ID da pasta reconhecido"
    except Exception as e:
        msg = str(e)[:140]
        return False, f"Falha ao acessar: {msg}. Compartilhe com {service_account_email() or 'a conta de serviço'} (Editor)."


def read_tab(ref, tab):
    """Lê uma aba como DataFrame. Levanta exceção se não houver acesso."""
    import pandas as pd
    ws = open_spreadsheet(ref).worksheet(tab)
    rows = ws.get_all_records()
    return pd.DataFrame(rows)


_DISC = {"t": 0, "v": None}


def discover(force=False):
    """Planilhas e pastas que a conta de serviço enxerga (ou seja, as que foram compartilhadas com ela).
    Alimenta as listas de escolha em Configurações → conexões. Retorna {'planilhas': [...], 'pastas': [...]}."""
    import time
    if not force and _DISC["v"] and time.time() - _DISC["t"] < 60:
        return _DISC["v"]
    cli = _client()
    out = {"planilhas": [], "pastas": []}
    for kind, mime, dest in (("s", "application/vnd.google-apps.spreadsheet", "planilhas"), ("p", "application/vnd.google-apps.folder", "pastas")):
        tok = None
        for _ in range(5):
            params = {"q": f"mimeType='{mime}' and trashed=false", "fields": "nextPageToken,files(id,name)", "pageSize": 200,
                      "supportsAllDrives": "true", "includeItemsFromAllDrives": "true", "orderBy": "name"}
            if tok:
                params["pageToken"] = tok
            r = cli.http_client.request("get", "https://www.googleapis.com/drive/v3/files", params=params).json()
            out[dest] += [{"id": f["id"], "name": f["name"]} for f in r.get("files", [])]
            tok = r.get("nextPageToken")
            if not tok:
                break
    _DISC.update(t=time.time(), v=out)
    return out


def create_spreadsheet(title, folder_ref=""):
    """Cria uma planilha vazia (nas abas, cada formulário cria o que precisa ao gravar). Retorna (id, url)."""
    fid = extract_id(folder_ref) if folder_ref else None
    sh = _client().create(title, folder_id=fid) if fid else _client().create(title)
    _DISC["v"] = None
    return sh.id, f"https://docs.google.com/spreadsheets/d/{sh.id}/edit"
