from datetime import datetime
from pathlib import Path

from src.db.database import obter_conexao
from src.db.repository import salvar_conciliacao, salvar_dae
from src.engine.conciliador import conciliar
from src.engine.verificador_pagamento import verificar_pagamentos
from src.extractors.dae_extractor import extrair_dae
from src.extractors.pagamento_extractor import extrair_pagamentos
from src.extractors.relatorio_extractor import ler_relatorio
from src.models.dae_models import (
    DaeDocumento,
    DaePagamentoNaoLocalizado,
    NotaConciliada,
    NotaNaoEncontrada,
    PagamentoConfirmado,
)
from src.reports.report_generator import (
    gerar_relatorio_pagamentos_confirmados,
    gerar_relatorio_pagamentos_nao_localizados,
    gerar_relatorios,
)


def processar_lote(
    caminhos_dae: list[str],
    caminho_relatorio: str | None = None,
    diretorio_saida: str | None = None,
    coluna_nf: str | None = None,
) -> tuple[Path | None, Path | None, list[NotaConciliada], list[NotaNaoEncontrada], list[DaeDocumento]]:
    daes = [extrair_dae(caminho) for caminho in caminhos_dae]

    if caminho_relatorio is None:
        return None, None, [], [], daes

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

    saida = diretorio_saida or str(Path(caminhos_dae[0]).parent if caminhos_dae else Path.cwd())
    caminho_conciliadas, caminho_nao_encontradas = gerar_relatorios(conciliadas, nao_encontradas, saida)
    return caminho_conciliadas, caminho_nao_encontradas, conciliadas, nao_encontradas, daes


def verificar_pagamentos_lote(
    daes: list[DaeDocumento],
    caminho_relatorio_pagamento: str,
    diretorio_saida: str | None = None,
) -> tuple[Path, Path, list[PagamentoConfirmado], list[DaePagamentoNaoLocalizado]]:
    linhas_pagamento = extrair_pagamentos(caminho_relatorio_pagamento)
    confirmados, nao_localizados = verificar_pagamentos(daes, linhas_pagamento)

    saida = diretorio_saida or str(Path(caminho_relatorio_pagamento).parent)
    diretorio = Path(saida)
    diretorio.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_confirmados = diretorio / f"pagamentos_confirmados_{timestamp}.xlsx"
    caminho_nao_localizados = diretorio / f"pagamentos_nao_localizados_{timestamp}.xlsx"

    gerar_relatorio_pagamentos_confirmados(confirmados, caminho_confirmados)
    gerar_relatorio_pagamentos_nao_localizados(nao_localizados, caminho_nao_localizados)

    return caminho_confirmados, caminho_nao_localizados, confirmados, nao_localizados
