from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models.dae_models import DaePagamentoNaoLocalizado, NotaConciliada, NotaNaoEncontrada, PagamentoConfirmado

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

COLUNAS_PAGAMENTOS_CONFIRMADOS = [
    "Nosso Número",
    "Pagamento",
    "Referência",
    "Receita",
    "Val. Principal",
    "Val. Total",
]

COLUNAS_PAGAMENTOS_NAO_LOCALIZADOS = [
    "Arquivo de Origem",
    "Código da Receita",
    "Referência",
    "Valor Principal (R$)",
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


def gerar_relatorio_nao_encontradas_pdf(nao_encontradas: list[NotaNaoEncontrada], caminho: Path) -> Path:
    documento = SimpleDocTemplate(
        str(caminho),
        pagesize=landscape(A4),
        title="AuditaDAE - Notas Nao Encontradas",
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("AuditaDAE — Notas Não Encontradas", estilos["Title"]),
        Paragraph(f"Gerado em {datetime.now():%d/%m/%Y %H:%M}", estilos["Normal"]),
        Spacer(1, 12),
    ]

    dados = [COLUNAS_NAO_ENCONTRADAS] + [
        [
            nota.numero_nf,
            nota.data_emissao or "",
            nota.cnpj_emitente or "",
            nota.status,
        ]
        for nota in nao_encontradas
    ]

    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8f1f1f")),
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


def gerar_relatorio_pagamentos_confirmados(confirmados: list[PagamentoConfirmado], caminho: Path) -> Path:
    linhas = [
        [
            confirmado.linha_pagamento.nosso_numero,
            confirmado.linha_pagamento.data_pagamento,
            confirmado.linha_pagamento.referencia_bruta,
            f"{confirmado.linha_pagamento.codigo_receita or ''} - {confirmado.linha_pagamento.descricao_receita or ''}",
            confirmado.linha_pagamento.valor_principal,
            confirmado.linha_pagamento.valor_total,
        ]
        for confirmado in confirmados
    ]
    _gerar_planilha(caminho, COLUNAS_PAGAMENTOS_CONFIRMADOS, linhas)
    return caminho


def gerar_relatorio_pagamentos_nao_localizados(nao_localizados: list[DaePagamentoNaoLocalizado], caminho: Path) -> Path:
    linhas = [
        [
            nao_localizado.arquivo_origem,
            nao_localizado.codigo_receita,
            nao_localizado.referencia,
            nao_localizado.valor_principal,
            nao_localizado.status,
        ]
        for nao_localizado in nao_localizados
    ]
    _gerar_planilha(caminho, COLUNAS_PAGAMENTOS_NAO_LOCALIZADOS, linhas)
    return caminho


def _tabela_pagamentos(dados: list[list], cor_cabecalho: str) -> Table:
    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(cor_cabecalho)),
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
    return tabela


def gerar_relatorio_pagamentos_pdf(
    confirmados: list[PagamentoConfirmado],
    nao_localizados: list[DaePagamentoNaoLocalizado],
    caminho: Path,
) -> Path:
    documento = SimpleDocTemplate(
        str(caminho),
        pagesize=landscape(A4),
        title="AuditaDAE - Relatorio de Pagamentos",
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("AuditaDAE — Relatório de Pagamentos", estilos["Title"]),
        Paragraph(f"Gerado em {datetime.now():%d/%m/%Y %H:%M}", estilos["Normal"]),
        Spacer(1, 12),
    ]

    elementos.append(Paragraph("Pagamentos Confirmados", estilos["Heading2"]))
    dados_confirmados = [COLUNAS_PAGAMENTOS_CONFIRMADOS] + [
        [
            confirmado.linha_pagamento.nosso_numero,
            confirmado.linha_pagamento.data_pagamento or "",
            confirmado.linha_pagamento.referencia_bruta or "",
            f"{confirmado.linha_pagamento.codigo_receita or ''} - {confirmado.linha_pagamento.descricao_receita or ''}",
            f"{confirmado.linha_pagamento.valor_principal:.2f}" if confirmado.linha_pagamento.valor_principal is not None else "",
            f"{confirmado.linha_pagamento.valor_total:.2f}" if confirmado.linha_pagamento.valor_total is not None else "",
        ]
        for confirmado in confirmados
    ]
    elementos.append(_tabela_pagamentos(dados_confirmados, "#1f6f43"))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("Não Localizados no Relatório de Pagamentos", estilos["Heading2"]))
    dados_nao_localizados = [COLUNAS_PAGAMENTOS_NAO_LOCALIZADOS] + [
        [
            nao_localizado.arquivo_origem,
            nao_localizado.codigo_receita or "",
            nao_localizado.referencia or "",
            f"{nao_localizado.valor_principal:.2f}" if nao_localizado.valor_principal is not None else "",
            nao_localizado.status,
        ]
        for nao_localizado in nao_localizados
    ]
    elementos.append(_tabela_pagamentos(dados_nao_localizados, "#8f1f1f"))

    documento.build(elementos)
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
