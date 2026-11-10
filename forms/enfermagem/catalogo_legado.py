# -*- coding: utf-8 -*-
"""Catalogo ANTERIOR da Visita Tecnica de Enfermagem (43 itens, 11 grupos), usado so para ler
o historico de visitas feitas antes do padrao de 10/11/2026 (74 itens). Nao use para novas visitas."""
_BRUTOS = [
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


GRUPOS = []
_num = 0
for _gi, (_nome, _itens) in enumerate(_BRUTOS, start=1):
    _lista = []
    for _ii, (_texto, _previsto) in enumerate(_itens, start=1):
        _num += 1
        _lista.append({"num": _num, "ref": f"{_gi}.{_ii}", "texto": _texto, "previsto": _previsto})
    GRUPOS.append({"nome": _nome, "itens": _lista})
TOTAL_ITENS = _num
