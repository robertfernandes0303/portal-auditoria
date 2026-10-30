"""Armazenamento da configuração do portal (usuários, perfis, unidades, conexões).
Backends: SQLite (padrão; arquivo portal.db), JSON local (teste) ou planilha Google (hospedagem sem disco persistente)."""
import json, os, re, threading, copy
from core import settings
from core.catalog import DEFAULT_PROFILES, DEFAULT_UNITS

_LOCK = threading.Lock()


def slug(txt):
    import unicodedata
    t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "item"


def _defaults():
    admin_mail = settings.secret("portal.admin_email", "admin.inicial@portal.local")
    return {
        "profiles": copy.deepcopy(DEFAULT_PROFILES),
        "units": [{"id": slug(n), "nome": n, "ativo": True} for n in DEFAULT_UNITS],
        "users": [{"id": "u-admin", "name": "Administrador Inicial", "mail": admin_mail, "role": "admin",
                   "scope": "all", "units": [], "ov": {}, "active": True, "fict": True}],
        "connections": {},
        "credentials": {},
        "audit": [],
        "plans": {},
    }


class JsonBackend:
    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return None
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)


class SqliteBackend:
    """Banco SQLite (um único arquivo, portal.db, sem servidor). Tabelas: profiles, units, users, connections,
    credentials, plans, audit e meta. Gravação em uma transação (tudo ou nada), modo WAL. Se o banco está vazio e existe
    um portal_config.json antigo na mesma pasta, importa esse arquivo na primeira leitura."""
    LISTAS = ("profiles", "units", "users", "connections", "credentials", "plans", "audit")

    def __init__(self, path):
        self.path = path
        self.legado = os.path.join(os.path.dirname(path), "portal_config.json")

    def _con(self):
        import sqlite3
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        con = sqlite3.connect(self.path, timeout=15)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript("""
        CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, label TEXT, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS units(id TEXT PRIMARY KEY, nome TEXT NOT NULL, ativo INTEGER NOT NULL DEFAULT 1, ord INTEGER NOT NULL, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, mail TEXT NOT NULL UNIQUE, name TEXT, role TEXT, scope TEXT, ativo INTEGER NOT NULL DEFAULT 1, ord INTEGER NOT NULL, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS connections(k TEXT PRIMARY KEY, planilha TEXT, pasta TEXT, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS credentials(mail TEXT PRIMARY KEY, hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS plans(k TEXT PRIMARY KEY, unit TEXT, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, who TEXT, what TEXT);
        """)
        return con

    def load(self):
        con = self._con()
        try:
            if con.execute("SELECT 1 FROM meta WHERE k='init'").fetchone() is None:
                if os.path.exists(self.legado):
                    with open(self.legado, encoding="utf-8") as f:
                        antigo = json.load(f)
                    con.close()
                    self.save(antigo)
                    con = self._con()
                else:
                    return None
            j = json.loads
            d = {
                "profiles": {r[0]: j(r[1]) for r in con.execute("SELECT id, data FROM profiles")},
                "units": [j(r[0]) for r in con.execute("SELECT data FROM units ORDER BY ord")],
                "users": [j(r[0]) for r in con.execute("SELECT data FROM users ORDER BY ord")],
                "connections": {r[0]: j(r[1]) for r in con.execute("SELECT k, data FROM connections")},
                "credentials": {r[0]: r[1] for r in con.execute("SELECT mail, hash FROM credentials")},
                "plans": {r[0]: j(r[1]) for r in con.execute("SELECT k, data FROM plans")},
                "audit": [{"ts": r[0], "who": r[1], "what": r[2]} for r in con.execute("SELECT ts, who, what FROM audit ORDER BY id DESC")],
            }
            for k, v in con.execute("SELECT k, v FROM meta WHERE k<>'init'"):
                d[k] = j(v)
            return d
        finally:
            con.close()

    def save(self, data):
        con = self._con()
        try:
            dump = lambda o: json.dumps(o, ensure_ascii=False)
            with con:                                       # transação única
                for t in self.LISTAS:
                    con.execute(f"DELETE FROM {t}")
                con.execute("DELETE FROM meta")
                con.execute("INSERT INTO meta VALUES('init','1')")
                for k, p in data.get("profiles", {}).items():
                    con.execute("INSERT INTO profiles VALUES(?,?,?)", (k, p.get("label"), dump(p)))
                for i, u in enumerate(data.get("units", [])):
                    con.execute("INSERT INTO units VALUES(?,?,?,?,?)", (u["id"], u["nome"], 1 if u.get("ativo", True) else 0, i, dump(u)))
                for i, u in enumerate(data.get("users", [])):
                    con.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?)", (u["id"], u["mail"].strip().lower(), u.get("name"), u.get("role"),
                                u.get("scope"), 1 if u.get("active", True) else 0, i, dump(u)))
                for k, c in data.get("connections", {}).items():
                    con.execute("INSERT INTO connections VALUES(?,?,?,?)", (k, c.get("planilha", ""), c.get("pasta", ""), dump(c)))
                for m, h in data.get("credentials", {}).items():
                    con.execute("INSERT INTO credentials VALUES(?,?)", (m, h))
                for k, p in data.get("plans", {}).items():
                    con.execute("INSERT INTO plans VALUES(?,?,?)", (k, p.get("unit"), dump(p)))
                for a in reversed(data.get("audit", [])):
                    con.execute("INSERT INTO audit(ts,who,what) VALUES(?,?,?)", (a.get("ts"), a.get("who"), a.get("what")))
                for k, v in data.items():
                    if k not in self.LISTAS:
                        con.execute("INSERT INTO meta VALUES(?,?)", (k, dump(v)))
        finally:
            con.close()


