# Portal de Auditoria · São Lucas Instituto (CDQ)

Portal único para visitas e auditorias. Interface em `portal_ui/index.html` (HTML/JS puro, aprovada no protótipo — **não alterar o layout**);
regras de negócio em Python puro (`core/api.py`, `core/store.py`, `core/perms.py`, `core/drive.py`); `core/host.py` é a **única** peça que
conhece o Streamlit. Para trocar de host (FastAPI/Flask/etc.) reescreve-se só `host.py` (o protocolo é: a interface envia `{id, action, payload}`
e recebe `{boot, reply}`; ver `core/host.py`).

## Rodar
**Local**: `pip install -r requirements.txt && streamlit run app.py` (sem segredos entra em modo de teste, com seletor de usuário).
**Docker (qualquer servidor)**: `docker build -t portal . && docker run -p 8501:8501 -v portal_data:/data -v $PWD/secrets.toml:/app/.streamlit/secrets.toml portal`
**Streamlit Community Cloud**: aponte para `app.py` e cole o conteúdo de `.streamlit/secrets.example.toml` preenchido em *Secrets*.
Atrás de proxy reverso (Nginx/IIS/Azure): habilitar WebSocket e encaminhar `/` e `/_stcore/stream`.

## Configuração (segredos)
Ver `.streamlit/secrets.example.toml`. Variáveis de ambiente equivalentes: `PORTAL_ADMIN_EMAIL`, `PORTAL_CONFIG_BACKEND`, `PORTAL_CONFIG_SHEET`, `PORTAL_DATA_DIR`.
- `config_backend = json` guarda usuários/perfis/unidades/conexões em `PORTAL_DATA_DIR/portal_config.json` (precisa de disco persistente: volume Docker).
- `config_backend = sheets` guarda na planilha Google `Portal_Config` (célula A1 da aba `Config`); use em hosts sem disco (Streamlit Cloud).
- Login Microsoft: `docs/LOGIN_MICROSOFT.md`. Google Drive: conta de serviço em `[gcp_service_account]`; compartilhe cada planilha/pasta cadastrada com o e-mail dela (Editor).

## Primeiro acesso
O Administrador inicial é o e-mail de `admin_email`. Em Configurações > Permissionamento, troque pela(s) pessoa(s) real(is) e
cadastre os demais. Em Configurações > Unidades e conexões, cadastre unidades e o endereço (URL ou ID) da planilha e da pasta de cada formulário.

## Segurança
Permissões e escopo de unidade são validados **no servidor** (`core/api.py`); a interface só mostra o que o servidor envia. Invariantes:
ao menos 1 Administrador, conta inicial não removível, ninguém altera o próprio perfil, só Administrador mexe em administradores, unidades não são excluídas (só desativadas).
Segredos nunca vão para o repositório. Trilha de auditoria das alterações em `audit` da configuração.

## Testes
`python -m pytest -q tests`

## Estado
Pronto: login, perfis, permissionamento, unidades, conexões Drive (cadastro/teste), layout. Próximo: migrar cada formulário (Institucional primeiro) para dentro do portal,
mantendo código/regras/Sheets inalterados; depois painéis, evolução, plano de ação e PDF lendo do Drive.

## Formulários migrados
- **Auditoria Institucional (`aud`)**: `forms/institucional/` (schema.py e sheets_backend.py originais; única mudança: imports relativos). `logic.py` reproduz as regras de app.py
  (validação numérica, totais, % de conformidade, registros Visitas/Itens). Rascunho compatível com o app antigo (mesmo formato). O backend lê as planilhas do cadastro do portal
  (Configurações > Unidades e conexões; linha "Consolidado" = planilha consolidada + pasta para criar planilhas das unidades).
- Próximos: Enfermagem, Hospital, UPA/PAM (mesmo padrão: `forms/<nome>/`, entrada em `core/forms_api.py`, tela no portal).

### Visita Técnica · Enfermagem (migrada)
Pacote `forms/enfermagem/` (regras e backend originais; `adapter.py` liga ao portal). Conexão em
Configurações → Unidades e conexões → formulário "Enfermagem": **uma única planilha** e **uma pasta de evidências**
(linha "Planilha única do formulário"). O hospital pode ser uma unidade cadastrada ou texto livre (só perfis globais).
Fotos: reduzidas no navegador (1600 px, JPEG 80), PDF até 10 MB, até 20 anexos por item. Sem credenciais Google,
grava em modo local de teste (`dados_locais/`, `evidencias_locais/`).

### Visita Técnica · Hospital (migrada)
Pacote `forms/hospital_v03/` (24 seções / 77 itens; campos Achado, Evidência e Impacto; etapas 25 Quadro-síntese e
26 Pendências/Observações finais; abas `VT_*`). Mesma tela e mesma conexão da Enfermagem (planilha única + pasta de evidências).
Telas compartilhadas: `portal_ui` (`vtbridge.js`, variante `v03` no catálogo).

### Visita Técnica · UPA e PAM (migrada)
Pacote `forms/upa/` (11 seções / 107 itens; Resposta/valor + Fonte; foco Essencial/Complementar; modo "só essenciais";
impacto por seção; recuperação de anexos do Drive). Abas `UPA_*`. Mesma tela compartilhada (`variant: upa`) e mesma
conexão (planilha única + pasta de evidências).

### Separação das planilhas
Cada formulário grava na sua própria planilha (e, no Institucional, cada unidade na sua). O portal **recusa** cadastrar a mesma
planilha em dois lugares e a mesma pasta de evidências em formulários diferentes (Configurações → Unidades e conexões).
Motivo: Institucional e Enfermagem usam abas com o mesmo nome (Visitas, Itens, Rascunho) e colunas diferentes.


## Publicação e SQLite
Ver `docs/PUBLICAR_STREAMLIT_GITHUB.md` e `docs/SQLITE_PARA_TI.md`.
