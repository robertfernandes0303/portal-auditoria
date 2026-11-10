"""Regras da Enfermagem portadas de app.py sem alterar regra: catálogo, totais, % de OK e linhas gravadas. Puro Python."""
from . import schema as sc


def catalogo():
    return [{"nome": g["nome"], "itens": [dict(i) for i in g["itens"]]} for g in sc.GRUPOS]


def config():
    return {"opcoes": sc.OPCOES_SITUACAO, "rotulos": sc.ROTULOS, "exige_obs": sc.EXIGE_OBS, "modulos": sc.MODULOS_ESPECIFICOS, "max_anexos": sc.MAX_ANEXOS_POR_ITEM, "ufs": sc.UFS, "total": sc.TOTAL_ITENS,
            "ext": sc.EXTENSOES_PERMITIDAS, "max_pdf_mb": sc.MAX_MB_PDF}


def novo_codigo(hospital):
    return sc.gerar_codigo_visita(hospital)


def limpar(dados):
    resp = {}
    for k, v in (dados.get("respostas") or {}).items():
        try:
            n = int(k)
        except (TypeError, ValueError):
            continue
        v = v or {}
        sit = v.get("situacao") if v.get("situacao") in sc.OPCOES_SITUACAO else None
        resp[n] = {**v, "situacao": sit, "observacao": str(v.get("observacao") or "")[:4000]}
    prev = {}
    for k, v in (dados.get("previsto_informado") or {}).items():
        try:
            prev[int(k)] = str(v or "")[:1000]
        except (TypeError, ValueError):
            pass
    anex = {}
    for k, v in (dados.get("anexos") or {}).items():
        try:
            anex[int(k)] = list(v or [])[: sc.MAX_ANEXOS_POR_ITEM]
        except (TypeError, ValueError):
            pass
    return resp, prev, anex


def resumo_rascunho(dados):
    return sum(1 for v in (dados.get("respostas") or {}).values() if v.get("situacao"))


def itens_sem_observacao(dados):
    """Refs dos itens Parcial/Não sem observacao (regra do padrao: PC e NC exigem descricao objetiva)."""
    resp, _, _ = limpar(dados)
    faltam = []
    for g in sc.GRUPOS:
        for it in g["itens"]:
            r = resp.get(it["num"], {})
            if r.get("situacao") in sc.EXIGE_OBS and not str(r.get("observacao") or "").strip():
                faltam.append(it["ref"])
    return faltam


def montar_envio(dados):
    """Retorna (visita, itens, evidencias) com os mesmos campos que o app original gravava."""
    from datetime import date
    resp, prev, anex = limpar(dados)
    codigo, hospital = dados["codigo_visita"], dados["hospital"]
    d = date.fromisoformat(dados["data_visita"])
    data_txt = d.strftime("%d/%m/%Y")
    itens, evidencias = [], []
    cont = {sc.OK: 0, sc.PARCIAL: 0, sc.NAO: 0, sc.NA: 0}
    nao_pre = total_anexos = 0
    for g in sc.GRUPOS:
        for it in g["itens"]:
            n = it["num"]
            r = resp.get(n, {})
            sit = r.get("situacao")
            if sit in cont:
                cont[sit] += 1
            else:
                nao_pre += 1
            anx = anex.get(n, [])
            total_anexos += len(anx)
            itens.append({"Código da Visita": codigo, "Hospital": hospital, "Data da Visita": data_txt, "Grupo": g["nome"],
                          "Nº do Item": n, "Ref.": it["ref"], "Item a Verificar": it["texto"],
                          "Previsto no TR / Apêndices (sugerido)": "",
                          "Previsto informado pelo auditor": "", "Situação": sit or "Não preenchido",
                          "Observação": r.get("observacao", ""), "Qtde de Anexos": len(anx),
                          "Respondido em": r.get("respondido_em", "") if sit else ""})
            for a in anx:
                evidencias.append({"Código da Visita": codigo, "Hospital": hospital, "Nº do Item": n, "Ref.": it["ref"],
                                   "Arquivo": a.get("nome", ""), "Tipo": a.get("tipo", ""), "Tamanho (KB)": a.get("tamanho_kb", ""),
                                   "Enviado em": a.get("enviado_em", ""), "Link / Caminho": a.get("link", "")})
    base = cont[sc.OK] + cont[sc.PARCIAL] + cont[sc.NAO]
    pct = f"{(cont[sc.OK] / base * 100):.1f}%" if base else "—"
    visita = {"Código da Visita": codigo, "Hospital": hospital, "Cidade": dados.get("cidade", ""), "UF": dados.get("uf", ""),
              "Edital / Processo": dados.get("edital", ""), "Data da Visita": data_txt,
              "Responsável pela Visita": dados.get("responsavel_visita", ""), "Nome de Quem Acompanhou": dados.get("acompanhante", ""),
              "Início do Preenchimento": dados.get("timestamp_inicio") or "",
              "Fim do Preenchimento (Envio)": sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
              "Status da Visita": "Completa" if nao_pre == 0 else "Incompleta",
              "Total de Itens Avaliados": sc.TOTAL_ITENS - nao_pre, "Total OK": cont[sc.OK], "Total Parcial": cont[sc.PARCIAL],
              "Total Não": cont[sc.NAO], "Total N/A": cont[sc.NA], "Total Não Preenchido": nao_pre,
              "Percentual de OK": pct, "Total de Anexos": total_anexos,
              "RT de Enfermagem": str(dados.get("rt_enfermagem") or "")[:200], "Gestor da Unidade": str(dados.get("gestor_unidade") or "")[:200],
              "Perfil da Unidade": str(dados.get("perfil_unidade") or "")[:200],
              "Horário": str(dados.get("horario") or "")[:20],
              "Módulos Específicos Aplicáveis": ", ".join(m for m in (dados.get("modulos") or []) if m in sc.MODULOS_ESPECIFICOS)}
    return visita, itens, evidencias
