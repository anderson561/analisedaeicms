import csv
import re
from pathlib import Path

import openpyxl
import pdfplumber
import xlrd

from src.models.dae_models import LinhaRelatorio

PADRAO_COLUNA_NF = re.compile(r"n[uú]mero.*nota|n[ºo°]?\s*nf|nota\s*fiscal|^nf$", re.IGNORECASE)


def detectar_coluna_nf(cabecalho: list[str]) -> str | None:
    for nome in cabecalho:
        if nome and PADRAO_COLUNA_NF.search(nome.strip()):
            return nome
    return None


def _linhas_para_modelos(cabecalho: list[str], linhas: list[list], coluna_nf: str | None) -> list[LinhaRelatorio]:
    coluna_alvo = coluna_nf or detectar_coluna_nf(cabecalho)
    if coluna_alvo is None or coluna_alvo not in cabecalho:
        raise ValueError(
            "Não foi possível identificar a coluna de Número da Nota Fiscal. "
            "Informe explicitamente o nome da coluna (parâmetro coluna_nf)."
        )
    indice_nf = cabecalho.index(coluna_alvo)

    resultado = []
    for linha in linhas:
        if indice_nf >= len(linha) or linha[indice_nf] in (None, ""):
            continue
        dados = {cabecalho[i]: str(linha[i]) if i < len(linha) and linha[i] is not None else "" for i in range(len(cabecalho))}
        resultado.append(LinhaRelatorio(numero_nf=str(linha[indice_nf]), dados_originais=dados))
    return resultado


def _ler_xlsx(caminho: str, coluna_nf: str | None) -> list[LinhaRelatorio]:
    workbook = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    planilha = workbook.active
    linhas_iter = planilha.iter_rows(values_only=True)
    cabecalho = [str(c) if c is not None else "" for c in next(linhas_iter)]
    linhas = [list(linha) for linha in linhas_iter]
    return _linhas_para_modelos(cabecalho, linhas, coluna_nf)


def _ler_xls(caminho: str, coluna_nf: str | None) -> list[LinhaRelatorio]:
    workbook = xlrd.open_workbook(caminho)
    planilha = workbook.sheet_by_index(0)
    cabecalho = [str(planilha.cell_value(0, col)) for col in range(planilha.ncols)]
    linhas = [
        [planilha.cell_value(linha, col) for col in range(planilha.ncols)]
        for linha in range(1, planilha.nrows)
    ]
    return _linhas_para_modelos(cabecalho, linhas, coluna_nf)


def _ler_csv(caminho: str, coluna_nf: str | None) -> list[LinhaRelatorio]:
    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        linhas_todas = list(leitor)
    if not linhas_todas:
        return []
    cabecalho = linhas_todas[0]
    linhas = linhas_todas[1:]
    return _linhas_para_modelos(cabecalho, linhas, coluna_nf)


def _ler_pdf(caminho: str, coluna_nf: str | None) -> list[LinhaRelatorio]:
    cabecalho: list[str] | None = None
    linhas: list[list] = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            for tabela in pagina.extract_tables():
                if not tabela:
                    continue
                if cabecalho is None:
                    cabecalho = [str(c) if c is not None else "" for c in tabela[0]]
                    linhas.extend(tabela[1:])
                else:
                    linhas.extend(tabela)
    if cabecalho is None:
        return []
    return _linhas_para_modelos(cabecalho, linhas, coluna_nf)


def ler_relatorio(caminho: str, coluna_nf: str | None = None) -> list[LinhaRelatorio]:
    extensao = Path(caminho).suffix.lower()
    if extensao == ".xlsx":
        return _ler_xlsx(caminho, coluna_nf)
    if extensao == ".xls":
        return _ler_xls(caminho, coluna_nf)
    if extensao == ".csv":
        return _ler_csv(caminho, coluna_nf)
    if extensao == ".pdf":
        return _ler_pdf(caminho, coluna_nf)
    raise ValueError(f"Formato de relatório não suportado: {extensao}")
