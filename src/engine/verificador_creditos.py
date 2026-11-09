from src.models.dae_models import ItemListaNotas, NotaCredito

# Calçados em geral (capítulo 64 da NCM) e bolsas, mochilas e carteiras
# (posição 4202) ficam fora da verificação de créditos. O critério é o NCM,
# não a descrição: "MEIA SAPATILHA" (NCM 6115) é meia, e vários calçados vêm
# descritos só pela marca (ex.: "AZALEIA EVA PRETO").
PREFIXOS_NCM_EXCLUIDOS = ("64", "4202")


def eh_item_excluido(item: ItemListaNotas) -> bool:
    return bool(item.ncm) and item.ncm.startswith(PREFIXOS_NCM_EXCLUIDOS)


def _descricao_completa(item: ItemListaNotas) -> str:
    partes = [item.descricao]
    if item.cod_item:
        partes.append(f"CodItem: {item.cod_item}")
    if item.ncm:
        partes.append(f"NCM: {item.ncm}")
    return " / ".join(partes)


def _chave_ordenacao(nota: NotaCredito) -> tuple:
    dia = int(nota.data_emissao.split("/")[0])
    numero = int(nota.nota) if nota.nota.isdigit() else 0
    return (nota.ano, nota.mes, dia, numero, nota.nota)


def verificar_creditos(itens: list[ItemListaNotas]) -> tuple[list[NotaCredito], int]:
    """Soma VlLiqItem, VlCredEmpr, VlBcAntParc e VlCredAud por nota (número + data de
    emissão + UF), desconsiderando calçados, bolsas, mochilas e carteiras.
    Devolve as notas e a quantidade de itens excluídos."""
    notas: dict[tuple[str, str, str], NotaCredito] = {}
    excluidos = 0
    for item in itens:
        if eh_item_excluido(item):
            excluidos += 1
            continue
        chave = (item.nota, item.data_emissao, item.uf)
        nota = notas.get(chave)
        if nota is None:
            notas[chave] = NotaCredito(
                ano=item.ano,
                mes=item.mes,
                data_emissao=item.data_emissao,
                data_lancamento=item.data_lancamento,
                uf=item.uf,
                nota=item.nota,
                descricao=_descricao_completa(item),
                quantidade_itens=1,
                vl_liq_item=item.vl_liq_item,
                vl_cred_empr=item.vl_cred_empr,
                vl_bc_ant_parc=item.vl_bc_ant_parc,
                vl_cred_aud=item.vl_cred_aud,
            )
            continue
        nota.quantidade_itens += 1
        nota.vl_liq_item = round(nota.vl_liq_item + item.vl_liq_item, 2)
        nota.vl_cred_empr = round(nota.vl_cred_empr + item.vl_cred_empr, 2)
        nota.vl_bc_ant_parc = round(nota.vl_bc_ant_parc + item.vl_bc_ant_parc, 2)
        nota.vl_cred_aud = round(nota.vl_cred_aud + item.vl_cred_aud, 2)
    return sorted(notas.values(), key=_chave_ordenacao), excluidos
