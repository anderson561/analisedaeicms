from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def gerar_relatorio_conciliadas_pdf(conciliadas: list[NotaConciliada], caminho: Path) -> Path:
    documento = SimpleDocTemplate(
        str(caminho),
        pagesize=landscape(A4),
        title="AuditaDAE - Notas Conciliadas",
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("AuditaDAE — Notas Conciliadas", estilos["Title"]),
        Paragraph(f"Gerado em {datetime.now():%d/%m/%Y %H:%M}", estilos["Normal"]),
        Spacer(1, 12),
    ]

    dados = [COLUNAS_CONCILIADAS] + [
        [
            nota.numero_nf,
            nota.codigo_receita or "",
            nota.referencia or "",
            f"{nota.valor_principal:.2f}" if nota.valor_principal is not None else "",
            nota.especificacao_receita or "",
            nota.status,
        ]
        for nota in conciliadas
    ]

    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6f43")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(tabela)
    documento.build(elementos)
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
