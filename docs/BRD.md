# BRD — Documento de Requisitos de Negócio

**Produto:** AuditaDAE
**Versão do produto:** 1.1.0
**Versão do documento:** 1.0 — 24/11/2026
**Responsável pelo negócio:** Anderson (Norte Contabilidade — área fiscal)
**Documentos relacionados:** [FRD](FRD.md) · [SRS](SRS.md) · [TRD](TRD.md)

---

## 1. Resumo executivo

O AuditaDAE é um aplicativo desktop para Windows que automatiza a **auditoria do ICMS Antecipação** (antecipação tributária e antecipação parcial) de clientes de escritório contábil na Bahia. Ele cruza documentos oficiais da SEFAZ-BA (DAEs, relatórios de pagamento, parcelamentos, listas de notas da fiscalização) com as planilhas do escritório e gera relatórios Excel/PDF que mostram o que foi pago, o que não foi encontrado e onde há divergência de valor.

O objetivo é trocar uma conferência manual, nota por nota e DAE por DAE, por um processo repetível que leva minutos, deixa rastro e reduz o risco de autuação.

## 2. Contexto e problema

- Em fiscalizações e Ordens de Serviço da SEFAZ-BA, o auditor fiscal apresenta demonstrativos (por exemplo, "Antecipação parcial do ICMS recolhida a menor ou não recolhida — Lista de notas fiscais/itens") com centenas de páginas e milhares de itens.
- Para responder, o escritório precisa provar, para cada nota, **se o imposto foi recolhido, em qual DAE, em que data e por qual valor**, e apontar onde o cálculo do auditor diverge do cálculo da empresa.
- Hoje essa conferência é manual: buscar o número da nota dentro de cada DAE, somar itens, aplicar alíquota, descontar crédito e anotar o pagamento. O trabalho é lento e sujeito a erro, e um item esquecido vira débito na autuação.
- Os documentos da SEFAZ-BA têm armadilhas que enganam leituras simples: layouts que mudam entre anos, colunas sobrepostas no PDF, PDFs sem camada de texto e números de 3 dígitos na descrição do produto.

## 3. Objetivos de negócio

| ID | Objetivo | Indicador de sucesso |
|---|---|---|
| OBN-01 | Reduzir o tempo de conferência de uma fiscalização de ICMS Antecipação | Conferência anual de um cliente feita em minutos de processamento, não em dias de trabalho manual |
| OBN-02 | Não deixar nenhuma nota ou DAE sem classificação | Toda nota sai em um grupo explícito: conciliada/igual, diferente ou não encontrada |
| OBN-03 | Reduzir o risco de autuação por falta de prova de recolhimento | Cada nota conciliada traz o DAE, a referência, o valor e o arquivo de origem |
| OBN-04 | Padronizar a entrega ao cliente e ao fisco | Relatórios Excel/PDF com o mesmo layout: Ano → Mês, mês por extenso, totais |
| OBN-05 | Atender clientes diferentes sem reprogramação | Planilhas reconhecidas pela estrutura das colunas, não pelo nome da aba |

## 4. Partes interessadas

| Parte | Papel | Interesse |
|---|---|---|
| Analista fiscal do escritório (usuário principal) | Opera o sistema e entrega os relatórios | Rapidez, confiabilidade e relatórios prontos para anexar |
| Responsável pelo negócio (Anderson) | Define regras e prioridades | Redução de risco e de horas por fiscalização |
| Cliente do escritório (contribuinte) | Recebe os relatórios | Defesa contra a autuação; saber o que deve |
| Auditor fiscal da SEFAZ-BA | Destinatário indireto | Recebe a resposta fundamentada à Ordem de Serviço |

## 5. Escopo

### 5.1 Dentro do escopo (versão 1.1.0)

1. **Conciliação de notas × DAEs (aba Notas):** notas do mapa de aquisição citadas ou não em algum DAE; apuração mensal de ICMS AT; pagamentos e parcelamentos lidos da própria planilha.
2. **Verificação de pagamentos (aba Pagamentos):** DAEs de receita 1145/2175 × relatório anual de pagamentos da SEFAZ-BA.
3. **Verificação de parcelamentos (aba Parcelamento):** DAEs × "Relatório Débito do PAF".
4. **Pagamentos Notas:** relatório de Entradas (ICMS e ST/AT) × lista de notas fiscais/itens.
5. **Conciliação vs DAE:** relatório de Pagamentos Notas × DAEs.
6. **Verificar Créditos:** soma de valores e créditos por nota da lista da fiscalização, sem calçados, bolsas, mochilas e carteiras.
7. **Analisar Apuração:** Valor Pago calculado por nota e a Informação Norte (dados do DAE) para resposta à fiscalização.
8. Relatórios Excel e PDF sob demanda, histórico local das conciliações e atualização automática do aplicativo.

