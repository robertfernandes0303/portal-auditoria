# -*- coding: utf-8 -*-
"""
schema.py - Checklist de Visita Técnica · SESMT (Segurança e Medicina do Trabalho) das unidades hospitalares, São Lucas Instituto.

Fonte: planilha "Checklist SESMT Hospitalar · NR-01" (Padrão Enfermagem) enviada pela Célula de Qualidade: 18 grupos e 156 itens.
O Nº do item da planilha é a CHAVE ESTÁVEL que liga os dados históricos ao catálogo. Nunca renumere; item novo recebe número novo
(depois do último), mesmo que apareça no meio de um grupo.

Respostas (como na planilha): Conforme, Não conforme, Não se aplica. Internamente reaproveitam as constantes da Enfermagem
(OK = Conforme, NAO = Não conforme, NA = Não se aplica); não existe "Parcial". Na planilha gravada o texto é o da tela.
"""
import re
import unicodedata
from datetime import datetime, timedelta, timezone

UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]

FUSO_BRASILIA = timezone(timedelta(hours=-3))

OK = "OK"
NAO = "Não"
NA = "N/A"
PARCIAL = "Parcial"             # não é oferecido no SESMT; mantido só para o código compartilhado
OPCOES_SITUACAO = [OK, NAO, NA]
ROTULOS = {OK: "Conforme", NAO: "Não conforme", NA: "Não se aplica"}

# Limites de anexo (evidência) — iguais aos demais formulários de visita técnica
EXTENSOES_PERMITIDAS = ["jpg", "jpeg", "png", "pdf"]
MAX_ANEXOS_POR_ITEM = 20
MAX_MB_IMAGEM_ENTRADA = 20
MAX_MB_PDF = 10
LADO_MAX_IMAGEM_PX = 1600
QUALIDADE_JPEG = 80

