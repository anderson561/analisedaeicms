import re

import pdfplumber

from src.models.dae_models import DaeDocumento

LABELS_CODIGO_RECEITA = [
    r"C[oó]digo\s+da\s+Receita",
    r"C[oó]d\.?\s*Receita",
]
LABELS_REFERENCIA = [
    r"Refer[eê]ncia",
    r"Per[ií]odo\s+de\s+Apura[cç][aã]o",
    r"Compet[eê]ncia",
]
LABELS_VALOR_PRINCIPAL = [
    r"Valor\s+Principal",
    r"Valor\s+do\s+Principal",
]
LABELS_ESPECIFICACAO = [
    r"Especifica[cç][aã]o\s+da\s+Receita",
    r"Especifica[cç][aã]o",
]

ANCORAS_NOTAS_FISCAIS = [
    r"Notas\s+Fiscais\s*:?",
    r"NFe?s?\s*:?",
    r"\bNotas\b\s*:?",
]

# Ex.: "Notas Fiscais:15" seguido de quebra de linha — "15" é a CONTAGEM de notas
# que vem a seguir, não a primeira nota. O [ \t]* (sem \n) garante que só
# reconhecemos a contagem quando o número está na mesma linha do rótulo.
PADRAO_CONTAGEM_NOTAS = re.compile(
    r"(?:Notas\s+Fiscais|NFe?s?)\s*:[ \t]*(\d+)[ \t]*\n", re.IGNORECASE
)

# Delimita o bloco de notas fiscais até o próximo campo numerado do formulário
# (ex.: "12-RECEITA BRUTA ACUMULADA"), uma linha em branco, ou uma linha
# tracejada — separador comum entre duas vias/cópias do mesmo DAE impressas
# na mesma página, atrás da qual normalmente vem a linha de código de barras
# (números longos e dígitos verificadores soltos que não são notas fiscais).
PADRAO_FIM_BLOCO_NOTAS = re.compile(r"\n\s*\d{1,2}-[A-ZÀ-ÖØ-Ý]|\n\s*\n|\n-{5,}")

PADRAO_CODIGO_RECEITA = r"\d{3,4}[-./]?\d?"
PADRAO_REFERENCIA = r"\d{2}[/.]\d{2,4}(?:[/.]\d{2,4})?"
PADRAO_VALOR = r"R?\$?\s*[\d.]+,\d{2}"
PADRAO_ESPECIFICACAO = r"[^\n]+"

JANELA_PADRAO = 80


def _buscar_valor_apos_label(texto: str, labels: list[str], padrao_valor: str, janela: int = JANELA_PADRAO) -> str | None:
    for label in labels:
        m_label = re.search(label, texto, re.IGNORECASE)
        if not m_label:
            continue
        trecho = texto[m_label.end() : m_label.end() + janela]
        m_valor = re.search(padrao_valor, trecho)
        if m_valor:
            return m_valor.group(0).strip()
    return None


def _parse_valor_monetario(valor_texto: str | None) -> float | None:
    if not valor_texto:
        return None
    limpo = re.sub(r"[R$\s]", "", valor_texto)
    limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def extrair_notas_fiscais(texto: str) -> list[str]:
    m_contagem = PADRAO_CONTAGEM_NOTAS.search(texto)
    inicio_bloco = m_contagem.end() if m_contagem else None

    if inicio_bloco is None:
        for ancora in ANCORAS_NOTAS_FISCAIS:
            m_ancora = re.search(ancora, texto, re.IGNORECASE)
            if m_ancora:
                inicio_bloco = m_ancora.end()
                break

    if inicio_bloco is None:
        return []

    m_fim = PADRAO_FIM_BLOCO_NOTAS.search(texto, inicio_bloco)
    fim_bloco = m_fim.start() if m_fim else len(texto)
    bloco = texto[inicio_bloco:fim_bloco]
    return re.findall(r"\b\d{1,10}\b", bloco)


