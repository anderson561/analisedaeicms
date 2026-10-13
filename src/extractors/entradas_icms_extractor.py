import re

import pdfplumber

from src.models.dae_models import LinhaEntradaIcms

# O relatório "ACOMPANHAMENTO DE ENTRADAS" (SEFAZ-BA) tem camada de texto mas
# nenhuma grade vetorizada (extract_tables() não encontra nada). Pior: quando o
# nome do fornecedor é longo o suficiente para sobrepor visualmente a faixa das
# colunas CFOP/AC./UF, o próprio PDF tem os caracteres dessas colunas
# entrelaçados caractere-a-caractere com o nome (defeito do gerador do
# relatório, confirmado inspecionando um PDF real) -- não é recuperável nem
# via extract_words() com tolerância fina. Por isso a extração ignora
# completamente Código Fornecedor/CFOP/AC./UF/Base Cálculo/Alíq./Valor/
# Isentas/Outras e ancora só nos campos realmente necessários (Data, Nota,
# Valor Contábil, Tipo), que ficam sempre intactos.
PADRAO_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
PADRAO_MONEY = re.compile(r"^[\d.]+,\d{2}$")
PADRAO_TIPO = re.compile(r"^(ICMS|ST/AT)$", re.IGNORECASE)

TOLERANCIA_MESMA_LINHA = 1.5


def _parse_valor_monetario(valor_texto: str) -> float:
    limpo = valor_texto.replace(".", "").replace(",", ".")
    return float(limpo)


def _agrupar_em_linhas(palavras: list[dict], tolerancia_top: float = TOLERANCIA_MESMA_LINHA) -> list[list[dict]]:
    linhas: list[list[dict]] = []
    for palavra in sorted(palavras, key=lambda w: (w["top"], w["x0"])):
        if linhas and abs(linhas[-1][0]["top"] - palavra["top"]) <= tolerancia_top:
            linhas[-1].append(palavra)
        else:
            linhas.append([palavra])
    return [sorted(linha, key=lambda w: w["x0"]) for linha in linhas]


def _parse_linha(tokens: list[str]) -> LinhaEntradaIcms | None:
    indice_data = next((i for i, t in enumerate(tokens) if PADRAO_DATA.match(t)), None)
    if indice_data is None or indice_data + 4 >= len(tokens):
        return None

    data_texto = tokens[indice_data]
    nota = tokens[indice_data + 1]

    # Valor Contábil e Tipo são o único par confiável depois da Nota -- tudo
    # entre eles (Série/Espécie/Código Fornecedor/CFOP/AC./UF) é ignorado, já
    # que pode estar corrompido pela sobreposição descrita acima.
    valor_contabil = None
    tipo = None
    indice_valor = None
    for i in range(indice_data + 2, len(tokens) - 1):
        if PADRAO_MONEY.match(tokens[i]) and PADRAO_TIPO.match(tokens[i + 1]):
            valor_contabil = tokens[i]
            tipo = tokens[i + 1].upper()
            indice_valor = i
            break

    valor = None
    if valor_contabil is not None:
        valor = _parse_valor_monetario(valor_contabil)
    else:
        # Nome de fornecedor longo pode embaralhar o próprio token do Valor
        # Contábil; nesse caso ele é recomposto por Base + Isentas + Outras
        # (identidade conferida em todas as linhas legíveis de um PDF real).
        indice_tipo = next(
            (i for i in range(indice_data + 5, len(tokens)) if PADRAO_TIPO.match(tokens[i])), None
        )
        if indice_tipo is None:
            return None
        finais = [t for t in tokens[indice_tipo + 1 :] if PADRAO_MONEY.match(t)]
        if len(finais) < 5:
            return None
        base, _aliquota, _valor_imposto, isentas, outras = (_parse_valor_monetario(t) for t in finais[:5])
        valor = round(base + isentas + outras, 2)
        tipo = tokens[indice_tipo].upper()
        indice_valor = indice_tipo

    fornecedor_tokens = tokens[indice_data + 5 : indice_valor]
    fornecedor = " ".join(fornecedor_tokens).strip() or None

    dia, mes, ano = data_texto.split("/")
    return LinhaEntradaIcms(
        ano=int(ano),
        mes=int(mes),
        nota=nota,
        fornecedor=fornecedor,
        valor_contabil=valor,
        tipo=tipo,
    )


def _selecionar_melhor_linha_por_nota(linhas: list[LinhaEntradaIcms]) -> list[LinhaEntradaIcms]:
    """Por nota, mantém a linha "ICMS"; só cai para "ST/AT" se a nota não
    tiver nenhuma linha ICMS (ver decisão registrada no plano)."""
    melhor_por_nota: dict[tuple[int, int, str], LinhaEntradaIcms] = {}
    for linha in linhas:
        chave = (linha.ano, linha.mes, linha.nota)
        atual = melhor_por_nota.get(chave)
        if atual is None or (atual.tipo != "ICMS" and linha.tipo == "ICMS"):
            melhor_por_nota[chave] = linha
    return list(melhor_por_nota.values())


def extrair_entradas_icms(caminho_pdf: str) -> list[LinhaEntradaIcms]:
    linhas_encontradas: list[LinhaEntradaIcms] = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            palavras = pagina.extract_words(x_tolerance=1.5)
            for linha in _agrupar_em_linhas(palavras):
                resultado = _parse_linha([w["text"] for w in linha])
                if resultado is not None:
                    linhas_encontradas.append(resultado)

    return _selecionar_melhor_linha_por_nota(linhas_encontradas)
