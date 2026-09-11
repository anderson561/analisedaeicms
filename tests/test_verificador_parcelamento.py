from src.engine.verificador_parcelamento import verificar_parcelamento, verificar_parcelamento_por_valor
from src.models.dae_models import DaeDocumento, LinhaParcelamento


def _dae(codigo_receita, referencia, valor_principal, arquivo="dae.pdf"):
    return DaeDocumento(
        arquivo_origem=arquivo,
        codigo_receita=codigo_receita,
        referencia=referencia,
        valor_principal=valor_principal,
    )


def _linha_parcelamento(mes, ano, valor_historico, paf="810000.7810/24-5"):
    return LinhaParcelamento(
        paf=paf,
        arquivo_origem="parcelamento.pdf",
        mes_ocorrencia=mes,
        ano_ocorrencia=ano,
        valor_historico=valor_historico,
        valor_debito=valor_historico,
    )


def test_dae_com_match_de_valor_e_periodo_vai_para_encontrados():
    daes = [_dae("07.02.004", "07/2019", 1009.63)]
    linhas = [_linha_parcelamento(7, 2019, 1009.63)]

    encontrados, nao_encontrados = verificar_parcelamento(daes, linhas)

    assert len(encontrados) == 1
    assert not nao_encontrados
    assert encontrados[0].linha_parcelamento.valor_historico == 1009.63


def test_dae_sem_match_vai_para_nao_encontrados():
    daes = [_dae("07.02.004", "07/2019", 1009.63)]
    linhas = [_linha_parcelamento(7, 2019, 500.00)]

    encontrados, nao_encontrados = verificar_parcelamento(daes, linhas)

    assert not encontrados
    assert len(nao_encontrados) == 1
    assert nao_encontrados[0].referencia == "07/2019"


def test_qualquer_codigo_de_receita_e_considerado_sem_restricao():
    daes = [_dae("759", "09/2022", 400.00)]
    linhas = [_linha_parcelamento(9, 2022, 400.00)]

    encontrados, nao_encontrados = verificar_parcelamento(daes, linhas)

    assert len(encontrados) == 1
    assert not nao_encontrados


def test_periodo_diferente_nao_confunde_match_de_mesmo_valor():
    daes = [_dae("07.02.004", "05/2022", 784.01)]
    linhas = [_linha_parcelamento(6, 2022, 784.01)]

    encontrados, nao_encontrados = verificar_parcelamento(daes, linhas)

    assert not encontrados
    assert len(nao_encontrados) == 1


def test_tolerancia_aceita_pequena_diferenca_de_centavos():
    daes = [_dae("07.02.004", "09/2022", 852.93)]
    linhas = [_linha_parcelamento(9, 2022, 852.935)]

    encontrados, _ = verificar_parcelamento(daes, linhas)

    assert len(encontrados) == 1


def test_dae_sem_referencia_vai_para_nao_encontrados():
    daes = [_dae("07.02.004", None, 1009.63)]
    linhas = [_linha_parcelamento(7, 2019, 1009.63)]

    encontrados, nao_encontrados = verificar_parcelamento(daes, linhas)

    assert not encontrados
    assert len(nao_encontrados) == 1


def _linha_parcelamento_sem_periodo(valor_historico, arquivo_origem="Parcelamento"):
    return LinhaParcelamento(
        arquivo_origem=arquivo_origem,
        valor_historico=valor_historico,
        valor_debito=valor_historico,
    )


def test_verificar_por_valor_casa_mesmo_sem_periodo():
    daes = [_dae("1.802", "015/2026", 1494.50)]
    linhas = [_linha_parcelamento_sem_periodo(1494.50)]

    encontrados, nao_encontrados = verificar_parcelamento_por_valor(daes, linhas)

    assert len(encontrados) == 1
    assert not nao_encontrados


def test_verificar_por_valor_ignora_dae_sem_referencia_de_periodo():
    daes = [_dae(None, None, 1494.50)]
    linhas = [_linha_parcelamento_sem_periodo(1494.50)]

    encontrados, nao_encontrados = verificar_parcelamento_por_valor(daes, linhas)

    assert len(encontrados) == 1


def test_verificar_por_valor_sem_match_vai_para_nao_encontrados():
    daes = [_dae("1.802", "015/2026", 999.99)]
    linhas = [_linha_parcelamento_sem_periodo(1494.50)]

    encontrados, nao_encontrados = verificar_parcelamento_por_valor(daes, linhas)

    assert not encontrados
    assert len(nao_encontrados) == 1
