# AuditaDAE

Conciliação automática entre o mapa de notas fiscais sujeitas a ICMS Antecipação Tributária (planilha exportada do sistema fiscal, aba `NF_Aquisicao`) e os DAE/DARF de ICMS (PDF) efetivamente pagos. Aplicativo desktop, com histórico persistido em SQLite local — todo o processamento é local; a única comunicação de rede é a checagem de atualizações no início (ver [Atualização automática](#atualização-automática-e-releases)).

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

## Atualização automática e releases

Ao abrir o `.exe` empacotado (não em modo desenvolvimento), o AuditaDAE consulta em segundo plano o último [release do repositório no GitHub](https://github.com/anderson561/analisedaeicms/releases/latest). Se houver uma versão mais nova, pergunta se pode baixar e aplicar; ao concluir, pede confirmação para fechar e reabrir na nova versão. Se a checagem falhar (sem internet, GitHub fora do ar), avisa e segue funcionando normalmente com a versão atual. Se a pasta de instalação não tiver permissão de escrita, apenas avisa que há uma versão nova, sem aplicar sozinho.

Checklist para publicar uma nova versão:

1. Atualize `__version__` em [`src/version.py`](src/version.py).
2. Rode `build.bat` para gerar `dist/AuditaDAE/`.
3. Compacte o conteúdo da pasta (sem pasta-wrapper) com o nome exato `AuditaDAE-Windows-x64.zip`:
   ```powershell
   Compress-Archive -Path "dist\AuditaDAE\*" -DestinationPath "AuditaDAE-Windows-x64.zip"
   ```
4. Crie uma tag `vX.Y.Z` e um [Release](https://github.com/anderson561/analisedaeicms/releases/new) no GitHub nessa tag, anexando o zip gerado — o nome do arquivo precisa ser exatamente `AuditaDAE-Windows-x64.zip` (o updater ignora qualquer outro asset, inclusive o "Source code (zip)" que o GitHub anexa automaticamente).

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
