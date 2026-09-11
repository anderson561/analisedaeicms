import openpyxl
import pdfplumber

from src.models.dae_models import LinhaIcmsAt
from src.reports.report_generator import gerar_relatorio_icms_at_excel, gerar_relatorio_icms_at_pdf


def _linhas_exemplo() -> list[LinhaIcmsAt]:
    return [
        LinhaIcmsAt(ano=2021, mes=6, valor_apurado=3017.16, valor_pago=1187.99, valor_a_recolher=1829.17),
        LinhaIcmsAt(ano=2021, mes=7, valor_apurado=0.0, valor_pago=2219.19, valor_a_recolher=0.0),
        LinhaIcmsAt(ano=2022, mes=1, valor_apurado=1052.27, valor_pago=0.0, valor_a_recolher=1052.27),
    ]


def test_gerar_relatorio_icms_at_excel_agrupado_por_ano_e_mes(tmp_path):
    caminho = tmp_path / "icms_at.xlsx"

    resultado = gerar_relatorio_icms_at_excel(_linhas_exemplo(), caminho)

    assert resultado == caminho
    assert caminho.exists()

    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    valores = [[c.value for c in linha] for linha in planilha.iter_rows()]

    assert valores[0][0] == "Ano 2021"
    assert valores[1][0] == "Mês 06"
    assert valores[2][0] == "Valor Apurado (R$)"
    assert valores[3][0] == 3017.16
    assert valores[3][1] == 1187.99
    assert valores[3][2] == 1829.17

    assert valores[5][0] == "Mês 07"

    indice_ano_2022 = next(i for i, linha in enumerate(valores) if linha[0] == "Ano 2022")
    assert valores[indice_ano_2022 + 1][0] == "Mês 01"


def test_gerar_relatorio_icms_at_excel_lista_vazia(tmp_path):
    caminho = tmp_path / "icms_at_vazio.xlsx"

    resultado = gerar_relatorio_icms_at_excel([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_icms_at_pdf_contem_titulo_e_valores(tmp_path):
    caminho = tmp_path / "icms_at.pdf"

    resultado = gerar_relatorio_icms_at_pdf(_linhas_exemplo(), caminho)

    assert resultado == caminho
    assert caminho.exists()

    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    assert "Buscas ICMS Antecipação Tributária" in texto
    assert "Ano 2021" in texto
    assert "Mês 06" in texto
    assert "3017.16" in texto
    assert "1829.17" in texto
    assert "Ano 2022" in texto


def test_gerar_relatorio_icms_at_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "icms_at_vazio.pdf"

    resultado = gerar_relatorio_icms_at_pdf([], caminho)

    assert resultado.exists()
