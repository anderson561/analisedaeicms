from datetime import datetime

import openpyxl

from src.extractors.icms_at_extractor import eh_icms_at_disponivel, extrair_icms_at


def _construir_planilha_icms_at(caminho, incluir_aba_icms_at: bool = True):
    workbook = openpyxl.Workbook()
    aba = workbook.active
    aba.title = "ICMS_AT" if incluir_aba_icms_at else "Outra"

    aba.append(["MACEDO COMERCIAL DE CALCADOS LTDA"])
    aba.append(["RUA QUALQUER, 1241"])
    aba.append(["CNPJ: 04.074.648/0003-25"])
    aba.append([])
    aba.append(["FALTA DE RECOLHIMENTO DO ICMS ANTECIPACAO TRIBUTARIA"])
    aba.append(["Descrição"] + [datetime(2021, mes, 1) for mes in range(1, 13)])
    aba.append(["Operação"] + [datetime(2021, mes, 28) for mes in range(1, 13)])
    aba.append(["ICMS Antecipação Tributária apurado"] + [100.0 + mes for mes in range(1, 13)])
    aba.append(["1.145 - ICMS ANTECIPAÇÃO TRIBUTÁRIA"] + [50.0 + mes for mes in range(1, 13)])
    aba.append(["ICMS Antecipação Tributária a Recolher"] + [50.0 for _ in range(1, 13)])
    aba.append([])
    aba.append([])

    aba.append(["FALTA DE RECOLHIMENTO DO ICMS ANTECIPACAO TRIBUTARIA"])
    aba.append(["Descrição"] + [datetime(2022, mes, 1) for mes in range(1, 13)])
    aba.append(["Operação"] + [datetime(2022, mes, 28) for mes in range(1, 13)])
    aba.append(["ICMS Antecipação Tributária apurado"] + [200.0 + mes for mes in range(1, 13)])
    aba.append(["1.145 - ICMS ANTECIPAÇÃO TRIBUTÁRIA"] + [80.0 + mes for mes in range(1, 13)])
    aba.append(["ICMS Antecipação Tributária a Recolher"] + [120.0 for _ in range(1, 13)])

    workbook.save(caminho)


def test_eh_icms_at_disponivel_verdadeiro_quando_aba_existe(tmp_path):
    caminho = tmp_path / "com_icms_at.xlsx"
    _construir_planilha_icms_at(caminho)

    assert eh_icms_at_disponivel(str(caminho)) is True


def test_eh_icms_at_disponivel_falso_quando_aba_ausente(tmp_path):
    caminho = tmp_path / "sem_icms_at.xlsx"
    _construir_planilha_icms_at(caminho, incluir_aba_icms_at=False)

    assert eh_icms_at_disponivel(str(caminho)) is False


def test_extrair_icms_at_le_dois_blocos_de_ano(tmp_path):
    caminho = tmp_path / "icms_at.xlsx"
    _construir_planilha_icms_at(caminho)

    linhas = extrair_icms_at(str(caminho))

    assert len(linhas) == 24

    linha_2021_06 = next(l for l in linhas if l.ano == 2021 and l.mes == 6)
    assert linha_2021_06.valor_apurado == 106.0
    assert linha_2021_06.valor_pago == 56.0
    assert linha_2021_06.valor_a_recolher == 50.0

    linha_2022_12 = next(l for l in linhas if l.ano == 2022 and l.mes == 12)
    assert linha_2022_12.valor_apurado == 212.0
    assert linha_2022_12.valor_pago == 92.0
    assert linha_2022_12.valor_a_recolher == 120.0
