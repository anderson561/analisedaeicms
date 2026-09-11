import re
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from src.models.dae_models import LinhaParcelamento
from src.ocr.tesseract_setup import configurar_tesseract

DPI_RENDER = 300

# O "Relatorio Debito do PAF" nao tem camada de texto nem grade vetorizada (a
# pagina inteira e desenhada como curvas/vetores) -- diferente do relatorio anual
# de pagamentos, aqui nao ha grid pra segmentar celulas, entao o OCR e feito na
# pagina inteira e cada linha de parcela e extraida por regex.
PADRAO_LINHA_PARCELA = re.compile(
    r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+Parcelado\D*?(\d+)\D*?([\d.,]+)\D*?(\d+)\D*?([\d.,]+)\D*?(\d+)",
    re.IGNORECASE,
)
PADRAO_PAF = re.compile(r"\d{6}\.\d{4}/\d{2}-\d")


def _parse_valor(texto: str | None) -> float | None:
    if not texto:
        return None
    try:
        return float(texto.strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _mes_ano_ocorrencia(data_ocorrencia: str | None) -> tuple[int, int] | None:
    if not data_ocorrencia:
        return None
    partes = data_ocorrencia.strip().split("/")
    if len(partes) != 3:
        return None
    try:
        return int(partes[1]), int(partes[2])
    except ValueError:
        return None


def _construir_linha(
    paf: str | None,
    arquivo_origem: str,
    data_ocorrencia: str,
    data_vencimento: str,
    valor_hist_txt: str,
    valor_debito_txt: str,
) -> LinhaParcelamento:
    mes_ano = _mes_ano_ocorrencia(data_ocorrencia)
    return LinhaParcelamento(
        paf=paf,
        arquivo_origem=arquivo_origem,
        data_ocorrencia=data_ocorrencia,
        data_vencimento=data_vencimento,
        mes_ocorrencia=mes_ano[0] if mes_ano else None,
        ano_ocorrencia=mes_ano[1] if mes_ano else None,
        valor_historico=_parse_valor(valor_hist_txt),
        valor_debito=_parse_valor(valor_debito_txt),
    )


def extrair_parcelamento(caminho_pdf: str) -> list[LinhaParcelamento]:
    configurar_tesseract()
    arquivo_origem = Path(caminho_pdf).name
    linhas_parcelamento: list[LinhaParcelamento] = []

    documento = fitz.open(caminho_pdf)
    try:
        for pagina in documento:
            pixmap = pagina.get_pixmap(dpi=DPI_RENDER)
            imagem = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            texto = pytesseract.image_to_string(imagem, lang="por", config="--psm 6")

            paf_match = PADRAO_PAF.search(texto)
            paf = paf_match.group(0) if paf_match else None

            for match in PADRAO_LINHA_PARCELA.finditer(texto):
                data_ocorrencia, data_vencimento, _aliq, valor_hist, _multa_hist, valor_debito, _multa_debito = (
                    match.groups()
                )
                linhas_parcelamento.append(
                    _construir_linha(paf, arquivo_origem, data_ocorrencia, data_vencimento, valor_hist, valor_debito)
                )
    finally:
        documento.close()

    return linhas_parcelamento
