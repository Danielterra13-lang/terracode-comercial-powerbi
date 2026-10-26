"""Medidas DAX do modelo TerraCode Comercial.

Cada item: (pasta, nome, dax, formato, descrição[, dataCategory])
Formato começando com "=" vira formatStringDefinition (format string dinâmica).
"""
FECH = "TREATAS(VALUES(Calendario[Data]), Negocios[data_fechamento_dia]), REMOVEFILTERS(Calendario), REMOVEFILTERS('Eixo Meta')"
# O eixo do gráfico Meta vs Realizado filtra a calendário por mês; nas medidas que deslocam datas
# esse filtro precisa sair junto, senão o deslocamento cruza com o mês original e zera.
SEM_EIXO = "REMOVEFILTERS('Eixo Meta')"
BRL, PCT, INT = "\\R\\$ #,0", "0.0%", "#,0"

MEDIDAS = [
 ("1. Volume","Leads","COUNTROWS(Negocios)",INT,"Negócios criados no período (data de criação)."),
 ("1. Volume","Em aberto",'CALCULATE(COUNTROWS(Negocios), Negocios[Status] = "Em aberto")',INT,"Negócios criados no período que ainda não foram fechados."),
 ("1. Volume","Vendas",f'CALCULATE(COUNTROWS(Negocios), Negocios[Status] = "Ganho", {FECH})',INT,"Negócios ganhos no período (data de fechamento)."),
 ("1. Volume","Perdidos",f'CALCULATE(COUNTROWS(Negocios), Negocios[Status] = "Perdido", {FECH})',INT,"Negócios perdidos ou desqualificados no período (data de fechamento)."),
 ("2. Receita","Receita",f"CALCULATE(SUM(Negocios[Valor]), {FECH})",BRL,"Valor dos negócios ganhos no período (data de fechamento)."),
 ("2. Receita","Ticket médio","DIVIDE([Receita], [Vendas])",BRL,"Receita dividida pela quantidade de vendas."),
 ("2. Receita","Desconto médio",f'CALCULATE(AVERAGE(Negocios[Desconto]), Negocios[Status] = "Ganho", {FECH})',PCT,"Desconto médio concedido nas vendas do período."),
 ("2. Receita","Receita acumulada no ano",f"CALCULATE([Receita], DATESYTD(Calendario[Data]), {SEM_EIXO})",BRL,None),
 ("3. Conversão","Vendas da coorte",'CALCULATE(COUNTROWS(Negocios), Negocios[Status] = "Ganho")',INT,"Dos leads criados no período, quantos viraram venda (em qualquer data)."),
 ("3. Conversão","Perdidos da coorte",'CALCULATE(COUNTROWS(Negocios), Negocios[Status] = "Perdido")',INT,None),
 ("3. Conversão","Conversão da coorte","DIVIDE([Vendas da coorte], [Leads])",PCT,"Percentual dos leads criados no período que viraram venda. Meses recentes ainda têm negócios em aberto, então a taxa tende a subir."),
 ("3. Conversão","Conversão do período","DIVIDE([Vendas], [Leads])",PCT,"Vendas fechadas no período sobre leads criados no período. Visão operacional: mistura coortes, use com cuidado."),
 ("3. Conversão","Win rate","DIVIDE([Vendas da coorte], [Vendas da coorte] + [Perdidos da coorte])",PCT,"Entre os negócios da coorte que já foram decididos, quantos foram ganhos."),
 ("3. Conversão","Ciclo de venda (mediana, dias)",f'CALCULATE(MEDIAN(Negocios[Ciclo (dias)]), Negocios[Status] = "Ganho", {FECH})',"#,0.0","Mediana de dias entre criação e fechamento das vendas do período."),
 ("3. Conversão","Negócios na fase",
  """VAR _fase = MAX('Fase Funil'[Ordem])
RETURN
    IF(
        _fase = 7,
        [Vendas da coorte],
        CALCULATE(COUNTROWS(Negocios), Negocios[ordem_etapa_maxima] >= _fase)
    )""",INT,"Leads da coorte que chegaram pelo menos até a fase. Use com 'Fase Funil'[Fase] no eixo."),
 ("3. Conversão","% do topo do funil","DIVIDE([Negócios na fase], CALCULATE([Negócios na fase], 'Fase Funil'[Ordem] = 1, REMOVEFILTERS('Fase Funil')))",PCT,None),
 ("4. Metas","Meta","SUM(Metas[Meta (valor)])",BRL,"Meta de receita do período."),
 ("4. Metas","% da meta","DIVIDE([Receita], [Meta])",PCT,None),
 ("4. Metas","Gap da meta","[Receita] - [Meta]",BRL,"Positivo: acima da meta. Negativo: quanto falta."),
 ("4. Metas","Meta acumulada no ano",f"CALCULATE([Meta], DATESYTD(Calendario[Data]), {SEM_EIXO})",BRL,None),
 ("4. Metas","% da meta no ano","DIVIDE([Receita acumulada no ano], [Meta acumulada no ano])",PCT,None),
 ("5. Comparativos","Receita ano anterior","CALCULATE([Receita], SAMEPERIODLASTYEAR(Calendario[Data]))",BRL,None),
 ("5. Comparativos","Var. receita vs ano anterior","DIVIDE([Receita] - [Receita ano anterior], [Receita ano anterior])",PCT,None),
 ("5. Comparativos","Leads ano anterior","CALCULATE([Leads], SAMEPERIODLASTYEAR(Calendario[Data]))",INT,None),
 ("5. Comparativos","Var. leads vs ano anterior","DIVIDE([Leads] - [Leads ano anterior], [Leads ano anterior])",PCT,None),
 ("5. Comparativos","Vendas ano anterior","CALCULATE([Vendas], SAMEPERIODLASTYEAR(Calendario[Data]))",INT,None),
 ("5. Comparativos","Var. vendas vs ano anterior","DIVIDE([Vendas] - [Vendas ano anterior], [Vendas ano anterior])",PCT,None),
 ("5. Comparativos","Ticket médio ano anterior","CALCULATE([Ticket médio], SAMEPERIODLASTYEAR(Calendario[Data]))",BRL,None),
 ("5. Comparativos","Var. ticket vs ano anterior","DIVIDE([Ticket médio] - [Ticket médio ano anterior], [Ticket médio ano anterior])",PCT,None),
 ("5. Comparativos","Conversão da coorte ano anterior","CALCULATE([Conversão da coorte], SAMEPERIODLASTYEAR(Calendario[Data]))",PCT,None),
 ("6. Perdas","% das perdas","DIVIDE([Perdidos], CALCULATE([Perdidos], REMOVEFILTERS('Motivo Perda')))",PCT,"Participação do motivo no total de perdas do período."),
 ("7. Atendimento","Conversas","SUM(Conversas[qtd_conversas])",INT,"Conversas iniciadas no canal de mensagens."),
 ("8. Apoio","Data de referência","CALCULATE(MAX(Negocios[data_criacao_dia]), REMOVEFILTERS())","dd/mm/yyyy","Última data com dados. Substitui TODAY(), que deixava o painel vazio com base estática."),
]

