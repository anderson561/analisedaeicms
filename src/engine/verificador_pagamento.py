import re

from src.models.dae_models import DaeDocumento, DaePagamentoNaoLocalizado, LinhaPagamentoDae, PagamentoConfirmado

CODIGOS_RECEITA_ALVO = {"1145", "2175"}

PADRAO_CODIGO = re.compile(r"^(\d{3,4})")
PADRAO_REFERENCIA_DAE = re.compile(r"^(\d{1,2})/(\d{4})$")


def _normalizar_codigo(codigo: str | None) -> str | None:
    if not codigo:
        return None
    m = PADRAO_CODIGO.match(codigo)
    return m.group(1) if m else None


def _referencia_dae_para_mes_ano(referencia: str | None) -> tuple[int, int] | None:
    if not referencia:
        return None
    m = PADRAO_REFERENCIA_DAE.match(referencia)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def verificar_pagamentos(
    daes: list[DaeDocumento],
    linhas_pagamento: list[LinhaPagamentoDae],
    tolerancia: float = 0.01,
) -> tuple[list[PagamentoConfirmado], list[DaePagamentoNaoLocalizado]]:
    """Confirma se cada DAE (código 1145/2175) foi efetivamente pago, cruzando seu
    valor_principal e referência contra as linhas do relatório anual de pagamentos.

    DAEs com outros códigos de receita são ignorados por esta verificação.
    """
    confirmados: list[PagamentoConfirmado] = []
    nao_localizados: list[DaePagamentoNaoLocalizado] = []

    for dae in daes:
        codigo = _normalizar_codigo(dae.codigo_receita)
        if codigo not in CODIGOS_RECEITA_ALVO:
            continue

        mes_ano_dae = _referencia_dae_para_mes_ano(dae.referencia)
        correspondente = None
        if mes_ano_dae is not None and dae.valor_principal is not None:
            for linha in linhas_pagamento:
                if (linha.mes_referencia, linha.ano_referencia) != mes_ano_dae:
                    continue
                if linha.valor_principal is None:
                    continue
                if abs(linha.valor_principal - dae.valor_principal) < tolerancia:
                    correspondente = linha
                    break

        if correspondente is not None:
            confirmados.append(
                PagamentoConfirmado(dae_arquivo_origem=dae.arquivo_origem, linha_pagamento=correspondente)
            )
        else:
            nao_localizados.append(
                DaePagamentoNaoLocalizado(
                    arquivo_origem=dae.arquivo_origem,
                    codigo_receita=dae.codigo_receita,
                    referencia=dae.referencia,
                    valor_principal=dae.valor_principal,
                )
            )

    return confirmados, nao_localizados
