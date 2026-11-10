# -*- coding: utf-8 -*-
"""
schema.py - Checklist de Visita Tecnica de Enfermagem (Sao Lucas Instituto)

Catalogo de grupos e itens + constantes + colunas das planilhas.

Padrao vigente desde 10/11/2026 (Checklist Institucional de Acompanhamento da Enfermagem, 74 itens).
IMPORTANTE: o numero global do item (1..N) e a CHAVE ESTAVEL que liga os dados
historicos ao catalogo. Nunca renumere; para itens novos, use numeros novos
(depois do ultimo) mesmo que o item apareca no meio de um grupo (campo "ref"
define o rotulo exibido, ex.: "2.6"). A lista abaixo e uma PROPOSTA a ser
validada pela area tecnica de enfermagem; as referencias normativas citadas em
"previsto" sao sugestoes e devem ser conferidas.
"""
import re
import unicodedata
from datetime import datetime, timedelta, timezone

UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]

FUSO_BRASILIA = timezone(timedelta(hours=-3))

OK = "OK"
PARCIAL = "Parcial"
NAO = "Não"
NA = "N/A"
OPCOES_SITUACAO = [OK, PARCIAL, NAO, NA]
# Valores gravados continuam OK/Parcial/Não/N/A (compatibilidade com leitores e planilhas);
# a tela mostra a classificacao do padrao: C, PC, NC, NA.
ROTULOS = {OK: "Conforme", PARCIAL: "Parcialmente conforme", NAO: "Não conforme", NA: "Não se aplica"}
# Itens PC e NC exigem observacao objetiva (regra do padrao)
EXIGE_OBS = [PARCIAL, NAO]
MODULOS_ESPECIFICOS = ["CME", "Centro Cirúrgico", "UTI", "Pediatria", "Obstetrícia", "Transporte/Ambulância", "Hemoterapia", "Classificação de Risco", "Unidade de Internação"]

# Limites de anexo (evidencia)
EXTENSOES_PERMITIDAS = ["jpg", "jpeg", "png", "pdf"]
MAX_ANEXOS_POR_ITEM = 20
MAX_MB_IMAGEM_ENTRADA = 20
MAX_MB_PDF = 10
LADO_MAX_IMAGEM_PX = 1600
QUALIDADE_JPEG = 80

# (nome do grupo, [(texto do item, ''), ...]) - Checklist Institucional de Acompanhamento da Enfermagem
# (padrao de 10/11/2026; 74 itens numerados como no PDF, ref = numero do item)
GRUPOS_BRUTOS = [
    ('GESTÃO E RESPONSABILIDADE TÉCNICA', [
        ('Certidão/registro de Responsabilidade Técnica vigente', ''),
        ('Regimento do Serviço de Enfermagem atualizado', ''),
        ('Escala mensal completa, assinada e disponível', ''),
        ('Dimensionamento da equipe de enfermagem avaliado', ''),
        ('Cobertura de ausências, férias e afastamentos adequada', ''),
        ('Enfermeiro presente conforme necessidade assistencial', ''),
        ('Supervisão dos técnicos/auxiliares evidenciada', ''),
        ('Reuniões periódicas da enfermagem com registro em ata', ''),
        ('Indicadores acompanhados e analisados pela RT', ''),
        ('Plano de ação das não conformidades acompanhado pela RT', ''),
    ]),
    ('SEGURANÇA DO PACIENTE', [
        ('Identificação segura do paciente', ''),
        ('Alergias identificadas e sinalizadas', ''),
        ('Protocolo de prevenção de quedas implantado e aplicado', ''),
        ('Avaliação de risco de lesão por pressão quando aplicável', ''),
        ('Segurança na prescrição, preparo e administração de medicamentos', ''),
        ('Aplicação dos 9 certos na administração de medicamentos', ''),
        ('Eventos adversos e incidentes notificados', ''),
        ('Eventos analisados com plano de ação quando necessário', ''),
        ('Orientação ao paciente/família registrada', ''),
        ('Alta segura implantada quando aplicável', ''),
    ]),
    ('AUDITORIA DA ASSISTÊNCIA E PRONTUÁRIO', [
        ('Evolução de enfermagem presente e adequada', ''),
        ('Anotação de enfermagem presente e adequada', ''),
        ('Identificação e rastreabilidade do profissional', ''),
        ('Registros datados, legíveis e rastreáveis', ''),
        ('Prescrição de enfermagem quando aplicável', ''),
        ('SAE/Processo de Enfermagem quando aplicável', ''),
        ('Sinais vitais registrados conforme protocolo', ''),
        ('Administração e checagem de medicamentos', ''),
        ('Dieta checada conforme prescrição', ''),
        ('Dispositivos identificados, datados e monitorados', ''),
        ('Orientações e alta registradas', ''),
    ]),
    ('URGÊNCIA E EMERGÊNCIA', [
        ('Carrinho de emergência completo e organizado', ''),
        ('Lacre e controle de abertura do carrinho', ''),
        ('Medicamentos de emergência dentro da validade', ''),
        ('Materiais de emergência dentro da validade', ''),
        ('Checklist diário do carrinho realizado', ''),
        ('Desfibrilador testado e operacional', ''),
        ('Laringoscópio testado e operacional', ''),
        ('Material de intubação disponível e conferido', ''),
        ('Oxigênio e dispositivos disponíveis e funcionantes', ''),
        ('Equipe conhece o fluxo de atendimento às emergências', ''),
    ]),
    ('MEDICAMENTOS E MATERIAIS', [
        ('Armazenamento de medicamentos adequado', ''),
        ('Controle de validade de medicamentos e materiais', ''),
        ('Multidoses identificadas com data de abertura e validade', ''),
        ('Medicamentos de alta vigilância identificados e controlados', ''),
        ('Diluições padronizadas disponíveis', ''),
        ('Estoque de itens críticos monitorado', ''),
        ('Ausência de medicamentos/materiais vencidos', ''),
        ('Controle de temperatura quando aplicável', ''),
    ]),
    ('PREVENÇÃO E CONTROLE DE INFECÇÕES', [
        ('Higienização das mãos conforme boas práticas', ''),
        ('Preparação alcoólica disponível nos pontos necessários', ''),
        ('Uso adequado de EPIs', ''),
        ('Precauções padrão e específicas implantadas', ''),
        ('Técnica asséptica nos procedimentos invasivos', ''),
        ('Limpeza/desinfecção de equipamentos assistenciais', ''),
        ('Equipos, almotolias e frascos identificados', ''),
        ('Bundles aplicáveis implantados e monitorados', ''),
        ('Limpeza terminal registrada quando aplicável', ''),
        ('Interface com SCIH/CCIH e acompanhamento de IRAS quando aplicável', ''),
    ]),
    ('EDUCAÇÃO PERMANENTE', [
        ('Cronograma anual de treinamentos disponível', ''),
        ('Treinamentos previstos realizados', ''),
        ('Listas de presença e evidências arquivadas', ''),
        ('Integração de novos profissionais realizada', ''),
        ('Treinamentos definidos a partir de incidentes/NC executados', ''),
    ]),
    ('INDICADORES DE ENFERMAGEM', [
        ('Quedas', ''),
        ('Lesão por pressão', ''),
        ('Erros/incidentes relacionados a medicamentos', ''),
        ('Eventos adversos', ''),
        ('Flebite e complicações de acesso, quando aplicável', ''),
        ('Perda de dispositivos, quando aplicável', ''),
        ('Absenteísmo da equipe', ''),
        ('Treinamentos realizados', ''),
        ('Conformidade dos prontuários', ''),
        ('Outros indicadores pertinentes ao perfil da unidade', ''),
    ]),
]

