"""Leitores da aba "Analisar Apuração": o relatório de créditos gerado pela
aba Verificar Créditos (Excel ou PDF) e a planilha de DAEs com a coluna
"Informações de Pagamento (DAE)"."""

import re
from pathlib import Path

import openpyxl
import pdfplumber

from src.engine.conciliador import sanitize_nf_numero
from src.models.dae_models import NotaCredito

PADRAO_DATA_CURTA = re.compile(r"^\d{2}/\d{2}/\d{2}$")
PADRAO_SO_DIGITOS = re.compile(r"^\d+$")
PADRAO_COLUNA_NF_DAE = re.compile(r"n[uú]mero.*(nf|nota)", re.IGNORECASE)
PADRAO_COLUNA_INFORMACAO_DAE = re.compile(r"informa[cç][oõ]es.*pagamento", re.IGNORECASE)

# Cabeçalhos de COLUNAS_CREDITOS (report_generator) -> campo de NotaCredito.
# VlBcAntParc é opcional: relatórios gerados antes dessa coluna não a têm.
COLUNA_NOTA = "Nº Nota"
CAMPOS_TEXTO = {
    "Data Emissão": "data_emissao",
    "Data Lançamento": "data_lancamento",
    "UF": "uf",
    COLUNA_NOTA: "nota",
    "Descrição / CodItem / NCM": "descricao",
}
CAMPOS_VALOR = {
    "VlLiqItem (R$)": "vl_liq_item",
    "VlCredEmpr (R$)": "vl_cred_empr",
    "VlBcAntParc (R$)": "vl_bc_ant_parc",
    "VlCredAud (R$)": "vl_cred_aud",
}


def _texto(celula) -> str:
    return " ".join(str(celula).split()) if celula is not None else ""


def _valor(celula) -> float:
    if isinstance(celula, (int, float)):
        return float(celula)
    texto = _texto(celula)
    return float(texto.replace(".", "").replace(",", ".")) if texto else 0.0


def _notas_das_linhas(linhas: list[list]) -> list[NotaCredito]:
    notas: list[NotaCredito] = []
    indices: dict[str, int] | None = None
    for linha in linhas:
        textos = [_texto(c) for c in linha]
        if COLUNA_NOTA in textos:
            # As 5 primeiras colunas têm ordem fixa no relatório; pela posição,
            # porque no PDF o cabeçalho às vezes sai partido ("Data Emissã" |
            # "o Data Lançamento"). Os valores são localizados pelo nome.
            indices = {nome: posicao for posicao, nome in enumerate(CAMPOS_TEXTO)}
            indices.update({nome: textos.index(nome) for nome in CAMPOS_VALOR if nome in textos})
            continue
        if indices is None:
            continue
        numero = textos[indices[COLUNA_NOTA]] if indices[COLUNA_NOTA] < len(textos) else ""
        if not PADRAO_SO_DIGITOS.match(numero):
            continue  # títulos de ano/mês, linhas de total, linhas vazias

        campos = {campo: textos[indices[nome]] for nome, campo in CAMPOS_TEXTO.items() if nome in indices}
        campos.update({campo: _valor(linha[indices[nome]]) for nome, campo in CAMPOS_VALOR.items() if nome in indices})
        emissao = campos.get("data_emissao", "")
        if not PADRAO_DATA_CURTA.match(emissao):
            continue
        _, mes, ano = emissao.split("/")
        notas.append(
            NotaCredito(
                ano=2000 + int(ano),
                mes=int(mes),
                data_lancamento=campos.pop("data_lancamento", "") or None,
                quantidade_itens=0,
                vl_bc_ant_parc=campos.pop("vl_bc_ant_parc", 0.0),
                **campos,
            )
        )
    if indices is None:
        raise ValueError(f"Relatório de créditos sem a coluna '{COLUNA_NOTA}'. Use o relatório gerado pela aba Verificar Créditos.")
    return notas


def _linhas_xlsx(caminho: str) -> list[list]:
    workbook = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    return [list(linha) for planilha in workbook.worksheets for linha in planilha.iter_rows(values_only=True)]


def _linhas_pdf(caminho: str) -> list[list]:
    linhas: list[list] = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            for tabela in pagina.extract_tables():
                linhas.extend(tabela)
    return linhas


def extrair_notas_relatorio_creditos(caminho: str) -> list[NotaCredito]:
    if Path(caminho).suffix.lower() == ".pdf":
        return _notas_das_linhas(_linhas_pdf(caminho))
    return _notas_das_linhas(_linhas_xlsx(caminho))


def _valores_com_mesclagem(planilha) -> list[list]:
    """Valores da planilha com cada célula mesclada repetindo o valor do
    canto superior esquerdo -- um DAE costuma cobrir várias notas."""
    valores = [list(linha) for linha in planilha.iter_rows(values_only=True)]
    for faixa in planilha.merged_cells.ranges:
        valor = valores[faixa.min_row - 1][faixa.min_col - 1]
        for linha in range(faixa.min_row - 1, faixa.max_row):
            for coluna in range(faixa.min_col - 1, faixa.max_col):
                valores[linha][coluna] = valor
    return valores


def extrair_informacoes_dae(caminho: str) -> dict[str, str]:
    """Mapa nº da nota (sem zeros à esquerda) -> texto de "Informações de
    Pagamento (DAE)", em todas as abas da planilha."""
    informacoes: dict[str, str] = {}
    workbook = openpyxl.load_workbook(caminho, data_only=True)
    for planilha in workbook.worksheets:
        coluna_nf = coluna_info = None
        for linha in _valores_com_mesclagem(planilha):
            textos = [_texto(c) for c in linha]
            cabecalho_nf = next((i for i, t in enumerate(textos) if PADRAO_COLUNA_NF_DAE.search(t)), None)
            cabecalho_info = next((i for i, t in enumerate(textos) if PADRAO_COLUNA_INFORMACAO_DAE.search(t)), None)
            if cabecalho_nf is not None and cabecalho_info is not None:
                coluna_nf, coluna_info = cabecalho_nf, cabecalho_info
                continue
            if coluna_nf is None or max(coluna_nf, coluna_info) >= len(textos):
                continue
            numero, informacao = textos[coluna_nf], textos[coluna_info]
            if PADRAO_SO_DIGITOS.match(numero) and informacao:
                informacoes.setdefault(sanitize_nf_numero(numero), informacao)
    return informacoes
