"""Fotos de evidência no detalhe da visita: acesso por escopo, só ids da própria visita, redução e limites."""
import base64
import io

import pytest

from core import evidencias


class _Fake:
    pass


def _visitas(monkeypatch, visitas):
    monkeypatch.setattr(evidencias.readers, "load", lambda store, mail: {"visits": visitas})


def _png(w=3000, h=2000):
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (w, h), (200, 30, 30)).save(b, "PNG")
    return b.getvalue()


def test_visita_fora_do_escopo_e_negada(monkeypatch):
    _visitas(monkeypatch, [{"mod": "enf", "id": "ENF-1", "unit": "A"}])
    with pytest.raises(evidencias.Negado):
        evidencias.listar(None, "x@y", "enf", "ENF-OUTRA")
    with pytest.raises(evidencias.Negado):
        evidencias.listar(None, "x@y", "inexistente", "ENF-1")


def test_lista_agrupa_por_item(monkeypatch):
    _visitas(monkeypatch, [{"mod": "enf", "id": "ENF-1", "unit": "A"}])
    monkeypatch.setattr(evidencias.settings, "google_configured", lambda: True)
    monkeypatch.setattr(evidencias, "_ref", lambda s, f, u: "REF")
    monkeypatch.setattr(evidencias, "_linhas_evid", lambda f, r: [
        {"Código da Visita": "ENF-1", "Nº do Item": "3", "Arquivo": "a.jpg", "Tipo": "imagem",
         "Link / Caminho": "https://drive.google.com/file/d/ABCDEFGHIJKLMNOPQ/view"},
        {"Código da Visita": "ENF-1", "Nº do Item": "3", "Arquivo": "b.pdf", "Tipo": "",
         "Link / Caminho": "https://drive.google.com/open?id=ZZZZZZZZZZZZZZZZZZ"},
        {"Código da Visita": "ENF-2", "Nº do Item": "3", "Arquivo": "c.jpg", "Tipo": "imagem",
         "Link / Caminho": "https://drive.google.com/file/d/OUTRAVISITAAAAAAAAA/view"},
        {"Código da Visita": "ENF-1", "Nº do Item": "x", "Arquivo": "d.jpg", "Tipo": "imagem", "Link / Caminho": "/d/QQQQQQQQQQQQQQQQQQ"}])
    r = evidencias.listar(None, "x@y", "enf", "ENF-1")
    assert list(r["itens"]) == ["3"]
    assert [e["tipo"] for e in r["itens"]["3"]] == ["imagem", "pdf"]
    assert r["itens"]["3"][1]["id"] == "ZZZZZZZZZZZZZZZZZZ"


def test_obter_so_aceita_id_da_visita_e_reduz_imagem(monkeypatch):
    _visitas(monkeypatch, [{"mod": "enf", "id": "ENF-1", "unit": "A"}])
    monkeypatch.setattr(evidencias.settings, "google_configured", lambda: True)
    monkeypatch.setattr(evidencias, "_ref", lambda s, f, u: "REF")
    monkeypatch.setattr(evidencias, "_linhas_evid", lambda f, r: [
        {"Código da Visita": "ENF-1", "Nº do Item": "1", "Arquivo": "a.png", "Tipo": "imagem",
         "Link / Caminho": "https://drive.google.com/file/d/ABCDEFGHIJKLMNOPQ/view"}])
    pedidos = []
    monkeypatch.setattr(evidencias, "_baixar_google", lambda fid: pedidos.append(fid) or _png())
    with pytest.raises(evidencias.Negado):
        evidencias.obter(None, "x@y", "enf", "ENF-1", "ARQUIVOALHEIOQUALQUER")
    assert pedidos == []                    # id fora da visita nunca chega ao Drive
    r = evidencias.obter(None, "x@y", "enf", "ENF-1", "ABCDEFGHIJKLMNOPQ")
    from PIL import Image
    im = Image.open(io.BytesIO(base64.b64decode(r["b64"])))
    assert r["mime"] == "image/jpeg" and max(im.size) <= evidencias.MAX_PX


def test_pdf_grande_demais_e_recusado(monkeypatch):
    _visitas(monkeypatch, [{"mod": "enf", "id": "ENF-1", "unit": "A"}])
    monkeypatch.setattr(evidencias.settings, "google_configured", lambda: True)
    monkeypatch.setattr(evidencias, "_ref", lambda s, f, u: "REF")
    monkeypatch.setattr(evidencias, "_linhas_evid", lambda f, r: [
        {"Código da Visita": "ENF-1", "Nº do Item": "1", "Arquivo": "a.pdf", "Tipo": "pdf",
         "Link / Caminho": "https://drive.google.com/file/d/ABCDEFGHIJKLMNOPQ/view"}])
    monkeypatch.setattr(evidencias, "_baixar_google", lambda fid: b"0" * (evidencias.MAX_PDF + 1))
    with pytest.raises(evidencias.Negado):
        evidencias.obter(None, "x@y", "enf", "ENF-1", "ABCDEFGHIJKLMNOPQ")
