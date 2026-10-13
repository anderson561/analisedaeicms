import re
import unicodedata

import openpyxl

from src.extractors.relatorio_extractor import detectar_coluna_nf
from src.models.dae_models import LinhaRelatorio

PADRAO_TITULO_ANO = re.compile(r"^ano\s+(\d{4})$", re.IGNORECASE)
PADRAO_SO_DIGITOS = re.compile(r"^\d+$")

MESES_POR_NOME = {
    nome: numero
    for numero, nome in enumerate(
        ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
        start=1,
    )
}


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def _texto(celula) -> str:
    return str(celula).strip() if celula is not None else ""


def _titulo_ano(linha: tuple) -> int | None:
    textos = [_texto(c) for c in linha if _texto(c)]
    if len(textos) != 1:
        return None
    correspondencia = PADRAO_TITULO_ANO.match(textos[0])
    return int(correspondencia.group(1)) if correspondencia else None


def _titulo_mes(linha: tuple) -> int | None:
    textos = [_texto(c) for c in linha if _texto(c)]
    if len(textos) != 1:
        return None
    return MESES_POR_NOME.get(_sem_acento(textos[0]).lower())


def _cabecalho_com_coluna_nf(linha: tuple) -> tuple[list[str], int] | None:
    cabecalho = [_texto(c) for c in linha]
    coluna = detectar_coluna_nf(cabecalho)
    return (cabecalho, cabecalho.index(coluna)) if coluna is not None else None


def _dados_da_linha(
    linha: tuple, cabecalho: list[str], aba: str, ano: int | None, mes: int | None
) -> dict[str, str]:
    dados = {"Aba": aba}
    if ano is not None:
        dados["Ano"] = str(ano)
    if mes is not None:
        dados["Mês"] = str(mes)
    for indice, nome in enumerate(cabecalho):
        if nome and indice < len(linha) and linha[indice] is not None:
            dados[nome] = _texto(linha[indice])
    # Células além do cabeçalho (ex.: anotação manual do usuário ao lado da nota)
    extras = [_texto(c) for c in linha[len(cabecalho):] if _texto(c)]
    sem_nome = [_texto(linha[i]) for i, nome in enumerate(cabecalho) if not nome and i < len(linha) and _texto(linha[i])]
    observacao = " | ".join(sem_nome + extras)
    if observacao:
        dados["Observação"] = observacao
    return dados


def extrair_notas_relatorio_conciliado(caminho: str) -> list[LinhaRelatorio]:
    """Lê todas as abas do relatório "Pagamentos Notas" (ou similar) e devolve
    uma LinhaRelatorio por nota, com Aba/Ano/Mês e demais colunas em
    `dados_originais`. A coluna da nota é localizada pelo cabeçalho (repetido a
    cada mês); títulos "Ano XXXX" e nome do mês definem o período."""
    workbook = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    resultado: list[LinhaRelatorio] = []
    vistas: set[tuple[int | None, int | None, str]] = set()
    cabecalho_encontrado = False

    for planilha in workbook.worksheets:
        ano: int | None = None
        mes: int | None = None
        cabecalho: list[str] | None = None
        coluna_nf = -1
        for linha in planilha.iter_rows(values_only=True):
            novo_ano = _titulo_ano(linha)
            if novo_ano is not None:
                ano, mes, cabecalho = novo_ano, None, None
                continue
            novo_mes = _titulo_mes(linha)
            if novo_mes is not None:
                mes, cabecalho = novo_mes, None
                continue
            candidato = _cabecalho_com_coluna_nf(linha)
            if candidato is not None:
                cabecalho, coluna_nf = candidato
                cabecalho_encontrado = True
                continue
            if cabecalho is None or coluna_nf >= len(linha):
                continue
            numero = _texto(linha[coluna_nf])
            if not PADRAO_SO_DIGITOS.match(numero):
                continue
            chave = (ano, mes, numero.lstrip("0") or "0")
            if chave in vistas:
                continue
            vistas.add(chave)
            resultado.append(
                LinhaRelatorio(
                    numero_nf=numero, dados_originais=_dados_da_linha(linha, cabecalho, planilha.title, ano, mes)
                )
            )

    if not cabecalho_encontrado:
        raise ValueError(
            "Não foi possível identificar a coluna de número da nota no relatório. "
            "Esperado cabeçalho como 'Número do Documento'."
        )
    return resultado
