# -*- coding: utf-8 -*-
"""
schema.py
Fonte única da verdade do Checklist de Visita Institucional (auditoria).

Baseado no arquivo "Checklist_Visita_Institucional_Sao_Lucas.xlsx" enviado
pelo usuário: 26 seções, 251 itens. A seção "CAPACIDADE E OCUPAÇÃO" é do
tipo "quantidade" (resposta livre: número inteiro, percentual ou texto,
todos opcionais/podem ficar em branco). As demais 25 seções são do tipo
"checklist" (Conforme / Não Conforme / Não se Aplica + Observações), e
para finalizar uma seção checklist todo item precisa de uma resposta —
"Não se Aplica" é a forma correta de pular um item que não existe naquela
unidade.

Mesmo padrão do projeto "Canal de Eventos Adversos": 14 unidades, 1 arquivo/
planilha por unidade + 1 consolidado.
"""
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Fuso de Brasília (UTC-3), independente do fuso do servidor de hospedagem —
# mesmo racional do projeto de Eventos Adversos.
# ---------------------------------------------------------------------------
FUSO_BRASILIA = timezone(timedelta(hours=-3))


def agora_brasilia() -> datetime:
    return datetime.now(FUSO_BRASILIA)


# ---------------------------------------------------------------------------
# 14 unidades (mesma lista do Canal de Eventos Adversos — ajustar aqui se a
# lista de unidades auditadas for diferente).
# ---------------------------------------------------------------------------
UNIDADES = [
    "Aripuanã",
    "Campo Novo do Parecis - CAPS",
    "Campo Verde",
    "Guarantã do Norte",
    "Juína",
    "Juscimeira",
    "Pedro de Toledo",
    "Pontes e Lacerda",
    "São José do Rio Claro - Hospital",
    "São José do Rio Claro - PAM",
    "São Lourenço da Serra",
    "Sumaré - Área Cura",
    "Sumaré - Macarenko",
    "Sumaré - Matão",
]

# ---------------------------------------------------------------------------
# Opções de resposta dos itens de checklist
# ---------------------------------------------------------------------------
CONFORME = "Conforme"
NAO_CONFORME = "Não Conforme"
NAO_SE_APLICA = "Não se Aplica"
OPCOES_CHECKLIST = [CONFORME, NAO_CONFORME, NAO_SE_APLICA]

