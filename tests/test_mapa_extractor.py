import openpyxl

from src.extractors.mapa_extractor import eh_mapa_aquisicao, extrair_notas_mapa_aquisicao


def _montar_mapa_ficticio(caminho):
    workbook = openpyxl.Workbook()
    planilha = workbook.active
    planilha.title = "NF_Aquisicao"

    linhas = [
        ["EMPRESA FICTÍCIA LTDA", None, None, None, None, "Secretaria da Fazenda"],
        ["ENDEREÇO FICTÍCIO", None, None, None, None, None],
        ["CNPJ: 00.000.000/0000-00", None, None, None, None, None],
        [None, None, None, None, None, None],
        ["FALTA DE RECOLHIMENTO DO ICMS ANTECIPAÇÃO", None, None, None, None, None],
        ["Data", "Data", "Nota Fiscal", None, None, "Emitente"],
        ["Emissão", "Entrada", "EFD", "Esp", "Nº", "CNPJ"],
        ["2026-01-06", "2026-01-12", "Sim", "NF", 710948, "11.222.333/0001-44"],
        ["2026-01-06", "2026-01-12", "Sim", "NF", 710948, "11.222.333/0001-44"],
        ["2026-01-07", "2026-01-13", "Sim", "NF", 2404, "22.333.444/0001-55"],
    ]
    for linha in linhas:
        planilha.append(linha)
    workbook.save(caminho)


def test_eh_mapa_aquisicao_detecta_pela_aba(tmp_path):
    caminho = tmp_path / "mapa.xlsx"
    _montar_mapa_ficticio(str(caminho))

    assert eh_mapa_aquisicao(str(caminho)) is True


def test_extrai_notas_distintas_com_metadados(tmp_path):
    caminho = tmp_path / "mapa.xlsx"
    _montar_mapa_ficticio(str(caminho))

    linhas = extrair_notas_mapa_aquisicao(str(caminho))

    assert len(linhas) == 2
    por_nf = {linha.numero_nf: linha for linha in linhas}
    assert "710948" in por_nf
    assert por_nf["710948"].dados_originais["CNPJ Emitente"] == "11.222.333/0001-44"
    assert "2404" in por_nf
