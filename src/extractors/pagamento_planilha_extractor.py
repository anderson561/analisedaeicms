from datetime import datetime

import openpyxl

from src.models.dae_models import LinhaPagamentoDae, LinhaParcelamento

COLUNAS_ESPERADAS = [
    "nosso número",
    "pagamento",
    "referência",
    "receita",
    "valor principal",
    "valor total",
]


def _para_float(valor) -> float | None:
    if valor is None:
        return None
    return float(valor)


def _localizar_linha_cabecalho(linhas: list[tuple]) -> int | None:
    for indice, linha in enumerate(linhas):
        normalizada = [str(c).strip().lower() if c is not None else "" for c in linha]
        if all(coluna in normalizada for coluna in COLUNAS_ESPERADAS):
            return indice
    return None


def extrair_pagamentos_e_parcelamento_de_planilha(
    caminho: str, abas: list[str]
) -> tuple[list[LinhaPagamentoDae], list[LinhaParcelamento]]:
    """Lê abas no formato 'pagamento_dae' (Nosso Número/Pagamento/Referência/
    Receita/Valor Principal/Valor Total) e separa cada linha pelo tipo da
    célula de Referência: uma data vira LinhaPagamentoDae (competência
    mês/ano, ex.: códigos 1145/2175), qualquer outra coisa (ex.: "015/023",
    parcela atual/total) vira LinhaParcelamento, sem mês/ano de ocorrência."""
    pagamentos: list[LinhaPagamentoDae] = []
    parcelamentos: list[LinhaParcelamento] = []

    workbook = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    try:
        for aba in abas:
            planilha = workbook[aba]
            linhas = list(planilha.iter_rows(values_only=True))
            if not linhas:
                continue

            indice_cabecalho = _localizar_linha_cabecalho(linhas)
            if indice_cabecalho is None:
                continue
            cabecalho = [str(c).strip().lower() if c is not None else "" for c in linhas[indice_cabecalho]]
            indice = {coluna: cabecalho.index(coluna) for coluna in COLUNAS_ESPERADAS}

            for linha in linhas[indice_cabecalho + 1 :]:
                if not linha or linha[indice["nosso número"]] is None:
                    continue

                nosso_numero = str(linha[indice["nosso número"]])
                data_pagamento = (
                    str(linha[indice["pagamento"]]) if linha[indice["pagamento"]] is not None else None
                )
                referencia_valor = linha[indice["referência"]]
                receita_completa = str(linha[indice["receita"]]) if linha[indice["receita"]] is not None else ""
                codigo_receita, _, descricao_receita = receita_completa.partition(" - ")
                valor_principal = _para_float(linha[indice["valor principal"]])
                valor_total = _para_float(linha[indice["valor total"]])

                if isinstance(referencia_valor, datetime):
                    pagamentos.append(
                        LinhaPagamentoDae(
                            nosso_numero=nosso_numero,
                            data_pagamento=data_pagamento,
                            referencia_bruta=f"{referencia_valor.month:02d}/{referencia_valor.year}",
                            mes_referencia=referencia_valor.month,
                            ano_referencia=referencia_valor.year,
                            codigo_receita=codigo_receita.strip() or None,
                            descricao_receita=descricao_receita.strip() or None,
                            valor_principal=valor_principal,
                            valor_total=valor_total,
                        )
                    )
                else:
                    parcelamentos.append(
                        LinhaParcelamento(
                            arquivo_origem=aba,
                            data_vencimento=data_pagamento,
                            valor_historico=valor_principal,
                            valor_debito=valor_total,
                        )
                    )
    finally:
        workbook.close()

    return pagamentos, parcelamentos
