---
name: icms-tax-audit-orchestrator
description: Workflow operacional de 4 fases para auditoria fiscal, revisão de parametrizações de ICMS/ICMS-ST e planejamento tributário estadual.
---

# 🔄 Workflow: Orquestração de Auditoria e Planejamento de ICMS

Este fluxo guia o agente passo a passo na revisão fiscal e otimização das operações tributáveis pelo ICMS.

## 📋 Fase 1: Saneamento de Cadastros e Classificação (NCM/CEST)
1. **Auditoria de Cadastros:** Mapeie o cadastro de produtos (NCM, Descrição, CEST, Unidade de Medida).
2. **Triagem de Enquadramento:** Verifique se os produtos estão sujeitos ao regime de Substituição Tributária nos Estados de operação.
3. **Validação do CST/CSOSN e CFOP:** Garanta a coerência entre a natureza da operação (saída, entrada, devolução, transferência) e o código de tributação do ICMS.

## 🔬 Fase 2: Auditoria de Alíquotas, MVA e Benefícios Fiscais
1. **Revisão de Alíquotas Intrastaduais e Interestaduais:** Cheque a aplicação das alíquotas internas vigentes e as regras do FECOEP (Fundo de Combate à Pobreza).
2. **Cálculo da MVA Ajustada:** Recalcule as margens de valor agregado em operações interestaduais com alíquotas diferenciadas.
3. **Checagem de Benefícios Fiscais:** Valide o enquadramento em regimes especiais e a existência de laudos/condicionantes.

## 🧠 Fase 3: Cruzamento de Obrigações Acessórias (SPED vs NF-e)
1. **Conferência EFD-ICMS/IPI:** Cruze as informações dos documentos fiscais de entrada e saída (Bloco C) com os registros de apuração (Bloco E).
2. **Análise do CIAP (Bloco G):** Verifique se o cálculo da fração $1/48$ de crédito sobre bens do ativo imobilizado respeita a proporção de saídas tributadas/isentas.
3. **Reconciliação de Saldos Credores:** Identifique acúmulo de créditos e viabilidade de transferência/ressarcimento (e.g., e-Ressarcimento/CAT 42 em SP).

## 📄 Fase 4: Relatório Executivo e Plano de Ação
Consolidar a auditoria no relatório final contendo:
1. **Resumo Executivo para a Diretoria:** Exposição do passivo potencial ou das oportunidades de recuperação de créditos.
2. **Matriz de Riscos e Oportunidades:** Tabela contendo divergências identificadas, valor do impacto financeiro e fundamentação legal.
3. **Recomendações e Parametrização:** Roteiro técnico com alterações de regras no sistema ERP/SFT para correção de emissões futuras.