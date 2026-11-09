import openpyxl

from src.models.dae_models import NotaCredito
from src.reports.report_generator import (
    COLUNAS_CREDITOS,
    gerar_relatorio_creditos_excel,
    gerar_relatorio_creditos_pdf,
)


def _nota(nota, mes, liq, empr, aud, dia="13"):
    return NotaCredito(
        ano=2024,
        mes=mes,
        data_emissao=f"{dia}/{mes:02d}/24",
        data_lancamento=f"22/{mes:02d}/24",
        uf="MG",
        nota=nota,
        descricao="MEIA / CodItem: X / NCM: 61159600",
        quantidade_itens=1,
        vl_liq_item=liq,
        vl_cred_empr=empr,
        vl_bc_ant_parc=liq,
        vl_cred_aud=aud,
    )


def test_excel_agrupa_por_mes_com_totais_mensais_e_geral(tmp_path):
    notas = [_nota("32326", 5, 749.76, 30.0, 30.0), _nota("1", 5, 100.0, 7.0, 7.0), _nota("2", 6, 50.0, 3.5, 3.5)]
    caminho = tmp_path / "creditos.xlsx"

    gerar_relatorio_creditos_excel(notas, caminho)

    linhas = [list(r) for r in openpyxl.load_workbook(caminho).active.iter_rows(values_only=True)]
    assert linhas[0][0] == "Ano 2024"
    assert linhas[1][0] == "Maio"
    assert linhas[2] == COLUNAS_CREDITOS
    assert linhas[3] == ["13/05/24", "22/05/24", "MG", "32326", "MEIA / CodItem: X / NCM: 61159600", 749.76, 30.0, 749.76, 30.0]
    assert linhas[5][4] == "Total de Maio"
    assert linhas[5][5:] == [849.76, 37.0, 849.76, 37.0]
    assert "Junho" in [linha[0] for linha in linhas]
    assert linhas[-1][4] == "Total Geral"
    assert linhas[-1][5:] == [899.76, 40.5, 899.76, 40.5]


def test_excel_lista_vazia_tem_cabecalho(tmp_path):
    caminho = tmp_path / "vazio.xlsx"

    gerar_relatorio_creditos_excel([], caminho)

    primeira = next(openpyxl.load_workbook(caminho).active.iter_rows(values_only=True))
    assert list(primeira) == COLUNAS_CREDITOS


def test_pdf_gerado(tmp_path):
    caminho = tmp_path / "creditos.pdf"

    resultado = gerar_relatorio_creditos_pdf([_nota("32326", 5, 749.76, 30.0, 30.0)], caminho)

    assert resultado.exists() and resultado.stat().st_size > 0


def test_pdf_lista_vazia(tmp_path):
    assert gerar_relatorio_creditos_pdf([], tmp_path / "vazio.pdf").exists()
