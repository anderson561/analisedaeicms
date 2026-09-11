---
name: performance-optimization-orchestrator
description: Workflow operacional em 4 fases para identificação de gargalos, profiling, reescrita de código/queries e validação por testes de carga.
---

# 🔄 Workflow: Orquestração de Otimização de Performance

Este fluxo guia o especialista em performance passo a passo na resolução de problemas de latência, vazão ou uso excessivo de recursos.

## 📋 Fase 1: Coleta de Baseline e Telemetria
1. **Definição de SLAs/SLOs:** Estabeleça a meta alvo (ex: Latência p99 < 50ms, Throughput > 5.000 RPS, CPU < 70%).
2. **Medição Atual (Baseline):** Execute testes de carga (k6, Locust, wrk) para capturar as métricas atuais do sistema sob estresse.
3. **Captura de Traces e Profiling:** Gere Flame Graphs de CPU e Heap, e colete métricas de APM (Datadog, Prometheus/Grafana, Jaeger).

## 🔬 Fase 2: Análise de Causa Raiz e Identificação de Gargalo
1. **Classificação do Limite:** Identifique se o sistema está limitado por **CPU** (CPU-bound), **Memória** (Memory/GC-bound), **I/O de Rede/Disco** (I/O-bound) ou **Locks/Contenção** (Lock-bound).
2. **Deep-Dive de Código/Dados:**
   * Se Banco de Dados: Execute `EXPLAIN (ANALYZE, BUFFERS)` para avaliar leituras de disco, ordenamentos em memória e scans indevidos.
   * Se Código/Aplicação: Analise as funções com maior tempo de retenção no Flame Graph.
   * Se Data Pipeline: Avalie o particionamento, tamanho de blocos, taxa de escrita e tempo de GC.

## 🧠 Fase 3: Aplicação de Otimizações Direcionadas
1. **Nível Arquitetural/Dados:**
   * Adicionar índices faltantes ou refatorar a estrutura do banco de dados.
   * Implementar estratégias de Caching (Redis/In-Memory) com invalidação correta.
   * Vetorizar chamadas e utilizar buffers de I/O maiores.
2. **Nível de Código:**
   * Reduzir alocações de memória temporárias e reusar buffers/objetos.
   * Converter loops ineficientes para complexidade algorítmica inferior.
   * Paralelizar tarefas independentes com uso eficiente de Thread Pools.

## 📄 Fase 4: Re-benchmarking, Validação e Relatório
1. **Teste de Carga Comparativo:** Execute exatamente o mesmo cenário de carga da Fase 1.
2. **Validação do p99 e Throughput:** Confirme se as metas foram atingidas e se não houve vazamento de memória durante a bateria de testes.
3. **Emissão da Spec de Performance:** Entregue o relatório com a comparação de desempenho Antes vs. Depois.