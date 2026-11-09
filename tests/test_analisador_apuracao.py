from src.engine.analisador_apuracao import (
    INFORMACAO_SEM_ANTECIPACAO,
    INFORMACAO_SEM_DAE,
    analisar_apuracao,
)
from src.models.dae_models import ItemListaNotas, NotaCredito


def _credito(nota="32326", emissao="13/05/24", uf="MG"):
    _, mes, ano = emissao.split("/")
    return NotaCredito(
        ano=2000 + int(ano),
        mes=int(mes),
        data_emissao=emissao,
        uf=uf,
        nota=nota,
        descricao="MEIA",
        quantidade_itens=0,
        vl_liq_item=0.0,
        vl_cred_empr=0.0,
        vl_bc_ant_parc=0.0,
        vl_cred_aud=0.0,
    )


def _item(nota="32326", tot=199.92, aliq=20.5, empr=8.0, ncm="61159600", emissao="13/05/24", uf="MG"):
    _, mes, ano = emissao.split("/")
    return ItemListaNotas(
        data_emissao=emissao,
        ano=2000 + int(ano),
        mes=int(mes),
        uf=uf,
        nota=nota,
        descricao="MEIA",
        ncm=ncm,
        vl_liq_item=tot,
        vl_tot_item=tot,
        aliq_int=aliq,
        vl_cred_empr=empr,
        vl_bc_ant_parc=tot,
        vl_cred_aud=empr,
    )


def _itens_32326():
    return [
        _item(tot=199.92, empr=8.0),
        _item(tot=87.48, empr=3.5),
        _item(tot=87.48, empr=3.5),
        _item(tot=199.92, empr=8.0),
        _item(tot=87.48, empr=3.5),
        _item(tot=87.48, empr=3.5),
        _item(tot=600.0, empr=0.0, ncm="64041900"),  # calçado: fora
    ]


def test_calcula_valor_pago_da_nota_32326_e_traz_informacao_do_dae():
    credito = _credito()

    analises = analisar_apuracao([credito], _itens_32326(), {"32326": "DAE 2175 05-2024.R$ 123,70"})

    assert len(analises) == 1
    assert analises[0].nota == credito
    assert analises[0].valor_pago == 123.70  # (749,76 x 20,5%) - 30,00
    assert analises[0].informacao_norte == "DAE 2175 05-2024.R$ 123,70"


def test_usa_aliquota_de_cada_item():
    itens = [_item(tot=1000.0, aliq=18.0, empr=70.0), _item(tot=100.0, aliq=20.5, empr=5.0)]

    analise = analisar_apuracao([_credito()], itens, {})[0]

    assert analise.valor_pago == 125.5  # (180 - 70) + (20,50 - 5)


def test_nota_ausente_da_planilha_de_daes_e_sinalizada():
    analise = analisar_apuracao([_credito()], _itens_32326(), {})[0]

    assert analise.valor_pago == 123.70
    assert analise.informacao_norte == INFORMACAO_SEM_DAE


def test_nota_sem_itens_na_antecipacao_fica_sem_valor_pago():
    analise = analisar_apuracao([_credito(nota="9992")], _itens_32326(), {"9992": "DAE X"})[0]

    assert analise.valor_pago is None
    assert analise.informacao_norte == f"DAE X | {INFORMACAO_SEM_ANTECIPACAO}"


def test_casa_nota_por_numero_data_e_uf_ignorando_zeros_a_esquerda():
    itens = [_item(nota="032326"), _item(nota="32326", uf="SP", tot=5000.0)]

    analise = analisar_apuracao([_credito()], itens, {"32326": "DAE"})[0]

    assert analise.valor_pago == round(199.92 * 0.205 - 8.0, 2)
