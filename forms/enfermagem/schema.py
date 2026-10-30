# -*- coding: utf-8 -*-
"""
schema.py - Checklist de Visita Tecnica de Enfermagem (Sao Lucas Instituto)

Catalogo de grupos e itens + constantes + colunas das planilhas.

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

# Limites de anexo (evidencia)
EXTENSOES_PERMITIDAS = ["jpg", "jpeg", "png", "pdf"]
MAX_ANEXOS_POR_ITEM = 20
MAX_MB_IMAGEM_ENTRADA = 20
MAX_MB_PDF = 10
LADO_MAX_IMAGEM_PX = 1600
QUALIDADE_JPEG = 80

# (nome do grupo, [(texto do item, previsto no TR / apendices sugerido), ...])
GRUPOS_BRUTOS = [
    ('1. Gestão e responsabilidade técnica da enfermagem', [
        ('Confirmar a existência de enfermeiro responsável técnico (RT) com registro ativo no COREN e a formalização da designação.',
         'Lei 7.498/1986 e normas COFEN/COREN: serviço de enfermagem sob responsabilidade de enfermeiro habilitado. Confirmar exigência específica do TR.'),
        ('Verificar a existência de organograma, regimento ou manual do serviço de enfermagem e de POPs atualizados.',
         'Apêndice/TR: organização técnica e assistencial formalizada. Confirmar no documento do hospital.'),
        ('Verificar a existência e o funcionamento de comissões ligadas à enfermagem (ex.: padronização, ética, educação permanente).',
         'A definir conforme TR/hospital.'),
        ('Verificar a disponibilidade de registro dos profissionais ativos (COREN) e controle de vencimento.',
         'Resolução COFEN aplicável; confirmar controle in loco.'),
    ]),
    ('2. Dimensionamento e escalas', [
        ('Confirmar o quantitativo de enfermeiros por setor e por turno (atual).',
         'Resolução COFEN 543/2017 (dimensionamento) e quantitativo mínimo do TR, se fixado.'),
        ('Confirmar o quantitativo de técnicos e auxiliares de enfermagem por setor e por turno (atual).',
         'Resolução COFEN 543/2017; proporção enfermeiro/técnico conforme perfil assistencial.'),
        ('Verificar a existência de escalas formalizadas, cobertura de faltas, férias e afastamentos.',
         'TR: continuidade da assistência e equipe suficiente.'),
        ('Verificar o vínculo dos profissionais (próprio, terceirizado, cooperativa, plantonista) e o valor praticado por categoria.',
         'A confirmar; subsidia a proposta.'),
        ('Verificar o índice de absenteísmo, rotatividade e uso de horas extras ou banco de horas.',
         'Informação gerencial; sem referência numérica no TR.'),
    ]),
    ('3. Pronto atendimento / urgência e emergência', [
        ('Verificar o acolhimento com classificação de risco: local, protocolo adotado, enfermeiro classificador por turno.',
         'Política Nacional de Humanização; protocolo de classificação de risco. Confirmar exigência do TR.'),
        ('Verificar a equipe de enfermagem da sala de emergência/estabilização por turno.',
         'TR: equipe compatível com o perfil do serviço.'),
        ('Verificar carrinho de emergência: lacre, checagem periódica, medicamentos e materiais dentro do prazo.',
         'Apêndice: carros de emergência disponíveis e funcionantes.'),
        ('Verificar a sala de medicação, observação e procedimentos (curativo, nebulização) quanto a estrutura e rotina de enfermagem.',
         'Quantitativo de salas previsto no TR, quando houver.'),
    ]),
    ('4. Internação / enfermarias', [
        ('Verificar a aplicação da Sistematização da Assistência de Enfermagem (SAE/Processo de Enfermagem) e seus registros.',
         'Resolução COFEN 358/2009.'),
        ('Verificar a passagem de plantão estruturada e o registro em prontuário.',
         'Boas práticas de segurança do paciente.'),
        ('Verificar a distribuição dos leitos por enfermaria e a relação paciente/profissional.',
         'Total de leitos e distribuição previstos no TR.'),
        ('Verificar a rotina de sinais vitais, balanço hídrico e escalas de risco (queda, lesão por pressão).',
         'Protocolos de segurança do paciente (MS/ANVISA).'),
    ]),
    ('5. UTI / cuidados críticos', [
        ('Confirmar o número de leitos de UTI ativos e a equipe de enfermagem por turno.',
         'RDC 7/2010 e Resolução COFEN 543/2017; leitos de UTI previstos no TR.'),
        ('Verificar a existência de enfermeiro coordenador/RT da UTI.',
         'RDC 7/2010.'),
        ('Verificar a rotina de cuidados críticos: bundles de prevenção de infecção, balanço hídrico, sedação e ventilação.',
         'Protocolos assistenciais; confirmar adoção.'),
        ('Verificar monitores, ventiladores, bombas de infusão e rotina de checagem pela enfermagem.',
         'Apêndice: equipamentos disponíveis e funcionantes.'),
    ]),
    ('6. Centro cirúrgico / RPA / CME (interface de enfermagem)', [
        ('Verificar a equipe de enfermagem do centro cirúrgico (circulante, instrumentador) por turno.',
         'TR: equipe compatível com o perfil e metas cirúrgicas.'),
        ('Verificar a aplicação da lista de verificação de cirurgia segura.',
         'Protocolo de Cirurgia Segura (MS/ANVISA).'),
        ('Verificar a equipe e a capacidade da RPA, com monitorização e rotina de alta da sala.',
         'Vagas/leitos de RPA previstos no TR.'),
        ('Verificar a interface com a CME: rastreabilidade de materiais, rotina de entrega e recebimento.',
         'RDC 15/2012.'),
    ]),
    ('7. Obstetrícia e neonatal', [
        ('Verificar a equipe de enfermagem (incluindo enfermeiro obstetra, se houver) em pré-parto, parto e pós-parto.',
         'TR: assistência materno-infantil conforme perfil.'),
        ('Verificar a assistência imediata ao recém-nascido e a disponibilidade de materiais de reanimação.',
         'Apêndice: equipamentos de emergência disponíveis.'),
        ('Verificar a equipe de enfermagem neonatal e a rotina de cuidados e identificação do RN.',
         'A confirmar conforme perfil do hospital.'),
    ]),
    ('8. Segurança do paciente e medicação', [
        ('Verificar o Núcleo de Segurança do Paciente e a notificação de eventos adversos.',
         'RDC 36/2013; Portaria MS 529/2013.'),
        ('Verificar a identificação do paciente (pulseira e protocolo).',
         'Protocolo de identificação do paciente.'),
        ('Verificar o processo de prescrição, preparo e administração de medicamentos (dupla checagem de alta vigilância).',
         'Apêndice 1, 2.1: segurança na prescrição, preparo, dispensação e administração.'),
        ('Verificar a prevenção de quedas e de lesão por pressão (escalas e registro).',
         'Protocolos de segurança do paciente.'),
        ('Verificar a higienização das mãos: insumos, adesão e monitoramento.',
         'Protocolo de higiene das mãos (ANVISA).'),
    ]),
    ('9. Biossegurança e controle de infecção', [
        ('Verificar a disponibilidade de EPI e a rotina de reposição.',
         'NR-32.'),
        ('Verificar a vacinação e o acompanhamento de saúde ocupacional da equipe de enfermagem.',
         'NR-32; PCMSO.'),
        ('Verificar a segregação e o descarte de resíduos e perfurocortantes nos postos de enfermagem.',
         'RDC 222/2018 e NR-32.'),
        ('Verificar a articulação com a CCIH: precauções e isolamentos.',
         'RDC 36/2013; legislação de CCIH.'),
    ]),
    ('10. Materiais, equipamentos e insumos de enfermagem', [
        ('Verificar a disponibilidade de materiais e insumos de uso diário (curativo, acesso venoso, sondas).',
         'Apêndice: insumos essenciais disponíveis.'),
        ('Verificar bombas de infusão, monitores, oxímetros, glicosímetros e aspiradores por setor (quantidade e funcionamento).',
         'Apêndice 1, 2.3.'),
        ('Verificar o fluxo de solicitação e dispensação de materiais e medicamentos (farmácia/almoxarifado).',
         'Apêndice 1, 2.1.'),
    ]),
    ('11. Educação permanente, registros e documentação', [
        ('Verificar o programa de educação permanente, treinamentos e registro de participação.',
         'TR: equipes qualificadas.'),
        ('Verificar o tipo de prontuário (eletrônico, físico, híbrido) e a qualidade dos registros de enfermagem.',
         'Apêndice 1, 2.1: registros rastreáveis.'),
        ('Verificar os indicadores de enfermagem acompanhados (quedas, LPP, flebite, eventos adversos).',
         'Apêndice 2: indicadores, quando houver.'),
    ]),
]

# Estrutura final: lista de grupos, cada um com itens numerados globalmente.
GRUPOS = []
_num = 0
for _gi, (_nome, _itens) in enumerate(GRUPOS_BRUTOS, start=1):
    _lista = []
    for _ii, (_texto, _previsto) in enumerate(_itens, start=1):
        _num += 1
        _lista.append({"num": _num, "ref": f"{_gi}.{_ii}", "texto": _texto, "previsto": _previsto})
    GRUPOS.append({"nome": _nome, "itens": _lista})

TOTAL_ITENS = _num

COLUNAS_VISITA = [
    "Código da Visita", "Hospital", "Cidade", "UF", "Edital / Processo", "Data da Visita",
    "Responsável pela Visita", "Nome de Quem Acompanhou", "Início do Preenchimento",
    "Fim do Preenchimento (Envio)", "Status da Visita", "Total de Itens Avaliados",
    "Total OK", "Total Parcial", "Total Não", "Total N/A", "Total Não Preenchido",
    "Percentual de OK", "Total de Anexos",
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
