import pdfplumber

from src.models.dae_models import NotaConciliada
from src.reports.report_generator import gerar_relatorio_conciliadas_pdf


def test_gerar_relatorio_conciliadas_pdf_contem_os_dados(tmp_path):
    conciliadas = [
        NotaConciliada(
            numero_nf="1020",
            codigo_receita="113-5",
            referencia="05/2026",
            valor_principal=450.00,
            especificacao_receita="ICMS ST Antecipado",
        ),
        NotaConciliada(
            numero_nf="1021",
            codigo_receita="113-5",
            referencia="05/2026",
            valor_principal=450.00,
            especificacao_receita="ICMS ST Antecipado",
        ),
    ]
    caminho = tmp_path / "conciliadas.pdf"

    resultado = gerar_relatorio_conciliadas_pdf(conciliadas, caminho)

    assert resultado == caminho
    assert caminho.exists()

    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    assert "Notas Conciliadas" in texto
    assert "1020" in texto
    assert "1021" in texto
    assert "113-5" in texto
    assert "05/2026" in texto
    assert "450.00" in texto
    assert "ICMS ST Antecipado" in texto


def test_gerar_relatorio_conciliadas_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "conciliadas_vazio.pdf"

    resultado = gerar_relatorio_conciliadas_pdf([], caminho)

    assert resultado.exists()
