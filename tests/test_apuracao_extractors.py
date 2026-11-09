import openpyxl

from src.extractors.apuracao_extractors import (
    extrair_informacoes_dae,
    extrair_notas_relatorio_creditos,
)
from src.models.dae_models import NotaCredito
from src.reports.report_generator import gerar_relatorio_creditos_excel, gerar_relatorio_creditos_pdf


def _nota(nota, emissao, uf, liq, empr, bc, aud, descricao="MEIA / CodItem: X / NCM: 61159600"):
    _, mes, ano = emissao.split("/")
    return NotaCredito(
        ano=2000 + int(ano),
        mes=int(mes),
        data_emissao=emissao,
        data_lancamento="22/05/24",
        uf=uf,
        nota=nota,
        descricao=descricao,
        quantidade_itens=1,
        vl_liq_item=liq,
        vl_cred_empr=empr,
        vl_bc_ant_parc=bc,
        vl_cred_aud=aud,
    )


NOTAS = [
    _nota("368470", "19/03/24", "SP", 799.2, 55.95, 799.2, 55.95),
    _nota("32326", "13/05/24", "MG", 1749.76, 30.0, 749.76, 29.5, descricao=" ".join(["VESTUARIO"] * 12)),
]


def _campos(nota: NotaCredito) -> tuple:
    return (nota.nota, nota.data_emissao, nota.uf, nota.vl_liq_item, nota.vl_cred_empr, nota.vl_bc_ant_parc, nota.vl_cred_aud)


def test_le_relatorio_de_creditos_em_excel_gerado_pelo_app(tmp_path):
    caminho = gerar_relatorio_creditos_excel(NOTAS, tmp_path / "creditos.xlsx")

    lidas = extrair_notas_relatorio_creditos(str(caminho))

    assert [_campos(n) for n in lidas] == [_campos(n) for n in NOTAS]
    assert lidas[1].descricao == NOTAS[1].descricao
    assert (lidas[1].ano, lidas[1].mes, lidas[1].data_lancamento) == (2024, 5, "22/05/24")


def test_le_relatorio_de_creditos_em_pdf_gerado_pelo_app(tmp_path):
    caminho = gerar_relatorio_creditos_pdf(NOTAS, tmp_path / "creditos.pdf")

    lidas = extrair_notas_relatorio_creditos(str(caminho))

    assert [_campos(n) for n in lidas] == [_campos(n) for n in NOTAS]
    assert lidas[1].descricao == NOTAS[1].descricao


def test_relatorio_de_creditos_sem_coluna_de_nota_levanta_erro(tmp_path):
    caminho = tmp_path / "outro.xlsx"
    workbook = openpyxl.Workbook()
    workbook.active.append(["Foo", "Bar"])
    workbook.save(str(caminho))

    try:
        extrair_notas_relatorio_creditos(str(caminho))
    except ValueError as erro:
        assert "Nº Nota" in str(erro)
    else:
        raise AssertionError("esperava ValueError")


def _planilha_daes(tmp_path):
    workbook = openpyxl.Workbook()
    planilha = workbook.active
    planilha.append(["Ano", "Número da NF", "Código da Receita (CFOP)", "Valor Principal (R$)", "Informações de Pagamento (DAE)"])
    planilha.append(["2024", "368470", "2175", 107.89, "DAE 2175 03-2024.R$ 231,19"])
    planilha.append([None, 17516, None, 123.3, None])
    planilha.append(["2024", "032326", "2175", 123.7, "DAE 2175 05-2024.R$ 123,70"])
    planilha.append([None, "144676-2175-nº do pagamento", None, None, None])
    planilha.merge_cells("E2:E3")
    caminho = tmp_path / "daes.xlsx"
    workbook.save(str(caminho))
    return str(caminho)


def test_informacoes_dae_por_nota_com_celula_mesclada(tmp_path):
    informacoes = extrair_informacoes_dae(_planilha_daes(tmp_path))

    assert informacoes["368470"] == "DAE 2175 03-2024.R$ 231,19"
    assert informacoes["17516"] == "DAE 2175 03-2024.R$ 231,19"
    assert informacoes["32326"] == "DAE 2175 05-2024.R$ 123,70"
    assert len(informacoes) == 3
