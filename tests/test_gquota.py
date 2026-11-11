import pytest
from core import gquota


def test_janela_deslizante_espera_quando_cheia(monkeypatch):
    gquota._marcas.clear()
    t = {"v": 100.0}; dormiu = []
    monkeypatch.setattr(gquota, "LIMITE", 3)

    def dormir(s):
        dormiu.append(s); t["v"] += s
    for _ in range(3):
        assert gquota.aguardar_vaga(lambda: t["v"], dormir) == 0
    assert gquota.aguardar_vaga(lambda: t["v"], dormir) > 0     # a 4ª espera a janela abrir
    assert dormiu and dormiu[0] <= gquota.JANELA + 0.1
    gquota._marcas.clear()


def test_429_repete_e_depois_funciona(monkeypatch):
    from gspread.exceptions import APIError
    gquota._marcas.clear()
    class R:  # resposta falsa do Google
        status_code = 429
        text = '{"error":{"code":429,"message":"quota","status":"RESOURCE_EXHAUSTED"}}'
        def json(self): return {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
    n = {"c": 0}
    def fn():
        n["c"] += 1
        if n["c"] < 3:
            raise APIError(R())
        return "ok"
    esperas = []
    assert gquota._com_retentativa(fn, dormir=esperas.append) == "ok"
    assert n["c"] == 3 and len(esperas) == 2


def test_erro_diferente_de_429_nao_repete():
    from gspread.exceptions import APIError
    gquota._marcas.clear()
    class R:
        status_code = 403
        text = '{"error":{"code":403,"message":"no","status":"PERMISSION_DENIED"}}'
        def json(self): return {"error": {"code": 403, "message": "no", "status": "PERMISSION_DENIED"}}
    n = {"c": 0}
    def fn():
        n["c"] += 1; raise APIError(R())
    with pytest.raises(APIError):
        gquota._com_retentativa(fn, dormir=lambda s: None)
    assert n["c"] == 1


def test_leitura_em_lote_uma_chamada_por_planilha(monkeypatch):
    from core import readers, drive
    readers.limpar_cache()
    chamadas = []

    class H:
        def values_batch_get(self, sid, ranges):
            chamadas.append((sid, ranges))
            return {"valueRanges": [{"values": [["Código da Visita", "Unidade"], ["A1", "Juína"]]},
                                    {"values": [["Código da Visita", "Resposta"], ["A1", "Conforme"]]}]}

    class C:
        http_client = H()
    monkeypatch.setattr(drive, "client", lambda: C())
    v, i = readers._ler_google("aud", "1k6c7s33yJwOdw43v671D07jeJpSPiNwlO9aTxSF1678")
    assert len(chamadas) == 1 and len(v) == 1 and v.iloc[0]["Unidade"] == "Juína" and len(i) == 1
    readers._ler_google("aud", "1k6c7s33yJwOdw43v671D07jeJpSPiNwlO9aTxSF1678")   # cache: sem nova chamada
    assert len(chamadas) == 1


def test_google_falha_mas_reaproveita_ultimo_dado(monkeypatch):
    from core import readers
    readers.limpar_cache()
    readers._CACHE[("x", "y")] = (0, "antigo")       # expirado
    def falha(): raise RuntimeError("429")
    assert readers._cached(("x", "y"), falha) == "antigo"
    with pytest.raises(RuntimeError):
        readers._cached(("novo", "z"), falha)
    readers.limpar_cache()


def test_fundo_cede_vaga_a_interacao(monkeypatch):
    import threading
    monkeypatch.setattr(gquota, "LIMITE", 4)
    monkeypatch.setattr(gquota, "LIMITE_FUNDO", 2)
    gquota._marcas.clear()
    t = {"v": 0.0}
    esperas = {}

    def fundo():
        gquota.modo_fundo()
        esperas["a"] = gquota.aguardar_vaga(lambda: t["v"], lambda s: t.__setitem__("v", t["v"] + s))
        esperas["b"] = gquota.aguardar_vaga(lambda: t["v"], lambda s: t.__setitem__("v", t["v"] + s))
        esperas["c"] = gquota.aguardar_vaga(lambda: t["v"], lambda s: t.__setitem__("v", t["v"] + s))   # 3ª: fundo só usa 2 vagas

    th = threading.Thread(target=fundo); th.start(); th.join()
    assert esperas["a"] == 0 and esperas["b"] == 0 and esperas["c"] > 0
    gquota._marcas.clear()
    for _ in range(4):                       # interação (thread principal) ainda tem as 4 vagas
        assert gquota.aguardar_vaga(lambda: 0.0, lambda s: None) == 0