### 5.2 Fora do escopo

- Envio de qualquer dado à SEFAZ ou a terceiros (o sistema só lê arquivos locais).
- Cálculo de multa, juros ou correção monetária.
- Estados além da Bahia (os layouts suportados são os da SEFAZ-BA).
- Notas que estão no DAE mas ausentes do mapa (sentido inverso da conciliação), excluído por decisão do negócio.
- Assinatura digital ou verificação de integridade dos documentos de entrada.

## 6. Regras de negócio

| ID | Regra |
|---|---|
| RN-01 | Uma nota está **conciliada** quando o seu número (sem pontuação e sem zeros à esquerda) aparece no campo "Notas Fiscais" de algum DAE processado. |
| RN-02 | A verificação de pagamentos considera apenas DAEs de receita **1145** (ICMS Antecipação Tributária) e **2175** (ICMS Antecipação Parcial). |
| RN-03 | Pagamento e parcela são confirmados pelo **valor principal** (diferença menor que R$ 0,01) **e pelo período**: a referência do DAE contra a referência do pagamento, ou contra o mês/ano da **Data de Ocorrência** do parcelamento (não da data de vencimento). |
| RN-04 | No cruzamento Entradas × lista de notas, a chave é **mês de lançamento + número da nota**. A data do relatório de Entradas é a de lançamento, não a de emissão. |
| RN-05 | A comparação de valores Entradas × notas é **exata ao centavo** (sem tolerância); a diferença é exibida. |
| RN-06 | Por nota, prefere-se a linha **ICMS** das Entradas; a linha **ST/AT** só é usada na falta dela. Nunca se somam as duas. |
| RN-07 | Na verificação de créditos, ficam de fora **calçados em geral (NCM capítulo 64)** e **bolsas, mochilas e carteiras (NCM 4202)**. O critério é o NCM, não a descrição. |
| RN-08 | **Valor Pago** de uma nota = Σ(VlTotItem × AliqInt do item) − Σ VlCredEmpr, usando a alíquota de cada item e não uma alíquota fixa. |
| RN-09 | Uma informação de pagamento em célula mesclada da planilha de DAEs vale para **todas as notas do bloco** (um DAE pode quitar várias notas). |
| RN-10 | Toda nota sem correspondência é **listada e sinalizada**, nunca descartada em silêncio. |
| RN-11 | Relatórios são agrupados **Ano → Mês**, com o mês por extenso, e gerados apenas quando o usuário pede. |

## 7. Premissas e restrições

- **Premissas:** os arquivos de entrada são os exportados pela SEFAZ-BA e pelo sistema fiscal do escritório, sem edição estrutural; o usuário tem acesso local aos arquivos do cliente.
- **Restrições:** Windows 10/11; uso individual em estação de trabalho; dados fiscais sigilosos (LGPD e sigilo fiscal) não podem sair da máquina; sem orçamento para serviços em nuvem.

## 8. Riscos de negócio

| Risco | Impacto | Mitigação |
|---|---|---|
| Mudança de layout dos documentos da SEFAZ-BA | Leitura errada ou vazia | Extração por posição e rótulos tolerantes; testes com amostras de anos diferentes; nenhuma nota descartada em silêncio (RN-10) |
| Nota classificada errada ("igual" em vez de "diferente") | Defesa fiscal incorreta | Comparação exata ao centavo, coluna Diferença e conferência com casos reais antes de cada versão |
| Vazamento de dados de cliente | Legal e reputacional | Processamento 100% local; o repositório não guarda arquivos de clientes |
| Executável sem assinatura digital | Alerta do Windows SmartScreen | Orientação no README; distribuição só pelo release oficial |

## 9. Benefícios esperados

- Menos horas por fiscalização e mais clientes atendidos pela mesma equipe.
- Respostas à fiscalização mais completas: cada nota com DAE, valor, data e número de pagamento.
- Achados que a conferência manual não pegava (exemplo real: notas que sumiam da lista por causa de um número de 3 dígitos na descrição).

## 10. Aprovação

| Papel | Nome | Data | Assinatura |
|---|---|---|---|
| Responsável pelo negócio | Anderson | | |
