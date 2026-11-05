# -*- coding: utf-8 -*-
"""
sheets_backend.py
Camada de integração com o Google Sheets (gspread + Service Account) para o
Checklist de Visita Institucional (auditoria).

Modelo de dados normalizado (pensado para alimentar um banco de dados
relacional depois, mesmo que quem preenche só veja o checklist puro):

  - Aba "Visitas": 1 linha por visita/auditoria completa (cabeçalho, datas
    de início/fim, totais e % de conformidade).
  - Aba "Itens": 1 linha por item respondido (até 251 linhas por visita),
    ligada à visita pela coluna "Código da Visita".

Cada unidade tem sua própria planilha (abas "Visitas" + "Itens" + "Rascunho")
e existe uma planilha Consolidada com as mesmas duas primeiras abas,
recebendo os dados de todas as unidades — mesmo padrão do Canal de Eventos
Adversos.

Este módulo nunca deve derrubar o app: qualquer falha de gravação é
capturada e reportada ao chamador como (sucesso=False, modo, mensagem).
Grava tudo em UMA única operação por visita (não a cada seção) — evita
gravações parciais e reduz chamadas de API (1 append de N linhas em vez de
N chamadas).

RASCUNHOS (auditoria feita em mais de um dia): além das abas "Visitas" e
"Itens", cada planilha DE UNIDADE (não a consolidada — rascunho é sempre
por unidade) ganha uma terceira aba "Rascunho", com no máximo 1 linha por
unidade: o progresso é sobrescrito a cada autosave, nunca acumulado.
`salvar_rascunho`/`carregar_rascunho`/`apagar_rascunho` são as únicas
funções que o app.py chama para isso.

IMPORTANTE — verificação de rascunho existente vs. falha de verificação:
Como a aba "Rascunho" é SOBRESCRITA (não acumulada), se o app achar
erroneamente que não existe rascunho — por causa de uma falha transitória
de rede/API, não porque realmente não existe — e deixar o usuário iniciar
uma auditoria nova, o próximo autosave vai APAGAR PERMANENTEMENTE o
progresso real anterior. Por isso `carregar_rascunho` nunca trata "não
consegui verificar" como se fosse "verifiquei e não existe": nesse caso
retorna o sentinela ERRO_VERIFICACAO_RASCUNHO em vez de None, e o app.py
deve bloquear o início de uma auditoria nova até conseguir confirmar de
verdade (ver `verificar_rascunho_pendente` em app.py).

CRIAÇÃO AUTOMÁTICA DE PLANILHAS (pastas do Google Drive): em vez de exigir
que alguém crie manualmente as 14 planilhas de unidade + a consolidada e
cole os IDs em config/mapeamento_unidades.json, o app pode criar essas
planilhas sozinho dentro de duas pastas do Drive informadas em
"pasta_visita_unidade" e "pasta_visita_consolidado" (compartilhadas com a
Service Account como Editor). Na primeira vez que uma unidade precisa
gravar algo, o app procura por título ("Auditoria_<Unidade>") dentro da
pasta; se não existir, cria. O resultado fica em cache na memória do
processo (não persiste em disco) para não repetir a busca a cada gravação.
Um ID explícito em "unidades"/"consolidado" no JSON sempre tem prioridade
sobre a busca por pasta.

Nota sobre criação de planilha nova via Service Account: contas de serviço
"avulsas" (fora de um Google Workspace com Drive Compartilhado) têm cota de
armazenamento própria igual a zero — criar um arquivo novo como Service
Account falha com "storage quota exceeded" mesmo dentro de uma pasta com
espaço disponível, porque o arquivo novo nasceria com ela como dona. A
solução é a pessoa criar as planilhas manualmente (dono = ela, com espaço
normal) dentro das pastas já compartilhadas — a Service Account só edita
depois, o que não consome cota dela.
"""
import json
import os

from .schema import COLUNAS_VISITA, COLUNAS_ITEM, agora_brasilia

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "mapeamento_unidades.json")
LOCAL_DIR = os.path.join(BASE_DIR, "dados_locais")

