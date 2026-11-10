"""Ações dos formulários hospedados no portal. Puro Python, sem Streamlit. Cada formulário tem um adapter em
forms/<pasta>/adapter.py com handle(ctx, act, pl); aqui ficam permissão, escopo de unidade e tradução do cadastro do portal
(Configurações > Unidades e conexões) para o formato que o backend original de cada formulário espera."""
import importlib
from core import perms, drive
from core.api import Rejected
from core.catalog import FORMS, unit_loc

PKG = {"aud": "institucional", "enf": "enfermagem", "sesmt": "sesmt", "v03": "hospital_v03", "upa": "upa"}


class Ctx:
    def __init__(self, store, mail, user):
        self.store, self.mail, self.user = store, mail, user
        names = {x["id"]: x["nome"] for x in store.units()}
        self.allowed = [names[i] for i in perms.allowed_unit_ids(store, user) if i in names]
        self.is_global = user["role"] == "admin" or user.get("scope") == "all"
        self.unit_names = list(names.values())

    def require_unit(self, nome, free=False):
        """Unidade cadastrada: precisa estar no acesso da pessoa. Nome livre (hospital fora do cadastro): só acesso global."""
        if free:
            return   # visita técnica a hospital/UPA em disputa de licitação: não é unidade do cadastro, sem filtro por unidade
        if nome in self.allowed:
            return
        raise Rejected("Unidade fora do seu acesso.")

    def conn(self, form):
        """Dict {unidade_nome|'__consolidado__': {planilha_id, pasta_id}} do cadastro do portal."""
        units = {u["id"]: u["nome"] for u in self.store.data["units"]}
        out = {}
        for k, v in self.store.data["connections"].items():
            f, uid = k.split("|", 1)
            if f == form:
                out["__consolidado__" if uid == "__consolidado__" else units.get(uid, uid)] = {
                    "planilha": drive.extract_id(v.get("planilha", "")) or "", "pasta": drive.extract_id(v.get("pasta", "")) or ""}
        return out


def handle(store, mail, act, pl):
    key = pl.get("form")
    if key not in PKG or not FORMS.get(key, {}).get("ready"):
        raise Rejected("Formulário ainda não está disponível no portal.")
    u = store.user_by_mail(mail)
    if not u or not u.get("active", True) or not perms.can_conduct_visit(store, u):
        raise Rejected("Somente o perfil Responsável pela visita (ou Administrador) registra, edita ou continua visitas. Você pode consultar as visitas em andamento no Início.")
    mod = importlib.import_module(f"forms.{PKG[key]}.adapter")
    return mod.handle(Ctx(store, mail, u), act, pl)


def fill_loc(d):
    """Unidade cadastrada: cidade e UF vêm do cadastro (a interface já preenche, aqui é a garantia no servidor).
    Nome fora do cadastro (hospital/UPA em licitação): mantém o que foi digitado."""
    loc = unit_loc(d.get("hospital"))
    if loc:
        d["cidade"], d["uf"] = loc
    return d


def safe(fn, *a):
    try:
        return fn(*a)
    except Exception:
        return None
