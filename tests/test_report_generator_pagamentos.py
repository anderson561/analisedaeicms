import openpyxl
import pdfplumber

from src.models.dae_models import DaePagamentoNaoLocalizado, LinhaPagamentoDae, PagamentoConfirmado
from src.reports.report_generator import (
    gerar_relatorio_pagamentos_confirmados,
    gerar_relatorio_pagamentos_nao_localizados,
    gerar_relatorio_pagamentos_pdf,
)


def test_gerar_relatorio_pagamentos_confirmados_contem_os_dados(tmp_path):
    confirmados = [
        PagamentoConfirmado(
            dae_arquivo_origem="Macedo DAE 1145 09-2022.pdf",
            linha_pagamento=LinhaPagamentoDae(
                nosso_numero="2113874976",
                data_pagamento="25/02/2022",
                referencia_bruta="1/2022",
                mes_referencia=1,
                ano_referencia=2022,
                codigo_receita="1145",
                descricao_receita="ICMS ANTECIPAÇÃO TRIBUTÁRIA",
                valor_principal=852.93,
                valor_total=852.93,
            ),
        )
    ]
    caminho = tmp_path / "pagamentos_confirmados.xlsx"

    resultado = gerar_relatorio_pagamentos_confirmados(confirmados, caminho)

    assert resultado == caminho
    assert caminho.exists()

    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    cabecalho = [c.value for c in planilha[1]]
    linha = [c.value for c in planilha[2]]

    assert cabecalho == ["Nosso Número", "Pagamento", "Referência", "Receita", "Val. Principal", "Val. Total"]
    assert linha[0] == "2113874976"
    assert linha[1] == "25/02/2022"
    assert linha[2] == "1/2022"
    assert linha[3] == "1145 - ICMS ANTECIPAÇÃO TRIBUTÁRIA"
    assert linha[4] == 852.93
    assert linha[5] == 852.93


def test_gerar_relatorio_pagamentos_confirmados_lista_vazia(tmp_path):
    caminho = tmp_path / "pagamentos_confirmados_vazio.xlsx"

    resultado = gerar_relatorio_pagamentos_confirmados([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_pagamentos_nao_localizados_contem_os_dados(tmp_path):
    nao_localizados = [
        DaePagamentoNaoLocalizado(
            arquivo_origem="Macedo DAE 2175 05-2022.pdf",
            codigo_receita="2175",
            referencia="05/2022",
            valor_principal=784.01,
        )
    ]
    caminho = tmp_path / "pagamentos_nao_localizados.xlsx"

    resultado = gerar_relatorio_pagamentos_nao_localizados(nao_localizados, caminho)

    assert resultado.exists()

    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    linha = [c.value for c in planilha[2]]

    assert linha[0] == "Macedo DAE 2175 05-2022.pdf"
    assert linha[1] == "2175"
    assert linha[2] == "05/2022"
    assert linha[3] == 784.01
    assert linha[4] == "Não Localizada no Relatório de Pagamentos"


def test_gerar_relatorio_pagamentos_nao_localizados_lista_vazia(tmp_path):
    caminho = tmp_path / "pagamentos_nao_localizados_vazio.xlsx"

    resultado = gerar_relatorio_pagamentos_nao_localizados([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_pagamentos_pdf_contem_as_duas_secoes(tmp_path):
    confirmados = [
        PagamentoConfirmado(
            dae_arquivo_origem="Macedo DAE 2175 05-2022.pdf",
            linha_pagamento=LinhaPagamentoDae(
                nosso_numero="2117979376",
                data_pagamento="27/06/2022",
                referencia_bruta="5/2022",
                mes_referencia=5,
                ano_referencia=2022,
                codigo_receita="2175",
                descricao_receita="ICMS - ANTECIPACAO PARCIAL",
                valor_principal=784.01,
                valor_total=784.01,
            ),
        )
    ]
    nao_localizados = [
        DaePagamentoNaoLocalizado(
            arquivo_origem="Macedo DAE 1145 09-2022.pdf",
            codigo_receita="1145",
            referencia="09/2022",
            valor_principal=4998.63,
        )
    ]
    caminho = tmp_path / "pagamentos.pdf"

    resultado = gerar_relatorio_pagamentos_pdf(confirmados, nao_localizados, caminho)

    assert resultado == caminho
    assert caminho.exists()

    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    assert "Relatório de Pagamentos" in texto
    assert "Pagamentos Confirmados" in texto
    assert "2117979376" in texto
    assert "784.01" in texto
    assert "Não Localizados" in texto
    assert "Macedo DAE 1145 09-2022.pdf" in texto
    assert "4998.63" in texto


def test_gerar_relatorio_pagamentos_pdf_listas_vazias(tmp_path):
    caminho = tmp_path / "pagamentos_vazio.pdf"

    resultado = gerar_relatorio_pagamentos_pdf([], [], caminho)

    assert resultado.exists()
