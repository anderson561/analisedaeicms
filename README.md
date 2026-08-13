# AuditaDAE

Conciliação automática entre DAE/DARF de ICMS (PDF) e o relatório de notas fiscais (Excel/CSV/PDF) da empresa. Aplicativo desktop, 100% offline, com histórico persistido em SQLite local.

## Funcionalidades

- Extração de PDFs de DAE/DARF: código da receita, referência, valor principal, especificação da receita e as notas fiscais citadas em "Informações Complementares".
- Leitura do relatório de notas fiscais em `.xlsx`, `.xls`, `.csv` ou `.pdf`, com detecção automática da coluna de número da nota.
- Conciliação: cada nota extraída do DAE é buscada no relatório (normalizando pontuação e zeros à esquerda).
- Geração de dois relatórios `.xlsx`: notas conciliadas e notas não encontradas.
- Histórico de conciliações salvo em `%LOCALAPPDATA%\AuditaDAE\auditadae.db`, mantido entre execuções.

## Instalação (desenvolvimento)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python run_app.py
```

Na janela: selecione (ou arraste) os PDFs de DAE, selecione o relatório de notas fiscais, clique em "Processar". Os dois relatórios `.xlsx` são salvos na mesma pasta do primeiro DAE selecionado.

## Testes

```bash
pytest tests/ -v
```

## Build do executável (.exe)

```bash
pyinstaller auditadae.spec --noconfirm
```

O executável é gerado em `dist/AuditaDAE.exe`, sem dependência de Python instalado na máquina de destino.

## Estrutura

```
src/
├── extractors/   # extração de PDF (DAE) e de relatório (xlsx/xls/csv/pdf)
├── models/       # modelos pydantic
├── db/           # SQLite (schema + repositório)
├── engine/       # motor de conciliação
├── reports/      # geração dos relatórios .xlsx de saída
├── gui/          # interface CustomTkinter
└── main.py       # orquestração ponta a ponta
tests/            # testes unitários (pytest)
```
