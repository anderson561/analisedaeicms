# TRD — Documento de Requisitos Técnicos

**Produto:** AuditaDAE 1.1.0
**Versão do documento:** 1.0 — 24/11/2026
**Documentos relacionados:** [BRD](BRD.md) · [FRD](FRD.md) · [SRS](SRS.md)

Este documento define **como** o sistema é construído: arquitetura, tecnologias, técnicas de extração, dados, empacotamento, atualização e qualidade.

---

## 1. Stack tecnológica

| Camada | Tecnologia (versão fixada em `requirements.txt`) |
|---|---|
| Linguagem | Python 3.13 |
| Interface | customtkinter 5.2.2 + tkinterdnd2 0.4.2 (arrastar e soltar) |
| Modelos de dados | pydantic 2.9.2 |
| PDF com texto | pdfplumber 0.11.4 |
| PDF vetorial / renderização | PyMuPDF 1.28.2 |
| OCR | Tesseract (idioma `por`) via pytesseract 0.3.13 |
| Planilhas | openpyxl 3.1.5 (`.xlsx`), xlrd 2.0.1 (`.xls`) |
| Relatórios PDF | reportlab 5.0.0 |
| Persistência | SQLite (biblioteca padrão) |
| Empacotamento | PyInstaller 6.11.1 (onedir) |
| Testes | pytest 8.3.3 |

## 2. Arquitetura

Arquitetura em camadas. As regras de negócio não dependem da interface:

```
GUI (src/gui/app.py)  ──►  Orquestração (src/main.py)  ──►  Extratores (src/extractors/)
        │                          │                         Motores    (src/engine/)
        ▼                          ▼                         Modelos    (src/models/)
Relatórios (src/reports/)    Persistência (src/db/)          OCR        (src/ocr/)
Atualizador (src/updater.py)
```

- **Extratores:** convertem arquivo → modelos pydantic. Nenhuma regra de cruzamento.
- **Motores:** funções puras sobre modelos (cruzamento, agrupamento, cálculo). São a camada mais testada.
- **Orquestração (`main.py`):** uma função `*_lote` por aba, que encadeia extração e motor.
- **Relatórios:** recebem modelos e escrevem `.xlsx`/`.pdf`, com helpers comuns de agrupamento Ano → Mês.
- **GUI:** estado por aba, sem compartilhar arquivos nem resultados entre abas; trabalho pesado em `threading.Thread`; o retorno à interface passa por `self.after(0, ...)`.

## 3. Estrutura de código

```
src/
├── gui/app.py                     # janela, 7 abas, handlers
├── main.py                        # orquestração por aba
├── models/dae_models.py           # modelos pydantic
├── extractors/
│   ├── dae_extractor.py           # DAE/DARF (posição das palavras)
│   ├── relatorio_extractor.py     # relatório simples xlsx/xls/csv/pdf
│   ├── mapa_extractor.py          # mapa NF_Aquisicao
│   ├── classificador_planilha.py  # detecção estrutural de fontes
│   ├── icms_at_extractor.py       # apuração ICMS AT
│   ├── pagamento_extractor.py     # relatório de pagamentos (OCR por célula)
│   ├── pagamento_planilha_extractor.py
│   ├── parcelamento_extractor.py  # Relatório Débito do PAF (OCR de página)
│   ├── entradas_icms_extractor.py # Acompanhamento de Entradas
│   ├── lista_notas_extractor.py   # Lista de notas fiscais/itens
│   ├── relatorio_conciliado_extractor.py
│   └── apuracao_extractors.py     # relatório de créditos + planilha de DAEs
├── engine/
│   ├── conciliador.py             # notas × DAEs
│   ├── verificador_pagamento.py   # DAEs × pagamentos
│   ├── verificador_parcelamento.py
│   ├── comparador_pagamentos_notas.py
│   ├── verificador_creditos.py
│   └── analisador_apuracao.py
├── reports/report_generator.py    # todos os relatórios Excel/PDF
├── db/                            # SQLite (schema + repositório)
├── ocr/tesseract_setup.py         # localiza o Tesseract embutido
├── updater.py, updater_helper.bat # atualização automática
└── version.py                     # __version__
```

## 4. Mapeamento requisito → componente

