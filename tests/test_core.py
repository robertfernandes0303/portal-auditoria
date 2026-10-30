import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["PORTAL_DATA_DIR"] = "/tmp/portal_test_data"
import shutil; shutil.rmtree("/tmp/portal_test_data", ignore_errors=True)
from core import drive, perms
from core.store import Store, slug


def test_extract_id():
    sid = "1l3r8_sN-G_Q3CyPVjZ0i1GeYD1jBmFu4kLqQDMNYHGQ"
    assert drive.extract_id(f"https://docs.google.com/spreadsheets/d/{sid}/edit#gid=0") == sid
    assert drive.extract_id(f"https://drive.google.com/drive/folders/{sid}?usp=sharing") == sid
    assert drive.extract_id(f"/d/{sid}/edit") == sid
    assert drive.extract_id(sid) == sid
    assert drive.extract_id("abc") is None and drive.extract_id("") is None


def test_defaults_and_scope():
    st = Store()
    assert len(st.units()) == 14 and st.user_by_mail("admin.inicial@portal.local")["role"] == "admin"
    adm = st.users()[0]
    assert perms.allowed_unit_ids(st, adm) == [u["id"] for u in st.units()]
    g = {"id": "x", "name": "G", "mail": "g@x.com", "role": "gestor", "scope": "sel", "units": ["juina"], "ov": {}, "active": True}
    assert perms.allowed_unit_ids(st, g) == ["juina"]
    assert not perms.can(st, g, "nova") and not perms.can(st, g, "perm")
    g["ov"] = {"nova": True}
    assert perms.can(st, g, "nova")
    g["ov"] = {"visitas": False}
    assert not perms.can(st, g, "visitas")


def test_admin_always_all_screens():
    st = Store(); adm = st.users()[0]; adm["ov"] = {"perm": False}
    assert perms.can(st, adm, "perm")


def test_conn_roundtrip():
    st = Store(); st.set_conn("aud", "juina", " https://docs.google.com/spreadsheets/d/AAAAAAAAAAAAAAAAAAAA/edit ", "")
    st.save(); st2 = Store()
    assert st2.conn("aud", "juina")["planilha"].startswith("https://docs.google")
