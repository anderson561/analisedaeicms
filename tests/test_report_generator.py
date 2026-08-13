import pdfplumber

from src.models.dae_models import NotaConciliada, NotaNaoEncontrada
from src.reports.report_generator import (
    gerar_relatorio_conciliadas_pdf,
    gerar_relatorio_nao_encontradas_pdf,
)


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


def test_gerar_relatorio_nao_encontradas_pdf_contem_os_dados(tmp_path):
    nao_encontradas = [
        NotaNaoEncontrada(
            numero_nf="1030",
            data_emissao="10/05/2026",
            cnpj_emitente="12.345.678/0001-90",
        ),
        NotaNaoEncontrada(
            numero_nf="1031",
            data_emissao="11/05/2026",
            cnpj_emitente="98.765.432/0001-10",
        ),
    ]
    caminho = tmp_path / "nao_encontradas.pdf"

    resultado = gerar_relatorio_nao_encontradas_pdf(nao_encontradas, caminho)

    assert resultado == caminho
    assert caminho.exists()

    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    assert "Notas Não Encontradas" in texto
    assert "1030" in texto
    assert "1031" in texto
    assert "10/05/2026" in texto
    assert "12.345.678/0001-90" in texto
    assert "Não Encontrada em Nenhum DAE Processado" in texto


def test_gerar_relatorio_nao_encontradas_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "nao_encontradas_vazio.pdf"

    resultado = gerar_relatorio_nao_encontradas_pdf([], caminho)

    assert resultado.exists()
