# AuditaDAE

Auditoria de ICMS Antecipação (SEFAZ-BA): cruza notas fiscais, DAE/DARF, relatórios de pagamento e de parcelamento, entradas e as listas de notas da fiscalização, e gera relatórios Excel/PDF. Aplicativo desktop com 7 abas independentes, com histórico persistido em SQLite local — todo o processamento é local; a única comunicação de rede é a checagem de atualizações no início (ver [Atualização automática](#atualização-automática-e-releases)).

## Funcionalidades

- Extração de PDFs de DAE/DARF (formato SEFAZ-BA) por posição geométrica das palavras: código da receita, referência, valor principal, especificação da receita e as notas fiscais citadas em "Informações Complementares".
- Leitura do mapa de notas (planilha com aba `NF_Aquisicao`, detectada automaticamente) ou de um relatório simples `.xlsx`/`.xls`/`.csv`/`.pdf` com detecção automática da coluna de número da nota.
- Conciliação: parte de cada nota do mapa e verifica se ela é citada em algum DAE do lote processado (normalizando pontuação e zeros à esquerda). Nota no mapa E em algum DAE → conciliada. Nota no mapa e ausente de todos os DAEs → não encontrada (possível ICMS antecipação não recolhido).
- Aba **Pagamentos**: confirma se cada DAE de receita 1145/2175 consta do relatório anual de pagamentos da SEFAZ-BA (PDF lido por OCR), casando valor principal e referência.
- Aba **Parcelamento**: confirma se cada DAE corresponde a uma parcela do "Relatório Débito do PAF" (PDF lido por OCR), casando valor histórico e mês/ano da Data de Ocorrência.
- Aba **Pagamentos Notas**: compara o relatório de Entradas (PDF SEFAZ-BA, linhas ICMS ou ST/AT) com a lista de notas fiscais/itens (PDF). Soma os itens de cada nota e cruza por mês de **lançamento** + número da nota, sem tolerância (exato ao centavo). Gera Excel e PDF com três grupos: Valores Iguais, Valores Diferentes (com coluna Diferença) e Notas Não Encontradas nas Entradas.
- Aba **Conciliação vs DAE**: recebe um ou mais DAE (PDF) e o relatório já conciliado de Pagamentos Notas (`.xlsx`, todas as abas). Para cada nota localiza o número nos DAE e devolve código da receita, referência, valor, especificação e o **arquivo do DAE**; notas ausentes de todos os DAE vão para um relatório de não encontradas, agrupado por ano e mês. Gera Excel e PDF das encontradas e das não encontradas.
- Aba **Verificar Créditos**: lê uma ou mais listas "Antecipação parcial… Lista de notas fiscais/itens" (PDF), descarta calçados (NCM 64) e bolsas, mochilas e carteiras (NCM 4202) e, por nota (número + data de emissão + UF), soma VlLiqItem, VlCredEmpr, VlBcAntParc e VlCredAud. Relatório Excel e PDF com datas de emissão e lançamento, UF, descrição/CodItem/NCM do 1º item, totais por mês e total geral.
- Aba **Analisar Apuração**: recebe o relatório de créditos (Excel ou PDF gerado na aba Verificar Créditos), a lista de notas fiscais/itens da antecipação (PDF) e a planilha de DAEs (`.xlsx`, coluna "Informações de Pagamento (DAE)"). Gera as tabelas de notas por Ano → Mês (Data Emissão, Nº Nota, Descrição/CodItem/NCM, VlLiqItem, VlCredEmpr, VlBcAntParc, VlCredAud) acrescidas de Valor Pago = Σ(VlTotItem × AliqInt) − VlCredEmpr e Informação Norte (texto do DAE; células mescladas valem para todas as notas do bloco), com totais por mês e geral. Notas fora da planilha de DAEs ou da antecipação são sinalizadas.
- Relatórios Excel e PDF gerados **sob demanda**: os botões aparecem depois que a ação da aba termina, e o usuário escolhe onde salvar. Todos agrupam por Ano → Mês, com o nome do mês por extenso (Janeiro, Fevereiro…). Os relatórios de notas conciliadas incluem a coluna "Arquivo do DAE".
- Histórico de conciliações salvo em `%LOCALAPPDATA%\AuditaDAE\auditadae.db`, mantido entre execuções.

## Documentação do projeto

- [BRD — Requisitos de Negócio](docs/BRD.md): problema, objetivos, escopo e regras de negócio
- [FRD — Requisitos Funcionais](docs/FRD.md): o que cada aba faz (entradas, regras, saídas)
- [SRS — Especificação de Requisitos de Software](docs/SRS.md): interfaces, requisitos não funcionais e aceite
- [TRD — Requisitos Técnicos](docs/TRD.md): arquitetura, extração, dados, empacotamento e atualização

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

Na janela, escolha a aba, selecione (ou arraste) os arquivos pedidos e clique no botão de ação (ex.: "Processar" na aba Notas). Ao terminar, use os botões "Gerar Relatório Excel/PDF" que aparecem na aba. Detalhes de cada aba em [FRD](docs/FRD.md).

## Testes

```bash
.venv\Scripts\python.exe -m pytest tests/ -q
```

Use sempre o Python da venv: neste ambiente o `python`/`pytest` do PATH é o da Microsoft Store, sem as dependências do projeto.

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
├── extractors/   # extração de PDF (DAE, Entradas, lista de notas) e de relatório (xlsx/xls/csv/pdf)
├── models/       # modelos pydantic
├── db/           # SQLite (schema + repositório)
├── engine/       # motor de conciliação
├── reports/      # geração dos relatórios .xlsx e .pdf de saída
├── gui/          # interface CustomTkinter
└── main.py       # orquestração ponta a ponta
tests/            # testes unitários (pytest)
```

*Documentação atualizada em 13/10/2026 — abas Pagamentos Notas e Conciliação vs DAE, meses por extenso e coluna "Arquivo do DAE" nos relatórios.*

*Documentação atualizada em 26/10/2026 — aba Verificar Créditos e correção da leitura da lista de notas (itens com número de 3 dígitos na descrição).*

*Documentação atualizada em 26/10/2026 — aba Analisar Apuração.*

*Documentação atualizada em 09/11/2026 — versão 1.1.0 publicada (abas Pagamentos Notas, Conciliação vs DAE, Verificar Créditos e Analisar Apuração).*

*Documentação atualizada em 24/11/2026 — criados BRD, FRD, SRS e TRD em `docs/`; README corrigido (abas Pagamentos e Parcelamento, relatórios sob demanda, comando de testes).*
