# TerraCode Academy | Painel Comercial

Reconstrução de um painel comercial em Power BI que construí para uma edtech, refeito do zero com dados sintéticos e modelo redesenhado.

A TerraCode Academy é uma escola de tecnologia fictícia com três frentes de venda: **Online**, **Presencial** e **Pós-graduação**. Nenhum dado real foi usado: todos os registros são gerados por `scripts/gerar_dados.py`, com seed fixa.

**[Ver o relatório publicado](https://app.powerbi.com/view?r=eyJrIjoiMWEyOTAwODAtZDdlNS00NjkzLWE0OTAtMjg4NGQxMWNlZGFiIiwidCI6ImQ0Njc3NjUyLTNmZjItNDdkZC04MzdlLWU4NmU3MmE3ZTkzMSJ9)**

## O que tem no relatório

| Página | Perguntas que responde |
|---|---|
| Visão geral | Quanto vendemos, quanto falta para a meta, como está a conversão dos leads |
| Funil e canais | Até onde os leads chegam, quais canais e faixas de lead score convertem |
| Time comercial | Quem está batendo meta, mês a mês, e com que ticket e ciclo |
| Perdas e atendimento | Por que perdemos e em que horário os leads conversam |
| Calendário | Como a receita se distribui nos dias do mês |

Tooltips com velocímetro de meta e comparativos (mês contra mês anterior, dia contra dia anterior) e painel de filtros que abre e fecha.

## Estrutura

```
data/              CSVs gerados (dimensões e fatos)
scripts/           gerar_dados.py: gerador dos dados sintéticos
scripts/pbip/      gerar_modelo.py, medidas.py, gerar_relatorio.py, validar.py
powerbi/           projeto PBIP (modelo em TMDL, relatório em PBIR)
```

## Como gerar os dados

```
cd scripts
python gerar_dados.py
```

Requisitos: Python 3.10+, pandas e numpy. Se o `pyarrow` estiver instalado, o script também gera Parquet.

## Como abrir no Power BI

1. Gere os dados (passo acima)
2. Abra `powerbi/TerraCode Comercial.pbip` no Power BI Desktop
3. Em Transformar dados > Gerenciar parâmetros, aponte `PastaDados` para a pasta `data` deste repositório na sua máquina (terminando com `\`)
4. Atualize

Na primeira abertura o Desktop baixa o visual Deneb da AppSource (precisa de internet).

### Relatório como código

O modelo e o relatório são gerados por scripts em `scripts/pbip`:

```
cd scripts/pbip
python gerar_modelo.py      # tabelas, relacionamentos e medidas (TMDL) + tema
python gerar_relatorio.py   # páginas, tooltips, painel de filtros e indicadores (PBIR)
python validar.py           # confere campos, medidas, navegação e termos proibidos
```

As medidas ficam em `scripts/pbip/medidas.py`, com pasta e descrição de cada uma.

O projeto está no formato PBIP: o modelo fica em TMDL e o relatório em PBIR, ambos em texto e versionáveis.

## Modelo de dados

Star schema com um negócio do CRM por linha na fato principal.

| Tabela | Grão | Linhas |
|---|---|---|
| `fato_negocios` | 1 negócio | ~50,7 mil |
| `fato_metas` | vendedor x mês (com ano) | 278 |
| `fato_conversas` | dia x hora | ~13,7 mil |
| `dim_calendario` | dia, com feriados nacionais e dia útil | 731 |
| `dim_pipeline` | Online, Presencial, Pós-graduação | 3 |
| `dim_etapa` | etapa por pipeline, com ordem e status | 27 |
| `dim_vendedor` | vendedor, com data de entrada e saída | 15 |
| `dim_fonte` | fonte técnica do CRM + canal agrupado | 11 |
| `dim_motivo_perda` | motivo + categoria | 13 |
| `dim_produto` | produto + preço de lista | 10 |
| `dim_forma_pagamento` | forma de pagamento | 5 |

### Decisões

- **Uma fato no lugar de cinco recortes.** Leads, ganhos, perdidos, fases e fluxos são o mesmo objeto (o negócio) em estados diferentes. Com uma tabela só, todas as métricas usam a mesma base e o mesmo corte de data.
- **Duas datas na fato.** `data_criacao` liga no calendário por relacionamento; `data_fechamento` é aplicada nas medidas com `TREATAS`. Isso permite separar conversão de período e conversão de coorte.
- **Etapa atual e etapa máxima.** `id_etapa` diz onde o negócio está; `id_etapa_maxima` diz até onde chegou. É o que viabiliza um funil real, inclusive para perdidos.
- **Motivo de perda principal + contagem.** O CRM permite marcar vários motivos. A fato guarda o principal e `qtd_motivos_perda`, sem tabela ponte. Mais simples e suficiente para a análise.
- **Metas com ano.** Grão vendedor x mês, ligado ao calendário pelo primeiro dia do mês.
- **Lead score nulo continua nulo.** Negócios criados à mão pelo vendedor não passam pelo scoring, e tratar como zero distorceria médias e faixas de temperatura.
- **Sem dado pessoal.** O painel não precisa de nome ou documento de cliente. O identificador é `NEG-000001`.
- **Duas visões de conversão.** *Conversão da coorte* (dos leads criados no período, quantos viraram venda) e *conversão do período* (vendas fechadas sobre leads criados no mesmo período). O painel original só tinha a segunda, que mistura coortes.
- **Funil comparável entre pipelines.** Cada pipeline tem etapas com nomes próprios; a coluna `fase_funil` e a tabela `Fase Funil` padronizam em seis fases + ganho.
- **Sem `TODAY()`.** A medida *Data de referência* usa a última data com dados.
- **Data de fechamento sem relação inativa.** As medidas por fechamento usam `TREATAS` em vez de `USERELATIONSHIP`. Negócios em aberto não têm data de fechamento, e uma relação (mesmo inativa) com chave vazia cria a linha "(Em branco)" no calendário e nos filtros.
- **Um visual customizado só.** O original usava seis. Ficou apenas o Deneb (certificado), nas barras com gradiente e cantos arredondados, que o nativo não faz. Meta vs realizado, velocímetro de meta, comparativos e calendário são nativos: tabelas auxiliares, colunas empilhadas e SVG gerado por DAX.
- **Meta vs realizado num eixo só.** Uma tabela auxiliar junta os 12 meses com Meta, Realizado e uma posição vazia, relacionada a `Calendario[mes]`. As linhas mostram o acumulado no ano e as colunas no fim mostram o total e a diferença. Como esse eixo filtra a calendário (e, por ela, a data de criação), as medidas por data de fechamento e as que deslocam datas removem o filtro do eixo explicitamente.
- **Comparativo com hastes.** Comparação entre dois períodos com colunas, uma linha acima delas e hastes desenhadas por barras de erro, com a variação numa categoria vazia no meio (rótulo via format string dinâmica).
- **Python fora do Power BI.** Geração e tratamento ficam no script versionado; o Power BI só consome CSV.

## O que o painel original tinha de problema

Achados do diagnóstico da versão anterior, que motivaram o redesenho:

1. **Sete planilhas que eram a mesma tabela.** Exports diferentes do mesmo objeto do CRM, cada um com suas colunas e tratamentos.
2. **Datas de corte desalinhadas.** A base de ganhos ia até outubro e as de leads e perdidos paravam em agosto. A taxa de conversão dos meses finais saía inflada.
3. **Pipeline definido pelo nome do vendedor.** No Power Query, o pipeline de cada lead era atribuído por uma lista fixa de nomes. Cinco vendedores fora da lista deixaram cerca de 1,1 mil leads sem pipeline, sumindo dos filtros.
4. **Espaço no final de uma string quebrava o mapeamento de canal.** A mesma fonte existia com e sem espaço no fim; só uma versão era mapeada, e 688 leads caíam em "outros".
5. **Meta ligada ao calendário pelo nome do mês.** Sem ano, com "agosto" em minúsculo, e numa relação muitos-para-muitos bidirecional. Janeiro do ano seguinte somaria com o anterior.
6. **Conversão misturando coortes.** Vendas por data de fechamento divididas por leads por data de criação, incluindo vendas de leads criados no ano anterior.
7. **Negócio criado no ato da venda inflando a conversão por canal.** Negócios sem fonte (criados à mão pelo vendedor) convertiam perto de 50%, contra cerca de 5% do formulário do site.
8. **Lead score nulo virando zero.** Puxava as medianas para baixo e jogava esses negócios na faixa "Frio".
9. **Medidas com `TODAY()`.** Com base estática, os cards de "hoje" ficavam vazios.
10. **Relatório pesado.** 17 páginas, sendo três idênticas mudando só o filtro de pipeline, 10 páginas de tooltip e 6 visuais customizados somando cerca de 20 MB.
11. **Dados pessoais sem necessidade.** Nome completo e CPF de clientes carregados no modelo.

## Bugs da reconstrução

O que quebrou no caminho e por quê. Cada um virou uma regra no `validar.py` ou no gerador.

1. **Format string dinâmica fora de ordem.** No TMDL, `formatStringDefinition` é um objeto filho da medida e precisa vir depois de todas as propriedades. Com `displayFolder` depois dele, o Desktop recusava abrir o projeto com erro de recuo.
2. **Referência cíclica na atualização.** As tabelas auxiliares (eixo do meta vs realizado, fases do funil, comparativos) começaram como tabelas calculadas em DAX. Uma delas relacionada à calendário, que é importada, travava a atualização inteira. Viraram tabelas fixas em Power Query (`#table`).
3. **Cache que não aceita a mudança.** Trocar o tipo de partição de uma tabela já existente esbarra no `cache.abf` do Desktop. A solução foi descartar o cache e deixar o modelo ser montado de novo a partir dos arquivos.
4. **Painel de filtros vazio.** No PBIR, a posição dos visuais dentro de um grupo é relativa ao grupo. Com posições absolutas, os segmentadores foram parar fora da tela e só o fundo branco aparecia.
5. **"Erro ao buscar os dados" no calendário.** Dois campos do mesmo visual com o mesmo nome de exibição ("Dia") quebravam a consulta.
6. **Rótulo da diferença na cor errada.** Na coluna "Diferença" do eixo não existe data no contexto; meta e receita ficavam vazias, o gap dava zero e zero caía no verde. A cor passou a usar os totais do período.
7. **Eixo auxiliar contaminando outras medidas.** O eixo do meta vs realizado filtra a calendário por mês e, por ela, a data de criação. Medidas por data de fechamento e as que deslocam datas (mês anterior, acumulado no ano) precisaram remover esse filtro explicitamente.
8. **"(Em branco)" nos filtros de ano.** Uma relação inativa pela data de fechamento, que é vazia nos negócios em aberto, criava a linha em branco no calendário. Trocada por `TREATAS`.