# (nome do grupo, [texto do item, ...]) — na ordem e com os textos da planilha do SESMT
GRUPOS_BRUTOS = [('IDENTIFICAÇÃO E GESTÃO DO SESMT',
  ['SESMT dimensionado/organizado conforme realidade e enquadramento da unidade',
   'Responsáveis do SESMT formalmente definidos e contatos disponíveis',
   'Rotina de inspeções de segurança estabelecida e com registros',
   'Pendências de inspeções anteriores acompanhadas até a conclusão',
   'Indicadores mensais de SST atualizados e apresentados à gestão',
   'Plano de trabalho/prioridades do SESMT definido para a unidade',
   'Registros e evidências de SST organizados e rastreáveis',
   'Comunicação entre SESMT, gestão, RH/DP, CCIH, NSP e lideranças funcionando']),
 ('PGR / GRO E INVENTÁRIO DE RISCOS',
  ['PGR vigente e disponível na unidade, elaborado e mantido em conformidade com a NR-01 (GRO/PGR)',
   'Plano de Ação do PGR, conforme NR-01, vigente, atualizado e com evidências de implementação e acompanhamento das medidas previstas na prática.',
   'Plano de ação do PGR atualizado, com responsáveis e prazos',
   'Riscos físicos identificados e avaliados quando aplicável',
   'Riscos químicos identificados e avaliados quando aplicável',
   'Riscos biológicos identificados e avaliados',
   'Riscos ergonômicos identificados e tratados',
   'Riscos de acidentes identificados e tratados',
   'Mudanças de processo, estrutura, equipamentos ou atividades incorporadas ao gerenciamento de riscos',
   'Medidas de prevenção implantadas acompanhadas quanto à eficácia']),
 ('PCMSO, ASO E SAÚDE OCUPACIONAL',
  ['PCMSO vigente e articulado com os riscos ocupacionais da unidade',
   'ASOs admissionais realizados e válidos',
   'ASOs periódicos realizados dentro do prazo',
   'ASOs de retorno ao trabalho realizados quando aplicável',
   'ASOs de mudança de risco ocupacional realizados quando aplicável',
   'ASOs demissionais realizados quando aplicável',
   'Exames complementares ocupacionais compatíveis com os riscos',
   'Restrições/recomendações ocupacionais comunicadas e acompanhadas de forma sigilosa',
   'Vacinação ocupacional dos trabalhadores expostos acompanhada',
   'Controle de afastamentos e retorno ao trabalho articulado com RH/DP e medicina ocupacional']),
 ('ACIDENTES, INCIDENTES E EXPOSIÇÃO A MATERIAL BIOLÓGICO',
  ['Fluxo de comunicação de acidentes de trabalho conhecido pelas lideranças',
   'Acidentes e incidentes registrados e investigados',
   'CAT emitida dentro do prazo quando aplicável',
   'Notificações compulsórias/SINAN realizadas quando aplicável',
   'Protocolo de exposição ocupacional a material biológico disponível e conhecido',
   'Atendimento pós-exposição acessível e com fluxo definido',
   'Paciente-fonte e trabalhador exposto avaliados conforme protocolo aplicável',
   'PEP para HIV disponível/encaminhada em tempo oportuno quando indicada',
   'Acompanhamento sorológico pós-exposição registrado conforme protocolo',
   'Análise de causa e plano de ação realizados após acidentes',
   'Reincidências de acidentes monitoradas']),
 ('EPI - EQUIPAMENTOS DE PROTEÇÃO INDIVIDUAL',
  ['Levantamento de EPIs necessários por função/risco atualizado',
   'EPIs possuem CA válido quando aplicável',
   'EPIs disponíveis em quantidade suficiente',
   'Entrega de EPI registrada individualmente',
   'Substituição de EPI danificado/desgastado ocorre em tempo adequado',
   'Colaboradores orientados quanto ao uso, guarda, higienização e conservação',
   'Uso de EPI observado durante as atividades',
   'EPIs específicos disponíveis para limpeza, lavanderia, nutrição, manutenção e áreas assistenciais',
   'Proteção ocular/facial disponível para atividades com risco de respingos',
   'Luvas adequadas ao risco e à atividade, sem substituições incompatíveis',
   'Calçados ocupacionais adequados aos riscos das funções',
   'Pendências de EPI acompanhadas até entrega/regularização']),
 ('NR-32 E SEGURANÇA EM SERVIÇOS DE SAÚDE',
  ['Trabalhadores conhecem os riscos biológicos de suas atividades',
   'Proibição de reencape e desconexão manual indevida de agulhas é cumprida',
   'Perfurocortantes são descartados imediatamente após o uso',
   'Coletor de perfurocortante está disponível próximo ao local de geração',
   'Coletores de perfurocortantes não ultrapassam o limite de enchimento',
   'Dispositivos de segurança são utilizados quando previstos/aplicáveis',
   'Ausência de adornos nas áreas em que a restrição é aplicável',
   'Alimentos e bebidas não são armazenados/consumidos em áreas assistenciais impróprias',
   'Calçados fechados são utilizados nas áreas de risco',
   'Trabalhadores recebem capacitação relacionada aos riscos do serviço de saúde',
   'Materiais biológicos são transportados em recipientes adequados e seguros']),
 ('PRODUTOS QUÍMICOS E SANEANTES',
  ['Produtos químicos/saneantes estão identificados e rotulados',
   'FDS/FISPQ dos produtos está disponível e acessível',
   'Produtos incompatíveis são armazenados separadamente quando necessário',
   'Diluições são realizadas conforme orientação do fabricante/procedimento',
   'Frascos de uso estão identificados, sem reutilização inadequada de embalagens',
   'EPIs para manipulação de produtos químicos estão disponíveis',
   'Local de armazenamento é ventilado, organizado e com acesso controlado quando necessário',
   'Equipe conhece conduta para derramamento, contato e intoxicação']),
 ('RESÍDUOS E PERFUROCORTANTES',
  ['PGRSS disponível e aplicado em interface com SST',
   'Segregação de resíduos ocorre no ponto de geração',
   'Lixeiras e recipientes estão identificados e adequados',
   'Resíduos infectantes são acondicionados corretamente',
   'Perfurocortantes são descartados em coletores apropriados',
   'Coleta interna é realizada com método e equipamentos seguros',
   'Trabalhadores da coleta utilizam EPIs adequados',
   'Abrigo de resíduos apresenta condições seguras de acesso e operação',
   'Fluxo de resíduos evita exposição desnecessária de trabalhadores e usuários']),
 ('ERGONOMIA E MOVIMENTAÇÃO DE PACIENTES/CARGAS',
  ['Riscos ergonômicos das funções foram identificados',
   'Postos administrativos possuem condições ergonômicas adequadas',
   'Altura de bancadas e superfícies de trabalho é adequada ou possui medidas de controle',
   'Cadeiras e assentos estão em condições seguras e adequadas',
   'Movimentação/transferência de pacientes é realizada com técnica e recursos adequados',
   'Macas, cadeiras de rodas e equipamentos de transporte estão conservados',
   'Movimentação manual de cargas possui orientação e medidas de prevenção',
   'Queixas ergonômicas e situações de sobrecarga são registradas e tratadas']),
 ('SEGURANÇA CONTRA INCÊNDIO E EMERGÊNCIAS',
  ['Extintores estão acessíveis, sinalizados e dentro da validade',
   'Rotas de fuga estão desobstruídas e sinalizadas',
   'Saídas de emergência estão livres e funcionais',
   'Iluminação de emergência está funcionando',
   'Sinalização de emergência está visível',
   'Brigada de emergência está constituída/treinada conforme aplicável',
   'Plano de emergência/abandono está disponível e conhecido',
   'Simulados ou exercícios de emergência são realizados conforme planejamento',
   'Materiais combustíveis não obstruem quadros elétricos, rotas ou equipamentos de combate a incêndio']),
 ('INSTALAÇÕES, MANUTENÇÃO E SEGURANÇA ELÉTRICA',
  ['Pisos estão íntegros, sem buracos, desníveis ou risco de queda',
   'Corredores e áreas de circulação estão desobstruídos',
   'Ralos, tampas, grelhas e aberturas apresentam condição segura',
   'Tomadas, interruptores e espelhos estão íntegros',
   'Ausência de fios expostos, emendas improvisadas ou extensões inadequadas',
   'Quadros elétricos estão identificados, fechados e com acesso desobstruído',
   'Manutenções preventivas relacionadas à segurança estão em dia',
   'Ordens de serviço de riscos de SST possuem acompanhamento e prazo',
   'Equipamentos danificados/inseguros são retirados de uso ou sinalizados até correção']),
 ('GASES MEDICINAIS E CILINDROS',
  ['Central de gases apresenta condições seguras de acesso e armazenamento',
   'Cilindros estão identificados quanto ao conteúdo/condição',
   'Cilindros estão fixados contra queda',
   'Cilindros cheios e vazios são segregados/identificados',
   'Transporte de cilindros é realizado com carrinho adequado e proteção',
   'Fontes de ignição e materiais incompatíveis são controlados na área',
   'Plano de contingência para falha/falta de gases medicinais é conhecido']),
 ('RADIOLOGIA E RADIAÇÕES IONIZANTES',
  ['Programa/documentação de proteção radiológica aplicável está disponível e atualizado',
   'Trabalhadores ocupacionalmente expostos utilizam dosimetria quando aplicável',
   'Dosímetros são utilizados, armazenados e enviados conforme rotina definida',
   'Sinalização de radiação e controle de acesso estão adequados',
   'EPIs de proteção radiológica estão íntegros e armazenados corretamente',
   'Manutenções e testes dos equipamentos estão atualizados',
   'Orientações de segurança para gestantes e demais trabalhadores estão definidas']),
 ('LAVANDERIA, HIGIENE, NUTRIÇÃO E APOIO',
  ['Fluxo de roupa suja e limpa reduz risco de exposição ocupacional',
   'Área suja da lavanderia possui EPIs e barreiras adequadas',
   'Transporte de roupa suja é realizado em recipientes/carrinhos adequados',
   'Equipe de higienização utiliza EPIs compatíveis com cada atividade',
   'DML está organizado e sem riscos de queda/exposição química',
   'Na cozinha, há proteção adequada contra cortes, calor e escorregamentos',
   'Equipamentos de cozinha possuem condições seguras de uso e proteção',
   'Calçados antiderrapantes são utilizados onde há risco de piso molhado/escorregadio']),
 ('TREINAMENTOS, DDS E CULTURA DE SEGURANÇA',
  ['Treinamento admissional de SST é realizado e registrado',
   'Treinamentos obrigatórios aplicáveis estão dentro da validade',
   'DDS é realizado conforme rotina definida e com registro',
   'Conteúdos de DDS são compatíveis com riscos e ocorrências da unidade',
   'Lideranças participam das ações preventivas de SST',
   'Campanhas de prevenção possuem evidências e lista de participação',
   'Trabalhadores sabem como comunicar risco, incidente e acidente',
   'Novos procedimentos/equipamentos geram orientação prévia aos trabalhadores']),
 ('CIPA E PARTICIPAÇÃO DOS TRABALHADORES',
  ['CIPA está constituída quando aplicável e documentação está organizada',
   'Reuniões da CIPA ocorrem conforme planejamento e possuem atas',
   'Pendências apontadas pela CIPA são acompanhadas',
   'Mapa/percepção de riscos e participação dos trabalhadores são considerados nas ações',
   'Processo eleitoral, designações e treinamentos estão documentados quando aplicáveis']),
 ('TERCEIROS E PRESTADORES DE SERVIÇO',
  ['Terceiros recebem orientações de segurança antes/início das atividades',
   'Documentação de SST de terceiros é verificada conforme risco/contrato',
   'EPIs e medidas de controle dos terceiros são fiscalizados',
   'Serviços de manutenção/obra possuem isolamento e sinalização adequados',
   'Acidentes com terceirizados possuem fluxo de comunicação definido',
   'Atividades críticas possuem autorização/procedimento quando aplicável']),
 ('DOCUMENTOS, REGISTROS E INDICADORES',
  ['POPs do SESMT estão atualizados, aprovados e disponíveis',
   'Registros de inspeção possuem data, setor, evidência e responsável',
   'Planos de ação possuem criticidade, responsável, prazo e status',
   'Fotos/evidências de antes e depois estão organizadas',
   'Controle de entrega de EPI está atualizado',
   'Controle de treinamentos e DDS está atualizado',
   'Controle de acidentes/incidentes está atualizado',
   'Dias sem acidentes e demais indicadores definidos estão atualizados',
   'Pendências críticas são comunicadas formalmente à gestão',
   'Rechecagem das não conformidades é registrada'])]

