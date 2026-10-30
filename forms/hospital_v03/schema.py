# -*- coding: utf-8 -*-
"""
schema.py - Checklist de Visita Tecnica (Sao Lucas Instituto) - modelo V03, 24 secoes / 77 itens

Catalogo de grupos e itens + constantes + colunas das planilhas.

IMPORTANTE: o numero global do item (1..N) e a CHAVE ESTAVEL que liga os dados
historicos ao catalogo. Nunca renumere; para itens novos, use numeros novos
(depois do ultimo) mesmo que o item apareca no meio de um grupo (campo "ref"
define o rotulo exibido, ex.: "2.6"). A lista abaixo e uma PROPOSTA a ser
validada pela area tecnica; as referencias normativas citadas em
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

# (nome da secao, [(item a verificar, previsto no TR / apendices - modelo V03), ...])
# Fonte: V03 - Checklist da Visita Tecnica (Hospital Regional Dr. Julio Perez Antelo, Guajara-Mirim/RO,
# Edital 3/2026/SESAU-CECOMP). Os textos 'previsto' sao SUGESTAO desse edital; em outro hospital o auditor
# pode informar o previsto proprio em cada item.
GRUPOS_BRUTOS = [
    ("1. Documentação e visão geral", [
        ("Confirmar a emissão do Atestado de Visita Técnica - Anexo XX.",
         "Edital 6.3 / Anexo XX: se realizada a visita, deve ser emitido o Atestado de Visita Técnica e apresentado com a Proposta de Trabalho."),
        ("Registrar eventuais restrições estruturais, funcionais ou operacionais informadas pela SESAU.",
         "Edital 6.4: a visita destina-se ao conhecimento das condições estruturais, funcionais, técnicas e operacionais; cabe à interessada avaliar e registrar as informações necessárias à proposta."),
        ("Verificar AVCB, Licença Sanitária e licença/alvará municipal aplicável.",
         "TR: operação deve observar regularidade legal/sanitária e requisitos aplicáveis. Os documentos analisados não fixam número/validade desses alvarás; confirmar situação vigente in loco."),
    ]),
    ("2. Capacidade instalada e leitos", [
        ("Confirmar o número total de leitos instalados, identificando os leitos operacionais e inativos e os respectivos motivos de bloqueio.",
         "Total 83 Leitos Internação. (1 Cuidados neonatais, 10 UTI, 25 Cirurgicos, 22 Clinico Adulto, 10 Obstetrico Cirúrgico, 15 Clinica Pediatrica), 4 Leitos RPA, 2 Leitos Emergecia, 9 Leitos observação."),
        ("Verificar a quantidade e as condições dos leitos de isolamento.",
         "TR: Não informa o quantitativo d leitos de isolamento. Confirmar capacidade instalada/operacional in loco."),
        ("Verificar a quantidade e as condições dos leitos de observação.",
         "TR: define leito hospitalar de observação (<24h), 9 leitos de obervacao."),
        ("Confirmar o número de leitos de UTI instalados e efetivamente operacionais.",
         "TR: UTI Adulto foi identificado 10 leitos de UTI fixado nos documentos analisados."),
    ]),
    ("3. Pronto atendimento / urgência e emergência", [
        ("Verificar o dimensionamento da recepção por turno, a existência de liderança responsável e a disponibilidade de equipamentos em quantidade adequada.",
         "TR exige estrutura de pessoal e recursos suficientes ao funcionamento. Não foi identificado dimensionamento numérico da recepção por turno."),
        ("Verificar a existência e a quantidade de controladores de acesso por turno.",
         "TR: serviços de apoio/controle devem garantir funcionamento regular e segurança. Não foi identificado quantitativo de controladores por turno."),
        ("Verificar o fluxo de acolhimento e classificação de risco, incluindo local de realização, metodologia, funcionamento por turno e integração com os fluxos assistenciais da unidade.",
         "TR: atendimento de urgência/emergência e fluxos assistenciais devem funcionar de forma organizada e integrada. 1 sala de acolhimento com classificação de risco. Não foi identificado quantitativo/escala específica para classificação de risco."),
        ("Verificar a quantidade, a organização e as condições dos consultórios, salas de atendimento e áreas de observação.",
         "TR prevê 2 consultorios médicos e 1 sala para atendimento indiferenciado, 1 sala de curativo, 1 sala de higienização, 1 sala de pequena cirurgia, 1 sala de repouso/observação, 1 sala emergência e 1 sala de nebulização."),
        ("Confirmar o número de médicos por turno e o respectivo valor praticado.",
         "TR exige equipe assistencial compatível com o perfil e continuidade dos serviços. Não foi identificado quantitativo de médicos por turno."),
        ("Verificar a estrutura da sala de emergência, incluindo número de leitos, monitores, desfibrilador, ventiladores, bombas de infusão, aspiradores, carrinho de emergência e gases medicinais, bem como o número de médicos por turno.",
         "TR exige equipe e equipamentos assistenciais compatíveis com o perfil e continuidade dos serviços. 1 sala com 2 leitos. Não foi identificado quantitativo de médicos por turno."),
    ]),
    ("4. Internação / enfermarias", [
        ("Confirmar a distribuição dos leitos por clínica, especialidade e setor, bem como o número de médicos por turno e os valores praticados.",
         "TR exige equipe assistencial compatível com o perfil e continuidade dos serviços. A quantidade de leitos por setor são 25 Cirurgicos, 22 Clinico Adulto, 10 Obstetrico Cirúrgico, 15 Clinica Pediatrica. Não foi identificado quantitativo de médicos por turno."),
        ("Verificar a quantidade de maqueiros, horários de cobertura e setores atendidos.",
         "TR exige recursos humanos suficientes e continuidade assistencial. Não foi identificado quantitativo/horário de maqueiros."),
        ("Verificar a cobertura da secretaria de ala, incluindo horários, setores atendidos e número de colaboradores por turno.",
         "TR exige suporte administrativo necessário à operação. Não foi identificado quantitativo/horário de secretaria de ala."),
    ]),
    ("5. UTI adulto", [
        ("Confirmar o número de médicos por turno e os valores praticados.",
         "TR exige equipe assistencial compatível com o perfil e continuidade dos serviços. Não foi identificado quantitativo de médicos por turno."),
        ("Confirmar o número de leitos de UTI ativos.",
         "TR: informa a quantidade de 10 leitos de UTI"),
        ("Verificar a disponibilidade e o funcionamento de monitores multiparamétricos, ventiladores, bombas de infusão e demais equipamentos essenciais, incluindo carrinho de emergência, desfibrilador e gases medicinais.",
         "Apêndice 1, 2.3: equipamentos médico-assistenciais necessários devem estar disponíveis e funcionantes, com manutenção preventiva; carros de emergência e gases medicinais também devem estar disponíveis. Sem quantitativo específico."),
    ]),
    ("6. Centro cirúrgico / RPA – interface assistencial", [
        ("Confirmar o número de salas cirúrgicas instaladas e operacionais e verificar a adequação dos fluxos assistenciais e físicos à regulamentação aplicável.",
         "Apêndice 2: meta quantitativa mensal de 175 cirurgias (40 ortopédicas, 75 gerais, 35 urológicas e 60 ginecológicas — metas por categoria; o total contratual indicado na tabela é 175/mês). Foi identificado número de 3 salas cirúrgicas fixado."),
        ("Identificar as especialidades e o perfil das cirurgias realizadas ou previstas, bem como o número de médicos por turno.",
         "TR exige equipe assistencial compatível com o perfil e continuidade dos serviços. Ortopedia, Cirurgia geral, Urologia e Ginecologia, Não foi identificado quantitativo de médicos por turno."),
        ("Caracterizar a realização de cirurgias eletivas e de urgência/emergência, horários de funcionamento e volume médio mensal de procedimentos.",
         "Apêndice 2: meta global de cirurgias = 175/mês (2.100/ano). O documento não discrimina, nessa meta, volume eletivo versus urgência/emergência nem horário de funcionamento."),
        ("Verificar a capacidade da RPA, incluindo número de leitos/vagas, recursos de monitorização e equipamentos disponíveis.",
         "Apêndice 2 define leito de recuperação pós-cirúrgica/pós-anestésica; foi identificado o quantitativo de 4 vagas/leitos de RPA. Apêndice 1, 2.3 exige equipamentos necessários disponíveis e funcionantes."),
        ("Identificar os equipamentos médico-assistenciais essenciais disponíveis, discriminando os funcionantes e inoperantes.",
         "Apêndice 1, 2.3: disponibilidade e funcionamento dos equipamentos necessários, identificação de manutenção preventiva, carros/materiais de emergência, medicamentos/insumos e gases medicinais. Sem quantitativos específicos."),
    ]),
    ("7. Obstetrícia / PPP / neonatal", [
        ("Verificar a estrutura destinada ao pré-parto, parto e pós-parto, incluindo quantidade e condições das salas PPP.",
         "Apêndice 2 define leito PPP, 3 leitos em sala de pré-parto, partp, e pós-parto e 2 leitos de gestação de alto risco. Não foi identificado quantitativo de salas/leitos PPP fixado."),
        ("Verificar a estrutura do centro obstétrico, a capacidade para cesáreas e urgências obstétricas e o volume médio mensal de partos.",
         "Apêndice 2: meta de Partos (normal + cesáreo) = 35/mês (420/ano). Não foi identificado número de salas do centro obstétrico."),
        ("Verificar as condições para assistência imediata ao recém-nascido e a disponibilidade de estrutura e equipamentos para reanimação neonatal.",
         "TR inclui assistência materno-infantil conforme perfil hospitalar. Apêndice 1, 2.3 exige equipamentos e materiais de emergência disponíveis e funcionantes. Quantitativos neonatais de 1 leito específico. ."),
    ]),
    ("8. Terapia renal substitutiva / hemodiálise", [
        ("Confirmar o número de máquinas/pontos instalados e efetivamente operacionais.",
         "Apêndice 2: Terapia Renal Substitutiva/Hemodiálise com meta de 450 sessões/mês (5.400/ano), definida com base na capacidade instalada. O documento não explicita, na tabela de metas, número de máquinas/pontos."),
        ("Confirmar o número de médicos por turno e os valores praticados.",
         "TR exige equipe assistencial compatível com o perfil e continuidade dos serviços. Não foi identificado quantitativo de médicos por turno."),
        ("Caracterizar o atendimento prestado, identificando a assistência ambulatorial e/ou aos pacientes internados.",
         "Apêndice 2: TRS/Hemodiálise = 450 sessões/mês (5.400/ano). Confirmar in loco o perfil efetivo (ambulatorial e/ou internados), pois a meta não o discrimina."),
        ("Identificar as principais limitações de capacidade instalada e de equipamentos com impacto na operação do serviço.",
         "Apêndice 2 informa que a meta de TRS foi definida com base na capacidade teórica anual calculada a partir da estrutura instalada; meta = 450 sessões/mês. Registrar limitações que impeçam essa capacidade."),
    ]),
    ("9. Banco de sangue", [
        ("Verificar o fluxo do serviço, equipamentos disponíveis, horário de funcionamento, composição da equipe, carga horária do médico responsável e valor praticado.",
         "TR exige suporte diagnóstico/terapêutico e continuidade assistencial. Não foi identificado, nos documentos analisados, quantitativo de equipe, carga horária ou valor específico do serviço hemoterápico."),
        ("Confirmar o escopo e os procedimentos efetivamente realizados pelo serviço.",
         "TR: confirmar escopo real do serviço de apoio. Não foi identificado rol quantitativo específico no material analisado para esta linha."),
    ]),
    ("10. CME", [
        ("Verificar o fluxo do serviço, equipamentos disponíveis, horário de funcionamento e composição da equipe.",
         "TR exige serviço de apoio compatível com a operação e continuidade assistencial. Não foi identificado quantitativo/horário específico para esta linha; confirmar capacidade instalada e equipe in loco."),
    ]),
    ("11. Ambulatório", [
        ("Identificar as especialidades ofertadas, horários de atendimento e valores praticados.",
         "TR: Não foi identificado dado quantitativo/especificação objetiva correspondente nos documentos analisados; confirmar in loco."),
        ("Confirmar o número de consultórios disponíveis e a capacidade física do ambulatório.",
         "TR prevê atendimento ambulatorial; 7 Clinicas especializadas, 1 consultório não medico, 1 sala de apoio telediagnóstico, 1 sala de cirurgia ambulatorial, 1 sala de curativo, 1 sala de enfermagem, 1 sala de gesso, 1 sala de imunização."),
        ("Verificar a organização das agendas, a origem dos encaminhamentos e o fluxo de acesso regulado.",
         "TR: acesso deve observar regulação e integração com a rede. Não foi identificado quantitativo de agendas; confirmar origem dos encaminhamentos e fluxo regulado."),
        ("Identificar os procedimentos ambulatoriais efetivamente realizados.",
         "TR contempla serviços assistenciais ambulatoriais conforme perfil. Não foi identificado rol quantitativo específico; confirmar escopo in loco."),
    ]),
    ("12. Remoções", [
        ("Caracterizar o serviço de remoção: próprio ou terceirizado, quantidade e tipos de ambulâncias, horários de cobertura e volume médio mensal de remoções.",
         "TR exige continuidade do cuidado e integração da rede/transferências. Não foi identificado quantitativo/tipo de ambulâncias nem meta mensal de remoções."),
    ]),
    ("13. SADT – laboratório e diagnóstico por imagem", [
        ("Caracterizar o laboratório: próprio ou terceirizado, horário de funcionamento, cobertura de urgência, principais exames disponíveis e volume médio mensal.",
         "Apêndice 2/Apêndice 1: integração com SADT e disponibilidade do apoio diagnóstico devem ser asseguradas. Não foi identificada meta quantitativa mensal de exames laboratoriais na Tabela 6."),
        ("Verificar radiologia fixa e móvel: equipamentos, condições de funcionamento, emissão de laudos, cobertura médica, horários, valores praticados e volume médio mensal de exames.",
         "Apêndice 2: Radiologia (raio-X) é serviço monitorado; o texto mantém metas pactuadas, mas a Tabela 6 exibida não apresenta meta mensal específica para RX. Confirmar equipamentos, laudos e produção in loco."),
        ("Verificar a ultrassonografia: disponibilidade, horários, emissão de laudos, cobertura médica, valores praticados e volume médio mensal de exames.",
         "TR/SADT: ultrassonografia integra apoio diagnóstico conforme oferta da unidade. Não foi identificada meta quantitativa mensal específica nos documentos analisados."),
        ("Verificar a tomografia: equipamento, condições de funcionamento, disponibilidade de contraste, emissão de laudos, cobertura médica, horários, valores praticados e volume médio mensal de exames.",
         "Apêndice 2: Tomografia Computadorizada = meta de 500 exames/mês (6.000/ano)."),
        ("Verificar endoscopia e colonoscopia: equipamentos, condições de funcionamento, emissão de laudos, cobertura médica, horários, valores praticados e volume médio mensal de exames.",
         "TR/SADT: verificar oferta e capacidade real. Não foi identificada meta quantitativa mensal específica para endoscopia/colonoscopia nos documentos analisados."),
        ("Verificar ECG, EEG, Holter e MAPA: equipamentos, funcionamento, emissão de laudos, cobertura médica, horários, valores praticados e volume médio mensal de exames.",
         "Apêndice 2: ECG é serviço monitorado, porém a Tabela 6 não fixa meta mensal para ECG/EEG/Holter/MAPA. Confirmar capacidade, laudos e produção in loco."),
        ("Identificar outros exames ou procedimentos diagnósticos/terapêuticos disponíveis e o respectivo volume médio mensal.",
         "TR prevê integração com serviços de apoio diagnóstico e terapêutico. Não há meta única para “outros exames”; registrar serviços existentes e produção observada."),
    ]),
    ("14. Reabilitação e equipe multiprofissional", [
        ("Verificar a cobertura da fisioterapia hospitalar nas enfermarias, UTI e pós-operatório, bem como o atendimento ambulatorial, se existente.",
         "TR exige equipe multiprofissional compatível com o perfil assistencial e continuidade do cuidado. Não foi identificado quantitativo/carga horária de fisioterapia."),
        ("Verificar a cobertura e os fluxos assistenciais de nutrição, fonoaudiólogos, psicologia e serviço social.",
         "TR exige assistência multiprofissional conforme necessidade do paciente. Não foram identificados quantitativos/cargas horárias específicos para nutrição, fonoaudiólogos, psicologia e serviço social."),
    ]),
    ("15. NIR / RH / faturamento", [
        ("Verificar a existência e localização do NIR, horário de funcionamento, composição e quantitativo da equipe, cobertura médica e valores praticados.",
         "TR: regulação/acesso e integração da unidade com a rede devem ser assegurados. Não foi identificado quantitativo da equipe, cobertura médica do NIR."),
        ("Verificar o fluxo operacional do NIR e sua integração com regulação estadual, Urgência/Emergência, internação, UTI, centro cirúrgico e demais setores, incluindo processos de admissão, transferência, alta e gestão de leitos.",
         "TR: fluxo regulatório deve integrar admissão, internação, transferências e serviços assistenciais; confirmar integração do NIR com UE, internação, UTI, CC e rede estadual."),
        ("Verificar o dimensionamento das equipes de Faturamento, Recursos Humanos e SAME.",
         "TR exige estrutura administrativa e gerencial necessária à execução contratual. Não foram identificados quantitativos mínimos para Faturamento, RH e SAME."),
    ]),
    ("16. Farmácia", [
        ("Caracterizar a farmácia central e/ou satélites, horários de funcionamento e quantitativo de farmacêuticos e auxiliares.",
         "Apêndice 1, 2.1: segurança na prescrição, preparo, dispensação e administração de medicamentos deve ser verificada. Não foi identificado quantitativo de farmacêuticos/auxiliares nem horário mínimo."),
        ("Verificar o fluxo de dispensação e abastecimento de medicamentos e materiais aos setores assistenciais, incluindo dispensação por paciente/setor, atendimento às urgências, controle de medicamentos sujeitos a controle especial e eventuais limitações operacionais.",
         "Apêndice 1, 2.1: verificar segurança e integração da prescrição, preparo, dispensação e administração de medicamentos. Apêndice 1, 2.3: manter medicamentos/insumos essenciais disponíveis."),
    ]),
    ("17. Equipamentos médico-assistenciais e gases", [
        ("Realizar levantamento visual dos equipamentos críticos por setor e quantitativo aproximado, registrando equipamentos inoperantes, insuficientes ou ausentes com potencial impacto assistencial.",
         "Apêndice 1, 2.3: equipamentos médico-assistenciais necessários devem estar disponíveis, funcionantes e com manutenção preventiva identificada. Registrar ausências/inoperâncias; sem quantitativo geral fixado."),
        ("Verificar a disponibilidade, abrangência e condições da rede de oxigênio e ar comprimido.",
         "Apêndice 1, 2.3: verificar gases medicinais e demais recursos necessários à continuidade e segurança da assistência. Quantitativo/pontos não especificados."),
        ("Verificar a existência de geradores e/ou no-breaks para equipamentos críticos e identificar os setores contemplados.",
         "TR: infraestrutura deve sustentar continuidade operacional e segurança. Apêndice 2 inclui indicadores de sustentabilidade/infraestrutura. Não foi identificado quantitativo de geradores/no-breaks."),
    ]),
    ("18. Prontuário, prescrição e TI assistencial", [
        ("Identificar o tipo de prontuário utilizado - eletrônico, físico ou híbrido - e o sistema adotado.",
         "Apêndice 1, 2.1 exige prontuários e registros assistenciais rastreáveis. O tipo de prontuário/sistema não foi fixado nos documentos analisados; confirmar solução em uso."),
        ("Verificar a infraestrutura de rede de dados, incluindo pontos de rede, cobertura Wi-Fi, conectividade entre os setores assistenciais e administrativos e eventuais limitações de acesso.",
         "Apêndice 1, eixo 5: sistema de TI deve permitir disponibilidade contínua de informações gerenciais e acesso do Gestor Público. Infraestrutura física de rede/pontos não é quantificada."),
        ("Verificar a disponibilidade e as condições dos computadores impressoras, leitores e demais periféricos utilizados nos setores assistenciais e administrativos.",
         "Apêndice 1, eixo 5 exige sistema de TI funcional e disponibilidade contínua das informações. Não foi identificado quantitativo de computadores/periféricos."),
        ("Identificar os sistemas informatizados utilizados no laboratório, diagnóstico por imagem, farmácia, faturamento, regulação/NIR e demais sistemas de apoio, verificando a existência de integração entre eles.",
         "Apêndice 1, 5.2: relatórios gerenciais no sistema devem abranger produção, indicadores, faturamento, leitos, SADT e RH; verificar integração dos sistemas de apoio."),
        ("Caracterizar o suporte de TI: equipe própria ou terceirizada, cobertura presencial e/ou remota, horários de atendimento, tempo de resposta e suporte fora do horário administrativo para sistemas críticos.",
         "Apêndice 1, 5.1–5.3: TI deve manter informações atualizadas, acesso do Gestor Público e emissão padronizada de relatórios. Não foi fixado dimensionamento/horário do suporte."),
    ]),
    ("19. Equipe médica / enfermagem e cobertura assistencial", [
        ("Identificar os responsáveis técnicos e coordenações médicas atualmente vinculados aos principais serviços, bem como a existência de escalas médicas formalizadas e eventuais lacunas de cobertura.",
         "TR exige organização técnica/assistencial e equipes habilitadas para execução do escopo."),
        ("Mapear as especialidades médicas disponíveis por setor e por turno.",
         "Apêndice 2 explicita produção cirúrgica em Ortopedia, Cirurgia Geral, Urologia e Ginecologia e partos; demais especialidades devem ser confirmadas conforme perfil assistencial. Não fixa escala por turno."),
        ("Caracterizar a cobertura médica por especialidade: presencial 24 horas, horário parcial ou sobreaviso, incluindo os valores praticados.",
         "TR exige continuidade e disponibilidade da equipe assistencial. Não foi identificado padrão numérico de cobertura presencial/sobreaviso nem valores por especialidade."),
        ("Identificar eventual necessidade de ampliação de equipes ou retaguardas para cumprimento do escopo assistencial.",
         "TR atribui à contratada recursos humanos suficientes para a demanda e execução do escopo. Dimensionamento final deve considerar capacidade instalada, metas e gaps encontrados na visita."),
        ("Confirmar o quantitativo de enfermeiros e técnicos de enfermagem atuantes em cada setor e turno.",
         "TR exige recursos humanos suficientes e qualificados. Não foi identificado quantitativo mínimo por setor/turno; confrontar equipe atual com demanda, capacidade e metas."),
    ]),
    ("20. Estrutura física com impacto assistencial", [
        ("Verificar as condições de climatização e controle de temperatura dos ambientes assistenciais.",
         "TR/Apêndice 1: condições ambientais e infraestrutura devem garantir segurança e continuidade assistencial. Não foram identificados parâmetros quantitativos de climatização nesta linha."),
        ("Identificar problemas estruturais que possam limitar a capacidade operacional, a segurança assistencial ou a implantação dos serviços previstos.",
         "Edital 6.4: registrar condições estruturais, funcionais, técnicas e operacionais relevantes à proposta. Apêndice 1, 2.3: avaliar condições ambientais, leitos, equipamentos e recursos essenciais."),
    ]),
    ("21. Ouvidoria / SAU", [
        ("Verificar o sistema utilizado pela Ouvidoria/SAU, horário de funcionamento, quantitativo de profissionais e indicadores de satisfação disponíveis.",
         "Apêndice 1, 1.1–1.3: sistema formal de satisfação com instrumentos, canais, periodicidade e responsáveis; registros históricos/consolidados e evidência de uso dos resultados. Meta de satisfação ≥80% (Apêndice 2)."),
    ]),
    ("22. Higiene e limpeza / lavanderia / jardinagem", [
        ("Caracterizar o serviço de higiene e limpeza: próprio ou terceirizado, horários, quantitativo por turno e valores praticados.",
         "Apêndice 1, 2.2: verificar limpeza concorrente/terminal, resíduos, precauções, higiene das mãos, EPI, prevenção de infecções, não conformidades e planos de ação. Sem quantitativo de equipe fixado."),
        ("Caracterizar o serviço de lavanderia: interno ou terceirizado, capacidade/volume médio diário em kg e valores praticados.",
         "TR exige serviços de apoio necessários ao funcionamento regular. Não foi identificada capacidade mínima em kg/dia."),
        ("Verificar o serviço de jardinagem, incluindo horários de execução e valores praticados.",
         "TR inclui serviços não assistenciais necessários à operação. Não foram identificados horários específicos de jardinagem."),
    ]),
    ("23. Cozinha / nutrição / lactário", [
        ("Caracterizar o serviço de cozinha: próprio ou terceirizado e valores praticados.",
         "TR inclui alimentação/nutrição como apoio necessário à operação. Não foi identificado modelo obrigatório."),
        ("Verificar a cobertura do nutricionista, incluindo horários e valores praticados.",
         "TR exige assistência multiprofissional/nutricional conforme necessidade. Não foi identificada carga horária específico do nutricionista."),
        ("Verificar o horário de funcionamento do lactário e a adequação do fluxo operacional.",
         "TR contempla suporte materno-infantil e serviços de apoio. Não foi identificado horário mínimo do lactário; verificar adequação operacional/sanitária."),
    ]),
    ("24. Manutenção / engenharia clínica", [
        ("Caracterizar o serviço de manutenção: cobertura presencial e/ou sobreaviso, horários e valores praticados.",
         "Apêndice 1, 2.3: equipamentos devem apresentar manutenção preventiva identificada. Apêndice 2 inclui Plano de Manutenção Preventiva como indicador de sustentabilidade. Horário não fixados."),
        ("Caracterizar o serviço de engenharia clínica: cobertura presencial e/ou sobreaviso, horários e valores praticados.",
         "Apêndice 1, 2.3: verificar funcionamento e manutenção preventiva dos equipamentos médico-assistenciais. Não foi identificado dimensionamento, cobertura específica de engenharia clínica."),
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
    "Percentual de OK", "Total de Anexos", "Linhas do Quadro-Síntese", "Pendências Registradas",
    "Observações Finais",
]

COLUNAS_ITEM = [
    "Código da Visita", "Hospital", "Data da Visita", "Seção", "Nº do Item", "Ref.",
    "Item a Verificar", "Previsto no TR / Apêndices (modelo V03)", "Previsto informado pelo auditor",
    "Situação", "Achado / quantidade / GAP", "Evidência coletada", "Impacto na proposta",
    "Qtde de Anexos", "Respondido em",
]

COLUNAS_SINTESE = [
    "Código da Visita", "Hospital", "Nº", "Setor/Achado", "Referência TR / Apêndice",
    "Situação encontrada", "Risco/impacto assistencial",
    "Impacto em custo/dimensionamento/investimento", "Ação para a proposta",
]

COLUNAS_PENDENCIA = ["Código da Visita", "Hospital", "Nº", "Pendência / informação a solicitar após a visita"]

CAMPOS_SINTESE = ["setor", "referencia", "situacao", "risco", "custo", "acao"]

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
    """Formato: VT-<SIGLA>-<AAAAMMDD>-<4 hex> (ex.: VT-HRJPA-20261008-A3F9)."""
    import uuid
    return f"VT-{sigla_hospital(hospital)}-{agora_brasilia().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
