import re

from src.models.dae_models import DaeDocumento, DaeParceladoEncontrado, DaeParceladoNaoEncontrado, LinhaParcelamento

PADRAO_REFERENCIA_DAE = re.compile(r"^(\d{1,2})/(\d{4})$")


def _referencia_dae_para_mes_ano(referencia: str | None) -> tuple[int, int] | None:
    if not referencia:
        return None
    m = PADRAO_REFERENCIA_DAE.match(referencia)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def verificar_parcelamento(
    daes: list[DaeDocumento],
    linhas_parcelamento: list[LinhaParcelamento],
    tolerancia: float = 0.01,
) -> tuple[list[DaeParceladoEncontrado], list[DaeParceladoNaoEncontrado]]:
    """Confirma se cada DAE processado corresponde a uma parcela do relatório de
    parcelamentos (Relatório Débito do PAF), cruzando seu valor_principal e
    referência contra o valor histórico e o mês/ano de ocorrência de cada parcela.

    Diferente de verificar_pagamentos, não há restrição de código de receita aqui:
    um parcelamento pode envolver qualquer código.
    """
    encontrados: list[DaeParceladoEncontrado] = []
    nao_encontrados: list[DaeParceladoNaoEncontrado] = []

    for dae in daes:
        mes_ano_dae = _referencia_dae_para_mes_ano(dae.referencia)
        correspondente = None
        if mes_ano_dae is not None and dae.valor_principal is not None:
            for linha in linhas_parcelamento:
                if (linha.mes_ocorrencia, linha.ano_ocorrencia) != mes_ano_dae:
                    continue
                if linha.valor_historico is None:
                    continue
                if abs(linha.valor_historico - dae.valor_principal) < tolerancia:
                    correspondente = linha
                    break

        if correspondente is not None:
            encontrados.append(
                DaeParceladoEncontrado(dae_arquivo_origem=dae.arquivo_origem, linha_parcelamento=correspondente)
            )
        else:
            nao_encontrados.append(
                DaeParceladoNaoEncontrado(
                    arquivo_origem=dae.arquivo_origem,
                    codigo_receita=dae.codigo_receita,
                    referencia=dae.referencia,
                    valor_principal=dae.valor_principal,
                )
            )

    return encontrados, nao_encontrados


def verificar_parcelamento_por_valor(
    daes: list[DaeDocumento],
    linhas_parcelamento: list[LinhaParcelamento],
    tolerancia: float = 0.01,
) -> tuple[list[DaeParceladoEncontrado], list[DaeParceladoNaoEncontrado]]:
    """Mesma ideia de verificar_parcelamento, mas para linhas sem mês/ano de
    ocorrência (ex.: extraídas de uma planilha de parcelamento cuja
    "Referência" é só "parcela atual/total", não uma competência) -- o
    casamento é feito só pelo valor, sem restrição de código nem período.
    """
    encontrados: list[DaeParceladoEncontrado] = []
    nao_encontrados: list[DaeParceladoNaoEncontrado] = []

    for dae in daes:
        correspondente = None
        if dae.valor_principal is not None:
            for linha in linhas_parcelamento:
                if linha.valor_historico is None:
                    continue
                if abs(linha.valor_historico - dae.valor_principal) < tolerancia:
                    correspondente = linha
                    break

        if correspondente is not None:
            encontrados.append(
                DaeParceladoEncontrado(dae_arquivo_origem=dae.arquivo_origem, linha_parcelamento=correspondente)
            )
        else:
            nao_encontrados.append(
                DaeParceladoNaoEncontrado(
                    arquivo_origem=dae.arquivo_origem,
                    codigo_receita=dae.codigo_receita,
                    referencia=dae.referencia,
                    valor_principal=dae.valor_principal,
                )
            )

    return encontrados, nao_encontrados
