---
name: performance-engineering-rules
description: Regras globais de governança, vedações técnicas e restrições inegociáveis para alterações em código e banco de dados focadas em performance.
---

# 📜 Regras Globais: Engenharia de Performance de Software e Dados

## 🎯 Objetivo
Proibir padrões antidesempenho, prevenir degradação de throughput e garantir que nenhum código de alta latência ou consulta ineficiente seja aprovado para ambiente de produção.

## 🚫 Proibições Absolutas (Tolerância Zero)

### 1. Padrão N+1 em Consultas de Banco de Dados
* É terminantemente proibido executar consultas SQL dentro de loops de iteração de código. Exigir o uso de *Eager Loading*, JOINs apropriados ou agrupamento de IDs em lote (`WHERE id IN (...)`).

### 2. I/O Bloqueante em Event Loops Assíncronos
* É proibido executar operações de I/O síncronas/bloqueantes (ex: leitura de arquivo síncrona, chamadas HTTP síncronas) na *thread* principal de Event Loops (Node.js, asyncio, Netty, Tokio).

### 3. Alocação Desordenada de Memória / Unbounded Streams
* Proibido carregar conjuntos inteiros de dados (como arquivos de gigabytes ou tabelas de milhões de linhas) em memória RAM de uma única vez. Exigir streaming, paginação por cursor ou iteradores/generators.

### 4. Consultas SQL Sem Filtro Indexado
* Proibido executar queries `UPDATE` ou `DELETE` sem restrição baseada em chave primária ou índice ativo, bem como queries `SELECT` com wildcard inicial em texto (`LIKE '%termo'`).

## ⚠️ Travas Mínimas de Aceite
1. Nenhuma refatoração de performance pode introduzir regressões na exatidão funcional dos dados (validação por suíte de testes de regressão).
2. Qualquer query crítica com tempo de execução superior a **100ms** em dados representativos deve ser rejeitada e submetida a otimização de plano de execução.