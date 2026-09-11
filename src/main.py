from pathlib import Path

from src.db.database import obter_conexao
from src.db.repository import salvar_conciliacao, salvar_dae
from src.engine.conciliador import conciliar, filtrar_conciliadas_com_dados
from src.engine.verificador_pagamento import verificar_pagamentos
from src.engine.verificador_parcelamento import verificar_parcelamento, verificar_parcelamento_por_valor
from src.extractors.classificador_planilha import classificar_abas
from src.extractors.dae_extractor import extrair_dae
from src.extractors.icms_at_extractor import extrair_icms_at
from src.extractors.pagamento_extractor import extrair_pagamentos
from src.extractors.pagamento_planilha_extractor import extrair_pagamentos_e_parcelamento_de_planilha
from src.extractors.parcelamento_extractor import extrair_parcelamento
from src.extractors.relatorio_extractor import ler_relatorio
from src.models.dae_models import (
    DaeDocumento,
    DaeParceladoEncontrado,
    DaeParceladoNaoEncontrado,
    DaePagamentoNaoLocalizado,
    PagamentoConfirmado,
    ResultadoProcessamento,
)


def _extrair_daes(caminhos_dae: list[str]) -> list[DaeDocumento]:
    return [extrair_dae(caminho) for caminho in caminhos_dae]


def detectar_fontes_relatorio(caminho_relatorio: str) -> list[str]:
    if Path(caminho_relatorio).suffix.lower() != ".xlsx":
        return ["aquisicao"]
    classificacao = classificar_abas(caminho_relatorio)
    fontes = ["aquisicao"]
    if classificacao["apuracao"]:
        fontes.append("icms_at")
    if classificacao["pagamento_dae"]:
        fontes.append("pagamento_dae")
    return fontes


def processar_lote(
    caminhos_dae: list[str],
    caminho_relatorio: str | None = None,
    coluna_nf: str | None = None,
    buscar_aquisicao: bool = True,
    buscar_icms_at: bool = False,
    buscar_pagamento_dae: bool = False,
) -> ResultadoProcessamento:
    daes = _extrair_daes(caminhos_dae)

    if caminho_relatorio is None:
        return ResultadoProcessamento(daes=daes)

    resultado = ResultadoProcessamento(daes=daes)

    if buscar_aquisicao:
        linhas_relatorio = ler_relatorio(caminho_relatorio, coluna_nf=coluna_nf)

        conciliadas, nao_encontradas = conciliar(daes, linhas_relatorio)

        conexao = obter_conexao()
        try:
            nf_conciliadas = {nota.numero_nf for nota in conciliadas}
            for dae in daes:
                dae_id = salvar_dae(conexao, dae)
                for nf in dae.notas_fiscais:
                    status = "ENCONTRADO" if nf in nf_conciliadas else "NAO_ENCONTRADO"
                    salvar_conciliacao(conexao, dae_id, nf, status)
        finally:
            conexao.close()

        resultado.conciliadas = filtrar_conciliadas_com_dados(conciliadas)
        resultado.nao_encontradas = nao_encontradas

    if buscar_icms_at:
        resultado.linhas_icms_at = extrair_icms_at(caminho_relatorio)

    if buscar_pagamento_dae:
        abas_pagamento_dae = classificar_abas(caminho_relatorio)["pagamento_dae"]
        linhas_pagamento, linhas_parcelamento = extrair_pagamentos_e_parcelamento_de_planilha(
            caminho_relatorio, abas_pagamento_dae
        )
        resultado.pagamentos_confirmados, resultado.pagamentos_nao_localizados = verificar_pagamentos(
            daes, linhas_pagamento
        )
        resultado.parcelamento_encontrados, resultado.parcelamento_nao_encontrados = (
            verificar_parcelamento_por_valor(daes, linhas_parcelamento)
        )

    return resultado


def verificar_pagamentos_lote(
    caminhos_dae: list[str],
    caminhos_relatorio_pagamento: list[str],
) -> tuple[list[PagamentoConfirmado], list[DaePagamentoNaoLocalizado]]:
    daes = _extrair_daes(caminhos_dae)
    linhas_pagamento = [
        linha for caminho in caminhos_relatorio_pagamento for linha in extrair_pagamentos(caminho)
    ]
    confirmados, nao_localizados = verificar_pagamentos(daes, linhas_pagamento)
    return confirmados, nao_localizados


def verificar_parcelamento_lote(
    caminhos_dae: list[str],
    caminhos_parcelamento: list[str],
) -> tuple[list[DaeParceladoEncontrado], list[DaeParceladoNaoEncontrado]]:
    daes = _extrair_daes(caminhos_dae)
    linhas_parcelamento = [
        linha for caminho in caminhos_parcelamento for linha in extrair_parcelamento(caminho)
    ]
    return verificar_parcelamento(daes, linhas_parcelamento)
