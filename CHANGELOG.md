# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento semântico.

## [Não lançado]

### Adicionado
- Aba **Pagamentos Notas**: cruza o relatório de Entradas (ICMS / ST-AT) com a lista de notas fiscais/itens por mês de lançamento + número da nota, comparação exata ao centavo, com relatórios Excel/PDF de Valores Iguais, Valores Diferentes (coluna Diferença) e Notas Não Encontradas.
- Aba **Conciliação vs DAE**: concilia o relatório de Pagamentos Notas (`.xlsx`, todas as abas) contra DAEs em PDF; devolve os dados do DAE e o arquivo de origem, ou informa que a nota não está em nenhum DAE. Relatórios Excel/PDF de encontradas e não encontradas.
- Coluna "Arquivo do DAE" nos relatórios de notas conciliadas.
- Nomes de mês por extenso (Janeiro…Dezembro) em todos os relatórios.
- Testes: suíte passou de 156 para 167 testes.

### Corrigido
- Valores de Entradas não informados na aba Pagamentos Notas: o cruzamento usava o mês de emissão, mas a data do relatório de Entradas é a de lançamento (DataLcto). Passou a cruzar por mês de lançamento; linhas de Entradas com valor embaralhado por sobreposição de colunas no PDF são recompostas por Base + Isentas + Outras.
- Leitor de relatório reconhece a coluna "Número do Documento".

### Removido
- Cópias locais do scaffold de agentes (`.agents/`, `.claude/`); o ecossistema global em `~/.claude/agents` é a fonte única. Backups em `agents.bkp/` e `claude.bkp/`.
