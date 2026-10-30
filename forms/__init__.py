"""Formulários hospedados no portal. Cada formulário migrado expõe `render(ctx)` neste pacote.
Etapa 1: nenhum formulário migrado ainda (ver README: passo a passo). A regra é portar a lógica dos pacotes sem alterar
catálogo, validações, cálculos, rascunho/autosave nem a gravação; só a interface segue o layout do portal."""
import importlib
from core.catalog import FORMS


def get(form_key):
    """Retorna o módulo do formulário se já migrado (forms/<chave>.py com render(ctx)), senão None."""
    if not FORMS.get(form_key, {}).get("ready"):
        return None
    try:
        return importlib.import_module(f"forms.{form_key}")
    except ModuleNotFoundError:
        return None