# ------------------------------------------------------------ textos e cores
TXT = "9. Textos e cores"
def _var_txt(var, base, sufixo="vs ano anterior"):
    return f"""VAR _v = [{var}]
RETURN
    IF(
        ISBLANK([{base}]),
        "sem base para comparar",
        IF(_v >= 0, "▲ ", "▼ ") & FORMAT(ABS(_v), "0.0%") & " {sufixo}"
    )"""
def _var_cor(var, base):
    return f'IF(ISBLANK([{base}]), "#8A8A8A", IF([{var}] >= 0, "#2E7D5B", "#C8553D"))'
for rot, var, base in [("receita", "Var. receita vs ano anterior", "Receita ano anterior"),
                       ("vendas", "Var. vendas vs ano anterior", "Vendas ano anterior"),
                       ("leads", "Var. leads vs ano anterior", "Leads ano anterior"),
                       ("ticket", "Var. ticket vs ano anterior", "Ticket médio ano anterior")]:
    MEDIDAS.append((TXT, f"Texto var {rot}", _var_txt(var, base), None, None))
    MEDIDAS.append((TXT, f"Cor var {rot}", _var_cor(var, base), None, None))
MEDIDAS += [
 (TXT, "Texto var conversão", """VAR _atual = [Conversão da coorte]
VAR _anterior = [Conversão da coorte ano anterior]
VAR _pp = (_atual - _anterior) * 100
RETURN
    IF(
        ISBLANK(_anterior),
        "sem base para comparar",
        IF(_pp >= 0, "▲ ", "▼ ") & FORMAT(ABS(_pp), "0.0") & " p.p. vs ano anterior"
    )""", None, None),
 (TXT, "Cor var conversão", 'IF(ISBLANK([Conversão da coorte ano anterior]), "#8A8A8A", IF([Conversão da coorte] >= [Conversão da coorte ano anterior], "#2E7D5B", "#C8553D"))', None, None),
 (TXT, "Texto gap da meta", """VAR _gap = [Gap da meta]
RETURN
    IF(
        ISBLANK([Meta]),
        "sem meta no período",
        IF(
            _gap >= 0,
            "R$ " & FORMAT(_gap / 1000, "#,0") & " mil acima da meta",
            "faltam R$ " & FORMAT(-_gap / 1000, "#,0") & " mil para a meta"
        )
    )""", None, None),
 (TXT, "Cor gap da meta", 'IF([Gap da meta] >= 0, "#2E7D5B", "#C8553D")', None, None),
 (TXT, "Resumo do período", """VAR _ano =
    IF(HASONEVALUE(Calendario[Ano]), FORMAT(SELECTEDVALUE(Calendario[Ano]), "0"), "2024 e 2025")
VAR _pipe =
    IF(
        ISFILTERED(Pipeline[Pipeline]),
        IF(HASONEVALUE(Pipeline[Pipeline]), "pipeline " & SELECTEDVALUE(Pipeline[Pipeline]), "pipelines selecionados"),
        "todos os pipelines"
    )
RETURN
    _ano & ", " & _pipe & ": R$ " & FORMAT([Receita] / 1000000, "#,0.00") & " mi em receita, "
        & FORMAT([% da meta], "0%") & " da meta, " & FORMAT([Vendas], "#,0") & " vendas e "
        & FORMAT([Conversão da coorte], "0.0%") & " de conversão dos leads.\"""", None, None),
 (TXT, "Texto rodapé", '"Dados sintéticos  ·  atualizados até " & FORMAT([Data de referência], "dd/mm/yyyy")', None, None),
 (TXT, "Texto em aberto", 'FORMAT(DIVIDE([Em aberto], [Leads]), "0.0%") & " dos leads criados no período"', None, None),
]

