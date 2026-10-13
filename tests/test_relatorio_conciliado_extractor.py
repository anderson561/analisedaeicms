import openpyxl

from src.extractors.relatorio_conciliado_extractor import extrair_notas_relatorio_conciliado


def _salvar(tmp_path, abas: dict[str, list[list]]):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    for titulo, linhas in abas.items():
        planilha = workbook.create_sheet(titulo)
        for linha in linhas:
            planilha.append(linha)
    caminho = tmp_path / "relatorio.xlsx"
    workbook.save(str(caminho))
    return str(caminho)


def test_le_todas_as_abas_com_ano_mes_e_aba_de_origem(tmp_path):
    caminho = _salvar(
        tmp_path,
        {
            "Valores Iguais": [
                ["Ano 2021"],
                ["Janeiro"],
                ["Número do Documento", "Valor Notas (R$)", "Valor Entrada (R$)"],
                ["1113041", 2834.4, 2834.4, "Esta no DAE 1145"],
                ["1115087", 726.9, 726.9],
            ],
            "Valores Diferentes": [
                ["Ano 2021"],
                ["Março"],
                ["Número do Documento", "Descrição", "Valor Notas (R$)"],
                ["710944", "CHINELO", 1806.48],
                [],
                ["Abril"],
                ["Número do Documento", "Descrição", "Valor Notas (R$)"],
                ["4918559", "TENIS", 100.0],
            ],
        },
    )

    linhas = extrair_notas_relatorio_conciliado(caminho)

    assert [linha.numero_nf for linha in linhas] == ["1113041", "1115087", "710944", "4918559"]
    primeira = linhas[0].dados_originais
    assert primeira["Aba"] == "Valores Iguais"
    assert primeira["Ano"] == "2021"
    assert primeira["Mês"] == "1"
    assert primeira["Observação"] == "Esta no DAE 1145"
    assert linhas[2].dados_originais["Mês"] == "3"
    assert linhas[2].dados_originais["Descrição"] == "CHINELO"
    assert linhas[3].dados_originais["Mês"] == "4"


def test_ignora_linhas_nao_numericas_e_vazias(tmp_path):
    caminho = _salvar(
        tmp_path,
        {
            "Aba": [
                ["Ano 2022"],
                ["Fevereiro"],
                ["Número do Documento", "Valor Notas (R$)"],
                ["Total", 10],
                [None, None],
                ["  123 ", 5],
            ]
        },
    )

    linhas = extrair_notas_relatorio_conciliado(caminho)

    assert [linha.numero_nf for linha in linhas] == ["123"]


def test_cabecalho_alternativo_e_sem_ano_mes(tmp_path):
    caminho = _salvar(tmp_path, {"Aba": [["Nº NF", "Valor"], [777, 1.0]]})

    linhas = extrair_notas_relatorio_conciliado(caminho)

    assert [linha.numero_nf for linha in linhas] == ["777"]
    assert "Ano" not in linhas[0].dados_originais
    assert "Mês" not in linhas[0].dados_originais


def test_nota_repetida_no_mesmo_mes_nao_e_duplicada(tmp_path):
    caminho = _salvar(
        tmp_path,
        {
            "A": [["Ano 2021"], ["Janeiro"], ["Número do Documento"], ["10"], ["10"]],
            "B": [["Ano 2021"], ["Janeiro"], ["Número do Documento"], ["10"]],
        },
    )

    assert len(extrair_notas_relatorio_conciliado(caminho)) == 1


def test_planilha_sem_coluna_de_nota_levanta_erro(tmp_path):
    caminho = _salvar(tmp_path, {"Aba": [["Foo", "Bar"], [1, 2]]})

    try:
        extrair_notas_relatorio_conciliado(caminho)
    except ValueError as erro:
        assert "Número do Documento" in str(erro)
    else:
        raise AssertionError("esperava ValueError")
