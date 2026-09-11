from src.engine.verificador_pagamento import verificar_pagamentos
from src.models.dae_models import DaeDocumento, LinhaPagamentoDae


def _dae(codigo_receita, referencia, valor_principal, arquivo="dae.pdf"):
    return DaeDocumento(
        arquivo_origem=arquivo,
        codigo_receita=codigo_receita,
        referencia=referencia,
        valor_principal=valor_principal,
    )


def _linha_pagamento(mes, ano, valor_principal, nosso_numero="123"):
    return LinhaPagamentoDae(
        nosso_numero=nosso_numero,
        mes_referencia=mes,
        ano_referencia=ano,
        valor_principal=valor_principal,
        valor_total=valor_principal,
    )


def test_dae_com_match_de_valor_e_referencia_vai_para_confirmados():
    daes = [_dae("1145", "09/2022", 852.93)]
    linhas = [_linha_pagamento(9, 2022, 852.93)]

    confirmados, nao_localizados = verificar_pagamentos(daes, linhas)

    assert len(confirmados) == 1
    assert not nao_localizados
    assert confirmados[0].linha_pagamento.valor_principal == 852.93


def test_dae_sem_match_vai_para_nao_localizados():
    daes = [_dae("1145", "09/2022", 852.93)]
    linhas = [_linha_pagamento(9, 2022, 100.00)]

    confirmados, nao_localizados = verificar_pagamentos(daes, linhas)

    assert not confirmados
    assert len(nao_localizados) == 1
    assert nao_localizados[0].codigo_receita == "1145"


def test_codigo_receita_fora_do_alvo_e_ignorado():
    daes = [_dae("759", "09/2022", 400.00)]
    linhas = [_linha_pagamento(9, 2022, 400.00)]

    confirmados, nao_localizados = verificar_pagamentos(daes, linhas)

    assert not confirmados
    assert not nao_localizados


def test_referencia_diferente_nao_confunde_match_de_mesmo_valor():
    daes = [_dae("2175", "05/2022", 784.01)]
    linhas = [_linha_pagamento(6, 2022, 784.01)]

    confirmados, nao_localizados = verificar_pagamentos(daes, linhas)

    assert not confirmados
    assert len(nao_localizados) == 1


def test_tolerancia_aceita_pequena_diferenca_de_centavos():
    daes = [_dae("1145", "09/2022", 852.93)]
    linhas = [_linha_pagamento(9, 2022, 852.935)]

    confirmados, _ = verificar_pagamentos(daes, linhas)

    assert len(confirmados) == 1


def test_codigo_receita_com_sufixo_e_normalizado():
    daes = [_dae("1145-6", "09/2022", 852.93)]
    linhas = [_linha_pagamento(9, 2022, 852.93)]

    confirmados, _ = verificar_pagamentos(daes, linhas)

    assert len(confirmados) == 1
