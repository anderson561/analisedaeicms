# FRD — Documento de Requisitos Funcionais

**Produto:** AuditaDAE 1.1.0
**Versão do documento:** 1.0 — 24/11/2026
**Documentos relacionados:** [BRD](BRD.md) (regras RN-xx) · [SRS](SRS.md) · [TRD](TRD.md)

Este documento descreve **o que o sistema faz**, aba por aba: entradas, processamento, saídas e regras. As regras de negócio (RN-xx) estão no BRD.

---

## 1. Visão geral da interface

Janela única com sete abas independentes. Cada aba tem seus próprios campos de anexo e seu botão de ação, e **nenhuma aba depende do processamento de outra**. Abaixo das abas ficam sempre visíveis a barra de progresso e o histórico de conciliações.

| # | Aba | Ação principal |
|---|---|---|
| 1 | Notas | Processar |
| 2 | Pagamentos | Verificar Pagamentos |
| 3 | Parcelamento | Verificar Parcelamentos |
| 4 | Pagamentos Notas | Verificar Pagamentos x Notas |
| 5 | Conciliação vs DAE | Conciliar com DAE |
| 6 | Verificar Créditos | Verificar Créditos |
| 7 | Analisar Apuração | Analisar Apuração |

### Requisitos comuns a todas as abas

| ID | Requisito |
|---|---|
| RF-G01 | Todo campo de anexo aceita **arrastar e soltar** e o botão **Selecionar**. Os campos de lote aceitam vários arquivos. |
| RF-G02 | O botão de ação fica **desabilitado** até todos os campos obrigatórios da aba estarem preenchidos. |
| RF-G03 | O processamento roda **em segundo plano**, com a barra de progresso animada, sem travar a janela. |
| RF-G04 | Ao terminar, uma mensagem resume as **contagens** de cada grupo de resultado. Em caso de falha, uma mensagem de erro descreve o motivo. |
| RF-G05 | Os botões **Gerar Relatório Excel/PDF** só aparecem depois de um processamento concluído com sucesso. |
| RF-G06 | Os relatórios são gerados **sob demanda**. O usuário escolhe o nome e a pasta de destino. |
| RF-G07 | Os relatórios agrupam os dados **Ano → Mês**, com o mês por extenso; itens sem período identificado vão para "Sem Ano/Mês Identificado", por último. |

---

## 2. Aba 1 — Notas

**Objetivo:** conciliar as notas do mapa de aquisição com os DAEs e, se a planilha tiver outras fontes, tratá-las também.

| ID | Requisito |
|---|---|
| RF-N01 | Entradas: um ou mais **DAE/DARF em PDF** e, opcionalmente, um **relatório de notas** (`.xlsx`, `.xls`, `.csv` ou `.pdf`). |
| RF-N02 | Do DAE são extraídos: código da receita, referência (MM/AAAA), valor principal, especificação da receita e números das notas fiscais citadas. |
| RF-N03 | Em planilha `.xlsx`, o sistema **detecta pela estrutura das colunas** quais fontes existem: Aquisição (mapa de notas), Apuração ICMS AT e Pagamentos/Parcelamento. Com 2 ou mais fontes, pergunta quais processar; com 1, processa direto. |
| RF-N04 | **Aquisição:** cada nota do mapa é classificada como **Conciliada** (citada em algum DAE, RN-01) ou **Não Encontrada em Nenhum DAE**. |
| RF-N05 | **ICMS AT:** exibe a tabela mensal Apurado × Pago (código 1145) × A Recolher, sem cruzar com DAEs. |
| RF-N06 | **Pagamentos/Parcelamento da planilha:** linhas com referência em data seguem a regra de pagamento (RN-03); linhas com referência "parcela atual/total" casam só pelo valor. |
| RF-N07 | O resultado da conciliação é gravado no **histórico local**, exibido no rodapé da janela. |
| RF-N08 | Relatório **Conciliadas**: notas do mesmo DAE aparecem num bloco, com as colunas do DAE mescladas e a coluna **Arquivo do DAE**; blocos ordenados por valor decrescente. |
| RF-N09 | Relatório **Não Encontradas**: número da NF, data de emissão, CNPJ do emitente e status. |

## 3. Aba 2 — Pagamentos

| ID | Requisito |
|---|---|
| RF-P01 | Entradas: DAEs em PDF e um ou mais **relatórios anuais de pagamento** da SEFAZ-BA (PDF, inclusive sem camada de texto). |
| RF-P02 | Considera somente DAEs de receita 1145/2175 (RN-02). |
| RF-P03 | Classifica cada DAE como **Pagamento Confirmado** (valor e referência batem, RN-03) ou **Não Localizado no Relatório de Pagamentos**. |
| RF-P04 | O relatório traz, para os confirmados: Nosso Número, data de pagamento, referência, receita, valor principal e valor total. |

## 4. Aba 3 — Parcelamento

| ID | Requisito |
|---|---|
| RF-PA01 | Entradas: DAEs em PDF e um ou mais **"Relatório Débito do PAF"** (PDF, lido por OCR). |
| RF-PA02 | Sem restrição de código de receita. |
| RF-PA03 | Casa o valor principal do DAE com o **valor histórico** da parcela e a referência do DAE com o mês/ano da **Data de Ocorrência** (RN-03). |
| RF-PA04 | Classifica cada DAE como **Localizado no Parcelamento** (com PAF, datas e valores) ou **Não Localizado**. |

## 5. Aba 4 — Pagamentos Notas

