"""Regras da UPA/PAM portadas de app.py sem alterar regra: item respondido/verificado, totais e linhas gravadas. Puro Python."""
from datetime import date

from . import schema as sc


def catalogo():
    return [{"nome": g["nome"], "itens": [dict(i) for i in g["itens"]]} for g in sc.GRUPOS]


def config():
    return {"fontes": sc.OPCOES_FONTE, "max_anexos": sc.MAX_ANEXOS_POR_ITEM, "ufs": sc.UFS, "total": sc.TOTAL_ITENS,
            "essenciais": sc.TOTAL_ESSENCIAIS, "complementares": sc.TOTAL_COMPLEMENTARES,
            "ext": sc.EXTENSOES_PERMITIDAS, "max_pdf_mb": sc.MAX_MB_PDF}


def novo_codigo(unidade):
    return sc.gerar_codigo_visita(unidade)


def respondido(r):
    r = r or {}
    return bool(str(r.get("resposta", "")).strip()) or r.get("fonte") in (sc.NAO_VERIF, sc.NAO_SE_APLICA)


def verificado(r):
    r = r or {}
    return bool(str(r.get("resposta", "")).strip()) and r.get("fonte") in sc.FONTES_VERIFICADAS


def resumo_rascunho(dados):
    return sum(1 for v in (dados.get("respostas") or {}).values() if respondido(v))


def limpar(dados):
    resp = {}
    for k, v in (dados.get("respostas") or {}).items():
        try:
            n = int(k)
        except (TypeError, ValueError):
            continue
        v = v or {}
        fonte = v.get("fonte") if v.get("fonte") in sc.OPCOES_FONTE else None
        resp[n] = {**v, "fonte": fonte, "resposta": str(v.get("resposta") or "")[:4000], "obs": str(v.get("obs") or "")[:4000]}
    anex = {}
    for k, v in (dados.get("anexos") or {}).items():
        try:
            anex[int(k)] = list(v or [])[: sc.MAX_ANEXOS_POR_ITEM]
        except (TypeError, ValueError):
            pass
    imp = {}
    for k, v in (dados.get("impactos") or {}).items():
        try:
            imp[int(k)] = str(v or "")[:4000]
        except (TypeError, ValueError):
            pass
    return resp, anex, imp


def montar_envio(dados):
    """Retorna (visita, itens, evidencias, secoes) com os mesmos campos que o app original gravava."""
    resp, anex, imp = limpar(dados)
    codigo, unidade = dados["codigo_visita"], dados["hospital"]
    data_txt = date.fromisoformat(dados["data_visita"]).strftime("%d/%m/%Y")
    inicio = dados.get("timestamp_inicio") or ""
    itens, evidencias, secoes = [], [], []
    verif = nverif = nasp = nao_pre = total_anexos = resp_ess = resp_comp = 0
    for gi, g in enumerate(sc.GRUPOS):
        for it in g["itens"]:
            n = it["num"]
            r = resp.get(n, {})
            feito = respondido(r)
            if feito:
                if it["foco"] == sc.ESSENCIAL:
                    resp_ess += 1
                else:
                    resp_comp += 1
            else:
                nao_pre += 1
            if r.get("fonte") == sc.NAO_VERIF:
                nverif += 1
            elif r.get("fonte") == sc.NAO_SE_APLICA:
                nasp += 1
            elif verificado(r):
                verif += 1
            anx = anex.get(n, [])
            total_anexos += len(anx)
            itens.append({"Código da Visita": codigo, "Unidade": unidade, "Data da Visita": data_txt, "Seção": g["nome"],
                          "ID": it["ref"], "Foco": sc.ROTULO_FOCO[it["foco"]], "Pergunta ou dado a levantar": it["texto"],
                          "Resposta / valor": r.get("resposta", ""), "Fonte": r.get("fonte") or "",
                          "Verificado (OK)": "Sim" if verificado(r) else "Não", "Observação": r.get("obs", ""),
                          "Qtde de Anexos": len(anx), "Respondido em": r.get("respondido_em", "") if feito else ""})
            for a in anx:
                evidencias.append({"Código da Visita": codigo, "Unidade": unidade, "ID": it["ref"], "Ref.": it["ref"],
                                   "Arquivo": a.get("nome", ""), "Tipo": a.get("tipo", ""), "Tamanho (KB)": a.get("tamanho_kb", ""),
                                   "Enviado em": a.get("enviado_em", ""), "Link / Caminho": a.get("link", "")})
        txt = str(imp.get(gi, "")).strip()
        if txt:
            secoes.append({"Código da Visita": codigo, "Unidade": unidade, "Nº da Seção": gi + 1, "Seção": g["nome"],
                           "Impacto na proposta e providências São Lucas": txt})
    visita = {"Código da Visita": codigo, "Unidade": unidade, "Cidade": dados.get("cidade", ""), "UF": dados.get("uf", ""),
              "Edital / Processo": dados.get("edital", ""), "Data da Visita": data_txt,
              "Horário": dados.get("horario") or str(inicio)[11:16], "Visitantes": dados.get("responsavel_visita", ""),
              "Acompanhante / função": dados.get("acompanhante", ""), "Início do Preenchimento": inicio,
              "Fim do Preenchimento (Envio)": sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
              "Status da Visita": "Completa" if nao_pre == 0 else "Incompleta",
              "Total de Itens": sc.TOTAL_ITENS, "Itens Respondidos": sc.TOTAL_ITENS - nao_pre,
              "Essenciais Respondidos": resp_ess, "Complementares Respondidos": resp_comp,
              "Total Verificados": verif, "Total Não Verificados": nverif, "Total Não se Aplica": nasp,
              "Total Não Preenchido": nao_pre, "Total de Anexos": total_anexos, "Seções com Impacto Registrado": len(secoes)}
    return visita, itens, evidencias, secoes
