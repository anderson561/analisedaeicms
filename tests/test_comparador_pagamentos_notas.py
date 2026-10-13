from src.engine.comparador_pagamentos_notas import (
    STATUS_DIFERENTE,
    STATUS_IGUAL,
    STATUS_NAO_ENCONTRADA,
    NotaAgrupada,
    agrupar_notas_por_documento,
    comparar_com_entradas,
)
from src.models.dae_models import LinhaEntradaIcms, LinhaNotaItem


def _item(
    nota: str,
    descricao: str,
    valor: float,
    ano: int = 2021,
    mes: int = 1,
    lcto: tuple[int, int] | None = (2021, 1),
) -> LinhaNotaItem:
    return LinhaNotaItem(
        ano=ano,
        mes=mes,
        nota=nota,
        descricao=descricao,
        valor=valor,
        ano_lancamento=lcto[0] if lcto else None,
        mes_lancamento=lcto[1] if lcto else None,
    )


def _entrada(nota: str, valor: float, tipo: str = "ICMS", ano: int = 2021, mes: int = 1) -> LinhaEntradaIcms:
    return LinhaEntradaIcms(ano=ano, mes=mes, nota=nota, valor_contabil=valor, tipo=tipo, fornecedor="X")


def _agrupado(nota: str, total: float, lcto: tuple[int, int] | None = (2021, 1), mes: int = 1):
    return {
        (2021, mes, nota): NotaAgrupada(
            descricao="DESC",
            total=total,
            ano_lancamento=lcto[0] if lcto else None,
            mes_lancamento=lcto[1] if lcto else None,
        )
    }


def test_agrupar_notas_por_documento_soma_valores_e_corta_descricao():
    itens = [
        _item("1113041", "TENIS FAME/768 PT/CRJ 34", 59.05),
        _item("1113041", "TENIS FAME/768 PT/CRJ 35", 118.10),
    ]
    grupo = agrupar_notas_por_documento(itens)[(2021, 1, "1113041")]
    assert grupo.descricao == "TENIS FAME"
    assert grupo.total == 177.15


def test_agrupar_notas_por_documento_mantem_notas_separadas():
    grupos = agrupar_notas_por_documento([_item("1", "A/1", 10.0), _item("2", "B/2", 20.0)])
    assert (grupos[(2021, 1, "1")].descricao, grupos[(2021, 1, "1")].total) == ("A", 10.0)
    assert (grupos[(2021, 1, "2")].descricao, grupos[(2021, 1, "2")].total) == ("B", 20.0)


def test_agrupar_notas_por_documento_descricao_sem_barra_fica_intacta():
    grupos = agrupar_notas_por_documento([_item("1", "CHINELO CARTAGO MALTA IV BRANCO", 100.0)])
    assert grupos[(2021, 1, "1")].descricao == "CHINELO CARTAGO MALTA IV BRANCO"


def test_agrupar_notas_por_documento_arredonda_soma_para_evitar_ruido_de_float():
    itens = [_item("1", "X", 1806.48 / 11) for _ in range(11)]
    total = agrupar_notas_por_documento(itens)[(2021, 1, "1")].total
    assert round(total, 2) == total


def test_agrupar_notas_por_documento_guarda_data_de_lancamento():
    grupo = agrupar_notas_por_documento([_item("1", "A", 10.0, mes=3, lcto=(2021, 4))])[(2021, 3, "1")]
    assert (grupo.ano_lancamento, grupo.mes_lancamento) == (2021, 4)


def test_comparar_cruza_pelo_mes_de_lancamento_e_nao_pelo_de_emissao():
    # Emitida em março, lançada em abril: a Entrada está em abril.
    agrupado = _agrupado("1", 100.00, lcto=(2021, 4), mes=3)
    iguais, diferentes, nao_encontradas = comparar_com_entradas(agrupado, [_entrada("1", 100.00, mes=4)])
    assert len(iguais) == 1
    assert diferentes == [] and nao_encontradas == []
    assert iguais[0].mes == 3  # exibição continua pelo mês de emissão
    assert iguais[0].status == STATUS_IGUAL
    assert iguais[0].diferenca == 0.0


def test_comparar_nota_sem_data_de_lancamento_e_nao_encontrada():
    iguais, diferentes, nao_encontradas = comparar_com_entradas(
        _agrupado("1", 100.00, lcto=None), [_entrada("1", 100.00)]
    )
    assert iguais == [] and diferentes == []
    assert len(nao_encontradas) == 1
    assert nao_encontradas[0].status == STATUS_NAO_ENCONTRADA
    assert nao_encontradas[0].valor_entrada is None


def test_comparar_nota_ausente_nas_entradas_e_nao_encontrada():
    iguais, diferentes, nao_encontradas = comparar_com_entradas(_agrupado("1", 100.00), [])
    assert iguais == [] and diferentes == []
    assert [n.nota for n in nao_encontradas] == ["1"]


def test_comparar_um_centavo_de_diferenca_e_diferente_sem_tolerancia():
    iguais, diferentes, _ = comparar_com_entradas(_agrupado("1", 1806.48), [_entrada("1", 1806.47)])
    assert iguais == []
    assert len(diferentes) == 1
    assert diferentes[0].status == STATUS_DIFERENTE
    assert diferentes[0].diferenca == 0.01


def test_comparar_valores_identicos_ao_centavo_sao_iguais():
    iguais, diferentes, _ = comparar_com_entradas(_agrupado("1", 2299.44), [_entrada("1", 2299.44)])
    assert len(iguais) == 1 and diferentes == []


def test_comparar_usa_linha_icms_quando_ha_icms_e_st_at():
    entradas = [_entrada("1", 150.00, tipo="ST/AT"), _entrada("1", 100.00, tipo="ICMS")]
    iguais, _, _ = comparar_com_entradas(_agrupado("1", 100.00), entradas)
    assert len(iguais) == 1
    assert iguais[0].valor_entrada == 100.00


def test_comparar_usa_st_at_como_fallback_sem_icms():
    iguais, _, _ = comparar_com_entradas(_agrupado("1", 150.00), [_entrada("1", 150.00, tipo="ST/AT")])
    assert len(iguais) == 1
    assert iguais[0].valor_entrada == 150.00


def test_comparar_chave_duplicada_escolhe_valor_mais_proximo():
    # Mesmo nº de nota, fornecedores diferentes, no mesmo mês de lançamento.
    entradas = [_entrada("1", 999.00), _entrada("1", 100.00)]
    iguais, _, _ = comparar_com_entradas(_agrupado("1", 100.00), entradas)
    assert len(iguais) == 1
    assert iguais[0].valor_entrada == 100.00
