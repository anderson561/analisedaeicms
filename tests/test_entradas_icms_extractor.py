from src.extractors.entradas_icms_extractor import (
    _agrupar_em_linhas,
    _parse_linha,
    _selecionar_melhor_linha_por_nota,
)
from src.models.dae_models import LinhaEntradaIcms


def _linha_simples() -> list[str]:
    # Fornecedor curto, sem sobreposição com CFOP/AC./UF -- caso "limpo".
    return [
        "1082", "04/01/2021", "423", "1", "36", "2", "ROSEMERY", "ALMEIDA", "MACEDO",
        "1-411", "132", "BA", "679,48", "ICMS", "0,00", "18,00", "0,00", "0,00", "679,48",
    ]


def _linha_com_st_at() -> list[str]:
    # Nota interestadual: linha principal ICMS seguida da sub-linha ST/AT
    # (a sub-linha nao tem data/nota -- é ignorada por _parse_linha).
    return [
        "1074", "13/01/2021", "1113041", "4", "36", "14", "VULCABRAS", "-", "CE,",
        "CALCADOS", "E", "ARTIGOS", "ESPORTIVOS", "S/A", "2-403", "205", "CE",
        "2.834,40", "ICMS", "0,00", "12,00", "0,00", "0,00", "2.834,40",
    ]


def _linha_nome_corrompido() -> list[str]:
    # Simula a sobreposição real encontrada no PDF: caracteres do
    # fornecedor/CFOP ficam colados/entrelaçados em um único token, mas
    # Data/Nota (antes) e Valor Contábil/Tipo (depois) continuam intactos.
    return [
        "1069", "06/01/2021", "44353", "2", "36", "108",
        "TOPSHOES", "INDUSTRIA", "DE", "CALCAD2O-4S0", "3SA205CE",
        "2.555,20", "ICMS", "0,00", "12,00", "0,00", "0,00", "2.555,20",
    ]


def test_parse_linha_extrai_campos_essenciais():
    resultado = _parse_linha(_linha_simples())
    assert resultado is not None
    assert resultado.ano == 2021
    assert resultado.mes == 1
    assert resultado.nota == "423"
    assert resultado.valor_contabil == 679.48
    assert resultado.tipo == "ICMS"
    # Fornecedor é melhor-esforço (ver docstring do módulo): inclui à direita
    # o que sobrar até o Valor Contábil (aqui, CFOP/AC./UF), já que não
    # tentamos localizar o fim exato do nome.
    assert resultado.fornecedor.startswith("ROSEMERY ALMEIDA MACEDO")


def test_parse_linha_ignora_sub_linha_st_at_sem_data():
    assert _parse_linha(["ST/AT", "4.258,40", "18,00", "426,38", "0,00", "0,00"]) is None


def test_parse_linha_nota_interestadual_pega_linha_icms():
    resultado = _parse_linha(_linha_com_st_at())
    assert resultado is not None
    assert resultado.nota == "1113041"
    assert resultado.valor_contabil == 2834.40
    assert resultado.tipo == "ICMS"


def test_parse_linha_robusto_a_nome_de_fornecedor_corrompido():
    """Mesmo quando o nome do fornecedor sai com caracteres sobrepostos
    (defeito do PDF de origem, não do nosso parser), Nota/Valor Contábil/Tipo
    -- os únicos campos usados na comparação -- continuam corretos."""
    resultado = _parse_linha(_linha_nome_corrompido())
    assert resultado is not None
    assert resultado.nota == "44353"
    assert resultado.valor_contabil == 2555.20
    assert resultado.tipo == "ICMS"


def test_parse_linha_retorna_none_sem_par_valor_tipo():
    # Linha "Total CFOP" / linha zerada sem nenhum Tipo (ex.: fornecedor Nortec)
    assert _parse_linha(["1066", "19/01/2021", "20523", "1", "39", "33", "0,00", "0,00"]) is None


def test_agrupar_em_linhas_por_top_proximo():
    palavras = [
        {"text": "A", "x0": 10.0, "top": 100.0},
        {"text": "B", "x0": 30.0, "top": 100.5},
        {"text": "C", "x0": 10.0, "top": 120.0},
    ]
    linhas = _agrupar_em_linhas(palavras)
    assert len(linhas) == 2
    assert [w["text"] for w in linhas[0]] == ["A", "B"]
    assert [w["text"] for w in linhas[1]] == ["C"]


def test_selecionar_melhor_linha_prefere_icms_sobre_st_at():
    linhas = [
        LinhaEntradaIcms(ano=2021, mes=1, nota="1", valor_contabil=100.0, tipo="ST/AT"),
        LinhaEntradaIcms(ano=2021, mes=1, nota="1", valor_contabil=50.0, tipo="ICMS"),
    ]
    resultado = _selecionar_melhor_linha_por_nota(linhas)
    assert len(resultado) == 1
    assert resultado[0].tipo == "ICMS"
    assert resultado[0].valor_contabil == 50.0


def test_selecionar_melhor_linha_usa_st_at_como_fallback_sem_icms():
    linhas = [LinhaEntradaIcms(ano=2021, mes=1, nota="1", valor_contabil=100.0, tipo="ST/AT")]
    resultado = _selecionar_melhor_linha_por_nota(linhas)
    assert len(resultado) == 1
    assert resultado[0].tipo == "ST/AT"


def test_parse_linha_recompoe_valor_contabil_quando_token_do_valor_esta_embaralhado():
    # Fornecedor longo embaralha o próprio Valor Contábil ("L1T.3D0A1,93"):
    # recompõe por Base + Isentas + Outras (0,00 + 0,00 + 1.301,93).
    tokens = [
        "1", "1234", "03/11/2021", "127822", "2", "36", "25",
        "VULCABRAS", "AZALEIA-SE,CALCADO2S-", "4E0", "A3RTI2G0O4SS", "EESPORTIVOS", "L1T.3D0A1,93",
        "ICMS", "0,00", "0,00", "0,00", "0,00", "1.301,93",
    ]
    resultado = _parse_linha(tokens)
    assert resultado is not None
    assert resultado.nota == "127822"
    assert resultado.tipo == "ICMS"
    assert resultado.valor_contabil == 1301.93


def test_parse_linha_recomposicao_considera_base_de_calculo_diferente_de_zero():
    tokens = [
        "1160", "18/08/2021", "386031", "1", "36", "146", "NOME", "EMBARALHADO9",
        "ICMS", "635,76", "4,00", "25,44", "0,00", "0,00",
    ]
    resultado = _parse_linha(tokens)
    assert resultado is not None
    assert resultado.valor_contabil == 635.76