| Aba (FRD) | Orquestração | Extratores | Motor | Relatórios |
|---|---|---|---|---|
| Notas (RF-N) | `processar_lote` | dae, relatorio, mapa, classificador, icms_at, pagamento_planilha | conciliador, verificador_pagamento, verificador_parcelamento | conciliadas, não encontradas, icms_at, pagamentos, parcelamento |
| Pagamentos (RF-P) | `verificar_pagamentos_lote` | dae, pagamento | verificador_pagamento | pagamentos |
| Parcelamento (RF-PA) | `verificar_parcelamento_lote` | dae, parcelamento | verificador_parcelamento | parcelamento |
| Pagamentos Notas (RF-PN) | `verificar_pagamentos_notas_lote` | entradas_icms, lista_notas | comparador_pagamentos_notas | pagamentos_notas |
| Conciliação vs DAE (RF-CD) | `conciliar_relatorio_com_daes_lote` | dae, relatorio_conciliado | conciliador | conciliadas, não encontradas |
| Verificar Créditos (RF-VC) | `verificar_creditos_lote` | lista_notas | verificador_creditos | creditos |
| Analisar Apuração (RF-AA) | `analisar_apuracao_lote` | apuracao_extractors, lista_notas | analisador_apuracao | apuracao |

## 5. Técnicas de extração

A técnica de cada extrator é escolhida pelo que o PDF realmente contém (camada de texto? grade vetorial?), verificado antes de implementar.

| Documento | Técnica | Pontos de atenção |
|---|---|---|
| DAE/DARF | `pdfplumber.extract_words()` + leitura por **posição** (valor abaixo do rótulo, na mesma coluna, ancorado na posição real do rótulo) | O layout é multicoluna e `extract_text()` embaralha os campos. O prefixo numérico dos rótulos é opcional (layout de 2023 sem "1-"). Em "Notas Fiscais:15", o 15 é a contagem. |
| Relatório de pagamentos | PyMuPDF `find_tables()` acha a grade; **OCR por célula** | PDF sem texto (fonte Type3), mas com grade vetorial. |
| Relatório Débito do PAF | **OCR de página inteira** (300 DPI, `--psm 6`) + regex tolerante por linha | Sem texto e sem grade (página desenhada como curvas). |
| Acompanhamento de Entradas | `extract_words(x_tolerance=1.5)` + agrupamento por `top`; âncora Data → Nota → (valor, ICMS ou ST/AT) | Nomes longos de fornecedor sobrepõem colunas, com caracteres entrelaçados. Se o valor sai ilegível, é recomposto por Base + Isentas + Outras. |
| Lista de notas fiscais/itens | `extract_words(x_tolerance=1.5)`; item = **3 dígitos seguidos de 11 valores**; continuação da descrição e CodItem/NCM nas linhas seguintes | Números de 3 dígitos na descrição. Cabeçalho e rodapé de página no meio de um item são ignorados; "Total", "Período:" e a legenda encerram o bloco. |
| Planilhas (mapa, relatórios, DAEs) | openpyxl; localização por **cabeçalho**, não por posição nem nome de aba; células mescladas expandidas | Cabeçalhos repetidos por mês; títulos "Ano AAAA" e nome do mês dão o período. |
| Relatório de créditos em PDF (gerado pelo app) | `pdfplumber.extract_tables()` (a tabela tem grade) | O cabeçalho pode sair partido; as 5 primeiras colunas são lidas pela posição e os valores pelo nome. |

**Normalização:** números de nota sem pontuação e sem zeros à esquerda (`sanitize_nf_numero`); valores no formato brasileiro (`1.234,56`) convertidos para float e arredondados a 2 casas nas somas.

## 6. Modelo de dados

### 6.1 Modelos principais (pydantic, `src/models/dae_models.py`)
`DaeDocumento`, `LinhaRelatorio`, `NotaConciliada` (com `dae_arquivo_origem`), `NotaNaoEncontrada` (com ano/mês opcionais), `LinhaPagamentoDae`, `PagamentoConfirmado`, `LinhaParcelamento`, `LinhaIcmsAt`, `LinhaEntradaIcms`, `LinhaNotaItem`, `NotaFiscalComparada`, `ItemListaNotas`, `NotaCredito`, `AnaliseApuracao` e `ResultadoProcessamento` (agregado da aba Notas).

### 6.2 Persistência (SQLite)

```sql
dae_processado(id, arquivo_origem, codigo_receita, referencia,
               valor_principal, especificacao_receita, data_processamento)
conciliacao_historico(id, dae_id → dae_processado.id, numero_nf,
                      status ∈ {ENCONTRADO, NAO_ENCONTRADO}, data_processamento)
```

