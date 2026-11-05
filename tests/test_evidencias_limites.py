"""Limites de anexo (foto/PDF): extensão, tamanho, arquivo falso e redução da foto."""
import io
import pytest
from PIL import Image
from forms.enfermagem import evidencias as ev, schema as sc


def _jpg(w, h):
    b = io.BytesIO(); Image.new("RGB", (w, h), (10, 120, 200)).save(b, "JPEG", quality=95); return b.getvalue()


def test_foto_grande_e_reduzida():
    out, nome, mime, tipo = ev.preparar_arquivo(_jpg(4000, 3000), "IMG 1.JPG")
    im = Image.open(io.BytesIO(out)); assert max(im.size) <= sc.LADO_MAX_IMAGEM_PX and mime == "image/jpeg" and nome.endswith(".jpg")


@pytest.mark.parametrize("nome", ["virus.exe", "planilha.xlsx", "texto.txt", "semextensao"])
def test_extensao_nao_permitida(nome):
    with pytest.raises(ev.EvidenciaErro):
        ev.preparar_arquivo(b"abc", nome)


def test_pdf_acima_do_limite_e_arquivo_falso():
    with pytest.raises(ev.EvidenciaErro):
        ev.preparar_arquivo(b"%PDF-1.4" + b"0" * (sc.MAX_MB_PDF * 1024 * 1024 + 10), "grande.pdf")
    with pytest.raises(ev.EvidenciaErro):
        ev.preparar_arquivo(b"isto nao e uma imagem", "falsa.jpg")


def test_limite_por_item_igual_nos_formularios():
    from forms.hospital_v03 import schema as s3
    from forms.upa import schema as su
    from forms.institucional import schema as si
    assert sc.MAX_ANEXOS_POR_ITEM == s3.MAX_ANEXOS_POR_ITEM == su.MAX_ANEXOS_POR_ITEM == si.MAX_ANEXOS_POR_ITEM == 20
