"""Permissões: telas por perfil (+ ajustes pessoais) e unidades visíveis. Tudo calculado no servidor."""
from core.catalog import SCREENS


def effective_screens(store, user):
    prof = store.data["profiles"].get(user["role"])
    base = set(prof["screens"]) if prof else set()
    for s, _ in SCREENS:
        o = (user.get("ov") or {}).get(s)
        if o is True:
            base.add(s)
        elif o is False:
            base.discard(s)
    if user["role"] == "admin":
        base = {s for s, _ in SCREENS}
    return base


def can(store, user, screen):
    return bool(user) and user.get("active", True) and screen in effective_screens(store, user)


def allowed_unit_ids(store, user):
    """None = todas as unidades ativas; senão lista de ids."""
    ids = [u["id"] for u in store.units()]
    if not user:
        return []
    if user["role"] == "admin" or user.get("scope") == "all":
        return ids
    return [i for i in ids if i in set(user.get("units") or [])]


# Perfis que registram e continuam visitas (incluindo as em aberto). Gestor e Integrante da unidade só consultam as visitas em andamento.
CONDUZ_VISITA = ("admin", "resp")


def can_open_new_visit(store, user):
    return can(store, user, "nova")


def can_conduct_visit(store, user):
    """Registrar, editar, continuar e enviar visitas: só Responsável pela visita (e Administrador/CDQ), com a tela Nova visita."""
    return can(store, user, "nova") and user["role"] in CONDUZ_VISITA
