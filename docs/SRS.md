# SRS — Especificação de Requisitos de Software

**Produto:** AuditaDAE 1.1.0
**Versão do documento:** 1.0 — 24/11/2026
**Estrutura:** baseada na IEEE 830 / ISO/IEC/IEEE 29148
**Documentos relacionados:** [BRD](BRD.md) · [FRD](FRD.md) · [TRD](TRD.md)

---

## 1. Introdução

### 1.1 Propósito
Especificar os requisitos do AuditaDAE, aplicativo desktop de auditoria de ICMS Antecipação (SEFAZ-BA), servindo de referência para desenvolvimento, testes e aceite.

### 1.2 Escopo
O AuditaDAE lê documentos fiscais em PDF e planilhas, cruza notas fiscais, DAEs, pagamentos, parcelamentos e créditos, e gera relatórios Excel/PDF. Todo o processamento é local. O detalhamento funcional está no [FRD](FRD.md); este documento consolida os requisitos e acrescenta interfaces, atributos de qualidade e restrições.

### 1.3 Definições e siglas

| Termo | Significado |
|---|---|
| DAE / DARF | Documento de Arrecadação Estadual: guia de recolhimento do ICMS |
| ICMS AT | ICMS Antecipação Tributária (código de receita 1145) |
| Antecipação parcial | ICMS Antecipação Parcial (código de receita 2175) |
| PAF | Processo Administrativo Fiscal (parcelamento de débito) |
| NCM | Nomenclatura Comum do Mercosul (classificação fiscal do produto) |
| VlLiqItem, VlTotItem, VlCredEmpr, VlBcAntParc, AliqInt, VlCredAud | Colunas da "Lista de notas fiscais/itens" da SEFAZ-BA: valor líquido do item, valor total do item, crédito segundo a empresa, base de cálculo da antecipação, alíquota interna e crédito segundo o auditor |
| Informação Norte | Anotação de pagamento do escritório (DAE, valor, nº e data do pagamento) |
| Data de lançamento (DataLcto) | Data de entrada da nota na escrita fiscal; é a "Data" do relatório de Entradas |

### 1.4 Referências
BRD, FRD, TRD, `README.md`, `CHANGELOG.md`; layouts de documentos da SEFAZ-BA (DAE, Relatório de Pagamentos, Relatório Débito do PAF, Acompanhamento de Entradas, Lista de notas fiscais/itens).

## 2. Descrição geral

### 2.1 Perspectiva do produto
Aplicação autônoma (standalone) para Windows. Sem servidor: a única comunicação externa é a consulta de versão ao GitHub Releases. Os arquivos chegam pela interface (arrastar e soltar ou seleção) e os relatórios são gravados onde o usuário escolher.

### 2.2 Funções do produto
1. Conciliação notas × DAEs, com apuração ICMS AT e pagamentos/parcelamentos de planilha.
2. Verificação de DAEs × relatório de pagamentos.
3. Verificação de DAEs × parcelamentos (PAF).
4. Comparação Entradas × lista de notas.
5. Conciliação de relatório de notas × DAEs.
6. Verificação de créditos por nota.
7. Análise da apuração (Valor Pago e Informação Norte).
8. Relatórios Excel/PDF, histórico local e atualização automática.

### 2.3 Usuários
Analistas fiscais com domínio de ICMS e familiaridade com Excel, sem conhecimento técnico de software. Uso individual em estação de trabalho.

### 2.4 Ambiente operacional
Windows 10/11 64 bits; distribuído como pasta (PyInstaller onedir) com OCR embutido; não exige Python instalado.

### 2.5 Restrições de projeto
- Os dados fiscais não podem sair da máquina (sigilo fiscal e LGPD).
- Suporte apenas aos layouts da SEFAZ-BA.
- Executável sem assinatura digital (o SmartScreen alerta na primeira execução).

### 2.6 Premissas e dependências
Documentos no formato original da SEFAZ-BA; OCR (Tesseract, idioma português) para os PDFs sem camada de texto; acesso à internet só para a atualização automática, que é opcional.

## 3. Requisitos específicos

### 3.1 Requisitos funcionais
Os requisitos funcionais estão especificados, com identificadores, no [FRD](FRD.md):

| Grupo | IDs | Prioridade |
|---|---|---|
| Comuns às abas | RF-G01 a RF-G07 | Essencial |
| Notas | RF-N01 a RF-N09 | Essencial |
| Pagamentos | RF-P01 a RF-P04 | Essencial |
| Parcelamento | RF-PA01 a RF-PA04 | Essencial |
| Pagamentos Notas | RF-PN01 a RF-PN05 | Essencial |
| Conciliação vs DAE | RF-CD01 a RF-CD05 | Essencial |
| Verificar Créditos | RF-VC01 a RF-VC07 | Essencial |
| Analisar Apuração | RF-AA01 a RF-AA06 | Essencial |
| Sistema | RF-S01 a RF-S04 | Desejável |

