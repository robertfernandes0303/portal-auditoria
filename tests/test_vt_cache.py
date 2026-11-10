"""Velocidade da 1a abertura das visitas técnicas: planilha/aba em memória e lista de rascunhos com TTL curto.
Usa uma planilha Google simulada que conta as chamadas (sem rede)."""
import importlib
import json
import pytest

FORMS = ["forms.enfermagem", "forms.hospital_v03", "forms.upa"]


class FakeAba:
    def __init__(self, cont):
        self.cont, self.rows = cont, [["Código", "Hospital", "x", "Resp", "Atualizado", "dados"]]

    def get_all_values(self):
        self.cont["get_all_values"] += 1
        return [list(r) for r in self.rows]


class FakePlanilha:
    def __init__(self, cont, aba):
        self.cont, self.aba = cont, aba

    def worksheet(self, titulo):
        self.cont["worksheet"] += 1
        return self.aba


class FakeCliente:
    def __init__(self, cont, aba):
        self.cont, self.aba = cont, aba

    def open_by_key(self, key):
        self.cont["open_by_key"] += 1
        return FakePlanilha(self.cont, self.aba)


@pytest.fixture(params=FORMS)
def be(request, monkeypatch):
    be = importlib.import_module(request.param + ".sheets_backend")
    cont = {"open_by_key": 0, "worksheet": 0, "get_all_values": 0}
    aba = FakeAba(cont)
    cliente = FakeCliente(cont, aba)
    be._invalidar_tudo()
    monkeypatch.setattr(be, "_tem_credencial", lambda: True)
    monkeypatch.setattr(be, "_obter_cliente", lambda: cliente)
    monkeypatch.setattr(be, "_carregar_mapeamento", lambda: {"planilha_id": "PLANILHA_FAKE_123456", "pasta_evidencias": ""})
    be.cont, be.aba_fake = cont, aba
    yield be
    be._invalidar_tudo()


def test_tres_passos_seguidos_leem_a_planilha_uma_vez(be):
    be.listar_rascunhos_abertos()          # form_open
    be.listar_rascunhos_hospital("X")      # form_hospital
    be.carregar_rascunho_codigo("ABC")     # form_load
    assert be.cont == {"open_by_key": 1, "worksheet": 1, "get_all_values": 1}


def test_gravacao_invalida_a_lista(be):
    be.listar_rascunhos_abertos()
    be._invalidar_lista()                   # o que _gravar_rascunho_google faz ao terminar
    be.listar_rascunhos_abertos()
    assert be.cont["get_all_values"] == 2 and be.cont["open_by_key"] == 1


def test_lista_expira_pelo_ttl(be, monkeypatch):
    be.listar_rascunhos_abertos()
    be._CACHE_LISTA["t"] -= be.TTL_LISTA + 1
    be.listar_rascunhos_abertos()
    assert be.cont["get_all_values"] == 2


def test_erro_de_leitura_limpa_tudo_e_avisa(be):
    be.aba_fake.get_all_values = lambda: (_ for _ in ()).throw(RuntimeError("falha"))
    assert be.listar_rascunhos_abertos() == be.ERRO_VERIFICACAO_RASCUNHO
    assert be._CACHE_PLAN["obj"] is None and be._CACHE_LISTA["aba"] is None


def test_aquecer_prepara_tudo_e_nao_lanca(be):
    be.aquecer()
    be.listar_rascunhos_abertos()
    assert be.cont == {"open_by_key": 1, "worksheet": 1, "get_all_values": 1}


def test_rascunho_novo_aparece_apos_invalidar(be):
    assert be.listar_rascunhos_abertos() == []
    be.aba_fake.rows.append(["COD1", "Juína", "", "Ana", "10/11/2026 10:00:00", json.dumps({"hospital": "Juína"})])
    be._invalidar_lista()
    r = be.listar_rascunhos_abertos()
    assert [x["codigo"] for x in r] == ["COD1"]
