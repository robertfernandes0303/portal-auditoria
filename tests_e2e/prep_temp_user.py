"""Prepara o seed local: cria usuários com senha TEMPORÁRIA (troca obrigatória). Rodar com o servidor parado."""
import os, sys
os.environ.setdefault('PORTAL_DATA_DIR', '/tmp/seed_aud')
sys.path.insert(0, '..')
from core.store import Store
s = Store()
MAILS = ['temp@teste.local', 'temp2@teste.local']
s.data['users'] = [u for u in s.data['users'] if u['mail'] not in MAILS]
for i, m in enumerate(MAILS):
    s.data['users'].append({"id": "u-temp%d" % i, "name": "Pessoa Temporaria %d" % i, "mail": m, "role": "admin", "scope": "all", "units": [], "ov": {}, "active": True})
    s.set_password(m, 'Temporaria1', temporaria=True)
s.save()
print('ok', s.kind, s.must_change(MAILS[0]))
