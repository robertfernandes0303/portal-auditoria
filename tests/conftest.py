import importlib, pytest


@pytest.fixture(autouse=True)
def _tmp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("PORTAL_DATA_DIR", str(tmp_path))
    from core import settings
    importlib.reload(settings)


@pytest.fixture(autouse=True)
def _tmp_local(tmp_path, monkeypatch):
    from forms.institucional import sheets_backend
    monkeypatch.setattr(sheets_backend, "LOCAL_DIR", str(tmp_path / "dl"))
