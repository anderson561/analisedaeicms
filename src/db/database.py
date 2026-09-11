import os
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dae_processado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem TEXT NOT NULL,
    codigo_receita TEXT,
    referencia TEXT,
    valor_principal REAL,
    especificacao_receita TEXT,
    data_processamento TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conciliacao_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dae_id INTEGER NOT NULL REFERENCES dae_processado(id),
    numero_nf TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ENCONTRADO', 'NAO_ENCONTRADO')),
    data_processamento TEXT NOT NULL
);
"""


def caminho_banco() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    diretorio = Path(base) / "AuditaDAE"
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio / "auditadae.db"


def obter_conexao(caminho: Path | None = None) -> sqlite3.Connection:
    caminho = caminho or caminho_banco()
    conexao = sqlite3.connect(str(caminho))
    conexao.row_factory = sqlite3.Row
    conexao.executescript(SCHEMA_SQL)
    return conexao
