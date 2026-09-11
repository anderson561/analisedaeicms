import openpyxl
import pdfplumber

from src.models.dae_models import NotaConciliada, NotaNaoEncontrada
from src.reports.report_generator import (
    gerar_relatorio_conciliadas,
    gerar_relatorio_conciliadas_pdf,
    gerar_relatorio_nao_encontradas,
    gerar_relatorio_nao_encontradas_pdf,
)


def test_gerar_relatorio_conciliadas_pdf_contem_os_dados_agrupados_por_ano_e_mes(tmp_path):
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
            referencia="05/2025",
            valor_principal=300.00,
            especificacao_receita="ICMS ST Antecipado",
        ),
        NotaConciliada(
            numero_nf="1022",
            codigo_receita="113-5",
            referencia="06/2025",
            valor_principal=100.00,
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
    assert "1022" in texto
    assert "113-5" in texto
    assert "450.00" in texto
    assert "300.00" in texto
    assert "100.00" in texto
    assert "ICMS ST Antecipado" in texto

    ano_2025 = texto.index("Ano 2025")
    mes_05 = texto.index("Mês 05")
    mes_06 = texto.index("Mês 06")
    ano_2026 = texto.index("Ano 2026")
    assert ano_2025 < mes_05 < mes_06 < ano_2026


def test_gerar_relatorio_conciliadas_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "conciliadas_vazio.pdf"

    resultado = gerar_relatorio_conciliadas_pdf([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_conciliadas_excel_agrupa_por_ano_e_mes(tmp_path):
    conciliadas = [
        NotaConciliada(numero_nf="1020", codigo_receita="113-5", referencia="05/2026", valor_principal=450.00),
        NotaConciliada(numero_nf="1021", codigo_receita="113-5", referencia="05/2025", valor_principal=300.00),
        NotaConciliada(numero_nf="1022", codigo_receita="113-5", referencia="06/2025", valor_principal=100.00),
    ]
    caminho = tmp_path / "conciliadas.xlsx"

    resultado = gerar_relatorio_conciliadas(conciliadas, caminho)

    assert resultado == caminho
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    valores = [[c.value for c in linha] for linha in planilha.iter_rows()]

    assert valores[0][0] == "Ano 2025"
    assert valores[1][0] == "Mês 05"
    assert valores[2][0] == "Número da NF"
    assert valores[3][0] == "1021"
    assert valores[4][0] is None
    assert valores[5][0] == "Mês 06"
    assert valores[6][0] == "Número da NF"
    assert valores[7][0] == "1022"
    assert valores[8][0] is None
    assert valores[9][0] == "Ano 2026"
    assert valores[10][0] == "Mês 05"
    assert valores[12][0] == "1020"


def test_gerar_relatorio_conciliadas_excel_lista_vazia(tmp_path):
    caminho = tmp_path / "conciliadas_vazio.xlsx"

    resultado = gerar_relatorio_conciliadas([], caminho)

    assert resultado.exists()
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    assert [c.value for c in next(planilha.iter_rows())] == [
        "Número da NF",
        "Código da Receita",
        "Referência",
        "Valor Principal (R$)",
        "Especificação da Receita",
        "Status",
    ]


def test_gerar_relatorio_nao_encontradas_pdf_contem_os_dados_agrupados_por_ano_e_mes(tmp_path):
    nao_encontradas = [
        NotaNaoEncontrada(
            numero_nf="1030",
            data_emissao="10/05/2026",
            cnpj_emitente="12.345.678/0001-90",
        ),
        NotaNaoEncontrada(
            numero_nf="1031",
            data_emissao="11/06/2026",
            cnpj_emitente="98.765.432/0001-10",
        ),
        NotaNaoEncontrada(
            numero_nf="1032",
            data_emissao="15/05/2025",
            cnpj_emitente="11.222.333/0001-44",
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
    assert "1032" in texto
    assert "12.345.678/0001-90" in texto
    assert "Não Encontrada em Nenhum DAE Processado" in texto

    ano_2025 = texto.index("Ano 2025")
    ano_2026 = texto.index("Ano 2026")
    mes_05 = texto.index("Mês 05", ano_2026)
    mes_06 = texto.index("Mês 06", ano_2026)
    assert ano_2025 < ano_2026 < mes_05 < mes_06


def test_gerar_relatorio_nao_encontradas_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "nao_encontradas_vazio.pdf"

    resultado = gerar_relatorio_nao_encontradas_pdf([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_nao_encontradas_excel_agrupa_por_ano_e_mes(tmp_path):
    nao_encontradas = [
        NotaNaoEncontrada(numero_nf="1030", data_emissao="10/05/2026", cnpj_emitente="12.345.678/0001-90"),
        NotaNaoEncontrada(numero_nf="1032", data_emissao="15/05/2025", cnpj_emitente="11.222.333/0001-44"),
        NotaNaoEncontrada(numero_nf="1033", data_emissao=None, cnpj_emitente=None),
    ]
    caminho = tmp_path / "nao_encontradas.xlsx"

    resultado = gerar_relatorio_nao_encontradas(nao_encontradas, caminho)

    assert resultado == caminho
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    valores = [[c.value for c in linha] for linha in planilha.iter_rows()]

    assert valores[0][0] == "Ano 2025"
    assert valores[1][0] == "Mês 05"
    assert valores[3][0] == "1032"
    assert valores[5][0] == "Ano 2026"
    assert valores[6][0] == "Mês 05"
    assert valores[8][0] == "1030"

    ultimo_bloco_ano = [linha[0] for linha in valores].index("Sem Ano Identificado")
    assert valores[ultimo_bloco_ano + 1][0] == "Sem Mês Identificado"
    assert valores[ultimo_bloco_ano + 3][0] == "1033"


def test_gerar_relatorio_nao_encontradas_excel_lista_vazia(tmp_path):
    caminho = tmp_path / "nao_encontradas_vazio.xlsx"

    resultado = gerar_relatorio_nao_encontradas([], caminho)

    assert resultado.exists()
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    assert [c.value for c in next(planilha.iter_rows())] == [
        "Número da NF",
        "Data de Emissão",
        "CNPJ do Emitente",
        "Status",
    ]
