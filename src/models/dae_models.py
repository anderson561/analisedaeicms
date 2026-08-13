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
    arquivo_dae_origem: str
    codigo_receita: str | None = None
    valor_principal: float | None = None
    status: str = "Não Encontrada no Relatório"


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
