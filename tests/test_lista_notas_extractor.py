from src.extractors.lista_notas_extractor import _agrupar_em_linhas, _itens_das_linhas, _parse_item, _parse_linha


def _linha_item() -> list[str]:
    return [
        "05/01/21", "13/01/21", "--", "08/01/21", "08/01/21", "CE", "6101", "4", "1113041",
        "TENIS", "FAME/768", "PT/CRJ", "34", "001",
        "59,05", "0,00", "0,00", "59,05", "0,00", "7,09", "0,000", "59,05", "18,00", "7,09", "3,54",
    ]


def test_parse_linha_item_extrai_campos_essenciais():
    resultado = _parse_linha(_linha_item())
    assert resultado is not None
    assert resultado.ano == 2021
    assert resultado.mes == 1
    assert resultado.nota == "1113041"
    assert resultado.descricao == "TENIS FAME/768 PT/CRJ 34"
    assert resultado.valor == 59.05


def test_parse_linha_ignora_linha_de_metadado_coditem():
    assert _parse_linha(["CodItem:43430768-PT/CRJ-34", "-", "NCM:64041100"]) is None


def test_parse_linha_ignora_linha_de_cabecalho_ou_periodo():
    assert _parse_linha(["Período:", "2021/01"]) is None
    assert _parse_linha(["DataEmiss", "DataLcto", "DtaAud"]) is None


def test_parse_linha_retorna_none_sem_numero_de_item():
    # Descrição sem nenhum token de 3 dígitos (Item) antes do fim da linha.
    tokens = ["05/01/21", "13/01/21", "--", "08/01/21", "08/01/21", "CE", "6101", "4", "1113041", "SEM ITEM"]
    assert _parse_linha(tokens) is None


def test_agrupar_em_linhas_por_top_proximo():
    palavras = [
        {"text": "A", "x0": 10.0, "top": 50.0},
        {"text": "B", "x0": 30.0, "top": 50.2},
        {"text": "C", "x0": 10.0, "top": 70.0},
    ]
    linhas = _agrupar_em_linhas(palavras)
    assert len(linhas) == 2
    assert [w["text"] for w in linhas[0]] == ["A", "B"]


def test_parse_linha_le_data_de_lancamento():
    resultado = _parse_linha(_linha_item())
    assert (resultado.ano_lancamento, resultado.mes_lancamento) == (2021, 1)
    assert (resultado.ano, resultado.mes) == (2021, 1)


def test_parse_linha_emitida_em_um_mes_e_lancada_em_outro():
    tokens = _linha_item()
    tokens[0], tokens[1] = "22/03/21", "05/04/21"
    resultado = _parse_linha(tokens)
    assert (resultado.ano, resultado.mes) == (2021, 3)
    assert (resultado.ano_lancamento, resultado.mes_lancamento) == (2021, 4)


def test_parse_linha_sem_data_de_lancamento_fica_none():
    tokens = _linha_item()
    tokens[1] = "--"
    resultado = _parse_linha(tokens)
    assert resultado is not None
    assert resultado.ano_lancamento is None and resultado.mes_lancamento is None


def _valores(liq="199,92", cred_empr="8,00", cred_aud="8,00", bc="199,92", tot="199,92", aliq="20,50") -> list[str]:
    # VlLiqItem IPI VlDespAcess VlTotItem AliqUtil VlCredEmpr PercRedBc VlBcAntParc AliqInt VlCredAud VlAntParc
    return [liq, "0,00", "0,00", tot, "0,00", cred_empr, "0,000", bc, aliq, cred_aud, "32,98"]


def _linha_item_2024(descricao: list[str], item="001", **valores) -> list[str]:
    return ["13/05/24", "22/05/24", "--", "--", "13/05/24", "MG", "6102", "1", "32326", *descricao, item, *_valores(**valores)]


def test_parse_linha_com_numero_de_3_digitos_na_descricao():
    # "289" na descrição não pode ser confundido com o número do item.
    resultado = _parse_linha(_linha_item_2024(["BOTA", "PAMPILI", "289"], item="002"))
    assert resultado is not None
    assert resultado.descricao == "BOTA PAMPILI 289"
    assert resultado.valor == 199.92


def test_parse_item_completo_le_uf_e_creditos():
    item = _parse_item(
        _linha_item_2024(["VESTUARIO", "TRIPK.MEIA", "CURTA"], cred_empr="8,00", cred_aud="7,50", bc="1.199,92", tot="210,00", aliq="18,00")
    )
    assert item is not None
    assert item.data_emissao == "13/05/24"
    assert item.data_lancamento == "22/05/24"
    assert item.uf == "MG"
    assert item.nota == "32326"
    assert (item.vl_liq_item, item.vl_cred_empr, item.vl_cred_aud) == (199.92, 8.00, 7.50)
    assert item.vl_bc_ant_parc == 1199.92
    assert (item.vl_tot_item, item.aliq_int) == (210.0, 18.0)


def test_itens_das_linhas_junta_continuacao_coditem_e_ncm():
    linhas = [
        ["DataEmiss", "DataLcto"],
        _linha_item_2024(["VESTUARIO", "TRIPK.MEIA", "CURTA", "39/44", "BCPTMC"]),
        ["39/44"],
        ["CodItem:OIMSA81920-BCPTMC-39/44", "-"],
        ["NCM:61159600"],
        _linha_item_2024(["SAPATO"], item="002"),
        ["CodItem:24253190", "-", "NCM:64029990"],
        ["951-R", "SIAF", "-", "Sistema", "Integrado"],
        ["Total", "em", "2024/05", "246,00"],
    ]

    itens = _itens_das_linhas(linhas)

    assert len(itens) == 2
    assert itens[0].descricao == "VESTUARIO TRIPK.MEIA CURTA 39/44 BCPTMC 39/44"
    assert itens[0].cod_item == "OIMSA81920-BCPTMC-39/44"
    assert itens[0].ncm == "61159600"
    assert itens[1].descricao == "SAPATO"
    assert itens[1].cod_item == "24253190"
    assert itens[1].ncm == "64029990"


def test_itens_das_linhas_ncm_na_pagina_seguinte_ignora_cabecalho():
    linhas = [
        _linha_item_2024(["MEIA"]),
        ["951-R", "SIAF", "-", "Sistema", "Integrado"],
        ["SECRETARIA", "DA", "FAZENDA"],
        ["DataEmiss", "DataLcto"],
        ["A", "B", "C", "D=A+B+C"],
        ["CodItem:X1", "-", "NCM:61159500"],
    ]

    itens = _itens_das_linhas(linhas)

    assert itens[0].descricao == "MEIA"
    assert itens[0].ncm == "61159500"
