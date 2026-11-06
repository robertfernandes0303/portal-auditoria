"""Protege a cota do Google Sheets (≈60 leituras/min por conta de serviço): todas as chamadas do gspread passam por uma
janela deslizante compartilhada e, se o Google ainda responder 429, esperam e repetem. Aplica-se a todos os formulários."""
import threading
import time
from collections import deque

LIMITE = 45          # chamadas por janela (margem sob o limite de 60/min)
JANELA = 60.0        # segundos
TENTATIVAS = 4
ESPERA_429 = 8.0     # segundos (cresce a cada tentativa)

_lock = threading.Lock()
_marcas = deque()
_aplicado = False
_stats = {"calls": 0, "wait": 0.0, "r429": 0, "http": 0.0}


def snapshot():
    with _lock:
        return dict(_stats)


def aguardar_vaga(agora=time.monotonic, dormir=time.sleep):
    """Bloqueia até haver vaga na janela; devolve quantos segundos esperou."""
    esperou = 0.0
    while True:
        with _lock:
            t = agora()
            while _marcas and t - _marcas[0] >= JANELA:
                _marcas.popleft()
            if len(_marcas) < LIMITE:
                _marcas.append(t)
                _stats["calls"] += 1
                _stats["wait"] += esperou
                return esperou
            falta = JANELA - (t - _marcas[0]) + 0.05
        dormir(falta)
        esperou += falta


def _com_retentativa(fn, dormir=time.sleep):
    from gspread.exceptions import APIError
    for i in range(TENTATIVAS):
        aguardar_vaga()
        try:
            return fn()
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", 0)
            if code == 429 and i < TENTATIVAS - 1:
                with _lock:
                    _stats["r429"] += 1
                dormir(ESPERA_429 * (i + 1))
                continue
            raise


def aplicar():
    """Instala o limitador no cliente HTTP do gspread (uma vez por processo)."""
    global _aplicado
    if _aplicado:
        return
    from gspread.http_client import HTTPClient
    orig = HTTPClient.request

    def request(self, *a, **k):
        t0 = time.perf_counter()
        try:
            return _com_retentativa(lambda: orig(self, *a, **k))
        finally:
            with _lock:
                _stats["http"] += time.perf_counter() - t0
    HTTPClient.request = request
    _aplicado = True