# Estrutura final: lista de grupos, cada um com itens numerados globalmente (Nº da planilha).
GRUPOS = []
_num = 0
for _gi, (_nome, _itens) in enumerate(GRUPOS_BRUTOS, start=1):
    _lista = []
    for _ii, _texto in enumerate(_itens, start=1):
        _num += 1
        _lista.append({"num": _num, "ref": f"{_gi}.{_ii}", "texto": _texto, "previsto": ""})
    GRUPOS.append({"nome": _nome, "itens": _lista})

TOTAL_ITENS = _num


COLUNAS_VISITA = [
    "Código da Visita", "Unidade", "Cidade", "UF", "Data da Visita",
    "Responsável pela Visita", "Nome de Quem Acompanhou", "Início do Preenchimento",
    "Fim do Preenchimento (Envio)", "Status da Visita", "Total de Itens Avaliados",
    "Total Conforme", "Total Não Conforme", "Total Não se Aplica", "Total Não Preenchido",
    "Percentual de Conformidade", "Total de Anexos",
]

COLUNAS_ITEM = [
    "Código da Visita", "Unidade", "Data da Visita", "Grupo", "Nº do Item", "Ref.",
    "Item de Verificação", "Situação", "Observação", "Qtde de Anexos", "Respondido em",
]

COLUNAS_EVIDENCIA = [
    "Código da Visita", "Unidade", "Nº do Item", "Ref.", "Arquivo", "Tipo",
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
    """Formato: SES-<SIGLA>-<AAAAMMDD>-<4 hex> (ex.: SES-JUINA-20261110-A3F9)."""
    import uuid
    return f"SES-{sigla_hospital(hospital)}-{agora_brasilia().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
