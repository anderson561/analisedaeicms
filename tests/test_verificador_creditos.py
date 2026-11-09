from src.engine.verificador_creditos import eh_item_excluido, verificar_creditos
from src.models.dae_models import ItemListaNotas


def _item(nota="32326", ncm="61159600", liq=199.92, empr=8.0, aud=8.0, descricao="MEIA", emissao="13/05/24", **extra):
    dia, mes, ano = emissao.split("/")
    return ItemListaNotas(
        data_emissao=emissao,
        data_lancamento=extra.get("lancamento", "22/05/24"),
        ano=2000 + int(ano),
        mes=int(mes),
        uf=extra.get("uf", "MG"),
        nota=nota,
        descricao=descricao,
        cod_item=extra.get("cod_item", "COD1"),
        ncm=ncm,
        vl_liq_item=liq,
        vl_tot_item=extra.get("tot", liq),
        aliq_int=extra.get("aliq", 20.5),
        vl_cred_empr=empr,
        vl_bc_ant_parc=extra.get("bc", liq),
        vl_cred_aud=aud,
    )


def test_exclui_calcados_e_bolsas_pelo_ncm():
    assert eh_item_excluido(_item(ncm="64029990"))
    assert eh_item_excluido(_item(ncm="64041900"))
    assert eh_item_excluido(_item(ncm="42022210"))
    assert not eh_item_excluido(_item(ncm="61159600"))
    # Meia com "SAPATILHA" na descrição continua valendo: o critério é o NCM.
    assert not eh_item_excluido(_item(ncm="61159500", descricao="MEIA SAPATILHA INVISIVEL"))


def test_item_sem_ncm_nao_e_excluido():
    assert not eh_item_excluido(_item(ncm=None))


def test_soma_itens_da_mesma_nota_e_usa_descricao_do_primeiro_item():
    itens = [
        _item(liq=199.92, empr=8.0, aud=8.0, descricao="VESTUARIO TRIPK.MEIA CURTA", cod_item="OIMSA81920"),
        _item(liq=87.48, empr=3.5, aud=3.5, descricao="OUTRA MEIA"),
        _item(liq=87.48, empr=3.5, aud=3.5),
        _item(liq=87.48, empr=3.5, aud=3.5),
        _item(liq=199.92, empr=8.0, aud=8.0),
        _item(liq=87.48, empr=3.5, aud=3.5),
        _item(liq=600.0, empr=0.0, aud=123.0, ncm="64041900"),
    ]

    notas, excluidos = verificar_creditos(itens)

    assert excluidos == 1
    assert len(notas) == 1
    nota = notas[0]
    assert (nota.nota, nota.uf, nota.data_emissao, nota.data_lancamento) == ("32326", "MG", "13/05/24", "22/05/24")
    assert nota.quantidade_itens == 6
    assert (nota.vl_liq_item, nota.vl_cred_empr, nota.vl_cred_aud) == (749.76, 30.0, 30.0)
    assert nota.vl_bc_ant_parc == 749.76
    assert nota.descricao == "VESTUARIO TRIPK.MEIA CURTA / CodItem: OIMSA81920 / NCM: 61159600"


def test_mesmo_numero_em_datas_ou_ufs_diferentes_sao_notas_distintas():
    itens = [_item(nota="10"), _item(nota="10", uf="SP"), _item(nota="10", emissao="14/05/24")]

    notas, _ = verificar_creditos(itens)

    assert len(notas) == 3


def test_ordena_por_data_de_emissao_e_numero():
    itens = [_item(nota="20", emissao="20/06/24"), _item(nota="5", emissao="13/05/24"), _item(nota="3", emissao="13/05/24")]

    notas, _ = verificar_creditos(itens)

    assert [n.nota for n in notas] == ["3", "5", "20"]
