from src.engine.conciliador import conciliar, sanitize_nf_numero
from src.models.dae_models import DaeDocumento, LinhaRelatorio


def test_sanitize_remove_pontuacao_e_zeros_a_esquerda():
    assert sanitize_nf_numero("001020") == "1020"
    assert sanitize_nf_numero("1.020") == "1020"
    assert sanitize_nf_numero("00000") == "0"
    assert sanitize_nf_numero("1020") == "1020"


def test_nota_do_mapa_encontrada_em_dae_vai_para_conciliadas():
    dae = DaeDocumento(
        arquivo_origem="DAE_Maio_01.pdf",
        codigo_receita="113-5",
        referencia="05/2026",
        valor_principal=450.00,
        especificacao_receita="ICMS ST Antecipado",
        notas_fiscais=["1020"],
    )
    mapa = [LinhaRelatorio(numero_nf="1020", dados_originais={"Data Emissão": "2026-05-01"})]

    conciliadas, nao_encontradas = conciliar([dae], mapa)

    assert len(conciliadas) == 1
    assert conciliadas[0].numero_nf == "1020"
    assert conciliadas[0].codigo_receita == "113-5"
    assert conciliadas[0].referencia == "05/2026"
    assert conciliadas[0].valor_principal == 450.00
    assert conciliadas[0].especificacao_receita == "ICMS ST Antecipado"
    assert nao_encontradas == []


def test_nota_do_mapa_ausente_em_todos_os_daes_vai_para_nao_encontradas():
    dae = DaeDocumento(arquivo_origem="DAE_Maio_01.pdf", codigo_receita="113-5", notas_fiscais=["1020"])
    mapa = [
        LinhaRelatorio(numero_nf="1020"),
        LinhaRelatorio(
            numero_nf="9999",
            dados_originais={"Data Emissão": "2026-05-10", "CNPJ Emitente": "11.222.333/0001-44"},
        ),
    ]

    conciliadas, nao_encontradas = conciliar([dae], mapa)

    assert len(conciliadas) == 1
    assert len(nao_encontradas) == 1
    assert nao_encontradas[0].numero_nf == "9999"
    assert nao_encontradas[0].data_emissao == "2026-05-10"
    assert nao_encontradas[0].cnpj_emitente == "11.222.333/0001-44"


def test_match_ignora_zeros_a_esquerda_e_pontuacao():
    dae = DaeDocumento(arquivo_origem="dae.pdf", notas_fiscais=["01020"])
    mapa = [LinhaRelatorio(numero_nf="1.020")]

    conciliadas, nao_encontradas = conciliar([dae], mapa)

    assert len(conciliadas) == 1
    assert nao_encontradas == []


def test_nota_do_mapa_encontrada_em_qualquer_dae_do_lote():
    dae_1 = DaeDocumento(arquivo_origem="dae1.pdf", codigo_receita="113-5", notas_fiscais=["1020"])
    dae_2 = DaeDocumento(arquivo_origem="dae2.pdf", codigo_receita="2175", notas_fiscais=["2001", "2002"])
    mapa = [LinhaRelatorio(numero_nf="1020"), LinhaRelatorio(numero_nf="2002"), LinhaRelatorio(numero_nf="3000")]

    conciliadas, nao_encontradas = conciliar([dae_1, dae_2], mapa)

    assert {n.numero_nf for n in conciliadas} == {"1020", "2002"}
    assert {n.numero_nf for n in nao_encontradas} == {"3000"}
