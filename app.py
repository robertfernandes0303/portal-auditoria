"""Portal de Auditoria · São Lucas Instituto (CDQ). Ponto de entrada (Streamlit). A regra de negócio fica em core/api.py,
portátil para qualquer host (ver README)."""
from core import host

host.run()