SECOES = [
    {
        "nome": "CAPACIDADE E OCUPAÇÃO",
        "tipo": "quantidade",
        "itens": [
            {"num": 1, "texto": "Número de leitos de internação contratados", "tipo_resposta": "numero_inteiro"},
            {"num": 2, "texto": "Número de leitos de internação instalados/ativos", "tipo_resposta": "numero_inteiro"},
            {"num": 3, "texto": "Número de leitos de observação", "tipo_resposta": "numero_inteiro"},
            {"num": 4, "texto": "Número de leitos bloqueados/interditados", "tipo_resposta": "numero_inteiro"},
            {"num": 5, "texto": "Número de pacientes internados no momento da visita", "tipo_resposta": "numero_inteiro"},
            {"num": 6, "texto": "Número de pacientes em observação", "tipo_resposta": "numero_inteiro"},
            {"num": 7, "texto": "Pacientes aguardando internação", "tipo_resposta": "numero_inteiro"},
            {"num": 8, "texto": "Pacientes aguardando transferência", "tipo_resposta": "numero_inteiro"},
            {"num": 9, "texto": "Taxa de ocupação no momento da visita", "tipo_resposta": "numero_percentual"},
            {"num": 10, "texto": "Motivo de eventual bloqueio de leitos", "tipo_resposta": "texto_livre"},
        ],
    },
    {
        "nome": "RECEPÇÃO E CONTROLE DE ACESSO",
        "tipo": "checklist",
        "itens": [
            {"num": 11, "texto": "Organização e limpeza da recepção"},
            {"num": 12, "texto": "Acolhimento e orientação ao usuário"},
            {"num": 13, "texto": "Fluxo de atendimento organizado"},
            {"num": 14, "texto": "Controle de entrada e saída"},
            {"num": 15, "texto": "Identificação de visitantes, acompanhantes e prestadores"},
            {"num": 16, "texto": "Controle de acesso às áreas restritas"},
            {"num": 17, "texto": "Câmeras de monitoramento funcionando"},
            {"num": 18, "texto": "Cobertura adequada das câmeras e armazenamento das imagens"},
            {"num": 19, "texto": "Acessibilidade adequada"},
        ],
    },
    {
        "nome": "COMUNICAÇÃO VISUAL E TRANSPARÊNCIA",
        "tipo": "checklist",
        "itens": [
            {"num": 20, "texto": "Placa de horário de visitas instalada, visível e atualizada"},
            {"num": 21, "texto": "Gestão à Vista instalada e atualizada"},
            {"num": 22, "texto": "Placa de gratuidade dos serviços SUS visível"},
            {"num": 23, "texto": "Placas/orientações sobre prevenção de IRAS (Infecções Relacionadas à Assistência à Saúde)"},
            {"num": 24, "texto": "Orientações sobre higienização das mãos"},
            {"num": 25, "texto": "Direitos e deveres dos usuários disponíveis"},
            {"num": 26, "texto": "Canais da Ouvidoria disponíveis e atualizados"},
            {"num": 27, "texto": "Setores devidamente identificados"},
            {"num": 28, "texto": "Sinalização de emergência e rotas de fuga"},
            {"num": 29, "texto": "Identidade visual São Lucas adequada"},
            {"num": 30, "texto": "Murais e comunicados atualizados"},
        ],
    },
    {
        "nome": "ESCALAS E RECURSOS HUMANOS",
        "tipo": "checklist",
        "itens": [
            {"num": 31, "texto": "Escalas de trabalho à vista"},
            {"num": 32, "texto": "Escalas atualizadas"},
            {"num": 33, "texto": "Escalas devidamente assinadas"},
            {"num": 34, "texto": "Escala médica completa"},
            {"num": 35, "texto": "Escala de enfermagem completa"},
            {"num": 36, "texto": "Escalas das demais equipes assistenciais"},
            {"num": 37, "texto": "Profissionais presentes compatíveis com a escala"},
            {"num": 38, "texto": "Dimensionamento adequado à demanda"},
            {"num": 39, "texto": "Cobertura de faltas/afastamentos organizada"},
            {"num": 40, "texto": "Crachás e uniformes adequados"},
            {"num": 41, "texto": "Documentação profissional válida"},
            {"num": 42, "texto": "Treinamentos obrigatórios atualizados"},
            {"num": 43, "texto": "Controle de frequência realizado"},
            {"num": 44, "texto": "Absenteísmo e horas extras acompanhados"},
        ],
    },
    {
        "nome": "CORPO MÉDICO",
        "tipo": "checklist",
        "itens": [
            {"num": 45, "texto": "Cobertura dos plantões"},
            {"num": 46, "texto": "Pontualidade"},
            {"num": 47, "texto": "Especialidades compatíveis com o contrato"},
            {"num": 48, "texto": "Documentação profissional regular"},
            {"num": 49, "texto": "Registros médicos adequados em prontuário"},
            {"num": 50, "texto": "Prescrições devidamente preenchidas/assinadas"},
            {"num": 51, "texto": "Produção médica acompanhada"},
            {"num": 52, "texto": "Protocolos assistenciais conhecidos e aplicados"},
            {"num": 53, "texto": "Passagem de plantão adequada"},
        ],
    },
    {
        "nome": "ENFERMAGEM",
        "tipo": "checklist",
        "itens": [
            {"num": 54, "texto": "Dimensionamento adequado"},
            {"num": 55, "texto": "Cobertura das escalas"},
            {"num": 56, "texto": "Postos de enfermagem organizados"},
            {"num": 57, "texto": "Prontuário e registros assistenciais adequados"},
            {"num": 58, "texto": "Identificação segura do paciente"},
            {"num": 59, "texto": "Administração e checagem de medicamentos adequada"},
            {"num": 60, "texto": "Protocolos assistenciais disponíveis"},
            {"num": 61, "texto": "Carrinho de emergência conferido, lacrado e registrado"},
            {"num": 62, "texto": "Materiais e equipamentos disponíveis"},
            {"num": 63, "texto": "Passagem de plantão adequada"},
        ],
    },
    {
        "nome": "CENTRAL DE REGULAÇÃO",
        "tipo": "checklist",
        "itens": [
            {"num": 64, "texto": "Fluxo de regulação definido"},
            {"num": 65, "texto": "Solicitações de vagas registradas"},
            {"num": 66, "texto": "Transferências acompanhadas"},
            {"num": 67, "texto": "Pacientes aguardando transferência identificados"},
            {"num": 68, "texto": "Tempo de espera acompanhado"},
            {"num": 69, "texto": "Comunicação com unidades de destino registrada"},
            {"num": 70, "texto": "A unidade possui plano de contingência?"},
            {"num": 71, "texto": "Plano de contingência conhecido pela equipe"},
        ],
    },
    {
        "nome": "FARMÁCIA",
        "tipo": "checklist",
        "itens": [
            {"num": 72, "texto": "Organização e limpeza"},
            {"num": 73, "texto": "Controle de acesso"},
            {"num": 74, "texto": "Estoque adequado"},
            {"num": 75, "texto": "Controle de validade"},
            {"num": 76, "texto": "Ausência de medicamentos vencidos"},
            {"num": 77, "texto": "Medicamentos controlados armazenados adequadamente"},
            {"num": 78, "texto": "Registros de controlados atualizados"},
            {"num": 79, "texto": "Controle de temperatura"},
            {"num": 80, "texto": "Estoque mínimo/máximo acompanhado"},
            {"num": 81, "texto": "Inventário compatível com estoque físico"},
            {"num": 82, "texto": "Rastreabilidade e dispensação adequadas"},
        ],
    },
    {
        "nome": "FATURAMENTO",
        "tipo": "checklist",
        "itens": [
            {"num": 83, "texto": "Produção devidamente registrada"},
            {"num": 84, "texto": "Documentação compatível com procedimentos realizados"},
            {"num": 85, "texto": "Fechamentos dentro do prazo"},
            {"num": 86, "texto": "Inconsistências acompanhadas"},
            {"num": 87, "texto": "Glosas monitoradas"},
            {"num": 88, "texto": "Pendências identificadas"},
            {"num": 89, "texto": "Integração adequada entre assistência e faturamento"},
            {"num": 90, "texto": "Compatibilidade entre produção realizada, registrada e faturada"},
        ],
    },
    {
        "nome": "LIMPEZA E HIGIENIZAÇÃO",
        "tipo": "checklist",
        "itens": [
            {"num": 91, "texto": "Equipe presente conforme escala"},
            {"num": 92, "texto": "DML organizado"},
            {"num": 93, "texto": "Produtos identificados e armazenados corretamente"},
            {"num": 94, "texto": "Diluição de produtos conforme orientação"},
            {"num": 95, "texto": "Limpeza concorrente realizada"},
            {"num": 96, "texto": "Limpeza terminal registrada"},
            {"num": 97, "texto": "Banheiros limpos e abastecidos"},
            {"num": 98, "texto": "Ambientes assistenciais em condições adequadas"},
            {"num": 99, "texto": "POPs e rotinas disponíveis"},
        ],
    },
    {
        "nome": "NUTRIÇÃO",
        "tipo": "checklist",
        "itens": [
            {"num": 100, "texto": "Área limpa e organizada"},
            {"num": 101, "texto": "Armazenamento adequado dos alimentos"},
            {"num": 102, "texto": "Controle de validade"},
            {"num": 103, "texto": "Controle de temperatura"},
            {"num": 104, "texto": "Geladeiras/freezers em condições adequadas"},
            {"num": 105, "texto": "Dietas corretamente identificadas"},
            {"num": 106, "texto": "Dietas especiais atendidas corretamente"},
            {"num": 107, "texto": "Distribuição das dietas organizada"},
            {"num": 108, "texto": "Manipuladores devidamente uniformizados"},
            {"num": 109, "texto": "Controle diário das refeições distribuídas aos pacientes"},
            {"num": 110, "texto": "Controle diário das refeições distribuídas aos acompanhantes"},
            {"num": 111, "texto": "Controle diário das refeições distribuídas aos colaboradores"},
            {"num": 112, "texto": "Compatibilidade entre refeições produzidas/recebidas e efetivamente distribuídas"},
            {"num": 113, "texto": "Situação dos utensílios e eletrodomésticos"},
        ],
    },
    {
        "nome": "OXIGÊNIO E GASES MEDICINAIS",
        "tipo": "checklist",
        "itens": [
            {"num": 114, "texto": "Central de gases em condições adequadas"},
            {"num": 115, "texto": "Rede de oxigênio funcionando"},
            {"num": 116, "texto": "Reserva de oxigênio disponível"},
            {"num": 117, "texto": "Cilindros identificados e armazenados corretamente"},
            {"num": 118, "texto": "Cilindros fixados com segurança"},
            {"num": 119, "texto": "Controle de abastecimento"},
            {"num": 120, "texto": "Manutenção preventiva da rede"},
            {"num": 121, "texto": "Plano de contingência para falta de oxigênio"},
        ],
    },
    {
        "nome": "ENGENHARIA CLÍNICA",
        "tipo": "checklist",
        "itens": [
            {"num": 122, "texto": "Inventário atualizado"},
            {"num": 123, "texto": "Equipamentos patrimoniados/identificados"},
            {"num": 124, "texto": "Manutenções preventivas em dia"},
            {"num": 125, "texto": "Manutenções corretivas acompanhadas"},
            {"num": 126, "texto": "Calibrações atualizadas quando aplicáveis"},
            {"num": 127, "texto": "Equipamentos parados identificados"},
            {"num": 128, "texto": "Motivo e prazo para reparo registrados"},
            {"num": 129, "texto": "Equipamentos reserva disponíveis quando necessários"},
        ],
    },
    {
        "nome": "TI",
        "tipo": "checklist",
        "itens": [
            {"num": 130, "texto": "Sistemas funcionando"},
            {"num": 131, "texto": "Internet adequada"},
            {"num": 132, "texto": "Serviço de telefonia"},
            {"num": 133, "texto": "Computadores funcionando"},
            {"num": 134, "texto": "Impressoras funcionando"},
            {"num": 135, "texto": "Chamados de TI acompanhados"},
            {"num": 136, "texto": "Equipamentos de TI identificados"},
            {"num": 137, "texto": "Backup e segurança das informações"},
            {"num": 138, "texto": "Plano de contingência para indisponibilidade dos sistemas"},
        ],
    },
    {
        "nome": "CENTRO CIRÚRGICO",
        "tipo": "checklist",
        "itens": [
            {"num": 139, "texto": "Salas cirúrgicas ativas e organizadas"},
            {"num": 140, "texto": "Equipamentos funcionando"},
            {"num": 141, "texto": "Medicamentos e materiais disponíveis"},
            {"num": 142, "texto": "Checklist de cirurgia segura aplicado"},
            {"num": 143, "texto": "Registros cirúrgicos adequados"},
            {"num": 144, "texto": "Fluxo limpo/sujo adequado"},
            {"num": 145, "texto": "Limpeza entre procedimentos e terminal registrada"},
            {"num": 146, "texto": "Controle de acesso"},
            {"num": 147, "texto": "Condições de segurança adequadas"},
            {"num": 148, "texto": "SAEP implantada e devidamente registrada"},
            {"num": 149, "texto": "Mapa cirúrgico atualizado e disponível"},
            {"num": 150, "texto": "Compatibilidade entre mapa cirúrgico, procedimentos realizados e registros"},
            {"num": 151, "texto": "Cirurgias suspensas e respectivos motivos acompanhados"},
        ],
    },
    {
        "nome": "CME",
        "tipo": "checklist",
        "itens": [
            {"num": 152, "texto": "Fluxo de material sujo e limpo adequado"},
            {"num": 153, "texto": "Área de expurgo adequada"},
            {"num": 154, "texto": "Processamento correto dos materiais"},
            {"num": 155, "texto": "Autoclaves funcionando"},
            {"num": 156, "texto": "Manutenção preventiva em dia"},
            {"num": 157, "texto": "Indicadores químicos, físicos e biológicos controlados"},
            {"num": 158, "texto": "Rastreabilidade dos materiais esterilizados"},
            {"num": 159, "texto": "Armazenamento adequado dos materiais estéreis"},
            {"num": 160, "texto": "Registro e acompanhamento dos indicadores físicos dos ciclos de esterilização"},
            {"num": 161, "texto": "Registro de tempo, temperatura e pressão conforme equipamento/processo"},
            {"num": 162, "texto": "Evidências dos ciclos arquivadas e rastreáveis"},
            {"num": 163, "texto": "Instrumentais suficientes"},
            {"num": 164, "texto": "Controle de OMPE"},
        ],
    },
    {
        "nome": "RESÍDUOS",
        "tipo": "checklist",
        "itens": [
            {"num": 165, "texto": "Segregação correta dos resíduos"},
            {"num": 166, "texto": "Resíduos infectantes acondicionados adequadamente"},
            {"num": 167, "texto": "Perfurocortantes descartados corretamente"},
            {"num": 168, "texto": "Resíduos do Centro Cirúrgico conforme fluxo"},
            {"num": 169, "texto": "Lixeiras identificadas e adequadas"},
            {"num": 170, "texto": "Coleta interna organizada"},
            {"num": 171, "texto": "Abrigo temporário adequado"},
            {"num": 172, "texto": "PGRSS disponível e aplicado"},
            {"num": 173, "texto": "Coleta externa regularizada"},
        ],
    },
    {
        "nome": "LAVANDERIA / ROUPARIA",
        "tipo": "checklist",
        "itens": [
            {"num": 174, "texto": "Fluxo de roupa limpa e suja separado"},
            {"num": 175, "texto": "Armazenamento adequado"},
            {"num": 176, "texto": "Enxoval em quantidade suficiente"},
            {"num": 177, "texto": "Controle de entrada e saída"},
            {"num": 178, "texto": "Perdas/extravios acompanhados"},
            {"num": 179, "texto": "Roupa limpa protegida adequadamente"},
            {"num": 180, "texto": "Abastecimento dos setores adequado"},
        ],
    },
    {
        "nome": "TOMOGRAFIA",
        "tipo": "checklist",
        "itens": [
            {"num": 181, "texto": "Equipamento funcionando"},
            {"num": 182, "texto": "Manutenção preventiva atualizada"},
            {"num": 183, "texto": "Agenda/fluxo organizado"},
            {"num": 184, "texto": "Produção acompanhada"},
            {"num": 185, "texto": "Laudos dentro do prazo"},
            {"num": 186, "texto": "Insumos disponíveis"},
            {"num": 187, "texto": "Sala em condições adequadas"},
            {"num": 188, "texto": "Documentações/licenças aplicáveis regulares"},
            {"num": 189, "texto": "RDC 11 impressa e disponível no setor"},
        ],
    },
    {
        "nome": "RAIO-X",
        "tipo": "checklist",
        "itens": [
            {"num": 190, "texto": "Equipamento funcionando"},
            {"num": 191, "texto": "Manutenção preventiva atualizada"},
            {"num": 192, "texto": "Proteção radiológica adequada"},
            {"num": 193, "texto": "Dosimetria quando aplicável atualizada"},
            {"num": 194, "texto": "Produção acompanhada"},
            {"num": 195, "texto": "Laudos dentro do prazo"},
            {"num": 196, "texto": "Documentação/licenças aplicáveis atualizadas"},
            {"num": 197, "texto": "RDC 11 impressa e disponível no setor"},
        ],
    },
    {
        "nome": "LABORATÓRIO",
        "tipo": "checklist",
        "itens": [
            {"num": 198, "texto": "Área de coleta organizada"},
            {"num": 199, "texto": "Identificação correta das amostras"},
            {"num": 200, "texto": "Acondicionamento/transporte adequado"},
            {"num": 201, "texto": "Equipamentos funcionando"},
            {"num": 202, "texto": "Manutenções e calibrações atualizadas"},
            {"num": 203, "texto": "Controle de temperatura"},
            {"num": 204, "texto": "Insumos e reagentes dentro da validade"},
            {"num": 205, "texto": "Resultados liberados dentro dos prazos"},
            {"num": 206, "texto": "Controles de qualidade realizados"},
        ],
    },
    {
        "nome": "MOBILIÁRIO, PATRIMÔNIO E ESTRUTURA",
        "tipo": "checklist",
        "itens": [
            {"num": 207, "texto": "Mobiliários em bom estado"},
            {"num": 208, "texto": "Quantidade suficiente"},
            {"num": 209, "texto": "Camas e macas em condições adequadas"},
            {"num": 210, "texto": "Cadeiras e poltronas conservadas"},
            {"num": 211, "texto": "Equipamentos e mobiliários patrimoniados"},
            {"num": 212, "texto": "Ausência de mobiliário quebrado/inseguro"},
            {"num": 213, "texto": "Necessidades de substituição identificadas"},
            {"num": 214, "texto": "Paredes, pisos e tetos conservados"},
            {"num": 215, "texto": "Ausência de infiltrações"},
            {"num": 216, "texto": "Instalações elétricas e hidráulicas adequadas"},
            {"num": 217, "texto": "Ar-condicionado funcionando"},
            {"num": 218, "texto": "PMOC atualizado"},
        ],
    },
    {
        "nome": "GESTÃO DA QUALIDADE E SEGURANÇA",
        "tipo": "checklist",
        "itens": [
            {"num": 219, "texto": "Gestor conhece metas e obrigações contratuais"},
            {"num": 220, "texto": "Indicadores atualizados"},
            {"num": 221, "texto": "Produção x metas acompanhada"},
            {"num": 222, "texto": "Protocolos e POPs atualizados"},
            {"num": 223, "texto": "Segurança do Paciente acompanhada"},
            {"num": 224, "texto": "Eventos adversos notificados e analisados"},
            {"num": 225, "texto": "IRAS monitoradas"},
            {"num": 226, "texto": "Plano de ação das visitas anteriores acompanhado"},
            {"num": 227, "texto": "Licenças e alvarás vigentes"},
            {"num": 228, "texto": "Contratos de terceiros acompanhados"},
            {"num": 229, "texto": "Cronograma e comprovantes de dedetização/desinsetização/desratização"},
            {"num": 230, "texto": "Limpeza periódica da caixa d'água/reservatórios com registros e certificados"},
            {"num": 231, "texto": "Controle de potabilidade da água atualizado"},
            {"num": 232, "texto": "Laudos/análises de potabilidade disponíveis"},
            {"num": 233, "texto": "Não conformidades da qualidade da água tratadas e acompanhadas"},
        ],
    },
    {
        "nome": "GTH, HUMANIZAÇÃO E COMUNICAÇÃO",
        "tipo": "checklist",
        "itens": [
            {"num": 234, "texto": "GTH ativo"},
            {"num": 235, "texto": "Ações de humanização realizadas"},
            {"num": 236, "texto": "Campanhas institucionais executadas"},
            {"num": 237, "texto": "Evidências e registros fotográficos organizados"},
            {"num": 238, "texto": "Comunicação interna funcionando adequadamente"},
            {"num": 239, "texto": "Materiais institucionais atualizados"},
            {"num": 240, "texto": "Participação dos colaboradores nas ações"},
        ],
    },
    {
        "nome": "EXPERIÊNCIA DO USUÁRIO / OUVIDORIA",
        "tipo": "checklist",
        "itens": [
            {"num": 241, "texto": "Tempo de espera acompanhado"},
            {"num": 242, "texto": "Abordagem da equipe adequada"},
            {"num": 243, "texto": "Reclamações monitoradas"},
            {"num": 244, "texto": "Elogios registrados"},
            {"num": 245, "texto": "Demandas recorrentes tratadas"},
            {"num": 246, "texto": "Ouvidoria acessível"},
            {"num": 247, "texto": "Privacidade e dignidade do paciente preservadas"},
        ],
    },
    {
        "nome": "TRANSPORTE/REMOÇÃO",
        "tipo": "checklist",
        "itens": [
            {"num": 248, "texto": "Controle de viagens"},
            {"num": 249, "texto": "Controle de quilometragem"},
            {"num": 250, "texto": "Controle de origem e destino"},
            {"num": 251, "texto": "Controle de equipe"},
        ],
    },
]