# Precisa de escopo de escrita no Drive (não só leitura) para poder criar
# planilhas novas dentro das pastas informadas.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ABA_VISITAS = "Visitas"
ABA_ITENS = "Itens"
ABA_RASCUNHO = "Rascunho"
COLUNAS_RASCUNHO = ["Unidade", "Atualizado em", "Dados (JSON)"]

PREFIXO_PLACEHOLDER = "COLOQUE_"

# Sentinela retornado por carregar_rascunho() quando NÃO foi possível
# confirmar se existe ou não um rascunho (falha de rede/API) — bem
# diferente de None, que significa "confirmei: não existe". Ver nota no
# topo do arquivo sobre por que essa distinção é crítica.
ERRO_VERIFICACAO_RASCUNHO = "__ERRO_VERIFICACAO_RASCUNHO__"

# Cache em memória (vive enquanto o processo do servidor Streamlit estiver
# de pé) dos IDs de planilha já resolvidos por nome dentro de uma pasta —
# evita repetir a busca no Drive a cada gravação.
_CACHE_IDS_POR_PASTA = {}


def _carregar_mapeamento():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _credenciais_disponiveis(mapping):
    tem_credencial_env = bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
    tem_credencial_secrets = False
    try:
        import streamlit as st
        tem_credencial_secrets = "gcp_service_account" in st.secrets
    except Exception:
        pass

    algum_id_preenchido = any(
        v and not str(v).startswith(PREFIXO_PLACEHOLDER)
        for v in mapping.get("unidades", {}).values()
    ) or (bool(mapping.get("consolidado")) and not str(mapping.get("consolidado", "")).startswith(PREFIXO_PLACEHOLDER))

    alguma_pasta_configurada = any(
        mapping.get(chave) and not str(mapping.get(chave)).startswith(PREFIXO_PLACEHOLDER)
        for chave in ("pasta_visita_unidade", "pasta_visita_consolidado")
    )

    return (tem_credencial_env or tem_credencial_secrets) and (algum_id_preenchido or alguma_pasta_configurada)


def _obter_cliente_gspread():
    import gspread
    from google.oauth2.service_account import Credentials

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        info = json.loads(creds_json)
    else:
        import streamlit as st
        info = dict(st.secrets["gcp_service_account"])

    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def _buscar_ou_criar_planilha_na_pasta(cliente, nome_planilha, pasta_id):
    """Procura uma planilha com esse título exato dentro da pasta do Drive;
    cria se não existir. Resultado fica em cache em memória por (pasta_id,
    nome) para não repetir a busca a cada gravação enquanto o processo
    estiver rodando."""
    chave_cache = (pasta_id, nome_planilha)
    if chave_cache in _CACHE_IDS_POR_PASTA:
        return _CACHE_IDS_POR_PASTA[chave_cache]

    encontrada_id = None
    try:
        arquivos = cliente.list_spreadsheet_files(title=nome_planilha, folder_id=pasta_id)
        if arquivos:
            encontrada_id = arquivos[0]["id"]
    except Exception:
        encontrada_id = None  # busca falhou (permissão, API antiga etc.) — tenta criar mesmo assim

    if not encontrada_id:
        try:
            nova = cliente.create(nome_planilha, folder_id=pasta_id)
        except Exception as exc:
            if "storage quota" in str(exc).lower() or "quotaexceeded" in str(exc).lower():
                raise RuntimeError(
                    f"Não foi possível CRIAR '{nome_planilha}' — a Service Account não tem cota "
                    "própria de armazenamento no Drive (limitação do Google para contas de serviço "
                    "fora de um Workspace com Drive Compartilhado). Solução: crie essa planilha "
                    "manualmente (com esse nome exato) dentro da pasta — a Service Account só "
                    "precisa EDITAR, não criar, e edição não consome cota dela."
                ) from exc
            raise
        encontrada_id = nova.id

    _CACHE_IDS_POR_PASTA[chave_cache] = encontrada_id
    return encontrada_id


