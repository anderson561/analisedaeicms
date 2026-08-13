import re

from src.models.dae_models import DaeDocumento, LinhaRelatorio, NotaConciliada, NotaNaoEncontrada


def sanitize_nf_numero(nf: str) -> str:
    apenas_digitos = re.sub(r"\D", "", nf or "")
    sem_zeros_esquerda = apenas_digitos.lstrip("0")
    return sem_zeros_esquerda or "0"


def conciliar(
    daes: list[DaeDocumento], linhas_relatorio: list[LinhaRelatorio]
) -> tuple[list[NotaConciliada], list[NotaNaoEncontrada]]:
    indice_relatorio = {sanitize_nf_numero(linha.numero_nf): linha for linha in linhas_relatorio}

    conciliadas: list[NotaConciliada] = []
    nao_encontradas: list[NotaNaoEncontrada] = []

    for dae in daes:
        for nf_bruta in dae.notas_fiscais:
            nf_chave = sanitize_nf_numero(nf_bruta)
            if nf_chave in indice_relatorio:
                conciliadas.append(
                    NotaConciliada(
                        numero_nf=nf_bruta,
                        codigo_receita=dae.codigo_receita,
                        referencia=dae.referencia,
                        valor_principal=dae.valor_principal,
                        especificacao_receita=dae.especificacao_receita,
                    )
                )
            else:
                nao_encontradas.append(
                    NotaNaoEncontrada(
                        numero_nf=nf_bruta,
                        arquivo_dae_origem=dae.arquivo_origem,
                        codigo_receita=dae.codigo_receita,
                        valor_principal=dae.valor_principal,
                    )
                )

    return conciliadas, nao_encontradas
