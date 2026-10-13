# 📐 Spec: Critérios de Prontidão e Qualidade da Análise Tributária de ICMS

Esta especificação define o padrão executivo e os gabaritos de validação técnica que todo parecer, relatório de auditoria ou planejamento de ICMS deve apresentar.

## 1. Quadro-Resumo de Diagnóstico Operacional

Toda análise de ICMS deve apresentar a seguinte matriz estruturada no cabeçalho da entrega:

| Operação / NCM | Origem / Destino | Regime Tributário | Alíquota APLICADA | Alíquota CORRETA | Status / Risco |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **8471.30.12** | SP -> RJ | Normal | 12% | 4% (Importado) | ⚠️ Passivo Alto |
| **2202.10.00** | MG -> BA | ICMS-ST | MVA 40% | MVA Ajust. 52.3%| 🔴 Autuação ICMS-ST |
| **3926.90.90** | PR -> RS | DIFAL Cons. Final | Base Simples | Base Dupla | 🟡 Ajuste de Cálculo |

## 2. Estrutura Padrão da Ficha de Oportunidade ou Passivo
Cada achado fiscal deve conter obrigatoriamente os seguintes campos:

```markdown
### [ICMS-AUD-001] Divergência na Base de Cálculo do DIFAL em Operações Interestaduais
- **Impacto Financeiro Estivado:** R$ 150.000,00 (Últimos 5 anos)
- **Classificação:** Passivo Fiscal / Oportunidade de Recuperação
- **Estados Envolvidos:** Remetente (SP) -> Destinatário (GO)
- **Base Legal:** Lei Complementar nº 190/2022 e RICMS/GO Art. X

#### Descrição da Inconsistência
O estabelecimento aplicou o cálculo do Diferencial de Alíquota sem considerar a inclusão do próprio imposto na sua base de cálculo ("base dupla"), em desacordo com a legislação do Estado de destino.

#### Memória de Cálculo

$$Valor_{Base} = \frac{Valor_{Operação} - ICMS_{Origem}}{1 - ALIQ_{Destino}}$$

$$DIFAL = (Valor_{Base} \times ALIQ_{Destino}) - ICMS_{Origem}$$

#### Recomendação Corretiva
1. Retificar a EFD-ICMS/IPI dos períodos fiscais não decaídos.
2. Atualizar as tabelas de tributação do sistema fiscal para que o cálculo da base dupla ocorra de forma automatizada.