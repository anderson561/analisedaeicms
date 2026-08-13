from src.extractors.pagamento_extractor import _parse_linha, _parse_referencia, _parse_valor


def test_parse_referencia_com_zero_a_esquerda():
    assert _parse_referencia("09/2022") == (9, 2022)


def test_parse_referencia_sem_zero_a_esquerda():
    assert _parse_referencia("9/2022") == (9, 2022)


def test_parse_referencia_invalida():
    assert _parse_referencia("abc") is None
    assert _parse_referencia(None) is None


def test_parse_valor_valido():
    valor, revisar = _parse_valor("1.745,11")
    assert valor == 1745.11
    assert revisar is False


def test_parse_valor_sem_milhar():
    valor, revisar = _parse_valor("852,93")
    assert valor == 852.93
    assert revisar is False


def test_parse_valor_quatro_digitos_sem_separador_de_milhar():
    # Este relatorio imprime valores >= 1000 sem o separador de milhar (ex.: "1124,29").
    valor, revisar = _parse_valor("1124,29")
    assert valor == 1124.29
    assert revisar is False


def test_parse_valor_glitch_sem_virgula_marca_revisar():
    valor, revisar = _parse_valor("174511")
    assert valor is None
    assert revisar is True


def test_parse_linha_monta_modelo_completo():
    linha = _parse_linha(
        [
            "2113874976",
            "25/02/2022",
            "1/2022",
            "1145 - ICMS ANTECIPAÇÃO TRIBUTÁRIA",
            "852,93",
            "852,93",
        ]
    )
    assert linha.nosso_numero == "2113874976"
    assert linha.data_pagamento == "25/02/2022"
    assert linha.mes_referencia == 1
    assert linha.ano_referencia == 2022
    assert linha.codigo_receita == "1145"
    assert linha.descricao_receita == "ICMS ANTECIPAÇÃO TRIBUTÁRIA"
    assert linha.valor_principal == 852.93
    assert linha.valor_total == 852.93
    assert linha.revisar is False


def test_parse_linha_marca_revisar_quando_valor_falha():
    linha = _parse_linha(
        [
            "2122706563",
            "25/10/2022",
            "9/2022",
            "1145 - ICMS ANTECIPAÇÃO TRIBUTÁRIA",
            "1745,11",
            "174511",
        ]
    )
    assert linha.valor_total is None
    assert linha.revisar is True
