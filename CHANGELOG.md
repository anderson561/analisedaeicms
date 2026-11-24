# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento semântico.

## [Não lançado]

### Adicionado
- Documentação do projeto em `docs/`: BRD (negócio), FRD (funcional), SRS (especificação de software) e TRD (técnico).

### Corrigido
- README desatualizado: descrevia só a conciliação de notas, dizia que os relatórios eram dois `.xlsx` salvos automaticamente e trazia um comando de testes que falha fora da venv. Agora lista as 7 abas, os relatórios sob demanda (Excel/PDF) e o comando correto.

### Removido
- Nomes reais de cliente dos dados de teste (substituídos por nomes fictícios).
- Pastas de backup `agents.bkp/` e `claude.bkp/` do repositório (continuam apenas localmente, agora no `.gitignore`).

## [1.1.0] - 2026-11-09

### Adicionado
- Aba **Analisar Apuração**: cruza relatório de créditos + lista de antecipação + planilha de DAEs; acrescenta às tabelas de notas (sem Data Lançamento e UF) o Valor Pago (Σ VlTotItem × AliqInt − VlCredEmpr) e a Informação Norte do DAE; relatórios Excel/PDF. Suíte: 180 → 194 testes.
- Aba **Verificar Créditos**: soma VlLiqItem, VlCredEmpr, VlBcAntParc e VlCredAud por nota da lista de notas fiscais/itens, excluindo calçados (NCM 64) e bolsas, mochilas e carteiras (NCM 4202); relatórios Excel/PDF com totais por mês e geral. Suíte: 167 → 180 testes.
- Aba **Pagamentos Notas**: cruza o relatório de Entradas (ICMS / ST-AT) com a lista de notas fiscais/itens por mês de lançamento + número da nota, comparação exata ao centavo, com relatórios Excel/PDF de Valores Iguais, Valores Diferentes (coluna Diferença) e Notas Não Encontradas.
- Aba **Conciliação vs DAE**: concilia o relatório de Pagamentos Notas (`.xlsx`, todas as abas) contra DAEs em PDF; devolve os dados do DAE e o arquivo de origem, ou informa que a nota não está em nenhum DAE. Relatórios Excel/PDF de encontradas e não encontradas.
- Coluna "Arquivo do DAE" nos relatórios de notas conciliadas.
- Nomes de mês por extenso (Janeiro…Dezembro) em todos os relatórios.
- Testes: suíte passou de 156 para 167 testes.

### Corrigido
- Leitura da lista de notas fiscais/itens: quando a descrição tinha um número de 3 dígitos (ex.: "TENIS TRIUNFO / 835"), esse número era tomado pelo nº do item e a linha era descartada. Agora o item é o número de 3 dígitos seguido dos 11 valores da linha. No PDF de 2024 eram lidos 3.235 de 3.728 itens; no de 2021, 3.175 de 3.495 (23 notas sumiam da aba Pagamentos Notas).
- Valores de Entradas não informados na aba Pagamentos Notas: o cruzamento usava o mês de emissão, mas a data do relatório de Entradas é a de lançamento (DataLcto). Passou a cruzar por mês de lançamento; linhas de Entradas com valor embaralhado por sobreposição de colunas no PDF são recompostas por Base + Isentas + Outras.
- Leitor de relatório reconhece a coluna "Número do Documento".

### Removido
- Cópias locais do scaffold de agentes (`.agents/`, `.claude/`); o ecossistema global em `~/.claude/agents` é a fonte única. Backups em `agents.bkp/` e `claude.bkp/`.
