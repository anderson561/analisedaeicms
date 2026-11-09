import re

import pdfplumber

from src.models.dae_models import ItemListaNotas, LinhaNotaItem

# Relatório SEFAZ-BA "Antecipação parcial do ICMS... Lista de notas
# fiscais/itens". Cada linha de item tem a forma:
#   DataEmiss DataLcto DtaAud DtaMdfe DtaOcorr UF CFOP Serie NunDoc
#   <Descrição...> <Item (3 dígitos)> VlLiqItem IPI VlDespAcess VlTotItem
#   AliqUtil VlCredEmpr PercRedBc VlBcAntParc AliqInt VlCredAud VlAntParc
# seguida, às vezes, do resto da descrição e da linha "CodItem:... - NCM:..."
# (o NCM pode cair numa linha própria). Ao contrário do relatório de
# Entradas, aqui os tokens não ficam colados -- confirmado com pdfplumber em
# PDFs reais (extract_words já separa tudo).
PADRAO_DATA_CURTA = re.compile(r"^\d{2}/\d{2}/\d{2}$")
PADRAO_ITEM = re.compile(r"^\d{3}$")
PADRAO_MONEY = re.compile(r"^[\d.]+,\d{2,3}$")
PADRAO_COD_ITEM = re.compile(r"CodItem:\s*(.*?)\s*(?:-\s*)?(?:NCM:|$)")
PADRAO_NCM = re.compile(r"NCM:\s*(\d+)")

INDICE_DATA_LANCAMENTO = 1
INDICE_UF = 5
INDICE_CFOP = 6
INDICE_SERIE = 7
INDICE_NUNDOC = 8
INDICE_INICIO_DESCRICAO = 9

QUANTIDADE_VALORES_APOS_ITEM = 11
OFFSET_VL_LIQ_ITEM = 1
OFFSET_VL_TOT_ITEM = 4
OFFSET_VL_CRED_EMPR = 6
OFFSET_VL_BC_ANT_PARC = 8
OFFSET_ALIQ_INT = 9
OFFSET_VL_CRED_AUD = 10

# Linhas que encerram o bloco de um item (subtotal, novo período, rodapé
# da última página) e linhas de cabeçalho/rodapé repetidas a cada página.
PREFIXOS_FIM_DE_BLOCO = ("Total", "Período:", "DtaEmiss")
PREFIXOS_CABECALHO_RODAPE = (
    "SECRETARIA",
    "SAT/",
    "OS:",
    "Estabelecimento",
    "CNPJ:",
    "Demonstrativo:",
    "DataEmiss",
    "A B C",
)
PADRAO_RODAPE = re.compile(r"^\d+-R\s+SIAF\b")


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


def _indice_do_item(tokens: list[str]) -> int | None:
    """O Item é o token de 3 dígitos seguido dos 11 valores da linha -- a
    descrição pode conter números de 3 dígitos (ex.: "BOTA PAMPILI 289")."""
    for indice in range(INDICE_INICIO_DESCRICAO, len(tokens) - QUANTIDADE_VALORES_APOS_ITEM):
        valores = tokens[indice + 1 : indice + 1 + QUANTIDADE_VALORES_APOS_ITEM]
        if PADRAO_ITEM.match(tokens[indice]) and all(PADRAO_MONEY.match(v) for v in valores):
            return indice
    return None


def _parse_item(tokens: list[str]) -> ItemListaNotas | None:
    if len(tokens) <= INDICE_NUNDOC or not PADRAO_DATA_CURTA.match(tokens[0]):
        return None

    indice_item = _indice_do_item(tokens)
    if indice_item is None:
        return None

    _, mes, ano = tokens[0].split("/")
    data_lancamento = tokens[INDICE_DATA_LANCAMENTO]
    return ItemListaNotas(
        data_emissao=tokens[0],
        data_lancamento=data_lancamento if PADRAO_DATA_CURTA.match(data_lancamento) else None,
        ano=2000 + int(ano),
        mes=int(mes),
        uf=tokens[INDICE_UF],
        nota=tokens[INDICE_NUNDOC],
        descricao=" ".join(tokens[INDICE_INICIO_DESCRICAO:indice_item]).strip(),
        vl_liq_item=_parse_valor_monetario(tokens[indice_item + OFFSET_VL_LIQ_ITEM]),
        vl_tot_item=_parse_valor_monetario(tokens[indice_item + OFFSET_VL_TOT_ITEM]),
        aliq_int=_parse_valor_monetario(tokens[indice_item + OFFSET_ALIQ_INT]),
        vl_cred_empr=_parse_valor_monetario(tokens[indice_item + OFFSET_VL_CRED_EMPR]),
        vl_bc_ant_parc=_parse_valor_monetario(tokens[indice_item + OFFSET_VL_BC_ANT_PARC]),
        vl_cred_aud=_parse_valor_monetario(tokens[indice_item + OFFSET_VL_CRED_AUD]),
    )


def _parse_linha(tokens: list[str]) -> LinhaNotaItem | None:
    item = _parse_item(tokens)
    if item is None:
        return None

    ano_lancamento, mes_lancamento = None, None
    if item.data_lancamento is not None:
        _, mes_lcto, ano_lcto = item.data_lancamento.split("/")
        ano_lancamento, mes_lancamento = 2000 + int(ano_lcto), int(mes_lcto)

    return LinhaNotaItem(
        ano=item.ano,
        mes=item.mes,
        nota=item.nota,
        descricao=item.descricao,
        valor=item.vl_liq_item,
        ano_lancamento=ano_lancamento,
        mes_lancamento=mes_lancamento,
    )


def _itens_das_linhas(linhas: list[list[str]]) -> list[ItemListaNotas]:
    """Monta os itens completos: linha do item + continuação da descrição +
    CodItem/NCM, ignorando cabeçalho e rodapé de página no meio do bloco."""
    itens: list[ItemListaNotas] = []
    atual: ItemListaNotas | None = None
    viu_cod_item = False
    for tokens in linhas:
        item = _parse_item(tokens)
        if item is not None:
            itens.append(item)
            atual, viu_cod_item = item, False
            continue

        texto = " ".join(tokens).strip()
        if atual is None or not texto:
            continue
        if texto.startswith(PREFIXOS_FIM_DE_BLOCO):
            atual = None
            continue
        if texto.startswith(PREFIXOS_CABECALHO_RODAPE) or PADRAO_RODAPE.match(texto):
            continue

        cod_item = PADRAO_COD_ITEM.search(texto)
        ncm = PADRAO_NCM.search(texto)
        if cod_item:
            atual.cod_item = cod_item.group(1).rstrip(" -") or None
            viu_cod_item = True
        if ncm:
            atual.ncm = ncm.group(1)
        if not cod_item and not ncm and not viu_cod_item:
            atual.descricao = f"{atual.descricao} {texto}".strip()
    return itens


def _linhas_do_pdf(caminho_pdf: str) -> list[list[str]]:
    linhas: list[list[str]] = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            palavras = pagina.extract_words(x_tolerance=1.5)
            linhas.extend([w["text"] for w in linha] for linha in _agrupar_em_linhas(palavras))
    return linhas


def extrair_itens_notas(caminho_pdf: str) -> list[LinhaNotaItem]:
    itens: list[LinhaNotaItem] = []
    for tokens in _linhas_do_pdf(caminho_pdf):
        resultado = _parse_linha(tokens)
        if resultado is not None:
            itens.append(resultado)
    return itens


def extrair_itens_lista_completos(caminho_pdf: str) -> list[ItemListaNotas]:
    return _itens_das_linhas(_linhas_do_pdf(caminho_pdf))
