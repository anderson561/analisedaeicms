# AuditaDAE

Conciliação automática entre o mapa de notas fiscais sujeitas a ICMS Antecipação Tributária (planilha exportada do sistema fiscal, aba `NF_Aquisicao`) e os DAE/DARF de ICMS (PDF) efetivamente pagos. Aplicativo desktop, 100% offline, com histórico persistido em SQLite local.

## Funcionalidades

- Extração de PDFs de DAE/DARF (formato SEFAZ-BA) por posição geométrica das palavras: código da receita, referência, valor principal, especificação da receita e as notas fiscais citadas em "Informações Complementares".
- Leitura do mapa de notas (planilha com aba `NF_Aquisicao`, detectada automaticamente) ou de um relatório simples `.xlsx`/`.xls`/`.csv`/`.pdf` com detecção automática da coluna de número da nota.
- Conciliação: parte de cada nota do mapa e verifica se ela é citada em algum DAE do lote processado (normalizando pontuação e zeros à esquerda). Nota no mapa E em algum DAE → conciliada. Nota no mapa e ausente de todos os DAEs → não encontrada (possível ICMS antecipação não recolhido).
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

Dê dois cliques em **`build.bat`** (ou rode-o pelo terminal). Ele detecta o que mudou desde o último build e regenera só o necessário — use sempre que alterar o código e quiser atualizar o `.exe`.

Equivalente manual:

```bash
pyinstaller auditadae.spec --noconfirm
```

O executável é gerado em `dist/AuditaDAE/AuditaDAE.exe` (modo *onedir* — pasta com o `.exe` e suas dependências), sem depender de Python instalado na máquina de destino. Distribua a pasta `dist/AuditaDAE/` inteira, não apenas o `.exe` (ela depende da subpasta `_internal` ao lado).

> **Notas:**
> - O modo *onedir* foi escolhido em vez de *onefile* porque o onefile precisa se reextrair para uma pasta temporária a cada execução — em testes isso levou de 10 a 25+ segundos para a janela aparecer na primeira abertura (soma-se a isso o Windows Defender escaneando o executável recém-criado). Em modo onedir, a janela abre em ~2-3 segundos.
> - Como o `.exe` não é assinado digitalmente, o Windows SmartScreen deve exibir "Windows protegeu seu PC" na primeira execução em qualquer máquina nova (inclusive a que gerou o build) — basta clicar em "Mais informações" → "Executar assim mesmo". Não indica problema no aplicativo.

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