Local: `%LOCALAPPDATA%\AuditaDAE\auditadae.db`. Quando o app roda pela venv do Python da Microsoft Store, o Windows redireciona esse caminho para a pasta do pacote; o executável final grava no caminho normal.

## 7. Relatórios

- Helpers comuns: `_agrupar_por_ano_mes`, `_escrever_planilha_por_ano_mes`, `_elementos_por_ano_mes`, `_tabela_relatorio` e `_titulo_mes` (meses por extenso).
- PDF em A4 paisagem; descrições longas em `Paragraph`, com quebra de linha; larguras de coluna fixadas para caber em 698 pt úteis.
- Excel: formato `#,##0.00` nos valores, totais em negrito e mesclagem vertical por DAE no relatório de Conciliadas.

## 8. Empacotamento e distribuição

- **PyInstaller onedir** (`auditadae.spec`): `dist/AuditaDAE/AuditaDAE.exe` + `_internal/`. O onefile foi descartado por abrir em 10 a 25 s.
- **Tesseract embutido:** o `build.bat` copia `tesseract.exe`, **todas** as DLLs da instalação (um subconjunto falha em máquina limpa) e `por.traineddata` para `vendor/tesseract/` (fora do git), e o spec inclui essa pasta.
- **Build sem interação:** `.venv\Scripts\python.exe -m PyInstaller auditadae.spec --noconfirm`. O `build.bat` termina com `pause`.
- **Release:** zip do conteúdo de `dist/AuditaDAE/`, sem pasta-wrapper, com nome exato `AuditaDAE-Windows-x64.zip`; tag `vX.Y.Z`; `gh release create`.

## 9. Atualização automática

1. Só roda no executável (`updater.is_frozen()`), 1,5 s após abrir.
2. `GET releases/latest` (timeout de 10 s); compara a versão semântica com `src/version.py`. HTTP 404 significa "sem atualização"; outros erros viram aviso.
3. Com confirmação: baixa e extrai num staging **irmão** da instalação (mesmo volume, para o swap ser um rename).
4. Com nova confirmação: dispara `updater_helper.bat` destacado e fecha o app. O script espera o processo sair, renomeia a instalação para `AuditaDAE_old`, move o staging para o lugar (com rollback se falhar) e reabre o `.exe`.
5. O próximo início bem-sucedido apaga o `_old` e os stagings órfãos.
6. Pasta sem permissão de escrita: apenas avisa.

**Limitações conhecidas:** sem checksum nem assinatura do zip; sem rollback se a versão nova abrir mas tiver defeito.

## 10. Qualidade e processo

- **Testes:** `./.venv/Scripts/python.exe -m pytest tests/ -q`. Use sempre a venv: o `python` do PATH é o da Microsoft Store, sem as dependências. Na 1.1.0, 194 testes em 27 arquivos, com dados sintéticos (tokens, planilhas e PDFs gerados no teste).
- **Validação com dados reais:** antes de cada versão, rodar os fluxos alterados contra documentos reais e conferir os números. Os arquivos de clientes nunca entram no repositório.
- **Git:** uma branch por entrega (`feature/...`, `release/vX.Y.Z`), commits convencionais, PR para `main` com README e CHANGELOG atualizados no mesmo PR, merge e limpeza da branch. Não há CI configurado: a suíte roda localmente.
- **Versionamento:** SemVer em `src/version.py`; `CHANGELOG.md` no formato Keep a Changelog.

## 11. Segurança

- Processamento 100% local. A única chamada de rede é a consulta pública de versão.
- Nenhuma credencial no código: a API do GitHub é usada sem token.
- Sem `eval`/`exec`. Planilhas abertas com `data_only=True` (valores, sem executar fórmulas).
- Risco aceito: executável e zip sem assinatura digital.

## 12. Dívidas técnicas e evolução

| Item | Descrição |
|---|---|
| `src/gui/app.py` com cerca de 1.800 linhas | Extrair cada aba para seu próprio módulo/classe |
| `report_generator.py` com cerca de 1.100 linhas | Dividir por relatório, mantendo os helpers comuns |
| Sem CI | Adicionar GitHub Actions (Windows) rodando o pytest a cada PR |
| Atualização sem checksum | Publicar SHA-256 do zip no release e validar antes de aplicar |
| Assinatura de código | Certificado para evitar o alerta do SmartScreen |
| NCMs excluídos (64 e 4202) fixos no código | Tornar configuráveis se surgirem outros cenários |
