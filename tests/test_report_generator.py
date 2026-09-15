import openpyxl
import pdfplumber

from src.models.dae_models import NotaConciliada, NotaNaoEncontrada
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table

from src.reports.report_generator import (
    _agrupar_conciliadas_por_dae,
    _agrupar_por_ano_mes,
    _ano_mes_da_referencia,
    _elementos_conciliadas_agrupadas,
    gerar_relatorio_conciliadas,
    gerar_relatorio_conciliadas_pdf,
    gerar_relatorio_nao_encontradas,
    gerar_relatorio_nao_encontradas_pdf,
)


def test_gerar_relatorio_conciliadas_pdf_contem_os_dados_agrupados_por_ano_e_mes(tmp_path):
    conciliadas = [
        NotaConciliada(
            numero_nf="1020",
            codigo_receita="113-5",
            referencia="05/2026",
            valor_principal=450.00,
            especificacao_receita="ICMS ST Antecipado",
        ),
        NotaConciliada(
            numero_nf="1021",
            codigo_receita="113-5",
            referencia="05/2025",
            valor_principal=300.00,
            especificacao_receita="ICMS ST Antecipado",
        ),
        NotaConciliada(
            numero_nf="1022",
            codigo_receita="113-5",
            referencia="06/2025",
            valor_principal=100.00,
            especificacao_receita="ICMS ST Antecipado",
        ),
    ]
    caminho = tmp_path / "conciliadas.pdf"

    resultado = gerar_relatorio_conciliadas_pdf(conciliadas, caminho)

    assert resultado == caminho
    assert caminho.exists()

    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    assert "Notas Conciliadas" in texto
    assert "1020" in texto
    assert "1021" in texto
    assert "1022" in texto
    assert "113-5" in texto
    assert "450.00" in texto
    assert "300.00" in texto
    assert "100.00" in texto
    assert "ICMS ST Antecipado" in texto

    ano_2025 = texto.index("Ano 2025")
    mes_05 = texto.index("Mês 05")
    mes_06 = texto.index("Mês 06")
    ano_2026 = texto.index("Ano 2026")
    assert ano_2025 < mes_05 < mes_06 < ano_2026


