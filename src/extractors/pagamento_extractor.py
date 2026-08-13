import re

import fitz
import pytesseract
from PIL import Image

from src.models.dae_models import LinhaPagamentoDae
from src.ocr.tesseract_setup import configurar_tesseract

DPI_RENDER = 300
COLUNAS_ESPERADAS = 6

PADRAO_REFERENCIA = re.compile(r"^\s*(\d{1,2})/(\d{4})\s*$")
# O separador de milhar (".") e opcional: este relatorio imprime valores >= 1000
# sem ele (ex.: "1124,29"), entao o grupo inicial de digitos nao pode ser limitado a 1-3.
PADRAO_VALOR = re.compile(r"^\d+(\.\d{3})*,\d{2}$")

CONFIG_POR_COLUNA = {
    0: "--psm 7 -c tessedit_char_whitelist=0123456789",
    1: "--psm 7 -c tessedit_char_whitelist=0123456789/",
    2: "--psm 7 -c tessedit_char_whitelist=0123456789/",
    3: "--psm 7",
    4: "--psm 7 -c tessedit_char_whitelist=0123456789.,",
    5: "--psm 7 -c tessedit_char_whitelist=0123456789.,",
}

PAD_CELULA_PX = 2


def _parse_referencia(texto: str | None) -> tuple[int, int] | None:
    if not texto:
        return None
    m = PADRAO_REFERENCIA.match(texto)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _parse_valor(texto: str | None) -> tuple[float | None, bool]:
    if not texto or not PADRAO_VALOR.match(texto.strip()):
        return None, True
    normalizado = texto.strip().replace(".", "").replace(",", ".")
    return float(normalizado), False


def _parse_linha(valores: list[str]) -> LinhaPagamentoDae:
    nosso_numero, data_pagamento, referencia_bruta, receita, valor_principal_txt, valor_total_txt = valores

    mes_ano = _parse_referencia(referencia_bruta)
    valor_principal, revisar_principal = _parse_valor(valor_principal_txt)
    valor_total, revisar_total = _parse_valor(valor_total_txt)

    codigo_receita, descricao_receita = None, receita.strip() or None
    if receita and " - " in receita:
        codigo_receita, descricao_receita = (parte.strip() for parte in receita.split(" - ", 1))

    return LinhaPagamentoDae(
        nosso_numero=nosso_numero.strip(),
        data_pagamento=data_pagamento.strip() or None,
        referencia_bruta=referencia_bruta.strip() or None,
        mes_referencia=mes_ano[0] if mes_ano else None,
        ano_referencia=mes_ano[1] if mes_ano else None,
        codigo_receita=codigo_receita,
        descricao_receita=descricao_receita,
        valor_principal=valor_principal,
        valor_total=valor_total,
        revisar=revisar_principal or revisar_total or mes_ano is None,
    )


def _ocr_celula(imagem: Image.Image, bbox: tuple[float, float, float, float], escala: float, config: str) -> str:
    x0, y0, x1, y1 = bbox
    recorte = imagem.crop(
        (x0 * escala - PAD_CELULA_PX, y0 * escala - PAD_CELULA_PX, x1 * escala + PAD_CELULA_PX, y1 * escala + PAD_CELULA_PX)
    )
    return pytesseract.image_to_string(recorte, lang="por", config=config).strip()


def _selecionar_tabela_dados(pagina):
    tabelas = pagina.find_tables()
    for tabela in tabelas.tables:
        if tabela.col_count == COLUNAS_ESPERADAS:
            return tabela
    return None


def extrair_pagamentos(caminho_pdf: str) -> list[LinhaPagamentoDae]:
    configurar_tesseract()
    linhas_pagamento: list[LinhaPagamentoDae] = []

    documento = fitz.open(caminho_pdf)
    try:
        for pagina in documento:
            tabela = _selecionar_tabela_dados(pagina)
            if tabela is None:
                continue

            escala = DPI_RENDER / 72
            pixmap = pagina.get_pixmap(dpi=DPI_RENDER)
            imagem = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

            # Materializar em lista antes de iterar: acessar tabela.rows[1:] diretamente
            # no for produz bboxes incorretas para algumas linhas (comportamento observado
            # do PyMuPDF ao iterar o TableRows "ao vivo" em vez de uma lista já resolvida).
            linhas_dados = list(tabela.rows[1:])
            for linha in linhas_dados:
                valores = [
                    _ocr_celula(imagem, bbox, escala, CONFIG_POR_COLUNA[indice])
                    for indice, bbox in enumerate(linha.cells)
                ]
                if not any(valores):
                    continue
                linhas_pagamento.append(_parse_linha(valores))
    finally:
        documento.close()

    return linhas_pagamento
