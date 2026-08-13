import csv

import openpyxl
import pytest

from src.extractors.relatorio_extractor import detectar_coluna_nf, ler_relatorio


def test_detectar_coluna_nf_por_nomes_comuns():
    assert detectar_coluna_nf(["Data", "Número da Nota Fiscal", "Valor"]) == "Número da Nota Fiscal"
    assert detectar_coluna_nf(["Data", "NF", "Valor"]) == "NF"
    assert detectar_coluna_nf(["Cliente", "Nota Fiscal", "Total"]) == "Nota Fiscal"
    assert detectar_coluna_nf(["Cliente", "Total"]) is None


def test_ler_relatorio_xlsx(tmp_path):
    caminho = tmp_path / "relatorio.xlsx"
    workbook = openpyxl.Workbook()
    planilha = workbook.active
    planilha.append(["Data", "Número da Nota Fiscal", "Valor"])
    planilha.append(["01/05/2026", "1020", "450,00"])
    planilha.append(["02/05/2026", "1021", "300,00"])
    workbook.save(str(caminho))

    linhas = ler_relatorio(str(caminho))

    assert len(linhas) == 2
    assert linhas[0].numero_nf == "1020"
    assert linhas[0].dados_originais["Valor"] == "450,00"


def test_ler_relatorio_csv(tmp_path):
    caminho = tmp_path / "relatorio.csv"
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["Data", "Nota Fiscal", "Valor"])
        escritor.writerow(["01/05/2026", "2001", "100,00"])

    linhas = ler_relatorio(str(caminho))

    assert len(linhas) == 1
    assert linhas[0].numero_nf == "2001"


def test_ler_relatorio_coluna_nao_identificada_gera_erro(tmp_path):
    caminho = tmp_path / "relatorio.csv"
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["Cliente", "Total"])
        escritor.writerow(["Empresa X", "100,00"])

    with pytest.raises(ValueError):
        ler_relatorio(str(caminho))


def test_ler_relatorio_extensao_nao_suportada(tmp_path):
    caminho = tmp_path / "relatorio.txt"
    caminho.write_text("conteudo")

    with pytest.raises(ValueError):
        ler_relatorio(str(caminho))