# ---------------------------------------------------------------------------
# Colunas da aba "Visitas" (1 linha por visita/auditoria completa)
# ---------------------------------------------------------------------------
COLUNAS_VISITA = [
    "Código da Visita",
    "Unidade",
    "Data da Visita",
    "Responsável pela Visita",
    "Nome de Quem Acompanhou",
    "Início do Preenchimento",
    "Fim do Preenchimento (Envio)",
    "Status da Visita",
    "Total de Itens Aplicáveis",
    "Total Conforme",
    "Total Não Conforme",
    "Total Não se Aplica",
    "Total Não Preenchido",
    "Percentual de Conformidade",
]

# ---------------------------------------------------------------------------
# Colunas da aba "Itens" (1 linha por item respondido — formato normalizado,
# pensado para alimentar um banco de dados relacional depois: cada linha é
# um fato atômico ligado à visita pelo "Código da Visita").
# ---------------------------------------------------------------------------
COLUNAS_ITEM = [
    "Código da Visita",
    "Unidade",
    "Data da Visita",
    "Seção",
    "Nº do Item",
    "Item de Verificação",
    "Tipo de Campo",
    "Resposta",
    "Observações / Evidências",
    "Respondido em",
]


def slug_unidade(unidade: str) -> str:
    nfkd = unicodedata.normalize("NFKD", unidade)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.upper().replace(" ", "").replace("-", "")


def gerar_codigo_visita(unidade: str) -> str:
    """Formato: AUD-[UNIDADE]-[AAAAMMDD]-[XXXX] — identificador único da visita."""
    data = agora_brasilia().strftime("%Y%m%d")
    sufixo = str(uuid.uuid4()).upper()[:4]
    return f"AUD-{slug_unidade(unidade)}-{data}-{sufixo}"


def total_itens_checklist() -> int:
    """Quantos itens de checklist (fora CAPACIDADE E OCUPAÇÃO) existem no total."""
    return sum(len(s["itens"]) for s in SECOES if s["tipo"] == "checklist")


def total_itens_secao(secao: dict) -> int:
    return len(secao["itens"])
