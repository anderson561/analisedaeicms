import openpyxl

from src.models.dae_models import AnaliseApuracao, NotaCredito
from src.reports.report_generator import (
    COLUNAS_APURACAO,
    gerar_relatorio_apuracao_excel,
    gerar_relatorio_apuracao_pdf,
)


def _analise(nota, emissao, liq, valor_pago, informacao):
    _, mes, ano = emissao.split("/")
    credito = NotaCredito(
        ano=2000 + int(ano),
        mes=int(mes),
        data_emissao=emissao,
        data_lancamento="22/05/24",
        uf="MG",
        nota=nota,
        descricao="MEIA",
        quantidade_itens=1,
        vl_liq_item=liq,
        vl_cred_empr=30.0,
        vl_bc_ant_parc=liq,
        vl_cred_aud=30.0,
    )
    return AnaliseApuracao(nota=credito, valor_pago=valor_pago, informacao_norte=informacao)


ANALISES = [
    _analise("32326", "13/05/24", 749.76, 123.7, "DAE 2175 05-2024.R$ 123,70"),
    _analise("1", "20/05/24", 100.0, 10.0, "DAE Y"),
    _analise("9992", "30/09/24", 1107.84, None, "Não encontrada na planilha de antecipação"),
]


def test_colunas_sem_data_lancamento_e_uf_com_valor_pago_e_informacao_norte():
    assert COLUNAS_APURACAO == [
        "Data Emissão",
        "Nº Nota",
        "Descrição / CodItem / NCM",
        "VlLiqItem (R$)",
        "VlCredEmpr (R$)",
        "VlBcAntParc (R$)",
        "VlCredAud (R$)",
        "Valor Pago (R$)",
        "Informação Norte",
    ]


def test_excel_uma_tabela_por_mes_com_totais(tmp_path):
    caminho = gerar_relatorio_apuracao_excel(ANALISES, tmp_path / "apuracao.xlsx")

    linhas = [list(r) for r in openpyxl.load_workbook(caminho).active.iter_rows(values_only=True)]
    assert linhas[0][0] == "Ano 2024"
    assert linhas[1][0] == "Maio"
    assert linhas[2] == COLUNAS_APURACAO
    assert linhas[3] == ["13/05/24", "32326", "MEIA", 749.76, 30.0, 749.76, 30.0, 123.7, "DAE 2175 05-2024.R$ 123,70"]
    assert linhas[5][2] == "Total de Maio"
    assert linhas[5][3:8] == [849.76, 60.0, 849.76, 60.0, 133.7]
    assert linhas[-1][2] == "Total Geral"
    assert linhas[-1][3:8] == [1957.6, 90.0, 1957.6, 90.0, 133.7]
    nota_sem_valor = next(linha for linha in linhas if linha[1] == "9992")
    assert nota_sem_valor[7] is None


def test_excel_sem_tabela_de_analise_separada(tmp_path):
    caminho = gerar_relatorio_apuracao_excel(ANALISES, tmp_path / "apuracao.xlsx")

    textos = [c for r in openpyxl.load_workbook(caminho).active.iter_rows(values_only=True) for c in r if c]
    assert "Análise da Apuração" not in textos
    assert textos.count("Valor Pago (R$)") == 2  # um cabeçalho por mês (maio e setembro)


def test_pdf_gerado(tmp_path):
    caminho = gerar_relatorio_apuracao_pdf(ANALISES, tmp_path / "apuracao.pdf")

    assert caminho.exists() and caminho.stat().st_size > 0


def test_pdf_sem_notas(tmp_path):
    assert gerar_relatorio_apuracao_pdf([], tmp_path / "vazio.pdf").exists()
