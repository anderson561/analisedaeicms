# 📐 Spec: Critérios de Prontidão e Aceite de Performance (Performance Audit Readiness)

Esta especificação define a estrutura e o padrão de qualidade exigidos para qualquer relatório e entrega de otimização de performance técnica.

## 1. Quadro Comparativo Obrigatório de Performance

Toda entrega de otimização de performance deve apresentar a seguinte matriz consolidada na abertura do documento:

| Métrica / Vetor | Medição Antes (Baseline) | Medição Depois (Otimizado) | Variação (%) | Status do SLA |
| :--- | :--- | :--- | :--- | :--- |
| **Throughput (RPS)** | 1.200 RPS | 8.500 RPS | 🚀 +608% | ✅ Aprovado |
| **Latência p50 (Mediana)** | 45 ms | 8 ms | 🟢 -82% | ✅ Aprovado |
| **Latência p99 (Cauda)** | 850 ms | 35 ms | 🚀 -95% | ✅ Aprovado |
| **Uso de CPU (Sob Carga)**| 98% | 42% | 🟢 -57% | ✅ Aprovado |
| **Allocations / sec** | 4.2 GB/s | 350 MB/s | 🚀 -91% | ✅ Aprovado |

## 2. Estrutura Padrão do Relatório de Gargalo Técnico

Cada gargalo corrigido deve ser documentado no relatório final com os seguintes campos obrigatórios:

```markdown
### [PERF-OPT-001] Alta Latência por Scan Sequencial em Consulta de Vendas
- **Componente:** `Service-Orders / Postgres Database`
- **Impacto:** Latência de p99 elevada em 600ms durante horários de pico.
- **Tipo de Limitação:** I/O e CPU Bound (Banco de Dados)

#### Análise do Plano de Execução Original
```text
Seq Scan on relatorio_vendas  (cost=0.00..185420.00 rows=12500 width=48) 
  Filter: ((data_emissao >= '2026-01-01') AND (status = 'APROVADO'))
  Buffers: shared read=12450