import sqlite3
from datetime import datetime

from src.models.dae_models import DaeDocumento, RegistroConciliacao, RegistroDae


def salvar_dae(conexao: sqlite3.Connection, dae: DaeDocumento) -> int:
    agora = datetime.now().isoformat()
    cursor = conexao.execute(
        """
        INSERT INTO dae_processado
            (arquivo_origem, codigo_receita, referencia, valor_principal, especificacao_receita, data_processamento)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (dae.arquivo_origem, dae.codigo_receita, dae.referencia, dae.valor_principal, dae.especificacao_receita, agora),
    )
    conexao.commit()
    return cursor.lastrowid


def salvar_conciliacao(conexao: sqlite3.Connection, dae_id: int, numero_nf: str, status: str) -> int:
    agora = datetime.now().isoformat()
    cursor = conexao.execute(
        """
        INSERT INTO conciliacao_historico (dae_id, numero_nf, status, data_processamento)
        VALUES (?, ?, ?, ?)
        """,
        (dae_id, numero_nf, status, agora),
    )
    conexao.commit()
    return cursor.lastrowid


def listar_dae_processados(conexao: sqlite3.Connection) -> list[RegistroDae]:
    linhas = conexao.execute("SELECT * FROM dae_processado ORDER BY data_processamento DESC").fetchall()
    return [
        RegistroDae(
            id=linha["id"],
            arquivo_origem=linha["arquivo_origem"],
            codigo_receita=linha["codigo_receita"],
            referencia=linha["referencia"],
            valor_principal=linha["valor_principal"],
            especificacao_receita=linha["especificacao_receita"],
            data_processamento=datetime.fromisoformat(linha["data_processamento"]),
        )
        for linha in linhas
    ]


def listar_historico(conexao: sqlite3.Connection, limite: int = 100) -> list[RegistroConciliacao]:
    linhas = conexao.execute(
        "SELECT * FROM conciliacao_historico ORDER BY data_processamento DESC LIMIT ?", (limite,)
    ).fetchall()
    return [
        RegistroConciliacao(
            id=linha["id"],
            dae_id=linha["dae_id"],
            numero_nf=linha["numero_nf"],
            status=linha["status"],
            data_processamento=datetime.fromisoformat(linha["data_processamento"]),
        )
        for linha in linhas
    ]
