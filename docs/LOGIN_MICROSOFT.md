# Login Microsoft (Entra ID) — guia para a TI

O portal usa o login OIDC nativo do Streamlit (`st.login`). O portal **só identifica** a pessoa (e-mail); quem pode entrar e o que vê
é decidido pela lista de usuários em Configurações > Permissionamento. E-mail Microsoft que não está na lista cai na tela
"Seu e-mail ainda não tem acesso" (sem dados expostos).

## 1. Cadastro do aplicativo (Microsoft Entra ID)
1. Entra admin center > Identidade > Aplicativos > **Registros de aplicativo** > Novo registro.
2. Nome: `Portal de Auditoria`. Contas: **somente neste diretório (locatário único)**.
3. URI de redirecionamento (tipo **Web**): `https://<ENDERECO-DO-PORTAL>/oauth2callback`
   (teste local: `http://localhost:8501/oauth2callback`).
4. Anote: **ID do aplicativo (cliente)** e **ID do diretório (locatário)**.
5. Certificados e segredos > Novo segredo do cliente > anote o **valor** (aparece uma vez) e a validade.
6. Permissões de API: `openid`, `profile`, `email` (delegadas; já vêm por padrão, sem consentimento de administrador).
7. (Opcional, recomendado) Aplicativos empresariais > Portal de Auditoria > Propriedades > *Atribuição obrigatória = Sim* e atribua os grupos que podem entrar.

## 2. Segredos no host (nunca no GitHub)
```toml
[auth]
redirect_uri = "https://<ENDERECO-DO-PORTAL>/oauth2callback"
cookie_secret = "<texto aleatório longo>"
[auth.microsoft]
client_id = "<ID do aplicativo>"
client_secret = "<valor do segredo>"
server_metadata_url = "https://login.microsoftonline.com/<ID-DO-LOCATARIO>/v2.0/.well-known/openid-configuration"
client_kwargs = { prompt = "select_account", scope = "openid profile email" }
```
Em Docker/outros hosts sem `secrets.toml`, monte o arquivo em `/app/.streamlit/secrets.toml`.

## 3. Estados da tela de entrada
| Situação | O que a pessoa vê |
|---|---|
| Sem login | Botão "Entrar com conta Microsoft" |
| Microsoft ainda não configurado | Mensagem clara + (só em teste) seletor de usuário de teste |
| Logou, e-mail fora da lista | "O e-mail … ainda não tem acesso" + "Sair e trocar de conta" |
| Logou e autorizado | Portal, com as telas e unidades do perfil |
| Usuário removido/inativo depois | Volta à tela de acesso negado no próximo carregamento |

## 4. Pontos de atenção
- Renovar o segredo do cliente antes de vencer (calendário da TI).
- O e-mail usado é o `email` do token; a comparação ignora maiúsculas/minúsculas.
- Entrada por usuário e senha do próprio portal: **ainda não implementada** (campos presentes na tela; hoje orientam a usar a conta Microsoft).
