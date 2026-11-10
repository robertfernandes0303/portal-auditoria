"""Regras da Visita Técnica · SESMT: catálogo, totais, % de conformidade e linhas gravadas. Puro Python.
Mesmo modelo da Enfermagem; respostas: Conforme / Não conforme / Não se aplica (sem "Parcial")."""
from . import schema as sc


def catalogo():
    return [{"nome": g["nome"], "itens": [dict(i) for i in g["itens"]]} for g in sc.GRUPOS]


def config():
    return {"opcoes": sc.OPCOES_SITUACAO, "rotulos": sc.ROTULOS, "max_anexos": sc.MAX_ANEXOS_POR_ITEM, "ufs": sc.UFS, "total": sc.TOTAL_ITENS,
            "ext": sc.EXTENSOES_PERMITIDAS, "max_pdf_mb": sc.MAX_MB_PDF}


def novo_codigo(unidade):
    return sc.gerar_codigo_visita(unidade)


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
    anex = {}
    for k, v in (dados.get("anexos") or {}).items():
        try:
            anex[int(k)] = list(v or [])[: sc.MAX_ANEXOS_POR_ITEM]
        except (TypeError, ValueError):
            pass
    return resp, {}, anex


def resumo_rascunho(dados):
    return sum(1 for v in (dados.get("respostas") or {}).values() if v.get("situacao") in sc.OPCOES_SITUACAO)


def montar_envio(dados):
    """Retorna (visita, itens, evidencias) nas colunas da planilha do SESMT."""
    from datetime import date
    resp, _, anex = limpar(dados)
    codigo, unidade = dados["codigo_visita"], dados["hospital"]   # a interface chama o campo de "hospital" nos formulários de visita
    d = date.fromisoformat(dados["data_visita"])
    data_txt = d.strftime("%d/%m/%Y")
    itens, evidencias = [], []
    cont = {sc.OK: 0, sc.NAO: 0, sc.NA: 0}
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
            itens.append({"Código da Visita": codigo, "Unidade": unidade, "Data da Visita": data_txt, "Grupo": g["nome"],
                          "Nº do Item": n, "Ref.": it["ref"], "Item de Verificação": it["texto"],
                          "Situação": sc.ROTULOS.get(sit, "Não preenchido"),
                          "Observação": r.get("observacao", ""), "Qtde de Anexos": len(anx),
                          "Respondido em": r.get("respondido_em", "") if sit else ""})
            for a in anx:
                evidencias.append({"Código da Visita": codigo, "Unidade": unidade, "Nº do Item": n, "Ref.": it["ref"],
                                   "Arquivo": a.get("nome", ""), "Tipo": a.get("tipo", ""), "Tamanho (KB)": a.get("tamanho_kb", ""),
                                   "Enviado em": a.get("enviado_em", ""), "Link / Caminho": a.get("link", "")})
    base = cont[sc.OK] + cont[sc.NAO]
    pct = f"{(cont[sc.OK] / base * 100):.1f}%" if base else "—"
    visita = {"Código da Visita": codigo, "Unidade": unidade, "Cidade": dados.get("cidade", ""), "UF": dados.get("uf", ""),
              "Data da Visita": data_txt,
              "Responsável pela Visita": dados.get("responsavel_visita", ""), "Nome de Quem Acompanhou": dados.get("acompanhante", ""),
              "Início do Preenchimento": dados.get("timestamp_inicio") or "",
              "Fim do Preenchimento (Envio)": sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
              "Status da Visita": "Completa" if nao_pre == 0 else "Incompleta",
              "Total de Itens Avaliados": sc.TOTAL_ITENS - nao_pre, "Total Conforme": cont[sc.OK], "Total Não Conforme": cont[sc.NAO],
              "Total Não se Aplica": cont[sc.NA], "Total Não Preenchido": nao_pre,
              "Percentual de Conformidade": pct, "Total de Anexos": total_anexos}
    return visita, itens, evidencias
