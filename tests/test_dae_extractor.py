from src.extractors.dae_extractor import extrair_notas_fiscais, parse_dae_texto


def test_extrai_campos_do_cabecalho():
    texto = (
        "DAE - Documento de Arrecadação Estadual\n"
        "Código da Receita: 113-5\n"
        "Referência: 05/2026\n"
        "Valor Principal: R$ 450,00\n"
        "Especificação da Receita: ICMS ST Antecipado\n"
        "Informações Complementares:\n"
        "Ref. NFs: 1020, 1021, 1022\n"
    )
    dae = parse_dae_texto(texto, arquivo_origem="DAE_teste.pdf")

    assert dae.codigo_receita == "113-5"
    assert dae.referencia == "05/2026"
    assert dae.valor_principal == 450.00
    assert dae.especificacao_receita == "ICMS ST Antecipado"
    assert dae.notas_fiscais == ["1020", "1021", "1022"]


def test_extrai_notas_fiscais_com_virgulas():
    texto = "Informações Complementares\nNotas Fiscais: 1001, 1002, 1003\n\nOutra seção"
    assert extrair_notas_fiscais(texto) == ["1001", "1002", "1003"]


def test_extrai_notas_fiscais_com_hifen_e_barra():
    texto = "Notas Fiscais: 2001-2002/2003\n"
    assert extrair_notas_fiscais(texto) == ["2001", "2002", "2003"]


def test_extrai_notas_fiscais_com_quebras_de_linha_e_espacos():
    texto = "Notas Fiscais:\n3001\n3002 3003\n"
    assert extrair_notas_fiscais(texto) == ["3001", "3002", "3003"]


def test_sem_notas_fiscais_retorna_lista_vazia():
    texto = "Documento sem nenhuma referência a notas."
    assert extrair_notas_fiscais(texto) == []


def test_valor_principal_com_milhar():
    texto = "Valor Principal: R$ 1.200,00\n"
    dae = parse_dae_texto(texto)
    assert dae.valor_principal == 1200.00
