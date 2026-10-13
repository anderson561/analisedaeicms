from pydantic import BaseModel

from src.models.dae_models import LinhaEntradaIcms, LinhaNotaItem, NotaFiscalComparada

STATUS_IGUAL = "Igual"
STATUS_DIFERENTE = "Diferente"
STATUS_NAO_ENCONTRADA = "Não encontrada nas Entradas"


class NotaAgrupada(BaseModel):
    descricao: str
    total: float
    ano_lancamento: int | None = None
    mes_lancamento: int | None = None


def _descricao_consolidada(descricao_primeiro_item: str) -> str:
    return descricao_primeiro_item.split("/", 1)[0].strip()


def agrupar_notas_por_documento(itens: list[LinhaNotaItem]) -> dict[tuple[int, int, str], NotaAgrupada]:
    """Agrupa itens por (ano, mes de emissão, nota), somando os valores e
    derivando a descrição consolidada a partir do primeiro item de cada nota
    (cortada no primeiro "/"), conforme decidido com o Anderson."""
    grupos: dict[tuple[int, int, str], NotaAgrupada] = {}
    for item in itens:
        chave = (item.ano, item.mes, item.nota)
        atual = grupos.get(chave)
        if atual is None:
            grupos[chave] = NotaAgrupada(
                descricao=_descricao_consolidada(item.descricao),
                total=round(item.valor, 2),
                ano_lancamento=item.ano_lancamento,
                mes_lancamento=item.mes_lancamento,
            )
        else:
            atual.total = round(atual.total + item.valor, 2)
    return grupos


def _centavos(valor: float) -> int:
    return round(valor * 100)


def _indexar_entradas(linhas_entrada: list[LinhaEntradaIcms]) -> dict[tuple[int, int, str], list[LinhaEntradaIcms]]:
    por_chave: dict[tuple[int, int, str], list[LinhaEntradaIcms]] = {}
    for linha in linhas_entrada:
        por_chave.setdefault((linha.ano, linha.mes, linha.nota), []).append(linha)
    return por_chave


def _escolher_entrada(candidatas: list[LinhaEntradaIcms], total_notas: float) -> LinhaEntradaIcms:
    """Prefere a linha ICMS sobre ST/AT; entre candidatas empatadas (mesmo nº
    de nota em fornecedores diferentes no mesmo mês) usa a de valor mais
    próximo do total das notas."""
    return min(
        candidatas,
        key=lambda c: (c.tipo != "ICMS", abs(_centavos(c.valor_contabil) - _centavos(total_notas))),
    )


def comparar_com_entradas(
    agrupado: dict[tuple[int, int, str], NotaAgrupada],
    linhas_entrada: list[LinhaEntradaIcms],
) -> tuple[list[NotaFiscalComparada], list[NotaFiscalComparada], list[NotaFiscalComparada]]:
    """Cruza por (mês de LANÇAMENTO + nota): a coluna Data do relatório de
    Entradas é a data de lançamento (DataLcto da lista de notas), não a de
    emissão. Igualdade exata ao centavo."""
    entradas = _indexar_entradas(linhas_entrada)

    iguais: list[NotaFiscalComparada] = []
    diferentes: list[NotaFiscalComparada] = []
    nao_encontradas: list[NotaFiscalComparada] = []
    for (ano, mes, nota), grupo in agrupado.items():
        candidatas = []
        if grupo.ano_lancamento is not None and grupo.mes_lancamento is not None:
            candidatas = entradas.get((grupo.ano_lancamento, grupo.mes_lancamento, nota), [])

        if not candidatas:
            nao_encontradas.append(
                NotaFiscalComparada(
                    ano=ano,
                    mes=mes,
                    nota=nota,
                    descricao=grupo.descricao,
                    valor_notas=grupo.total,
                    status=STATUS_NAO_ENCONTRADA,
                )
            )
            continue

        entrada = _escolher_entrada(candidatas, grupo.total)
        igual = _centavos(grupo.total) == _centavos(entrada.valor_contabil)
        comparada = NotaFiscalComparada(
            ano=ano,
            mes=mes,
            nota=nota,
            descricao=grupo.descricao,
            fornecedor=entrada.fornecedor,
            valor_notas=grupo.total,
            valor_entrada=entrada.valor_contabil,
            diferenca=round(grupo.total - entrada.valor_contabil, 2),
            status=STATUS_IGUAL if igual else STATUS_DIFERENTE,
        )
        (iguais if igual else diferentes).append(comparada)

    return iguais, diferentes, nao_encontradas
