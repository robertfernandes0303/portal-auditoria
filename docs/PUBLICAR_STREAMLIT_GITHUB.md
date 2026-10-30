# Publicar para testes

## 1. GitHub (repositório público durante os testes)
O repositório não contém senha nem segredo (`.streamlit/secrets.toml`, `*.db` e `dados_teste/` ficam fora pelo .gitignore).
No Windows, dentro desta pasta, dê dois cliques em `publicar_github.bat` (pede o login do GitHub na primeira vez), ou:

    git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
    git push -u origin main

## 2. Streamlit Community Cloud (share.streamlit.io)
1. New app → repositório `robertfernandes0303/portal-auditoria`, branch `main`, arquivo principal `app.py`.
2. Advanced settings → Secrets (use `.streamlit/secrets.example.toml` como modelo):
   - `[portal]`: `admin_email`, `admin_password` (senha do primeiro login), `config_backend = "sheets"` e `config_sheet` (planilha Portal_Config; o Streamlit Cloud apaga arquivos ao reiniciar, então SQLite não serve lá), `password_login = "1"`.
   - `[gcp_service_account]`: a conta de serviço do Google. **Necessária**: é por ela que o portal lê e grava as planilhas e o Drive. Compartilhe com o e-mail dela a planilha Portal_Config e as planilhas/pastas de cada formulário.
3. Entre com `admin_email` + `admin_password`. Em Configurações > Permissionamento crie os logins (e senha) das pessoas de teste e defina os perfis. Depois troque a senha do admin e apague `admin_password` dos Secrets.
4. Em Configurações > Unidades e conexões: informe uma planilha e uma pasta **diferentes** para cada formulário (o portal recusa repetir).
5. Login Microsoft (Entra) fica para a TI no ambiente definitivo (`[auth]` nos Secrets).
