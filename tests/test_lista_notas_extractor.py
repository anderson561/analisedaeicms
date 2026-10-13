from src.extractors.lista_notas_extractor import _agrupar_em_linhas, _parse_linha


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