class SheetsBackend:
    """Guarda o JSON inteiro numa célula da aba 'Config' (A1) da planilha Portal_Config. Simples e auditável."""
    def __init__(self, ref):
        from core import drive
        self.ref = ref
        self.drive = drive

    def _ws(self):
        sh = self.drive.open_spreadsheet(self.ref)
        try:
            return sh.worksheet("Config")
        except Exception:
            return sh.add_worksheet("Config", rows=10, cols=2)

    def load(self):
        v = self._ws().acell("A1").value
        return json.loads(v) if v else None

    def save(self, data):
        txt = json.dumps(data, ensure_ascii=False)
        if len(txt) > 45000:
            raise ValueError("Configuração grande demais para uma célula; migrar para banco.")
        self._ws().update_acell("A1", txt)


class Store:
    def __init__(self):
        kind = settings.secret("portal.config_backend", "sqlite")
        if kind == "sheets" and settings.secret("portal.config_sheet"):
            self.backend = SheetsBackend(settings.secret("portal.config_sheet"))
            self.kind = "sheets"
        elif kind == "json":
            self.backend = JsonBackend(os.path.join(settings.DATA_DIR, "portal_config.json"))
            self.kind = "json"
        else:
            self.backend = SqliteBackend(os.path.join(settings.DATA_DIR, "portal.db"))
            self.kind = "sqlite"
        self.data = None
        self.reload()
        self._admin_inicial()

    def _admin_inicial(self):
        """Primeiro acesso em hospedagem nova: portal.admin_password (secrets) define a senha do administrador inicial
        (portal.admin_email) se ele ainda não tem senha. Depois disso, troque a senha em Permissionamento e remova o secret."""
        pw, am = settings.secret("portal.admin_password"), (settings.secret("portal.admin_email") or "").strip().lower()
        if pw and am and len(str(pw)) >= 8 and am not in self.data.get("credentials", {}):
            u = self.user_by_mail(am)
            if u and u["role"] == "admin":
                self.set_password(am, str(pw))

    def reload(self):
        with _LOCK:
            data = self.backend.load()
            base = _defaults()
            if data is None:
                data = base
                self.backend.save(data)
            for k, v in base.items():
                data.setdefault(k, v)
            self.data = data

    def save(self):
        with _LOCK:
            self.backend.save(self.data)

    # ---- auditoria
    def log(self, who, what):
        from datetime import datetime, timezone, timedelta
        ts = datetime.now(timezone(timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M")
        self.data["audit"] = ([{"ts": ts, "who": who, "what": what}] + self.data["audit"])[:200]

    # ---- credenciais (login por e-mail e senha)
    def set_password(self, mail, senha):
        from core import passwords
        self.data["credentials"][mail.strip().lower()] = passwords.hash_senha(senha)
        self.save()

    def check_password(self, mail, senha):
        from core import passwords
        h = self.data["credentials"].get((mail or "").strip().lower())
        u = self.user_by_mail(mail)
        return bool(h and u and u.get("active", True) and passwords.confere(senha or "", h))

    # ---- usuários
    def users(self):
        return self.data["users"]

    def user_by_mail(self, mail):
        m = (mail or "").strip().lower()
        for u in self.data["users"]:
            if u["mail"].strip().lower() == m:
                return u
        return None

    def admins_active(self, except_id=None):
        return [u for u in self.data["users"] if u["role"] == "admin" and u.get("active", True) and u["id"] != except_id]

    # ---- unidades
    def units(self, only_active=True):
        return [u for u in self.data["units"] if u.get("ativo", True) or not only_active]

    def unit_name(self, uid):
        for u in self.data["units"]:
            if u["id"] == uid:
                return u["nome"]
        return uid

    # ---- conexões (planilha/pasta por formulário x unidade)
    def conn(self, form, unit_id):
        return self.data["connections"].get(f"{form}|{unit_id}", {"planilha": "", "pasta": ""})

    def set_conn(self, form, unit_id, planilha, pasta):
        self.data["connections"][f"{form}|{unit_id}"] = {"planilha": planilha.strip(), "pasta": pasta.strip()}