### 3.2 Interfaces externas

#### 3.2.1 Interface com o usuário
- Janela de 820×640 px (mínimo 700×560, redimensionável), tema escuro, sete abas.
- Campos de anexo com arrastar e soltar; botões de ação desabilitados até a entrada estar completa; botões de relatório só depois do sucesso.
- Mensagens em português; erros mostrados em caixa de diálogo, nunca engolidos.

#### 3.2.2 Interfaces de arquivo (entrada)

| Documento | Formato | Abas que usam |
|---|---|---|
| DAE/DARF SEFAZ-BA | PDF com texto | Notas, Pagamentos, Parcelamento, Conciliação vs DAE |
| Mapa de notas / relatório simples | XLSX, XLS, CSV, PDF | Notas |
| Relatório anual de pagamentos | PDF sem texto, com grade (OCR por célula) | Pagamentos |
| Relatório Débito do PAF | PDF sem texto e sem grade (OCR de página) | Parcelamento |
| Acompanhamento de Entradas | PDF com texto | Pagamentos Notas |
| Lista de notas fiscais/itens | PDF com texto | Pagamentos Notas, Verificar Créditos, Analisar Apuração |
| Relatório de pagamentos de notas | XLSX gerado pelo app | Conciliação vs DAE |
| Relatório de créditos | XLSX ou PDF gerado pelo app | Analisar Apuração |
| Planilha de DAEs | XLSX com "Informações de Pagamento (DAE)" | Analisar Apuração |

#### 3.2.3 Interfaces de arquivo (saída)
Relatórios `.xlsx` (openpyxl) e `.pdf` A4 paisagem (reportlab), agrupados Ano → Mês, com títulos, cabeçalho por bloco, valores numéricos com formato monetário no Excel e totais onde especificado.

#### 3.2.4 Interfaces de software e comunicação
- **GitHub Releases API** (HTTPS, `GET /repos/anderson561/analisedaeicms/releases/latest`, timeout de 10 s) só para verificar a versão; o download do asset `AuditaDAE-Windows-x64.zip` exige confirmação do usuário.
- **SQLite** local em `%LOCALAPPDATA%\AuditaDAE\auditadae.db`.

### 3.3 Requisitos não funcionais

| ID | Categoria | Requisito |
|---|---|---|
| RNF-01 | Exatidão | Valores monetários arredondados a 2 casas; comparações de igualdade ao centavo (RN-05) ou com tolerância menor que R$ 0,01 (RN-03), conforme o fluxo. |
| RNF-02 | Completude | Nenhum registro de entrada é descartado sem aparecer num grupo de resultado ou numa contagem (RN-10). |
| RNF-03 | Privacidade | Nenhum conteúdo de arquivo de cliente é transmitido pela rede. |
| RNF-04 | Disponibilidade | O app funciona sem internet; só a atualização automática fica indisponível. |
| RNF-05 | Responsividade | O processamento roda fora da thread da interface; a janela continua respondendo durante leituras longas, inclusive OCR. |
| RNF-06 | Desempenho de início | O executável abre em poucos segundos (onedir; o onefile levava de 10 a 25 s e foi descartado). |
| RNF-07 | Confiabilidade da atualização | A troca de versão é atômica no mesmo volume, com rollback se a substituição falhar e backup mantido até o próximo início bem-sucedido. |
| RNF-08 | Manutenibilidade | Camadas separadas (extratores, motor, relatórios, interface); regras de negócio sem dependência da interface. |
| RNF-09 | Testabilidade | Suíte automatizada (pytest) cobrindo extratores, motores e relatórios; testes com dados sintéticos, sem arquivos de cliente; a suíte deve passar antes de qualquer versão. |
| RNF-10 | Portabilidade de dados | Planilhas de clientes diferentes são reconhecidas pela estrutura das colunas, não pelo nome da aba. |
| RNF-11 | Usabilidade | Todo texto da interface e dos relatórios em português; meses por extenso. |

### 3.4 Requisitos de dados
- Modelos tipados (pydantic) para documentos, linhas e resultados.
- Persistência apenas do histórico: tabelas `dae_processado` e `conciliacao_historico` (status `ENCONTRADO` ou `NAO_ENCONTRADO`).
- Os demais resultados vivem em memória até o usuário gerar o relatório.

## 4. Critérios de aceite da versão

1. Suíte completa verde (194 testes na 1.1.0).
2. Conferência com documentos reais de pelo menos um cliente para cada fluxo alterado, com os números registrados no CHANGELOG ou no PR.
3. O executável gerado abre e as abas carregam.
4. Release publicado com o asset `AuditaDAE-Windows-x64.zip` contendo `AuditaDAE.exe` na raiz.

## 5. Apêndice — Rastreabilidade

BRD (OBN, RN) → FRD (RF) → TRD (componentes) → testes (`tests/`). A matriz RN → RF está no FRD, seção 10; o mapeamento RF → módulo está no TRD, seção 4.
