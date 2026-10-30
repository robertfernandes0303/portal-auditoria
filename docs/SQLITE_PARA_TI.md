# SQLite no Portal de Auditoria (explicação para quem não é de TI)

**O que é:** SQLite é um banco de dados que vive em **um único arquivo** (`portal.db`). Não precisa instalar servidor, usuário nem porta: o portal abre o arquivo direto. É o formato que a TI pediu e facilita backup (copiar o arquivo) e migração.

**O que fica no SQLite:** cadastros do próprio portal — usuários, perfis, unidades, conexões (qual planilha/pasta de cada formulário), senhas (somente hash scrypt, nunca a senha), plano de ação e histórico de alterações.
Tabelas: `users`, `profiles`, `units`, `connections`, `credentials`, `plans`, `audit`, `meta`.

**O que NÃO muda:** as respostas das visitas continuam indo para as planilhas e pastas do Google (uma planilha e uma pasta diferentes por formulário). Por isso a **conta de serviço da API do Google continua necessária** (`[gcp_service_account]` nos Secrets).

**Onde fica:** pasta de dados (`PORTAL_DATA_DIR`, padrão `./data`). Em hospedagem com disco persistente (servidor/VM/Docker com volume), use isso. **Streamlit Community Cloud apaga arquivos ao reiniciar**: lá use `config_backend = "sheets"` (planilha Portal_Config) para os testes.

**Backup:** copie `portal.db` (e `portal.db-wal` se existir) com o portal parado, ou use `sqlite3 portal.db ".backup backup.db"`.
**Migração:** se existir `portal_config.json` antigo na pasta e o banco estiver vazio, ele é importado sozinho na primeira abertura.
