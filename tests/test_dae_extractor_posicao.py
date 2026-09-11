from src.extractors.dae_extractor import _extrair_dae_por_posicao


class _PaginaFalsa:
    """Substituto mínimo de uma página pdfplumber para testar a extração
    baseada em posição sem precisar de um PDF real."""

    def __init__(self, palavras: list[dict], width: float):
        self._palavras = palavras
        self.width = width

    def extract_words(self) -> list[dict]:
        return self._palavras


def _w(texto: str, x0: float, top: float, largura_estimada: float | None = None) -> dict:
    x1 = x0 + (largura_estimada if largura_estimada is not None else len(texto) * 6.0)
    return {"text": texto, "x0": x0, "x1": x1, "top": top, "bottom": top + 10}


def _montar_pagina_dae_generica() -> _PaginaFalsa:
    # Layout de duas colunas (esquerda: informações complementares / notas
    # fiscais; direita: campos principais do DAE), com uma segunda via
    # (cópia idêntica) separada por uma linha tracejada — mesma estrutura
    # observada em DAEs reais do SEFAZ-BA, com dados fictícios.
    palavras = [
        _w("1-CÓDIGO", 428.0, 133.0),
        _w("DA", 456.0, 133.0),
        _w("RECEITA", 465.0, 133.0),
        _w("1145", 428.0, 139.0),
        _w("4-REFERÊNCIA", 428.0, 197.0),
        _w("09/2022", 428.0, 203.0),
        _w("18-ESPECIFICAÇÃO", 148.0, 197.0),
        _w("DA", 199.0, 197.0),
        _w("RECEITA", 208.0, 197.0),
        _w("ICMS", 148.0, 204.0),
        _w("ANTECIPAÇÃO", 172.0, 204.0),
        _w("TRIBUTÁRIA", 240.0, 204.0),
        _w("7-VALOR", 428.0, 262.0),
        _w("PRINCIPAL", 452.0, 262.0),
        _w("R$", 428.0, 268.0),
        _w("4.998,63", 442.0, 268.0),
        _w("25-INFORMAÇÕES", 57.0, 284.0),
        _w("COMPLEMENTARES", 105.0, 284.0),
        _w("12-RECEITA", 304.0, 284.0),
        _w("BRUTA", 336.0, 284.0),
        _w("8-CORREÇÃO", 428.0, 284.0),
        _w("Notas", 57.0, 320.0),
        _w("Fiscais:3", 74.0, 320.0),
        _w("1020", 57.0, 327.0),
        _w("//", 79.0, 327.0),
        _w("1021", 84.0, 327.0),
        _w("//", 106.0, 327.0),
        _w("1022", 111.0, 327.0),
        # separador tracejado entre as duas vias impressas na mesma página
        _w("-" * 140, 40.0, 335.0, largura_estimada=500.0),
        # linha de código de barras da segunda via (dígitos soltos que NÃO
        # podem vazar para a lista de notas fiscais)
        _w("85800000007", 59.0, 345.0),
        _w("0", 125.0, 345.0),
        _w("84010005202", 135.0, 345.0),
        _w("9", 202.0, 345.0),
        # segunda via repete o rótulo — delimitador natural do bloco também
        _w("17-Nº", 57.0, 360.0),
        _w("SÉRIE", 80.0, 360.0),
    ]
    return _PaginaFalsa(palavras, width=595.0)


def test_extrai_dae_real_com_colunas_e_via_duplicada():
    pagina = _montar_pagina_dae_generica()
    dae = _extrair_dae_por_posicao(pagina, arquivo_origem="dae_teste.pdf")

    assert dae.codigo_receita == "1145"
    assert dae.referencia == "09/2022"
    assert dae.valor_principal == 4998.63
    assert dae.especificacao_receita == "ICMS ANTECIPAÇÃO TRIBUTÁRIA"
    assert dae.notas_fiscais == ["1020", "1021", "1022"]


def test_notas_fiscais_nao_vazam_digitos_do_codigo_de_barras_da_segunda_via():
    pagina = _montar_pagina_dae_generica()
    dae = _extrair_dae_por_posicao(pagina, arquivo_origem="dae_teste.pdf")

    assert "0" not in dae.notas_fiscais
    assert "9" not in dae.notas_fiscais
    assert len(dae.notas_fiscais) == 3


def _montar_pagina_dae_sem_prefixo_numerico() -> _PaginaFalsa:
    # Variante real observada em DAEs mais recentes do mesmo cliente: os
    # rótulos vêm sem o prefixo "N-" (ex.: "CÓDIGO" em vez de "1-CÓDIGO").
    palavras = [
        _w("CÓDIGO", 428.0, 133.0),
        _w("DA", 456.0, 133.0),
        _w("RECEITA", 465.0, 133.0),
        _w("1145", 428.0, 139.0),
        _w("REFERÊNCIA", 428.0, 197.0),
        _w("04/2023", 428.0, 203.0),
        _w("VALOR", 428.0, 262.0),
        _w("PRINCIPAL", 452.0, 262.0),
        _w("R$", 428.0, 268.0),
        _w("5.131,36", 442.0, 268.0),
        _w("ESPECIFICAÇÃO", 148.0, 197.0),
        _w("DA", 199.0, 197.0),
        _w("RECEITA", 208.0, 197.0),
        _w("ICMS", 148.0, 204.0),
        _w("ANTECIPAÇÃO", 172.0, 204.0),
        _w("TRIBUTÁRIA", 240.0, 204.0),
    ]
    return _PaginaFalsa(palavras, width=595.0)


def test_extrai_campos_quando_rotulos_nao_tem_prefixo_numerico():
    pagina = _montar_pagina_dae_sem_prefixo_numerico()
    dae = _extrair_dae_por_posicao(pagina, arquivo_origem="dae_teste.pdf")

    assert dae.codigo_receita == "1145"
    assert dae.referencia == "04/2023"
    assert dae.valor_principal == 5131.36
    assert dae.especificacao_receita == "ICMS ANTECIPAÇÃO TRIBUTÁRIA"
