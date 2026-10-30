"""Cria (ou atualiza) um administrador e define a senha dele no login por e-mail e senha.

Uso:  python -m core.bootstrap_admin --mail nome@isssl.com.br --name "Nome Sobrenome" [--senha ...]
Sem --senha, gera uma senha forte e mostra uma única vez. Rode no servidor onde ficam os dados do portal
(PORTAL_DATA_DIR). Em produção com login Microsoft, não é necessário."""
import argparse
import secrets
import string

from core.store import Store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--senha")
    a = ap.parse_args()
    senha = a.senha or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(14))
    if len(senha) < 8:
        raise SystemExit("A senha precisa ter pelo menos 8 caracteres.")
    st = Store()
    u = st.user_by_mail(a.mail)
    if u:
        u.update(role="admin", scope="all", units=[], active=True, name=a.name)
    else:
        st.data["users"].append({"id": "u-" + secrets.token_hex(4), "name": a.name, "mail": a.mail.strip().lower(), "role": "admin",
                                 "scope": "all", "units": [], "ov": {}, "active": True})
    st.set_password(a.mail, senha)
    st.log("bootstrap", f"Administrador {a.mail} criado/atualizado")
    st.save()
    print(f"E-mail: {a.mail}\nSenha:  {senha}")


if __name__ == "__main__":
    main()
