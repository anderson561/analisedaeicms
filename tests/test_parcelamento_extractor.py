from src.extractors.parcelamento_extractor import _construir_linha, _mes_ano_ocorrencia, _parse_valor


def test_mes_ano_ocorrencia_valido():
    assert _mes_ano_ocorrencia("31/07/2019") == (7, 2019)


def test_mes_ano_ocorrencia_invalida():
    assert _mes_ano_ocorrencia("abc") is None
    assert _mes_ano_ocorrencia(None) is None


def test_parse_valor_valido():
    assert _parse_valor("1.009,63") == 1009.63


def test_parse_valor_sem_milhar():
    assert _parse_valor("384,35") == 384.35


def test_parse_valor_invalido():
    assert _parse_valor("abc") is None
    assert _parse_valor(None) is None


def test_construir_linha_monta_modelo_completo():
    linha = _construir_linha(
        paf="810000.7810/24-5",
        arquivo_origem="2022.pdf",
        data_ocorrencia="31/07/2019",
        data_vencimento="25/08/2019",
        valor_hist_txt="1.009,63",
        valor_debito_txt="1.009,63",
    )
    assert linha.paf == "810000.7810/24-5"
    assert linha.arquivo_origem == "2022.pdf"
    assert linha.data_ocorrencia == "31/07/2019"
    assert linha.data_vencimento == "25/08/2019"
    assert linha.mes_ocorrencia == 7
    assert linha.ano_ocorrencia == 2019
    assert linha.valor_historico == 1009.63
    assert linha.valor_debito == 1009.63


def test_construir_linha_sem_paf_e_data_invalida():
    linha = _construir_linha(
        paf=None,
        arquivo_origem="2022.pdf",
        data_ocorrencia="invalida",
        data_vencimento="25/08/2019",
        valor_hist_txt="384,35",
        valor_debito_txt="384,35",
    )
    assert linha.paf is None
    assert linha.mes_ocorrencia is None
    assert linha.ano_ocorrencia is None
    assert linha.valor_historico == 384.35
