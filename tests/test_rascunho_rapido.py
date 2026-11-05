import json
from forms.institucional import sheets_backend as be


class H:
    def __init__(self, ret=None, exc=None): self.ret, self.exc, self.n = ret, exc, 0
    def values_batch_get(self, sid, ranges):
        self.n += 1
        if self.exc: raise self.exc
        return self.ret


class Cli:
    def __init__(self, h): self.http_client = h


class Erro(Exception):
    def __init__(self, c): self.response = type("R", (), {"status_code": c})()


def _prep(monkeypatch, h):
    monkeypatch.setattr(be, "_carregar_mapeamento", lambda: {"unidades": {"Juína": "X" * 20}})
    monkeypatch.setattr(be, "_credenciais_disponiveis", lambda m: True)
    monkeypatch.setattr(be, "_obter_cliente_gspread", lambda: Cli(h))


def test_uma_leitura_acha_rascunho(monkeypatch):
    dados = {"codigo_visita": "AUD-1"}
    h = H({"valueRanges": [{"values": [["Unidade", "Atualizado em", "Dados"], ["Outra", "x", "{}"], ["Juína", "05/11/2026 10:00:00", json.dumps(dados)]]}]})
    _prep(monkeypatch, h)
    r = be.carregar_rascunho_rapido("Juína")
    assert r == {"atualizado_em": "05/11/2026 10:00:00", "dados": dados} and h.n == 1


def test_sem_aba_e_sem_rascunho(monkeypatch):
    _prep(monkeypatch, H(exc=Erro(400))); assert be.carregar_rascunho_rapido("Juína") is None
    _prep(monkeypatch, H({"valueRanges": [{"values": [["Unidade", "a", "b"]]}]})); assert be.carregar_rascunho_rapido("Juína") is None


def test_falha_da_api_nao_vira_inexistente(monkeypatch):
    _prep(monkeypatch, H(exc=Erro(429)))
    assert be.carregar_rascunho_rapido("Juína") == be.ERRO_VERIFICACAO_RASCUNHO