def parse_dae_texto(texto: str, arquivo_origem: str = "") -> DaeDocumento:
    codigo_receita = _buscar_valor_apos_label(texto, LABELS_CODIGO_RECEITA, PADRAO_CODIGO_RECEITA)
    referencia = _buscar_valor_apos_label(texto, LABELS_REFERENCIA, PADRAO_REFERENCIA)
    valor_texto = _buscar_valor_apos_label(texto, LABELS_VALOR_PRINCIPAL, PADRAO_VALOR)
    especificacao = _buscar_valor_apos_label(texto, LABELS_ESPECIFICACAO, PADRAO_ESPECIFICACAO)
    notas_fiscais = extrair_notas_fiscais(texto)

    return DaeDocumento(
        arquivo_origem=arquivo_origem,
        codigo_receita=codigo_receita,
        referencia=referencia,
        valor_principal=_parse_valor_monetario(valor_texto),
        especificacao_receita=especificacao.strip(" :\t") if especificacao else None,
        notas_fiscais=notas_fiscais,
    )


# --- Extração baseada em posição geométrica -------------------------------
#
# O DAE padrão (SEFAZ-BA e similares) é um formulário em grade com várias
# colunas lado a lado na mesma faixa vertical (ex.: "1-CÓDIGO DA RECEITA" e
# "16-USO DA REPARTIÇÃO" compartilham a mesma altura). A extração de texto
# linear do pdfplumber intercala essas colunas em uma ordem que não
# corresponde à leitura humana, então cada valor acaba "colado" no rótulo
# errado. Em vez disso, localizamos cada rótulo pela sua posição (x, y) e
# lemos o valor na linha imediatamente abaixo, na mesma coluna.

ROTULO_CODIGO_RECEITA_POS = re.compile(r"^\d+-C[oó]digo", re.IGNORECASE)
ROTULO_REFERENCIA_POS = re.compile(r"^\d+-Refer[eê]ncia", re.IGNORECASE)
ROTULO_VALOR_PRINCIPAL_POS = re.compile(r"^\d+-Valor", re.IGNORECASE)
ROTULO_ESPECIFICACAO_POS = re.compile(r"^\d+-Especifica", re.IGNORECASE)

GAP_MAXIMO_MESMO_VALOR = 25.0
DISTANCIA_MAX_TOP_ROTULO = 15.0
TOLERANCIA_X_PRIMEIRA_PALAVRA = 15.0
FRACAO_LIMIAR_COLUNA_ESQUERDA_PADRAO = 0.45


def _valor_por_posicao(
    palavras: list[dict], padrao_rotulo: re.Pattern, distancia_max_top: float = DISTANCIA_MAX_TOP_ROTULO
) -> tuple[str, float] | None:
    """Localiza `padrao_rotulo` e lê o valor na linha abaixo, na mesma coluna.

    Retorna (texto_do_valor, x0_do_rotulo). O valor pode ter várias palavras:
    a partir da primeira palavra alinhada ao rótulo, seguimos coletando
    palavras vizinhas na mesma linha enquanto o espaço entre elas for o de
    um espaço normal — um salto grande indica que cruzamos para a coluna
    vizinha do formulário.
    """
    for palavra in sorted(palavras, key=lambda w: (w["top"], w["x0"])):
        if not padrao_rotulo.match(palavra["text"]):
            continue
        x0_rotulo = palavra["x0"]
        top_rotulo = palavra["top"]

        candidatas_primeira_palavra = [
            w
            for w in palavras
            if w["top"] > top_rotulo + 1
            and w["top"] - top_rotulo <= distancia_max_top
            and abs(w["x0"] - x0_rotulo) <= TOLERANCIA_X_PRIMEIRA_PALAVRA
        ]
        if not candidatas_primeira_palavra:
            continue

        primeira_palavra_valor = min(candidatas_primeira_palavra, key=lambda w: w["top"])
        top_valor = primeira_palavra_valor["top"]

        linha = sorted(
            (w for w in palavras if abs(w["top"] - top_valor) <= 1.5 and w["x0"] >= primeira_palavra_valor["x0"]),
            key=lambda w: w["x0"],
        )

        palavras_valor = [linha[0]]
        anterior = linha[0]
        for w in linha[1:]:
            if w["x0"] - anterior["x1"] > GAP_MAXIMO_MESMO_VALOR:
                break
            palavras_valor.append(w)
            anterior = w

        return " ".join(w["text"] for w in palavras_valor), x0_rotulo
    return None