# Estrutura final: lista de grupos, cada um com itens numerados globalmente.
GRUPOS = []
_num = 0
for _gi, (_nome, _itens) in enumerate(GRUPOS_BRUTOS, start=1):
    _lista = []
    for _ii, (_texto, _previsto) in enumerate(_itens, start=1):
        _num += 1
        _lista.append({"num": _num, "ref": str(_num), "texto": _texto, "previsto": _previsto})
    GRUPOS.append({"nome": _nome, "itens": _lista})

TOTAL_ITENS = _num

COLUNAS_VISITA = [
    "Código da Visita", "Hospital", "Cidade", "UF", "Edital / Processo", "Data da Visita",
    "Responsável pela Visita", "Nome de Quem Acompanhou", "Início do Preenchimento",
    "Fim do Preenchimento (Envio)", "Status da Visita", "Total de Itens Avaliados",
    "Total OK", "Total Parcial", "Total Não", "Total N/A", "Total Não Preenchido",
    "Percentual de OK", "Total de Anexos",
    "RT de Enfermagem", "Gestor da Unidade", "Perfil da Unidade", "Horário", "Módulos Específicos Aplicáveis",
]

COLUNAS_ITEM = [
    "Código da Visita", "Hospital", "Data da Visita", "Grupo", "Nº do Item", "Ref.",
    "Item a Verificar", "Previsto no TR / Apêndices (sugerido)", "Previsto informado pelo auditor",
    "Situação", "Observação", "Qtde de Anexos", "Respondido em",
]

COLUNAS_EVIDENCIA = [
    "Código da Visita", "Hospital", "Nº do Item", "Ref.", "Arquivo", "Tipo",
    "Tamanho (KB)", "Enviado em", "Link / Caminho",
]


def agora_brasilia() -> datetime:
    return datetime.now(FUSO_BRASILIA)


def chave_hospital(nome: str) -> str:
    """Chave de comparacao do nome do hospital: sem acentos, minuscula e sem
    espacos repetidos - 'Hospital  Sao Jose' == 'hospital são josé'."""
    nfkd = unicodedata.normalize("NFKD", nome or "")
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()


def sigla_hospital(nome: str) -> str:
    """Ate 8 letras/numeros maiusculos para compor o codigo da visita."""
    nfkd = unicodedata.normalize("NFKD", nome or "")
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    palavras = [p for p in re.split(r"[^A-Za-z0-9]+", sem_acento) if p and p.lower() not in ("de", "da", "do", "das", "dos", "e")]
    base = "".join(p[0] for p in palavras)[:6] or "HOSP"
    return base.upper()


def gerar_codigo_visita(hospital: str) -> str:
    """Formato: ENF-<SIGLA>-<AAAAMMDD>-<4 hex> (ex.: ENF-HRJPA-20261008-A3F9)."""
    import uuid
    return f"ENF-{sigla_hospital(hospital)}-{agora_brasilia().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
