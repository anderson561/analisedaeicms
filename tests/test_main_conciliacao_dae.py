import openpyxl

from src import main
from src.models.dae_models import DaeDocumento


def test_conciliar_relatorio_com_daes_lote_separa_encontradas_e_nao_encontradas(tmp_path, monkeypatch):
    workbook = openpyxl.Workbook()
    planilha = workbook.active
    for linha in (
        ["Ano 2021"],
        ["Janeiro"],
        ["Número do Documento", "Valor Notas (R$)"],
        ["1113041", 2834.4],
        ["999", 10],
    ):
        planilha.append(linha)
    caminho_relatorio = tmp_path / "relatorio.xlsx"
    workbook.save(str(caminho_relatorio))

    monkeypatch.setattr(
        main,
        "extrair_dae",
        lambda caminho: DaeDocumento(
            arquivo_origem=caminho,
            codigo_receita="1145",
            referencia="01/2021",
            valor_principal=2637.36,
            notas_fiscais=["1113041"],
        ),
    )

    conciliadas, nao_encontradas = main.conciliar_relatorio_com_daes_lote(
        [str(tmp_path / "DAE 1145.pdf")], str(caminho_relatorio)
    )

    assert [n.numero_nf for n in conciliadas] == ["1113041"]
    assert conciliadas[0].dae_arquivo_origem == "DAE 1145.pdf"
    assert conciliadas[0].valor_principal == 2637.36
    assert [(n.numero_nf, n.ano, n.mes) for n in nao_encontradas] == [("999", 2021, 1)]
