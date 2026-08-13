from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

from src.models.dae_models import NotaConciliada, NotaNaoEncontrada

COLUNAS_CONCILIADAS = [
    "Número da NF",
    "Código da Receita",
    "Referência",
    "Valor Principal (R$)",
    "Especificação da Receita",
    "Status",
]

COLUNAS_NAO_ENCONTRADAS = [
    "Número da NF",
    "Data de Emissão",
    "CNPJ do Emitente",
    "Status",
]


def _gerar_planilha(caminho: Path, colunas: list[str], linhas: list[list]) -> None:
    workbook = Workbook()
    planilha = workbook.active
    planilha.append(colunas)
    for linha in linhas:
        planilha.append(linha)
    workbook.save(str(caminho))


def gerar_relatorio_conciliadas(conciliadas: list[NotaConciliada], caminho: Path) -> Path:
    linhas = [
        [
            nota.numero_nf,
            nota.codigo_receita,
            nota.referencia,
            nota.valor_principal,
            nota.especificacao_receita,
            f"🟢 {nota.status}",
        ]
        for nota in conciliadas
    ]
    _gerar_planilha(caminho, COLUNAS_CONCILIADAS, linhas)
    return caminho


def gerar_relatorio_nao_encontradas(nao_encontradas: list[NotaNaoEncontrada], caminho: Path) -> Path:
    linhas = [
        [
            nota.numero_nf,
            nota.data_emissao,
            nota.cnpj_emitente,
            f"🔴 {nota.status}",
        ]
        for nota in nao_encontradas
    ]
    _gerar_planilha(caminho, COLUNAS_NAO_ENCONTRADAS, linhas)
    return caminho


def gerar_relatorios(
    conciliadas: list[NotaConciliada],
    nao_encontradas: list[NotaNaoEncontrada],
    diretorio_saida: str,
) -> tuple[Path, Path]:
    diretorio = Path(diretorio_saida)
    diretorio.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho_conciliadas = diretorio / f"relatorio_conciliadas_{timestamp}.xlsx"
    caminho_nao_encontradas = diretorio / f"relatorio_nao_encontradas_{timestamp}.xlsx"

    gerar_relatorio_conciliadas(conciliadas, caminho_conciliadas)
    gerar_relatorio_nao_encontradas(nao_encontradas, caminho_nao_encontradas)

    return caminho_conciliadas, caminho_nao_encontradas