def _resolver_sheet_id_unidade(cliente, unidade, mapping):
    """ID explícito em 'unidades' sempre tem prioridade; senão, busca/cria
    dentro de 'pasta_visita_unidade' (se configurada). None se nenhuma das
    duas coisas estiver disponível."""
    explicito = mapping.get("unidades", {}).get(unidade)
    if explicito and not str(explicito).startswith(PREFIXO_PLACEHOLDER):
        return explicito
    pasta_id = mapping.get("pasta_visita_unidade")
    if pasta_id and not str(pasta_id).startswith(PREFIXO_PLACEHOLDER):
        return _buscar_ou_criar_planilha_na_pasta(cliente, f"Auditoria_{unidade}", pasta_id)
    return None


def _resolver_sheet_id_consolidado(cliente, mapping):
    explicito = mapping.get("consolidado")
    if explicito and not str(explicito).startswith(PREFIXO_PLACEHOLDER):
        return explicito
    pasta_id = mapping.get("pasta_visita_consolidado")
    if pasta_id and not str(pasta_id).startswith(PREFIXO_PLACEHOLDER):
        return _buscar_ou_criar_planilha_na_pasta(cliente, "Auditoria_Consolidado", pasta_id)
    return None


def _obter_ou_criar_aba(planilha, titulo, colunas):
    """Retorna a worksheet pelo título; cria (com cabeçalho) se não existir."""
    import gspread

    try:
        return planilha.worksheet(titulo)
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title=titulo, rows=1000, cols=len(colunas) + 2)
        aba.append_row(colunas, value_input_option="USER_ENTERED")
        return aba


def _seguro_gs(v):
    """Texto que começa com = + - @ viraria fórmula no Sheets (USER_ENTERED): grava como texto literal."""
    if isinstance(v, str) and v[:1] in ("=", "@", "+", "-") and not v.lstrip("+-").replace(",", "").replace(".", "").isdigit():
        return "'" + v
    return v


def _gravar_planilha_google(cliente, sheet_id, linha_visita, linhas_itens):
    linha_visita = [_seguro_gs(v) for v in linha_visita]
    linhas_itens = [[_seguro_gs(v) for v in l] for l in linhas_itens]
    planilha = cliente.open_by_key(sheet_id)

    aba_visitas = _obter_ou_criar_aba(planilha, ABA_VISITAS, COLUNAS_VISITA)
    aba_visitas.append_row(linha_visita, value_input_option="USER_ENTERED")

    aba_itens = _obter_ou_criar_aba(planilha, ABA_ITENS, COLUNAS_ITEM)
    # Uma única chamada gravando todas as linhas de itens da visita de uma vez.
    aba_itens.append_rows(linhas_itens, value_input_option="USER_ENTERED")


def _gravar_google_sheets(visita: dict, itens: list, mapping):
    cliente = _obter_cliente_gspread()
    unidade = visita.get("Unidade", "")

    linha_visita = [str(visita.get(col, "")) for col in COLUNAS_VISITA]
    linhas_itens = [[str(item.get(col, "")) for col in COLUNAS_ITEM] for item in itens]

    sheet_id_unidade = _resolver_sheet_id_unidade(cliente, unidade, mapping)
    sheet_id_consolidado = _resolver_sheet_id_consolidado(cliente, mapping)

    gravou_unidade = gravou_consolidado = False
    if sheet_id_unidade:
        _gravar_planilha_google(cliente, sheet_id_unidade, linha_visita, linhas_itens)
        gravou_unidade = True
    if sheet_id_consolidado:
        _gravar_planilha_google(cliente, sheet_id_consolidado, linha_visita, linhas_itens)
        gravou_consolidado = True

    if not gravou_unidade and not gravou_consolidado:
        raise RuntimeError(
            f"Nenhuma planilha resolvida para a unidade '{unidade}' nem para o consolidado "
            "(verifique config/mapeamento_unidades.json)."
        )
    return gravou_unidade, gravou_consolidado


