from pathlib import Path

from src.db.database import obter_conexao
from src.db.repository import salvar_conciliacao, salvar_dae
from src.engine.conciliador import conciliar
from src.extractors.dae_extractor import extrair_dae
from src.extractors.relatorio_extractor import ler_relatorio
from src.models.dae_models import NotaConciliada, NotaNaoEncontrada
from src.reports.report_generator import gerar_relatorios


def processar_lote(
    caminhos_dae: list[str],
    caminho_relatorio: str,
    diretorio_saida: str | None = None,
    coluna_nf: str | None = None,
) -> tuple[Path, Path, list[NotaConciliada], list[NotaNaoEncontrada]]:
    daes = [extrair_dae(caminho) for caminho in caminhos_dae]
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
    return caminho_conciliadas, caminho_nao_encontradas, conciliadas, nao_encontradas
