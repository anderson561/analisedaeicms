from src.engine.conciliador import conciliar, sanitize_nf_numero
from src.models.dae_models import DaeDocumento, LinhaRelatorio


def test_sanitize_remove_pontuacao_e_zeros_a_esquerda():
    assert sanitize_nf_numero("001020") == "1020"
    assert sanitize_nf_numero("1.020") == "1020"
    assert sanitize_nf_numero("00000") == "0"
    assert sanitize_nf_numero("1020") == "1020"


def test_match_exato_vai_para_conciliadas():
    dae = DaeDocumento(
        arquivo_origem="DAE_Maio_01.pdf",
        codigo_receita="113-5",
        referencia="05/2026",
        valor_principal=450.00,
        especificacao_receita="ICMS ST Antecipado",
        notas_fiscais=["1020"],
    )
    relatorio = [LinhaRelatorio(numero_nf="1020")]

    conciliadas, nao_encontradas = conciliar([dae], relatorio)

    assert len(conciliadas) == 1
    assert conciliadas[0].numero_nf == "1020"
    assert conciliadas[0].codigo_receita == "113-5"
    assert conciliadas[0].referencia == "05/2026"
    assert conciliadas[0].valor_principal == 450.00
    assert conciliadas[0].especificacao_receita == "ICMS ST Antecipado"
    assert nao_encontradas == []


def test_nota_ausente_vai_para_nao_encontradas():
    dae = DaeDocumento(
        arquivo_origem="DAE_Maio_01.pdf",
        codigo_receita="113-5",
        valor_principal=1200.00,
        notas_fiscais=["9999"],
    )
    relatorio = [LinhaRelatorio(numero_nf="1020")]

    conciliadas, nao_encontradas = conciliar([dae], relatorio)

    assert conciliadas == []
    assert len(nao_encontradas) == 1
    assert nao_encontradas[0].numero_nf == "9999"
    assert nao_encontradas[0].arquivo_dae_origem == "DAE_Maio_01.pdf"
    assert nao_encontradas[0].valor_principal == 1200.00


def test_match_ignora_zeros_a_esquerda_e_pontuacao():
    dae = DaeDocumento(arquivo_origem="dae.pdf", notas_fiscais=["01020"])
    relatorio = [LinhaRelatorio(numero_nf="1.020")]

    conciliadas, nao_encontradas = conciliar([dae], relatorio)

    assert len(conciliadas) == 1
    assert nao_encontradas == []