# ------------------------------------------------------- visuais especiais
VIS = "10. Visuais especiais"
MEDIDAS += [
 (VIS, "Fixo meta", f"CALCULATE([Meta], {SEM_EIXO})", BRL, "Meta do período inteiro, repetida em qualquer ponto do eixo."),
 (VIS, "Fixo receita", f"CALCULATE([Receita], {SEM_EIXO})", BRL, None),
 (VIS, "MR YTD meta", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) <= 12, [Meta acumulada no ano])", BRL, "Linha da meta acumulada, só nos meses."),
 (VIS, "MR YTD realizado", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) <= 12, [Receita acumulada no ano])", BRL, None),
 (VIS, "MR Meta", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 13, [Fixo meta])", BRL, "Coluna da meta, na posição 13 do eixo."),
 (VIS, "MR Realizado", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 14, [Fixo receita])", BRL, None),
 (VIS, "MR Base", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 15, MIN([Fixo meta], [Fixo receita]))", BRL, "Parte invisível da coluna de diferença: o menor entre meta e realizado."),
 (VIS, "MR Acima", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 15 && [Fixo receita] >= [Fixo meta], [Fixo receita] - [Fixo meta])", BRL, None),
 (VIS, "MR Abaixo", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 15 && [Fixo receita] < [Fixo meta], [Fixo meta] - [Fixo receita])", BRL, None),
 (VIS, "MR Linha meta", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) >= 13, [Fixo meta])", BRL, "Linha pontilhada no topo da meta."),
 (VIS, "MR Linha realizado", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) >= 14, [Fixo receita])", BRL, None),
 (VIS, "MR Pt meta", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 13, [Fixo meta])", BRL, "Ponto invisível acima da coluna, só para carregar o rótulo fora da barra."),
 (VIS, "MR Pt realizado", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 14, [Fixo receita])", BRL, None),
 (VIS, "MR Pt diferença", "IF(SELECTEDVALUE('Eixo Meta'[Ordem]) = 15, MAX([Fixo meta], [Fixo receita]))",
  '= """" & IF([Fixo receita] >= [Fixo meta], "+", "-") & "R$ " & FORMAT(ABS([Fixo receita] - [Fixo meta]) / 1000000, "0.00") & " mi (" & FORMAT(DIVIDE([Fixo receita], [Fixo meta]) - 1, "+0.0%;-0.0%") & ")" & """"',
  "Ponto acima da coluna de diferença; o rótulo mostra a diferença em R$ e %."),
 (VIS, "MR Cor diferença", 'IF([Fixo receita] >= [Fixo meta], "#2E7D5B", "#C8553D")', None,
  "Cor do rótulo da diferença. Usa os valores fixos porque na coluna da diferença não há data no contexto."),
 (VIS, "MR eixo", "MAX([Fixo meta], [Fixo receita]) * 1.15", BRL, "Fim do eixo Y, com folga para os rótulos acima das colunas."),
 (VIS, "MR Rótulo diferença", """VAR _d = [Fixo receita] - [Fixo meta]
RETURN
    IF(_d >= 0, "+", "-") & "R$ " & FORMAT(ABS(_d) / 1000000, "#,0.00") & " mi  ("
        & FORMAT(DIVIDE([Fixo receita], [Fixo meta]) - 1, "+0.0%;-0.0%") & ")\"""", None, None),
 (VIS, "Receita mês anterior", f"CALCULATE([Receita], DATEADD(Calendario[Data], -1, MONTH), {SEM_EIXO})", BRL, None),
 (VIS, "Var. receita vs mês anterior", "DIVIDE([Receita] - [Receita mês anterior], [Receita mês anterior])", PCT, None),
 (VIS, "Texto var mês anterior", _var_txt("Var. receita vs mês anterior", "Receita mês anterior", "vs mês anterior"), None, None),
 (VIS, "Cor var mês anterior", _var_cor("Var. receita vs mês anterior", "Receita mês anterior"), None, None),
 (VIS, "Receita dia anterior", f"CALCULATE([Receita], DATEADD(Calendario[Data], -1, DAY), {SEM_EIXO})", BRL, None),
 (VIS, "Var. receita vs dia anterior", "DIVIDE([Receita] - [Receita dia anterior], [Receita dia anterior])", PCT, None),
 (VIS, "Texto var dia anterior", _var_txt("Var. receita vs dia anterior", "Receita dia anterior", "vs dia anterior"), None, None),
 (VIS, "Cor var dia anterior", _var_cor("Var. receita vs dia anterior", "Receita dia anterior"), None, None),
 (VIS, "Período (texto)", """VAR _ini = MIN(Calendario[Data])
VAR _fim = MAX(Calendario[Data])
RETURN
    SWITCH(
        TRUE(),
        _ini = _fim, FORMAT(_ini, "dd/mm/yyyy") & " (" & FORMAT(_ini, "dddd") & ")",
        FORMAT(_ini, "yyyymm") = FORMAT(_fim, "yyyymm"), FORMAT(_ini, "mmmm \\d\\e yyyy"),
        FORMAT(_ini, "dd/mm/yy") & " a " & FORMAT(_fim, "dd/mm/yy")
    )""", None, None),
 (VIS, "Calendário célula", """VAR _dia = SELECTEDVALUE(Calendario[Dia])
VAR _v = [Receita]
RETURN
    IF(
        NOT ISBLANK(_dia),
        _dia & UNICHAR(10) & IF(ISBLANK(_v), "-", "R$ " & FORMAT(_v / 1000, "#,0.0") & " mil")
    )""", None, "Número do dia + receita, para a matriz de calendário."),
 (VIS, "Rótulo receita", """VAR _v = [Receita]
RETURN
    IF(
        _v >= 1000000,
        "R$ " & FORMAT(_v / 1000000, "#,0.00") & " mi",
        "R$ " & FORMAT(_v / 1000, "#,0") & " mil"
    )""", None, None),
 (VIS, "Rótulo % perdas", 'FORMAT([% das perdas], "0.0%")', None, None),
 (VIS, "Rótulo conversão", 'FORMAT([Conversão da coorte], "0.0%")', None, None),
 (VIS, "SVG meta", """VAR _p = [% da meta]
VAR _cor =
    IF(_p >= 1, "%232E7D5B", IF(_p >= 0.8, "%23D9A441", "%23C8553D"))
VAR _n = 60
VAR _ativos = ROUND(MIN(_p, 1) * _n, 0)
VAR _marcas =
    CONCATENATEX(
        GENERATESERIES(0, _n - 1, 1),
        "<rect x='98' y='6' width='4' height='" & IF(MOD([Value], 5) = 0, 18, 11)
            & "' rx='2' fill='" & IF([Value] < _ativos, _cor, "%23E4E1D8")
            & "' transform='rotate(" & [Value] * 6 & " 100 100)'/>",
        ""
    )
RETURN
    IF(
        NOT ISBLANK(_p),
        "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'>"
            & _marcas
            & "<text x='100' y='110' text-anchor='middle' font-family='Bahnschrift, Segoe UI' font-size='38' font-weight='600' fill='%231A1A1A'>"
            & FORMAT(_p * 100, "0") & "%25</text>"
            & "<text x='100' y='136' text-anchor='middle' font-family='Segoe UI' font-size='13' fill='%236B6B6B'>da meta</text></svg>"
    )""", None, "Velocímetro de meta em SVG, escrito do zero. Exibido como imagem num cartão.", "ImageUrl"),
]

