"""Regras do formulário (portadas de app.py sem alteração de regra): validação dos campos numéricos, totais,
percentual e montagem das linhas gravadas nas abas Visitas e Itens. Puro Python, sem Streamlit."""
from datetime import datetime
from .schema import (CONFORME, NAO_CONFORME, NAO_SE_APLICA, OPCOES_CHECKLIST, SECOES, FUSO_BRASILIA,
                     agora_brasilia, gerar_codigo_visita)


def config():
    from . import schema as sc
    return {"max_anexos": sc.MAX_ANEXOS_POR_ITEM, "ext": sc.EXTENSOES_PERMITIDAS, "max_pdf_mb": sc.MAX_MB_PDF}


def _anexos(dados):
    """{num: [anexo,...]} — só campos conhecidos; só itens de checklist (não os de quantidade)."""
    out = {}
    for k, lst in (dados.get("anexos") or {}).items():
        try:
            n = int(k)
        except (TypeError, ValueError):
            continue
        ok = []
        for a in (lst or [])[:20]:
            if isinstance(a, dict) and a.get("nome"):
                ok.append({"nome": str(a.get("nome"))[:120], "link": str(a.get("link") or "")[:300],
                           "tamanho_kb": a.get("tamanho_kb", 0), "id_arquivo": str(a.get("id_arquivo") or "")[:80]})
        if ok:
            out[n] = ok
    return out


def catalogo():
    return [{"nome": s["nome"], "tipo": s["tipo"],
             "itens": [{"num": i["num"], "texto": i["texto"], "tipo_resposta": i.get("tipo_resposta", "checklist")} for i in s["itens"]]}
            for s in SECOES]


def novo_codigo(unidade):
    return gerar_codigo_visita(unidade)


def validar_quantidade(secao, valores):
    erros = []
    for item in secao["itens"]:
        if item["tipo_resposta"] not in ("numero_inteiro", "numero_percentual"):
            continue
        bruto = (valores.get(item["num"]) or "").strip()
        if not bruto:
            continue
        try:
            valor = float(bruto.replace(",", "."))
        except ValueError:
            erros.append(f"{item['num']}. {item['texto']}: \"{bruto}\" não é um número válido")
            continue
        if valor < 0:
            erros.append(f"{item['num']}. {item['texto']}: não pode ser negativo")
        elif item["tipo_resposta"] == "numero_percentual" and valor > 100:
            erros.append(f"{item['num']}. {item['texto']}: percentual deve estar entre 0 e 100")
    return erros


def limpar(dados):
    """Normaliza o que veio da interface (tipos, tamanhos, opções válidas)."""
    resp = {}
    for k, v in (dados.get("respostas_checklist") or {}).items():
        try:
            n = int(k)
        except (TypeError, ValueError):
            continue
        r = (v or {}).get("resposta")
        resp[n] = {"resposta": r if r in OPCOES_CHECKLIST else None, "observacao": str((v or {}).get("observacao") or "")[:1000]}
    vals = {}
    for k, v in (dados.get("valores_quantidade") or {}).items():
        try:
            vals[int(k)] = str(v or "")[:200]
        except (TypeError, ValueError):
            continue
    return resp, vals


def status_secoes(resp, vals, visitadas, concluidas):
    out = {}
    for s in SECOES:
        if s["tipo"] == "quantidade":
            out[s["nome"]] = "completa" if s["nome"] in concluidas else ("andamento" if s["nome"] in visitadas else "pendente")
        else:
            n = sum(1 for i in s["itens"] if resp.get(i["num"], {}).get("resposta") in OPCOES_CHECKLIST)
            out[s["nome"]] = "pendente" if n == 0 else ("andamento" if n < len(s["itens"]) else "completa")
    return out


def montar_registros(unidade, dados, agora=None):
    """Retorna (registro_visita, itens_registro, resumo, secoes_pendentes)."""
    agora = agora or agora_brasilia()
    resp, vals = limpar(dados)
    anx = _anexos(dados)
    total_anx = 0
    codigo = dados.get("codigo_visita") or gerar_codigo_visita(unidade)
    data_visita = str(dados["data_visita"])
    itens, conf, nconf, naplica, nprench = [], 0, 0, 0, 0
    for secao in SECOES:
        for item in secao["itens"]:
            if secao["tipo"] == "quantidade":
                bruto = vals.get(item["num"])
                resposta = "" if bruto in (None, "") else str(bruto)
                obs, tipo = "", item["tipo_resposta"]
            else:
                d = resp.get(item["num"], {})
                resposta, obs, tipo = d.get("resposta") or "", d.get("observacao", ""), "checklist"
                if resposta == CONFORME: conf += 1
                elif resposta == NAO_CONFORME: nconf += 1
                elif resposta == NAO_SE_APLICA: naplica += 1
                else: nprench += 1
            itens.append({"Código da Visita": codigo, "Unidade": unidade, "Data da Visita": data_visita, "Seção": secao["nome"],
                          "Nº do Item": item["num"], "Item de Verificação": item["texto"], "Tipo de Campo": tipo,
                          "Resposta": resposta, "Observações / Evidências": obs,
                          "Respondido em": agora.strftime("%d/%m/%Y %H:%M:%S"),
                          "Qtde de Anexos": len(anx.get(item["num"], [])) if secao["tipo"] != "quantidade" else 0,
                          "Links dos Anexos": " | ".join(f"{a['nome']} <{a['link']}>" if a["link"] else a["nome"]
                                                         for a in anx.get(item["num"], [])) if secao["tipo"] != "quantidade" else ""})
            if secao["tipo"] != "quantidade":
                total_anx += len(anx.get(item["num"], []))
    aval = conf + nconf
    pct = f"{(conf / aval * 100):.1f}%" if aval else ""
    visita = {"Código da Visita": codigo, "Unidade": unidade, "Data da Visita": data_visita,
              "Responsável pela Visita": dados.get("responsavel_visita", ""), "Nome de Quem Acompanhou": dados.get("acompanhante", ""),
              "Início do Preenchimento": dados.get("timestamp_inicio") or agora.strftime("%d/%m/%Y %H:%M:%S"),
              "Fim do Preenchimento (Envio)": agora.strftime("%d/%m/%Y %H:%M:%S"),
              "Status da Visita": "Incompleta" if nprench else "Completa", "Total de Itens Aplicáveis": aval,
              "Total Conforme": conf, "Total Não Conforme": nconf, "Total Não se Aplica": naplica,
              "Total Não Preenchido": nprench, "Percentual de Conformidade": pct, "Total de Anexos": total_anx}
    st = status_secoes(resp, vals, set(dados.get("secoes_visitadas") or []), set(dados.get("secoes_concluidas") or []))
    pend = [n for n, s in st.items() if s != "completa"]
    resumo = {"conforme": conf, "nao_conforme": nconf, "nao_aplica": naplica, "nao_preenchido": nprench, "percentual": pct}
    return visita, itens, resumo, pend
