"""Cidade/UF das unidades cadastradas: a tabela do servidor e a da interface precisam ser iguais."""
import re
from pathlib import Path
from core.catalog import UNIT_LOC, DEFAULT_UNITS, unit_loc
from core.forms_api import fill_loc


def test_toda_unidade_padrao_tem_cidade_e_uf():
    assert set(UNIT_LOC) == set(DEFAULT_UNITS)
    assert all(c and len(uf) == 2 for c, uf in UNIT_LOC.values())


def test_interface_igual_ao_servidor():
    html = (Path(__file__).resolve().parent.parent / "portal_ui" / "index.html").read_text(encoding="utf-8")
    bloco = re.search(r"var UNIT_LOC = \{(.*?)\};\nfunction unitLoc", html, re.S).group(1)
    js = {k: tuple(v) for k, v in re.findall(r"'([^']+)':\['([^']+)','([A-Z]{2})'\]", bloco) and
          [(k, (c, u)) for k, c, u in re.findall(r"'([^']+)':\['([^']+)','([A-Z]{2})'\]", bloco)]}
    assert js == UNIT_LOC


def test_fill_loc_preenche_unidade_cadastrada_e_respeita_nome_livre():
    d = fill_loc({"hospital": " juína ", "cidade": "errada", "uf": "SP"})
    assert (d["cidade"], d["uf"]) == ("Juína", "MT")
    d = fill_loc({"hospital": "Hospital Novo", "cidade": "Cuiabá", "uf": "MT"})
    assert (d["cidade"], d["uf"]) == ("Cuiabá", "MT")
    assert unit_loc("Sumaré - Matão") == ("Sumaré", "SP")
