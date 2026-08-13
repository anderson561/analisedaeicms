from datetime import datetime

from pydantic import BaseModel


class DaeDocumento(BaseModel):
    arquivo_origem: str
    codigo_receita: str | None = None
    referencia: str | None = None
    valor_principal: float | None = None
    especificacao_receita: str | None = None
    notas_fiscais: list[str] = []


class LinhaRelatorio(BaseModel):
    numero_nf: str
    dados_originais: dict[str, str] = {}


class NotaConciliada(BaseModel):
    numero_nf: str
    codigo_receita: str | None = None
    referencia: str | None = None
    valor_principal: float | None = None
    especificacao_receita: str | None = None
    status: str = "Conciliado"


class NotaNaoEncontrada(BaseModel):
    numero_nf: str
    data_emissao: str | None = None
    cnpj_emitente: str | None = None
    status: str = "Não Encontrada em Nenhum DAE Processado"


class LinhaPagamentoDae(BaseModel):
    nosso_numero: str
    data_pagamento: str | None = None
    referencia_bruta: str | None = None
    mes_referencia: int | None = None
    ano_referencia: int | None = None
    codigo_receita: str | None = None
    descricao_receita: str | None = None
    valor_principal: float | None = None
    valor_total: float | None = None
    revisar: bool = False


class PagamentoConfirmado(BaseModel):
    dae_arquivo_origem: str
    linha_pagamento: LinhaPagamentoDae
    status: str = "Pagamento Confirmado"


class DaePagamentoNaoLocalizado(BaseModel):
    arquivo_origem: str
    codigo_receita: str | None = None
    referencia: str | None = None
    valor_principal: float | None = None
    status: str = "Não Localizada no Relatório de Pagamentos"


class RegistroDae(BaseModel):
    id: int | None = None
    arquivo_origem: str
    codigo_receita: str | None = None
    referencia: str | None = None
    valor_principal: float | None = None
    especificacao_receita: str | None = None
    data_processamento: datetime


class RegistroConciliacao(BaseModel):
    id: int | None = None
    dae_id: int
    numero_nf: str
    status: str
    data_processamento: datetime
