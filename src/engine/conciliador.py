import re

from src.models.dae_models import DaeDocumento, LinhaRelatorio, NotaConciliada, NotaNaoEncontrada


def sanitize_nf_numero(nf: str) -> str:
    apenas_digitos = re.sub(r"\D", "", nf or "")
    sem_zeros_esquerda = apenas_digitos.lstrip("0")
    return sem_zeros_esquerda or "0"


def conciliar(
    daes: list[DaeDocumento], linhas_relatorio: list[LinhaRelatorio]
) -> tuple[list[NotaConciliada], list[NotaNaoEncontrada]]:
    """Concilia o mapa de notas (ex.: NF_Aquisicao) contra os DAEs processados.

    Cada nota do mapa é o ponto de partida: se ela é citada em algum DAE
    (campo "Notas Fiscais"), está conciliada; caso contrário, ela é reportada
    como não encontrada em nenhum DAE processado (possível ICMS antecipação
    não recolhido).
    """
    indice_notas_dae: dict[str, DaeDocumento] = {}
    for dae in daes:
        for nf_bruta in dae.notas_fiscais:
            indice_notas_dae.setdefault(sanitize_nf_numero(nf_bruta), dae)

    conciliadas: list[NotaConciliada] = []
    nao_encontradas: list[NotaNaoEncontrada] = []

    for linha in linhas_relatorio:
        nf_chave = sanitize_nf_numero(linha.numero_nf)
        dae_correspondente = indice_notas_dae.get(nf_chave)
        if dae_correspondente is not None:
            conciliadas.append(
                NotaConciliada(
                    numero_nf=linha.numero_nf,
                    codigo_receita=dae_correspondente.codigo_receita,
                    referencia=dae_correspondente.referencia,
                    valor_principal=dae_correspondente.valor_principal,
                    especificacao_receita=dae_correspondente.especificacao_receita,
                )
            )
        else:
            nao_encontradas.append(
                NotaNaoEncontrada(
                    numero_nf=linha.numero_nf,
                    data_emissao=linha.dados_originais.get("Data Emissão"),
                    cnpj_emitente=linha.dados_originais.get("CNPJ Emitente"),
                )
            )

    return conciliadas, nao_encontradas


def filtrar_conciliadas_com_dados(conciliadas: list[NotaConciliada]) -> list[NotaConciliada]:
    """Remove conciliadas cujo DAE correspondente não teve nenhum campo de cabeçalho
    extraído (código_receita/referência/valor_principal/especificação_receita todos
    vazios) -- a nota foi encontrada, mas sem dado útil para exibir no relatório."""
    return [
        nota
        for nota in conciliadas
        if nota.codigo_receita or nota.referencia or nota.valor_principal is not None or nota.especificacao_receita
    ]