| ID | Requisito |
|---|---|
| RF-PN01 | Entradas: um ou mais **relatórios de Entradas** (PDF "Acompanhamento de Entradas") e uma ou mais **listas de notas fiscais/itens** (PDF da fiscalização). |
| RF-PN02 | Das Entradas, lê apenas as linhas **ICMS** e **ST/AT** (RN-06). Se o valor contábil estiver ilegível no PDF, ele é recomposto como Base + Isentas + Outras. |
| RF-PN03 | Da lista, soma o **VlLiqItem** de todos os itens de cada nota. A descrição da nota é a do 1º item, cortada no primeiro "/". |
| RF-PN04 | Cruza pela chave **mês de lançamento + nota** (RN-04) e compara os valores ao centavo (RN-05). |
| RF-PN05 | Saída em três grupos: **Valores Iguais**, **Valores Diferentes** (com a coluna Diferença) e **Notas Não Encontradas nas Entradas** (notas sem lançamento). Excel com 3 abas; PDF com 3 seções. |

## 6. Aba 5 — Conciliação vs DAE

| ID | Requisito |
|---|---|
| RF-CD01 | Entradas: um ou mais **DAEs em PDF** e o **relatório já conciliado** (`.xlsx` gerado pela aba 4). |
| RF-CD02 | Lê **todas as abas** do relatório, achando a coluna "Número do Documento" pelo cabeçalho (repetido a cada mês) e o período pelos títulos "Ano AAAA" e nome do mês. Notas repetidas no mesmo mês contam uma vez. |
| RF-CD03 | Para cada nota encontrada num DAE, devolve código da receita, referência, valor principal, especificação e **arquivo do DAE**. |
| RF-CD04 | Notas ausentes de todos os DAEs vão para **Não Encontradas em Nenhum DAE**, agrupadas pelo ano/mês da planilha. |
| RF-CD05 | Uma nota encontrada num DAE sem dados de cabeçalho legíveis **não é descartada**: aparece com o arquivo do DAE. |

## 7. Aba 6 — Verificar Créditos

| ID | Requisito |
|---|---|
| RF-VC01 | Entrada: uma ou mais **listas de notas fiscais/itens** (PDF da fiscalização). |
| RF-VC02 | Lê de cada item: data de emissão, data de lançamento, UF, nota, descrição (inclusive a continuação em várias linhas), CodItem, NCM, VlLiqItem, VlTotItem, VlCredEmpr, VlBcAntParc, AliqInt e VlCredAud. |
| RF-VC03 | O nº do item é o número de 3 dígitos **seguido dos 11 valores** da linha. Números de 3 dígitos na descrição não podem ser confundidos com ele. |
| RF-VC04 | Exclui os itens de NCM 64 e 4202 (RN-07). |
| RF-VC05 | Agrupa por **nota + data de emissão + UF** e soma VlLiqItem, VlCredEmpr, VlBcAntParc e VlCredAud. |
| RF-VC06 | Relatório com uma linha por nota: Data Emissão, Data Lançamento, UF, Nº Nota, Descrição / CodItem / NCM (do 1º item) e os 4 valores, com **total por mês e total geral**. |
| RF-VC07 | A mensagem final informa os itens lidos, excluídos e considerados e o total de notas. |

## 8. Aba 7 — Analisar Apuração

| ID | Requisito |
|---|---|
| RF-AA01 | Entradas obrigatórias: (1) **relatório de créditos** gerado pela aba 6, em `.xlsx` ou `.pdf`; (2) uma ou mais **listas de antecipação** (PDF); (3) **planilha de DAEs** (`.xlsx` com a coluna "Informações de Pagamento (DAE)"). |
| RF-AA02 | As notas analisadas são as do relatório de créditos. VlTotItem e AliqInt vêm da lista de antecipação, pela mesma chave nota + emissão + UF e sem NCM 64/4202. |
| RF-AA03 | Calcula o **Valor Pago** de cada nota (RN-08). |
| RF-AA04 | Busca a **Informação Norte** pelo número da nota na planilha de DAEs, respeitando as células mescladas (RN-09). |
| RF-AA05 | Nota ausente da planilha de DAEs: "Não encontrada na planilha de DAEs". Nota ausente da antecipação: Valor Pago em branco e o aviso "Não encontrada na planilha de antecipação". |
| RF-AA06 | Relatório com uma tabela por mês: Data Emissão, Nº Nota, Descrição / CodItem / NCM, VlLiqItem, VlCredEmpr, VlBcAntParc, VlCredAud, **Valor Pago** e **Informação Norte**, com totais por mês e geral. |

---

## 9. Funções do sistema

| ID | Requisito |
|---|---|
| RF-S01 | **Histórico:** exibe as conciliações anteriores, que ficam guardadas entre execuções. |
| RF-S02 | **Atualização automática:** ao abrir o executável, verifica se há versão nova publicada. Com confirmação do usuário, baixa, substitui a instalação e reabre o app, mantendo um backup até o próximo início bem-sucedido. |
| RF-S03 | Se a pasta de instalação não permitir escrita, apenas avisa da nova versão, sem tentar instalar. |
| RF-S04 | Falhas de rede na verificação viram aviso; nunca impedem o uso do app. |

## 10. Matriz de rastreabilidade (regra de negócio → requisito)

| Regra | Requisitos |
|---|---|
| RN-01 | RF-N04, RF-CD03 |
| RN-02 | RF-P02 |
| RN-03 | RF-P03, RF-PA03, RF-N06 |
| RN-04, RN-05, RN-06 | RF-PN02, RF-PN04 |
| RN-07 | RF-VC04, RF-AA02 |
| RN-08 | RF-AA03 |
| RN-09 | RF-AA04 |
| RN-10 | RF-N04, RF-PN05, RF-CD04, RF-CD05, RF-AA05 |
| RN-11 | RF-G06, RF-G07 |