def _estilizar_cabecalho(ws, colunas):
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    for idx, titulo_coluna in enumerate(colunas, start=1):
        cel = ws.cell(row=1, column=idx, value=titulo_coluna)
        cel.font = Font(name="Arial", size=10, bold=True, color="FFFFFFFF")
        cel.fill = PatternFill("solid", fgColor="FF005F8A")
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    ws.column_dimensions["A"].width = 26
    for col_idx in range(2, len(colunas) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 22


def _criar_workbook_local():
    import openpyxl

    wb = openpyxl.Workbook()
    ws_visitas = wb.active
    ws_visitas.title = ABA_VISITAS
    _estilizar_cabecalho(ws_visitas, COLUNAS_VISITA)

    ws_itens = wb.create_sheet(ABA_ITENS)
    _estilizar_cabecalho(ws_itens, COLUNAS_ITEM)
    return wb


def _acrescentar_linhas_local(caminho, linha_visita, linhas_itens):
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side

    if not os.path.exists(caminho):
        wb = _criar_workbook_local()
    else:
        wb = openpyxl.load_workbook(caminho)
        if ABA_VISITAS not in wb.sheetnames:
            ws = wb.create_sheet(ABA_VISITAS)
            _estilizar_cabecalho(ws, COLUNAS_VISITA)
        if ABA_ITENS not in wb.sheetnames:
            ws = wb.create_sheet(ABA_ITENS)
            _estilizar_cabecalho(ws, COLUNAS_ITEM)

    thin_border = Border(bottom=Side(style="thin", color="FFD6EDF8"))

    ws_visitas = wb[ABA_VISITAS]
    linha_destino = ws_visitas.max_row + 1
    for idx, valor in enumerate(linha_visita, start=1):
        cel = ws_visitas.cell(row=linha_destino, column=idx, value=valor)
        if isinstance(valor, str):
            cel.data_type = "s"   # texto nunca vira fórmula
        cel.font = Font(name="Arial", size=10, color="FF2E2E2E")
        cel.alignment = Alignment(horizontal="left", vertical="top", wrap_text=False)
        cel.border = thin_border

    ws_itens = wb[ABA_ITENS]
    obs_idx = COLUNAS_ITEM.index("Observações / Evidências") + 1
    for valores in linhas_itens:
        linha_destino = ws_itens.max_row + 1
        for idx, valor in enumerate(valores, start=1):
            cel = ws_itens.cell(row=linha_destino, column=idx, value=valor)
            if isinstance(valor, str):
                cel.data_type = "s"   # texto nunca vira fórmula
            cel.font = Font(name="Arial", size=10, color="FF2E2E2E")
            cel.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=(idx == obs_idx)
            )
            cel.border = thin_border

    wb.save(caminho)


def _gravar_local(visita: dict, itens: list):
    os.makedirs(LOCAL_DIR, exist_ok=True)
    unidade = visita.get("Unidade", "SEM_UNIDADE")

    linha_visita = [str(visita.get(col, "")) for col in COLUNAS_VISITA]
    linhas_itens = [[str(item.get(col, "")) for col in COLUNAS_ITEM] for item in itens]

    caminho_unidade = os.path.join(LOCAL_DIR, f"Auditoria_{unidade}.xlsx")
    caminho_consolidado = os.path.join(LOCAL_DIR, "Auditoria_Consolidado.xlsx")

    _acrescentar_linhas_local(caminho_unidade, linha_visita, linhas_itens)
    _acrescentar_linhas_local(caminho_consolidado, linha_visita, linhas_itens)


def salvar_auditoria(visita: dict, itens: list):
    """
    Grava a visita (aba Visitas) + todos os itens respondidos (aba Itens) —
    na planilha da unidade E na consolidada — numa única operação.

    Retorna (sucesso: bool, modo: str, mensagem: str).
    """
    try:
        mapping = _carregar_mapeamento()
    except FileNotFoundError:
        mapping = {"unidades": {}, "consolidado": ""}

    if _credenciais_disponiveis(mapping):
        try:
            gravou_unidade, gravou_consolidado = _gravar_google_sheets(visita, itens, mapping)
            if gravou_unidade and gravou_consolidado:
                return True, "google_sheets", "Auditoria gravada no Google Sheets (unidade + consolidado)."
            elif gravou_consolidado:
                return True, "google_sheets_parcial", (
                    "Auditoria gravada apenas no consolidado — a planilha desta unidade não pôde "
                    "ser resolvida (verifique 'pasta_visita_unidade' ou o ID em config/mapeamento_unidades.json)."
                )
            else:
                return True, "google_sheets_parcial", (
                    "Auditoria gravada apenas na planilha da unidade — o consolidado não pôde ser "
                    "resolvido (verifique 'pasta_visita_consolidado' ou o ID em config/mapeamento_unidades.json)."
                )
        except Exception as exc:
            try:
                _gravar_local(visita, itens)
            except Exception:
                pass
            return False, "erro_google_sheets", f"Falha ao gravar no Google Sheets: {exc}"
    else:
        try:
            _gravar_local(visita, itens)
            return True, "local_fallback", (
                "Credenciais do Google Sheets ainda não configuradas neste ambiente. "
                "Auditoria salva localmente em modo de teste (pasta dados_locais/)."
            )
        except Exception as exc:
            return False, "erro_local", f"Falha ao gravar localmente: {exc}"