def test_gerar_relatorio_conciliadas_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "conciliadas_vazio.pdf"

    resultado = gerar_relatorio_conciliadas_pdf([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_conciliadas_excel_agrupa_por_ano_e_mes(tmp_path):
    conciliadas = [
        NotaConciliada(numero_nf="1020", codigo_receita="113-5", referencia="05/2026", valor_principal=450.00),
        NotaConciliada(numero_nf="1021", codigo_receita="113-5", referencia="05/2025", valor_principal=300.00),
        NotaConciliada(numero_nf="1022", codigo_receita="113-5", referencia="06/2025", valor_principal=100.00),
    ]
    caminho = tmp_path / "conciliadas.xlsx"

    resultado = gerar_relatorio_conciliadas(conciliadas, caminho)

    assert resultado == caminho
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    valores = [[c.value for c in linha] for linha in planilha.iter_rows()]

    assert valores[0][0] == "Ano 2025"
    assert valores[1][0] == "Mês 05"
    assert valores[2][0] == "Número da NF"
    assert valores[3][0] == "1021"
    assert valores[4][0] is None
    assert valores[5][0] == "Mês 06"
    assert valores[6][0] == "Número da NF"
    assert valores[7][0] == "1022"
    assert valores[8][0] is None
    assert valores[9][0] == "Ano 2026"
    assert valores[10][0] == "Mês 05"
    assert valores[12][0] == "1020"


def test_gerar_relatorio_conciliadas_excel_lista_vazia(tmp_path):
    caminho = tmp_path / "conciliadas_vazio.xlsx"

    resultado = gerar_relatorio_conciliadas([], caminho)

    assert resultado.exists()
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    assert [c.value for c in next(planilha.iter_rows())] == [
        "Número da NF",
        "Código da Receita",
        "Referência",
        "Valor Principal (R$)",
        "Especificação da Receita",
        "Status",
    ]


def test_gerar_relatorio_nao_encontradas_pdf_contem_os_dados_agrupados_por_ano_e_mes(tmp_path):
    nao_encontradas = [
        NotaNaoEncontrada(
            numero_nf="1030",
            data_emissao="10/05/2026",
            cnpj_emitente="12.345.678/0001-90",
        ),
        NotaNaoEncontrada(
            numero_nf="1031",
            data_emissao="11/06/2026",
            cnpj_emitente="98.765.432/0001-10",
        ),
        NotaNaoEncontrada(
            numero_nf="1032",
            data_emissao="15/05/2025",
            cnpj_emitente="11.222.333/0001-44",
        ),
    ]
    caminho = tmp_path / "nao_encontradas.pdf"

    resultado = gerar_relatorio_nao_encontradas_pdf(nao_encontradas, caminho)

    assert resultado == caminho
    assert caminho.exists()

    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    assert "Notas Não Encontradas" in texto
    assert "1030" in texto
    assert "1031" in texto
    assert "1032" in texto
    assert "12.345.678/0001-90" in texto
    assert "Não Encontrada em Nenhum DAE Processado" in texto

    ano_2025 = texto.index("Ano 2025")
    ano_2026 = texto.index("Ano 2026")
    mes_05 = texto.index("Mês 05", ano_2026)
    mes_06 = texto.index("Mês 06", ano_2026)
    assert ano_2025 < ano_2026 < mes_05 < mes_06


def test_gerar_relatorio_nao_encontradas_pdf_lista_vazia(tmp_path):
    caminho = tmp_path / "nao_encontradas_vazio.pdf"

    resultado = gerar_relatorio_nao_encontradas_pdf([], caminho)

    assert resultado.exists()


def test_gerar_relatorio_nao_encontradas_excel_agrupa_por_ano_e_mes(tmp_path):
    nao_encontradas = [
        NotaNaoEncontrada(numero_nf="1030", data_emissao="10/05/2026", cnpj_emitente="12.345.678/0001-90"),
        NotaNaoEncontrada(numero_nf="1032", data_emissao="15/05/2025", cnpj_emitente="11.222.333/0001-44"),
        NotaNaoEncontrada(numero_nf="1033", data_emissao=None, cnpj_emitente=None),
    ]
    caminho = tmp_path / "nao_encontradas.xlsx"

    resultado = gerar_relatorio_nao_encontradas(nao_encontradas, caminho)

    assert resultado == caminho
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    valores = [[c.value for c in linha] for linha in planilha.iter_rows()]

    assert valores[0][0] == "Ano 2025"
    assert valores[1][0] == "Mês 05"
    assert valores[3][0] == "1032"
    assert valores[5][0] == "Ano 2026"
    assert valores[6][0] == "Mês 05"
    assert valores[8][0] == "1030"

    ultimo_bloco_ano = [linha[0] for linha in valores].index("Sem Ano Identificado")
    assert valores[ultimo_bloco_ano + 1][0] == "Sem Mês Identificado"
    assert valores[ultimo_bloco_ano + 3][0] == "1033"


def test_gerar_relatorio_nao_encontradas_excel_lista_vazia(tmp_path):
    caminho = tmp_path / "nao_encontradas_vazio.xlsx"

    resultado = gerar_relatorio_nao_encontradas([], caminho)

    assert resultado.exists()
    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    assert [c.value for c in next(planilha.iter_rows())] == [
        "Número da NF",
        "Data de Emissão",
        "CNPJ do Emitente",
        "Status",
    ]


def _nota(numero_nf, codigo_receita, referencia, valor_principal, especificacao="ICMS ANTECIPAÇÃO TRIBUTÁRIA"):
    return NotaConciliada(
        numero_nf=numero_nf,
        codigo_receita=codigo_receita,
        referencia=referencia,
        valor_principal=valor_principal,
        especificacao_receita=especificacao,
    )


def test_agrupar_conciliadas_por_dae_junta_nfs_do_mesmo_dae_em_um_bloco():
    notas = [
        _nota("1", "1145", "12/2025", 100.0),
        _nota("2", "1145", "12/2025", 100.0),
        _nota("3", "1145", "12/2025", 100.0),
    ]

    blocos = _agrupar_conciliadas_por_dae(notas)

    assert len(blocos) == 1
    assert [n.numero_nf for n in blocos[0]] == ["1", "2", "3"]


def test_agrupar_conciliadas_por_dae_ordena_por_valor_decrescente():
    notas = [
        _nota("1", "2175", "12/2025", 184.48),
        _nota("2", "1145", "12/2025", 6405.82),
        _nota("3", "1145", "12/2025", 5703.74),
    ]

    blocos = _agrupar_conciliadas_por_dae(notas)

    assert [bloco[0].valor_principal for bloco in blocos] == [6405.82, 5703.74, 184.48]


def test_agrupar_conciliadas_por_dae_sem_valor_fica_por_ultimo_e_mantem_ordem():
    notas = [
        _nota("1", "1145", None, None),
        _nota("2", "9999", "12/2025", 100.0),
        _nota("3", "2175", None, None),
    ]

    blocos = _agrupar_conciliadas_por_dae(notas)

    assert blocos[0][0].valor_principal == 100.0
    assert [n.numero_nf for n in blocos[1]] == ["1"]
    assert [n.numero_nf for n in blocos[2]] == ["3"]


def test_gerar_relatorio_conciliadas_excel_mescla_nfs_do_mesmo_dae(tmp_path):
    conciliadas = [
        _nota("1", "1145", "12/2025", 5703.74),
        _nota("2", "1145", "12/2025", 6405.82),
        _nota("3", "1145", "12/2025", 6405.82),
        _nota("4", "1145", "12/2025", 6405.82),
        _nota("5", "2175", "12/2025", 184.48, especificacao="ICMS - ANTECIPACAO PARCIAL"),
    ]
    caminho = tmp_path / "conciliadas_mescladas.xlsx"

    gerar_relatorio_conciliadas(conciliadas, caminho)

    workbook = openpyxl.load_workbook(caminho)
    planilha = workbook.active
    valores = [[c.value for c in linha] for linha in planilha.iter_rows()]

    # Linha 0: "Mês 12" (sem ano identificável, referência não é reconhecida por
    # _ano_mes_da_referencia pois falta o padrão completo -- aqui usamos uma
    # referência válida "12/2025" que cai em Ano 2025 / Mês 12.
    assert valores[0][0] == "Ano 2025"
    assert valores[1][0] == "Mês 12"
    assert valores[2][0] == "Número da NF"

    # Bloco do maior valor (6405.82, NFs 2/3/4) vem primeiro.
    assert valores[3] == ["2", "1145", "12/2025", 6405.82, "ICMS ANTECIPAÇÃO TRIBUTÁRIA", "🟢 Conciliado"]
    assert valores[4][0] == "3"
    assert valores[4][1] is None
    assert valores[5][0] == "4"
    assert valores[5][1] is None

    # Bloco seguinte (5703.74, NF 1) -- bloco de uma linha só, sem mesclagem.
    assert valores[6] == ["1", "1145", "12/2025", 5703.74, "ICMS ANTECIPAÇÃO TRIBUTÁRIA", "🟢 Conciliado"]

    # Bloco do código 2175 (184.48, NF 5) por último.
    assert valores[7] == ["5", "2175", "12/2025", 184.48, "ICMS - ANTECIPACAO PARCIAL", "🟢 Conciliado"]

    faixas_mescladas = {str(faixa) for faixa in planilha.merged_cells.ranges}
    assert "B4:B6" in faixas_mescladas
    assert "C4:C6" in faixas_mescladas
    assert "D4:D6" in faixas_mescladas
    assert "E4:E6" in faixas_mescladas
    assert "F4:F6" in faixas_mescladas
    # bloco de uma linha só (5703.74) e o de 184.48 não geram merge nenhum
    assert not any(faixa.startswith("B7") or faixa.startswith("B8") for faixa in faixas_mescladas)


def test_gerar_relatorio_conciliadas_pdf_mescla_nfs_do_mesmo_dae(tmp_path):
    conciliadas = [
        _nota("1", "1145", "12/2025", 6405.82),
        _nota("2", "1145", "12/2025", 6405.82),
        _nota("3", "2175", "12/2025", 184.48),
    ]
    caminho = tmp_path / "conciliadas_mescladas.pdf"

    resultado = gerar_relatorio_conciliadas_pdf(conciliadas, caminho)

    assert resultado.exists()
    with pdfplumber.open(caminho) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)
    assert "1" in texto and "2" in texto and "3" in texto


def test_elementos_conciliadas_agrupadas_gera_span_para_bloco_com_mais_de_uma_nf():
    conciliadas = [
        _nota("1", "1145", "12/2025", 6405.82),
        _nota("2", "1145", "12/2025", 6405.82),
        _nota("3", "2175", "12/2025", 184.48),
    ]
    grupos = _agrupar_por_ano_mes(conciliadas, lambda n: _ano_mes_da_referencia(n.referencia))

    elementos = _elementos_conciliadas_agrupadas(getSampleStyleSheet(), grupos)

    tabela = next(el for el in elementos if isinstance(el, Table))
    spans = {(cmd[1], cmd[2]) for cmd in tabela._spanCmds}
    # linha 1 e 2 (0-indexed, após o cabeçalho na linha 0) formam o bloco das duas NFs de 6405.82
    for coluna in range(1, 6):
        assert ((coluna, 1), (coluna, 2)) in spans
    # bloco de uma linha só (NF 3, 184.48) não deve gerar nenhum span
    assert not any(inicio[1] == 3 for inicio, _fim in spans)