def _reconstruir_coluna_esquerda(palavras: list[dict], limiar_x0: float) -> str:
    relevantes = sorted((w for w in palavras if w["x0"] < limiar_x0), key=lambda w: (w["top"], w["x0"]))

    linhas: list[list[dict]] = []
    for palavra in relevantes:
        if linhas and abs(linhas[-1][0]["top"] - palavra["top"]) <= 1.5:
            linhas[-1].append(palavra)
        else:
            linhas.append([palavra])

    return "\n".join(" ".join(w["text"] for w in sorted(linha, key=lambda w: w["x0"])) for linha in linhas)


def _extrair_dae_por_posicao(pagina, arquivo_origem: str) -> DaeDocumento:
    palavras = pagina.extract_words()

    resultado_codigo = _valor_por_posicao(palavras, ROTULO_CODIGO_RECEITA_POS)
    referencia_resultado = _valor_por_posicao(palavras, ROTULO_REFERENCIA_POS)
    valor_resultado = _valor_por_posicao(palavras, ROTULO_VALOR_PRINCIPAL_POS)
    especificacao_resultado = _valor_por_posicao(palavras, ROTULO_ESPECIFICACAO_POS)

    codigo_texto = resultado_codigo[0] if resultado_codigo else None
    referencia_texto = referencia_resultado[0] if referencia_resultado else None
    valor_texto = valor_resultado[0] if valor_resultado else None
    especificacao_texto = especificacao_resultado[0] if especificacao_resultado else None

    # A coluna de "Informações Complementares"/"Notas Fiscais" fica sempre à
    # esquerda da coluna principal de campos (1-CÓDIGO, 4-REFERÊNCIA, ...).
    # Usamos a posição real do rótulo "Código da Receita" para calcular o
    # limite entre as colunas neste PDF específico, em vez de uma fração fixa
    # da página — os DAEs reais usados para validar isto têm margens/layout
    # ligeiramente diferentes entre si.
    if resultado_codigo:
        limiar_coluna_esquerda = resultado_codigo[1] * 0.5
    else:
        limiar_coluna_esquerda = pagina.width * FRACAO_LIMIAR_COLUNA_ESQUERDA_PADRAO

    codigo_receita = None
    if codigo_texto:
        m = re.search(PADRAO_CODIGO_RECEITA, codigo_texto)
        codigo_receita = m.group(0) if m else codigo_texto.strip()

    referencia = None
    if referencia_texto:
        m = re.search(PADRAO_REFERENCIA, referencia_texto)
        referencia = m.group(0) if m else referencia_texto.strip()

    valor_principal = None
    if valor_texto:
        m = re.search(PADRAO_VALOR, valor_texto)
        valor_principal = _parse_valor_monetario(m.group(0) if m else valor_texto)

    texto_coluna_esquerda = _reconstruir_coluna_esquerda(palavras, limiar_coluna_esquerda)
    notas_fiscais = extrair_notas_fiscais(texto_coluna_esquerda)

    return DaeDocumento(
        arquivo_origem=arquivo_origem,
        codigo_receita=codigo_receita,
        referencia=referencia,
        valor_principal=valor_principal,
        especificacao_receita=especificacao_texto.strip() if especificacao_texto else None,
        notas_fiscais=notas_fiscais,
    )


def extrair_dae(caminho_pdf: str) -> DaeDocumento:
    with pdfplumber.open(caminho_pdf) as pdf:
        dae = _extrair_dae_por_posicao(pdf.pages[0], caminho_pdf)
        if dae.codigo_receita or dae.notas_fiscais:
            return dae

        # Fallback para PDFs sem coordenadas de palavra confiáveis (ex.: OCR).
        partes_texto = [pagina.extract_text() or "" for pagina in pdf.pages]
        texto_completo = "\n".join(partes_texto)
        return parse_dae_texto(texto_completo, arquivo_origem=caminho_pdf)