# ---------------------------------------------------------------------------
# Rascunho (autosave) — permite retomar uma visita em outro dia. Sempre 1
# linha/arquivo por unidade: o progresso é SOBRESCRITO a cada autosave, não
# acumulado. Vive só na planilha/arquivo da unidade (não no consolidado).
# ---------------------------------------------------------------------------
def _caminho_rascunho_local(unidade):
    from .schema import slug_unidade
    return os.path.join(LOCAL_DIR, f"Rascunho_{slug_unidade(unidade)}.json")


def _salvar_rascunho_local(unidade, payload: dict):
    os.makedirs(LOCAL_DIR, exist_ok=True)
    with open(_caminho_rascunho_local(unidade), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def _carregar_rascunho_local(unidade):
    caminho = _caminho_rascunho_local(unidade)
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _apagar_rascunho_local(unidade):
    caminho = _caminho_rascunho_local(unidade)
    if os.path.exists(caminho):
        os.remove(caminho)


def _linha_rascunho_google(aba, unidade):
    """Retorna o índice da linha (1-based, já contando o cabeçalho) da
    unidade na aba Rascunho, ou None se ainda não houver rascunho dela."""
    valores_coluna_a = aba.col_values(1)
    for idx, valor in enumerate(valores_coluna_a[1:], start=2):
        if valor == unidade:
            return idx
    return None


def _salvar_rascunho_google(cliente, sheet_id, unidade, payload: dict):
    planilha = cliente.open_by_key(sheet_id)
    aba = _obter_ou_criar_aba(planilha, ABA_RASCUNHO, COLUNAS_RASCUNHO)
    linha = [unidade, payload["atualizado_em"], json.dumps(payload["dados"], ensure_ascii=False)]
    idx = _linha_rascunho_google(aba, unidade)
    if idx:
        aba.update(f"A{idx}:C{idx}", [linha], value_input_option="USER_ENTERED")
    else:
        aba.append_row(linha, value_input_option="USER_ENTERED")


def _carregar_rascunho_google(cliente, sheet_id, unidade):
    import gspread

    planilha = cliente.open_by_key(sheet_id)
    try:
        aba = planilha.worksheet(ABA_RASCUNHO)
    except gspread.exceptions.WorksheetNotFound:
        return None  # aba realmente não existe ainda -> confirmadamente não há rascunho
    idx = _linha_rascunho_google(aba, unidade)
    if not idx:
        return None
    valores_linha = aba.row_values(idx)
    if len(valores_linha) < 3:
        return None
    _, atualizado_em, dados_json = valores_linha[:3]
    try:
        return {"atualizado_em": atualizado_em, "dados": json.loads(dados_json)}
    except Exception:
        return None


def _apagar_rascunho_google(cliente, sheet_id, unidade):
    import gspread

    planilha = cliente.open_by_key(sheet_id)
    try:
        aba = planilha.worksheet(ABA_RASCUNHO)
    except gspread.exceptions.WorksheetNotFound:
        return
    idx = _linha_rascunho_google(aba, unidade)
    if idx:
        aba.delete_rows(idx)


def salvar_rascunho(unidade: str, dados: dict):
    """Autosave do progresso (chamado pelo app.py a cada interação dentro
    de uma seção). Nunca lança exceção — uma falha aqui só significa que
    aquele passo não ficou salvo para retomada, não deve travar o
    preenchimento."""
    payload = {"atualizado_em": agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"), "dados": dados}
    try:
        mapping = _carregar_mapeamento()
    except FileNotFoundError:
        mapping = {"unidades": {}, "consolidado": ""}

    if _credenciais_disponiveis(mapping):
        try:
            cliente = _obter_cliente_gspread()
            sheet_id = _resolver_sheet_id_unidade(cliente, unidade, mapping)
            if sheet_id:
                _salvar_rascunho_google(cliente, sheet_id, unidade, payload)
                return
        except Exception:
            pass  # cai para o fallback local abaixo
    try:
        _salvar_rascunho_local(unidade, payload)
    except Exception:
        pass


def carregar_rascunho(unidade: str):
    """Retorna:
      - {"atualizado_em": str, "dados": dict}  se existe rascunho salvo
      - None                                    se CONFIRMADO que não existe
      - ERRO_VERIFICACAO_RASCUNHO                se não foi possível
        verificar (falha de rede/API) — o chamador NUNCA deve tratar isso
        como "não existe", sob risco de deixar iniciar uma auditoria nova
        que sobrescreve um rascunho real no próximo autosave.
    """
    try:
        mapping = _carregar_mapeamento()
    except FileNotFoundError:
        mapping = {"unidades": {}, "consolidado": ""}

    if _credenciais_disponiveis(mapping):
        try:
            cliente = _obter_cliente_gspread()
            sheet_id = _resolver_sheet_id_unidade(cliente, unidade, mapping)
        except Exception:
            return ERRO_VERIFICACAO_RASCUNHO  # não sabemos se existe rascunho — não é seguro prosseguir como se não houvesse

        if sheet_id:
            try:
                # Consulta bem-sucedida ao Sheets é a resposta definitiva —
                # mesmo que seja None ("não há rascunho"), não cai para o
                # arquivo local depois (isso poderia mascarar uma falha real
                # com um resultado local vazio e dar falsa confiança).
                return _carregar_rascunho_google(cliente, sheet_id, unidade)
            except Exception:
                return ERRO_VERIFICACAO_RASCUNHO  # falha ao consultar -> NÃO é "confirmei que não existe"
        else:
            return None  # Sheets configurado, mas nada resolvível pra essa unidade — confirmadamente não há onde um rascunho dela teria sido salvo

    try:
        return _carregar_rascunho_local(unidade)
    except Exception:
        return None


def apagar_rascunho(unidade: str):
    """Chamado após o envio final bem-sucedido da auditoria, para não
    oferecer 'continuar' uma visita que já foi enviada."""
    try:
        mapping = _carregar_mapeamento()
    except FileNotFoundError:
        mapping = {"unidades": {}, "consolidado": ""}

    if _credenciais_disponiveis(mapping):
        try:
            cliente = _obter_cliente_gspread()
            sheet_id = _resolver_sheet_id_unidade(cliente, unidade, mapping)
            if sheet_id:
                _apagar_rascunho_google(cliente, sheet_id, unidade)
        except Exception:
            pass
    try:
        _apagar_rascunho_local(unidade)
    except Exception:
        pass


def _config_upload_apps_script():
    """Endpoint do Apps Script (grava no Drive do dono da pasta). GOOGLE_UPLOAD_JSON ou secrets [upload_drive]."""
    bruto = os.environ.get("GOOGLE_UPLOAD_JSON")
    if bruto:
        return json.loads(bruto)
    try:
        import streamlit as st
        if "upload_drive" in st.secrets:
            return dict(st.secrets["upload_drive"])
    except Exception:
        pass
    return None


def drive_para_evidencias():
    """(destino de upload, id da pasta) ou (None, None) => modo local de teste."""
    mapping = _carregar_mapeamento()
    pasta = mapping.get("pasta_evidencias") or mapping.get("pasta_visita_consolidado") or ""
    if not pasta or str(pasta).startswith(PREFIXO_PLACEHOLDER):
        return None, None
    cfg = _config_upload_apps_script()
    if cfg and cfg.get("url") and cfg.get("token"):
        from .evidencias import UploadAppsScript
        return UploadAppsScript(cfg["url"], cfg["token"], pasta), pasta
    if _credenciais_disponiveis(mapping):
        return _obter_cliente_gspread().http_client.session, pasta
    return None, None
