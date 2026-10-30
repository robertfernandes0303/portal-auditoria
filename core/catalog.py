"""Catálogo fixo: telas, perfis padrão, unidades iniciais e formulários do portal."""

SCREENS = [
    ("inicio", "Início"), ("nova", "Nova visita"), ("painel", "Painel de indicadores"),
    ("evol", "Evolução, comparativo e histórico"), ("visitas", "Visitas"), ("plano", "Plano de ação"),
    ("conta", "Minha conta"), ("perm", "Permissionamento"), ("conn", "Unidades e conexões"),
]
SCREEN_LABEL = dict(SCREENS)

DEFAULT_PROFILES = {
    "admin": {"label": "Administrador / CDQ", "builtin": True, "scope": "all",
              "desc": "Administração do portal e visão global de todas as unidades.",
              "screens": [s for s, _ in SCREENS]},
    "resp": {"label": "Responsável pela visita", "builtin": True, "scope": "all",
             "desc": "Visão global: todas as unidades, rankings, comparações e indicadores.",
             "screens": ["inicio", "nova", "painel", "evol", "visitas", "plano", "conta"]},
    "gestor": {"label": "Gestor da unidade", "builtin": True, "scope": "sel",
               "desc": "Visão da sua unidade: indicadores, visitas e plano de ação.",
               "screens": ["inicio", "painel", "evol", "visitas", "plano", "conta"]},
    "membro": {"label": "Integrante da unidade", "builtin": True, "scope": "sel",
               "desc": "Consulta dos indicadores e visitas da sua unidade.",
               "screens": ["inicio", "painel", "evol", "visitas", "plano", "conta"]},
}

# 14 unidades da Auditoria Institucional (a lista pode ser alterada em Configurações > Unidades e conexões)
DEFAULT_UNITS = [
    "Aripuanã", "Campo Novo do Parecis - CAPS", "Campo Verde", "Guarantã do Norte", "Juína", "Juscimeira",
    "Pedro de Toledo", "Pontes e Lacerda", "São José do Rio Claro - Hospital", "São José do Rio Claro - PAM",
    "São Lourenço da Serra", "Sumaré - Área Cura", "Sumaré - Macarenko", "Sumaré - Matão",
]

# kind: 'conformidade' (Conforme/Não Conforme -> % e meta) | 'levantamento' (OK/Parcial/Não ou fonte)
FORMS = {
    "aud": {"name": "Auditoria Institucional", "conn_mode": "por_unidade", "tag": "Auditoria", "icon": ":material/fact_check:",
            "ready": True, "tabs": {"visitas": "Visitas", "itens": "Itens", "rascunho": "Rascunho"},
            "unit_col": "Unidade", "pct_col": "Percentual de Conformidade", "date_col": "Data da Visita",
            "desc": "Auditoria institucional: documentação, processos assistenciais e indicadores."},
    "enf": {"name": "Visita Técnica · Enfermagem", "kind": "vt", "free": True, "conn_mode": "unica", "tag": "Enfermagem", "icon": ":material/favorite:",
            "ready": True, "tabs": {"visitas": "Visitas", "itens": "Itens", "rascunho": "Rascunho"},
            "unit_col": "Hospital", "pct_col": "Percentual de OK", "date_col": "Data da Visita",
            "desc": "Visita técnica de enfermagem: item verificado, previsto e situação, com evidências."},
    "v03": {"name": "Visita Técnica · Hospital", "kind": "vt", "variant": "v03", "free": True, "conn_mode": "unica", "tag": "Hospital", "icon": ":material/local_hospital:",
            "ready": True, "tabs": {"visitas": "VT_Visitas", "itens": "VT_Itens", "rascunho": "VT_Rascunho"},
            "unit_col": "Hospital", "pct_col": "Percentual de OK", "date_col": "Data da Visita",
            "desc": "Visita técnica do hospital: estrutura, gestão, urgência, farmácia e segurança."},
    "upa": {"name": "Visita Técnica · UPA e PAM", "kind": "vt", "variant": "upa", "free": True, "conn_mode": "unica", "tag": "UPA · PAM", "icon": ":material/emergency:",
            "ready": True, "tabs": {"visitas": "UPA_Visitas", "itens": "UPA_Itens", "rascunho": "UPA_Rascunho"},
            "unit_col": "Unidade", "pct_col": None, "date_col": "Data da Visita",
            "desc": "Checklist único para UPA e PAM: acolhimento, assistência e apoio diagnóstico."},
}
