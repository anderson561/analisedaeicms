import re

import pdfplumber

from src.models.dae_models import LinhaNotaItem

# Relatório SEFAZ-BA "Antecipação parcial do ICMS... Lista de notas
# fiscais/itens". Cada linha de item tem a forma:
#   DataEmiss DataLcto DtaAud DtaMdfe DtaOcorr UF CFOP Serie NunDoc
#   <Descrição...> <Item (3 dígitos)> VlLiqItem <demais colunas>
# seguida por uma linha de metadado "CodItem:... - NCM:..." que é ignorada.
# Ao contrário do relatório de Entradas, aqui os tokens não ficam colados --
# confirmado com pdfplumber em um PDF real (extract_words já separa tudo).
PADRAO_DATA_CURTA = re.compile(r"^\d{2}/\d{2}/\d{2}$")
PADRAO_ITEM = re.compile(r"^\d{3}$")
PADRAO_MONEY = re.compile(r"^[\d.]+,\d{2,3}$")

INDICE_DATA_LANCAMENTO = 1
INDICE_UF = 5
INDICE_CFOP = 6
INDICE_SERIE = 7
INDICE_NUNDOC = 8
INDICE_INICIO_DESCRICAO = 9


def _parse_valor_monetario(valor_texto: str) -> float:
    limpo = valor_texto.replace(".", "").replace(",", ".")
    return float(limpo)


def _agrupar_em_linhas(palavras: list[dict], tolerancia_top: float = 1.5) -> list[list[dict]]:
    linhas: list[list[dict]] = []
    for palavra in sorted(palavras, key=lambda w: (w["top"], w["x0"])):
        if linhas and abs(linhas[-1][0]["top"] - palavra["top"]) <= tolerancia_top:
            linhas[-1].append(palavra)
        else:
            linhas.append([palavra])
    return [sorted(linha, key=lambda w: w["x0"]) for linha in linhas]


def _parse_linha(tokens: list[str]) -> LinhaNotaItem | None:
    if len(tokens) <= INDICE_NUNDOC or not PADRAO_DATA_CURTA.match(tokens[0]):
        return None

    nun_doc = tokens[INDICE_NUNDOC]

    indice_item = next(
        (i for i in range(INDICE_INICIO_DESCRICAO, len(tokens)) if PADRAO_ITEM.match(tokens[i])),
        None,
    )
    if indice_item is None or indice_item + 1 >= len(tokens):
        return None

    descricao = " ".join(tokens[INDICE_INICIO_DESCRICAO:indice_item]).strip()
    valor_texto = tokens[indice_item + 1]
    if not PADRAO_MONEY.match(valor_texto):
        return None

    dia, mes, ano = tokens[0].split("/")
    ano_lancamento, mes_lancamento = None, None
    if PADRAO_DATA_CURTA.match(tokens[INDICE_DATA_LANCAMENTO]):
        _, mes_lcto, ano_lcto = tokens[INDICE_DATA_LANCAMENTO].split("/")
        ano_lancamento, mes_lancamento = 2000 + int(ano_lcto), int(mes_lcto)

    return LinhaNotaItem(
        ano=2000 + int(ano),
        mes=int(mes),
        nota=nun_doc,
        descricao=descricao,
        valor=_parse_valor_monetario(valor_texto),
        ano_lancamento=ano_lancamento,
        mes_lancamento=mes_lancamento,
    )


def extrair_itens_notas(caminho_pdf: str) -> list[LinhaNotaItem]:
    itens: list[LinhaNotaItem] = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            palavras = pagina.extract_words(x_tolerance=1.5)
            for linha in _agrupar_em_linhas(palavras):
                resultado = _parse_linha([w["text"] for w in linha])
                if resultado is not None:
                    itens.append(resultado)
    return itens