# Comparativo entre dois períodos com hastes (técnica das barras de erro)
def _cmp(tab, suf, ant, atu, var):
    o = f"SELECTEDVALUE('{tab}'[Ordem])"
    return [
     (VIS, f"Cmp {suf} valor", f"SWITCH({o}, 1, [{ant}], 3, [{atu}])", BRL, f"Colunas do comparativo. Use com '{tab}'[Período] no eixo."),
     (VIS, f"Cmp {suf} linha", f"""VAR _m = MAX([{ant}], [{atu}])
RETURN
    IF(_m > 0, _m * 1.35)""", BRL, "Linha horizontal acima das colunas."),
     (VIS, f"Cmp {suf} eixo", f"MAX([{ant}], [{atu}]) * 1.6", BRL, "Fim do eixo Y, para sobrar espaço para a linha e o rótulo."),
     (VIS, f"Cmp {suf} variação", f"IF({o} = 2 && NOT ISBLANK([{ant}]), [Cmp {suf} linha])",
      f'= """" & FORMAT([{var}], "▲ +0.0%;▼ -0.0%;0.0%") & """"', "Ponto no meio da linha; o rótulo mostra a variação (format string dinâmica)."),
     (VIS, f"Cmp {suf} anterior", f"IF({o} = 1, [Cmp {suf} linha])", BRL, "Ponto sobre a primeira coluna; a barra de erro desenha a haste até o topo dela."),
     (VIS, f"Cmp {suf} atual", f"IF({o} = 3, [Cmp {suf} linha])", BRL, "Ponto sobre a última coluna; a barra de erro desenha a haste até o topo dela."),
    ]
MEDIDAS += _cmp("Comparativo", "mês", "Receita mês anterior", "Receita", "Var. receita vs mês anterior")
MEDIDAS += _cmp("Comparativo Dia", "dia", "Receita dia anterior", "Receita", "Var. receita vs dia anterior")
