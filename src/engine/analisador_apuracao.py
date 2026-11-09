from src.engine.conciliador import sanitize_nf_numero
from src.engine.verificador_creditos import eh_item_excluido
from src.models.dae_models import AnaliseApuracao, ItemListaNotas, NotaCredito

INFORMACAO_SEM_DAE = "Não encontrada na planilha de DAEs"
INFORMACAO_SEM_ANTECIPACAO = "Não encontrada na planilha de antecipação"


def _chave(nota: str, data_emissao: str, uf: str) -> tuple[str, str, str]:
    return sanitize_nf_numero(nota), data_emissao, uf


def analisar_apuracao(
    notas_creditos: list[NotaCredito],
    itens_antecipacao: list[ItemListaNotas],
    informacoes_dae: dict[str, str],
) -> list[AnaliseApuracao]:
    """Para cada nota do relatório de créditos, calcula a partir dos itens da
    lista de antecipação (sem calçados/bolsas, pelo NCM):
      Valor Pago = Σ(VlTotItem × AliqInt) − Σ VlCredEmpr
    e traz a "Informações de Pagamento (DAE)" da planilha de DAEs."""
    itens_por_nota: dict[tuple[str, str, str], list[ItemListaNotas]] = {}
    for item in itens_antecipacao:
        if not eh_item_excluido(item):
            itens_por_nota.setdefault(_chave(item.nota, item.data_emissao, item.uf), []).append(item)

    analises: list[AnaliseApuracao] = []
    for nota in notas_creditos:
        informacao = informacoes_dae.get(sanitize_nf_numero(nota.nota), INFORMACAO_SEM_DAE)
        itens = itens_por_nota.get(_chave(nota.nota, nota.data_emissao, nota.uf))
        valor_pago = None
        if itens:
            valor_pago = round(sum(i.vl_tot_item * i.aliq_int / 100 - i.vl_cred_empr for i in itens), 2)
        else:
            informacao = f"{informacao} | {INFORMACAO_SEM_ANTECIPACAO}"
        analises.append(AnaliseApuracao(nota=nota, valor_pago=valor_pago, informacao_norte=informacao))
    return analises
