"""Gera o modelo semântico (TMDL) e a casca do relatório (PBIR) do TerraCode Comercial.

Uso: python gerar_modelo.py   (depois rode gerar_relatorio.py)
Os arquivos de tabela são sobrescritos; o cache local do Desktop (.pbi) não é tocado.
"""
import json, uuid, shutil
from pathlib import Path
from medidas import MEDIDAS

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "powerbi"
NOME = "TerraCode Comercial"
SM, RP = ROOT / f"{NOME}.SemanticModel", ROOT / f"{NOME}.Report"
T = "\t"
PASTA_PADRAO = "C:\\Users\\danie\\Downloads\\Terracode\\terracode-academy\\data\\"

def w(path, txt):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt, encoding="utf-8")
def q(nome):
    simples = nome.isascii() and nome.replace("_", "a").isalnum() and not nome[0].isdigit()
    return nome if simples else f"'{nome}'"
def guid_estavel(*partes):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "terracode|" + "|".join(partes)))

# ------------------------------------------------------------- tabelas CSV
I, N, S, DT, D, B = "Int64.Type", "type number", "type text", "type datetime", "type date", "type logical"
TMDL = {I: "int64", N: "double", S: "string", DT: "dateTime", D: "dateTime", B: "boolean"}
# coluna: (nome no modelo, coluna no CSV, tipo, oculta, formato, ordenar por [coluna CSV])
TABELAS = {
 "Negocios": dict(arquivo="fato_negocios", cols=[
    ("id_negocio","id_negocio",S,True,None,None),
    ("Data de criação","data_criacao",DT,False,"dd/mm/yyyy hh:nn",None),
    ("Data de fechamento","data_fechamento",DT,False,"dd/mm/yyyy hh:nn",None),
    ("Status","status",S,False,None,None),
    ("id_pipeline","id_pipeline",I,True,None,None),
    ("id_vendedor","id_vendedor",I,True,None,None),
    ("id_fonte","id_fonte",I,True,None,None),
    ("id_etapa","id_etapa",I,True,None,None),
    ("id_etapa_maxima","id_etapa_maxima",I,True,None,None),
    ("ordem_etapa_maxima","ordem_etapa_maxima",I,True,None,None),
    ("Lead score","lead_score",N,False,"#,0",None),
    ("id_motivo_perda","id_motivo_perda",I,True,None,None),
    ("Qtd motivos de perda","qtd_motivos_perda",I,True,None,None),
    ("id_produto","id_produto",I,True,None,None),
    ("id_forma_pagamento","id_forma_pagamento",I,True,None,None),
    ("Desconto","desconto_pct",N,False,"0%",None),
    ("Valor","valor",N,True,"\\R\\$ #,0.00",None),
    ("Ciclo (dias)","ciclo_dias",N,True,"#,0.0",None)],
  extra_m='''
    Datas = Table.AddColumn(Tipos, "data_criacao_dia", each Date.From([data_criacao]), type date),
    Datas2 = Table.AddColumn(Datas, "data_fechamento_dia", each Date.From([data_fechamento]), type date),
    Hora = Table.AddColumn(Datas2, "hora_criacao", each Time.Hour(Time.From([data_criacao])), Int64.Type),
    Faixa = Table.AddColumn(Hora, "faixa_score", each
        if [lead_score] = null then "Sem score"
        else if [lead_score] < 100 then "Frio"
        else if [lead_score] < 500 then "Morno"
        else if [lead_score] < 1000 then "Quente"
        else if [lead_score] < 5000 then "Muito quente"
        else "Pelando", type text),
    OrdemFaixa = Table.AddColumn(Faixa, "ordem_faixa_score", each
        List.PositionOf({"Frio","Morno","Quente","Muito quente","Pelando","Sem score"}, [faixa_score]) + 1, Int64.Type)
  in
    OrdemFaixa''', extra_cols=[
    ("data_criacao_dia","data_criacao_dia",D,True,"dd/mm/yyyy",None),
    ("data_fechamento_dia","data_fechamento_dia",D,True,"dd/mm/yyyy",None),
    ("Hora de criação","hora_criacao",I,False,"0",None),
    ("Faixa de score","faixa_score",S,False,None,"ordem_faixa_score"),
    ("ordem_faixa_score","ordem_faixa_score",I,True,None,None)]),
 "Metas": dict(arquivo="fato_metas", cols=[
    ("inicio_mes","inicio_mes",D,True,"dd/mm/yyyy",None),
    ("id_vendedor","id_vendedor",I,True,None,None),
    ("id_pipeline","id_pipeline",I,True,None,None),
    ("Meta (valor)","meta",N,True,"\\R\\$ #,0",None)]),
 "Conversas": dict(arquivo="fato_conversas", cols=[
    ("data","data",D,True,"dd/mm/yyyy",None),
    ("Hora","hora",I,False,"0",None),
    ("qtd_conversas","qtd_conversas",I,True,"#,0",None)]),
 "Calendario": dict(arquivo="dim_calendario", date_table=True, cols=[
    ("Data","data",D,False,"dd/mm/yyyy",None),
    ("Ano","ano",I,False,"0",None),
    ("mes","mes",I,True,"0",None),
    ("Mês","nome_mes",S,False,None,"mes"),
    ("Mês abrev.","mes_abrev",S,False,None,"mes"),
    ("Ano-mês","ano_mes",S,False,None,None),
    ("inicio_mes","inicio_mes",D,True,"dd/mm/yyyy",None),
    ("Trimestre","trimestre",S,False,None,None),
    ("Semana ISO","semana_iso",I,False,"0",None),
    ("Dia","dia",I,False,"0",None),
    ("dia_semana_num","dia_semana_num",I,True,"0",None),
    ("Dia da semana","dia_semana",S,False,None,"dia_semana_num"),
    ("Dia sem.","dia_semana_abrev",S,False,None,"dia_semana_num"),
    ("Semana do mês","semana_mes",I,False,"0",None),
    ("Feriado","feriado",B,False,None,None),
    ("Dia útil","dia_util",B,False,None,None)],
  extra_m='''
    Rotulo = Table.AddColumn(Tipos, "mes_ano", each [mes_abrev] & "/" & Text.End(Text.From([ano]), 2), type text)
  in
    Rotulo''', extra_cols=[("Mês/ano","mes_ano",S,False,None,"inicio_mes")]),
 "Pipeline": dict(arquivo="dim_pipeline", cols=[
    ("id_pipeline","id_pipeline",I,True,None,None),
    ("Pipeline","pipeline",S,False,None,"ordem"),
    ("ordem","ordem",I,True,None,None)]),
 "Etapa": dict(arquivo="dim_etapa", cols=[
    ("id_etapa","id_etapa",I,True,None,None),
    ("id_pipeline","id_pipeline",I,True,None,None),
    ("Etapa","etapa",S,False,None,None),
    ("Ordem da etapa","ordem_etapa",I,True,None,None),
    ("Status da etapa","status",S,False,None,None),
    ("Fase do funil","fase_funil",S,False,None,None)]),
 "Vendedor": dict(arquivo="dim_vendedor", cols=[
    ("id_vendedor","id_vendedor",I,True,None,None),
    ("Vendedor","vendedor",S,False,None,None),
    ("id_pipeline","id_pipeline",I,True,None,None),
    ("Data de entrada","data_entrada",D,False,"dd/mm/yyyy",None),
    ("Data de saída","data_saida",D,False,"dd/mm/yyyy",None),
    ("Ativo","ativo",B,False,None,None)]),
 "Fonte": dict(arquivo="dim_fonte", cols=[
    ("id_fonte","id_fonte",I,True,None,None),
    ("Fonte (CRM)","fonte_crm",S,False,None,None),
    ("Canal","canal",S,False,None,None)]),
 "Motivo Perda": dict(arquivo="dim_motivo_perda", cols=[
    ("id_motivo","id_motivo",I,True,None,None),
    ("Motivo","motivo",S,False,None,None),
    ("Categoria do motivo","categoria_motivo",S,False,None,None)]),
 "Produto": dict(arquivo="dim_produto", cols=[
    ("id_produto","id_produto",I,True,None,None),
    ("Produto","produto",S,False,None,None),
    ("id_pipeline","id_pipeline",I,True,None,None),
    ("Preço de lista","preco_lista",N,False,"\\R\\$ #,0",None)]),
 "Forma Pagamento": dict(arquivo="dim_forma_pagamento", cols=[
    ("id_forma_pagamento","id_forma_pagamento",I,True,None,None),
    ("Forma de pagamento","forma_pagamento",S,False,None,None)]),
}

def tabela_tmdl(nome, spec):
    cols = spec["cols"] + spec.get("extra_cols", [])
    tipos = ", ".join(f'{{"{src}", {tm}}}' for _, src, tm, *_ in spec["cols"])
    m = f'''let
    Origem = Csv.Document(File.Contents(PastaDados & "{spec["arquivo"]}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Cabecalhos = Table.PromoteHeaders(Origem, [PromoteAllScalars=true]),
    Nulos = Table.ReplaceValue(Cabecalhos, "", null, Replacer.ReplaceValue, Table.ColumnNames(Cabecalhos)),
    Tipos = Table.TransformColumnTypes(Nulos, {{{tipos}}}, "en-US")'''
    m += ("," + spec["extra_m"]) if "extra_m" in spec else "\nin\n    Tipos"
    out = [f"table {q(nome)}"]
    if spec.get("date_table"): out.append(f"{T}dataCategory: Time")
    out.append("")
    for cname, src, tm, hidden, fmt, sortby in cols:
        out.append(f"{T}column {q(cname)}")
        out.append(f"{T*2}dataType: {TMDL[tm]}")
        if fmt: out.append(f"{T*2}formatString: {fmt}")
        if hidden: out.append(f"{T*2}isHidden")
        if spec.get("date_table") and src == "data": out.append(f"{T*2}isKey")
        out.append(f"{T*2}summarizeBy: none")
        out.append(f"{T*2}sourceColumn: {src}")
        if sortby:
            alvo = next(c[0] for c in cols if c[1] == sortby)
            out.append(f"{T*2}sortByColumn: {q(alvo)}")
        if tm == D: out += ["", f"{T*2}annotation UnderlyingDateTimeDataType = Date"]
        out.append("")
    out += [f"{T}partition {q(nome)} = m", f"{T*2}mode: import", f"{T*2}source ="]
    out += [T*4 + l for l in m.splitlines()]
    out.append("")
    return "\n".join(out) + "\n"

for nome, spec in TABELAS.items():
    w(SM / f"definition/tables/{nome}.tmdl", tabela_tmdl(nome, spec))

# ---------------------------------------------------- tabelas calculadas
def tabela_calc(nome, linhas, desc, rotulo="Período"):
    """Tabela auxiliar fixa, em Power Query (#table). Tabela calculada em DAX relacionada a uma
    tabela importada (caso do Eixo Meta com a Calendario) trava a atualização com dependência circular."""
    corpo = ", ".join(f'{{{o}, "{r}"}}' for o, r in linhas)
    w(SM / f"definition/tables/{nome}.tmdl", f"""/// {desc}
table {q(nome)}

{T}column Ordem
{T*2}dataType: int64
{T*2}isHidden
{T*2}summarizeBy: none
{T*2}sourceColumn: Ordem

{T}column {q(rotulo)}
{T*2}dataType: string
{T*2}summarizeBy: none
{T*2}sourceColumn: {rotulo}
{T*2}sortByColumn: Ordem

{T}partition {q(nome)} = m
{T*2}mode: import
{T*2}source =
{T*4}#table(type table [Ordem = Int64.Type, #"{rotulo}" = text], {{{corpo}}})
""")
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
tabela_calc("Fase Funil", list(enumerate(["1. Novo lead", "2. Tentativa de contato", "3. Contato feito", "4. Descoberta",
            "5. Negociação", "6. Fechamento", "7. Ganho"], 1)), "Fases padronizadas do funil, comparáveis entre pipelines", "Fase")
tabela_calc("Eixo Meta", list(enumerate(MESES, 1)) + [(13, "Meta"), (14, "Realizado"), (15, "")],
            "Eixo do gráfico Meta vs Realizado: meses + complemento. Relacionado a Calendario[mes]")
tabela_calc("Comparativo", [(1, "Mês anterior"), (2, ""), (3, "Mês atual")],
            "Eixo do comparativo mensal (a categoria vazia carrega o rótulo da variação)")
tabela_calc("Comparativo Dia", [(1, "Dia anterior"), (2, ""), (3, "Dia")],
            "Eixo do comparativo diário (a categoria vazia carrega o rótulo da variação)")

# ---------------------------------------------------------------- medidas
lin = ["table Medidas", ""]
for item in MEDIDAS:
    pasta, nome, dax, fmt, desc = item[:5]
    categoria = item[5] if len(item) > 5 else None
    if desc: lin.append(f"{T}/// {desc}")
    linhas = dax.splitlines()
    if len(linhas) == 1:
        lin.append(f"{T}measure {q(nome)} = {dax}")
    else:
        lin.append(f"{T}measure {q(nome)} =")
        lin += [T*3 + l for l in linhas]
    if fmt and not fmt.startswith("="): lin.append(f"{T*2}formatString: {fmt}")
    if categoria: lin.append(f"{T*2}dataCategory: {categoria}")
    lin.append(f"{T*2}displayFolder: {pasta}")
    # formatStringDefinition é um objeto filho: no TMDL precisa vir depois de todas as propriedades
    if fmt and fmt.startswith("="): lin += ["", f"{T*2}formatStringDefinition {fmt}"]
    lin.append("")
lin += [f"{T}column Coluna", f"{T*2}dataType: string", f"{T*2}isHidden", f"{T*2}summarizeBy: none", f"{T*2}sourceColumn: Coluna", "",
        f"{T}partition Medidas = m", f"{T*2}mode: import", f"{T*2}source =", f"{T*4}#table(type table [Coluna = text], {{}})", ""]
w(SM / "definition/tables/Medidas.tmdl", "\n".join(lin) + "\n")

# -------------------------------------------------------- relacionamentos
RELS = [
 ("Negocios","data_criacao_dia","Calendario","Data"),
 ("Negocios","id_pipeline","Pipeline","id_pipeline"),
 ("Negocios","id_vendedor","Vendedor","id_vendedor"),
 ("Negocios","id_fonte","Fonte","id_fonte"),
 ("Negocios","id_etapa","Etapa","id_etapa"),
 ("Negocios","id_motivo_perda","Motivo Perda","id_motivo"),
 ("Negocios","id_produto","Produto","id_produto"),
 ("Negocios","id_forma_pagamento","Forma Pagamento","id_forma_pagamento"),
 ("Metas","inicio_mes","Calendario","Data"),
 ("Metas","id_vendedor","Vendedor","id_vendedor"),
 ("Metas","id_pipeline","Pipeline","id_pipeline"),
 ("Conversas","data","Calendario","Data"),
 ("Calendario","mes","Eixo Meta","Ordem"),
]
lin = []
for ft, fc, tt, tc in RELS:
    lin += [f"relationship {guid_estavel(ft, fc, tt, tc)}", f"{T}fromColumn: {q(ft)}.{q(fc)}", f"{T}toColumn: {q(tt)}.{q(tc)}", ""]
w(SM / "definition/relationships.tmdl", "\n".join(lin))

w(SM / "definition/expressions.tmdl", f'''/// Pasta onde estão os CSVs gerados por scripts/gerar_dados.py (terminar com \\)
expression PastaDados = "{PASTA_PADRAO}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]

{T}annotation PBI_ResultType = Text
''')
w(SM / "definition/database.tmdl", "database\n\tcompatibilityLevel: 1606\n\n")
ordem = list(TABELAS) + ["Fase Funil", "Eixo Meta", "Comparativo", "Comparativo Dia", "Medidas"]
w(SM / "definition/model.tmdl", "model Model\n\tculture: pt-BR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: pt-BR\n"
  "\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
  "annotation __PBI_TimeIntelligenceEnabled = 0\n\nannotation PBI_ProTooling = [\"DevMode\"]\n\n"
  + "".join(f"ref table {q(t)}\n" for t in ordem) + "\n")
w(SM / "definition.pbism", json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
  "version": "4.2", "settings": {}}, indent=2))
for pasta, tipo in ((SM, "SemanticModel"), (RP, "Report")):
    w(pasta / ".platform", json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
      "metadata": {"type": tipo, "displayName": NOME}, "config": {"version": "2.0", "logicalId": guid_estavel(tipo)}}, indent=2))

# ------------------------------------------------------- casca do relatório
w(ROOT / f"{NOME}.pbip", json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
  "version": "1.0", "artifacts": [{"report": {"path": f"{NOME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
w(RP / "definition.pbir", json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}}}, indent=2))
w(RP / "definition/version.json", json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2))
F_TIT = "Bahnschrift, 'Segoe UI Semibold', sans-serif"
TEMA = {
 "name": "TerraCode Editorial",
 "dataColors": ["#1F6F78", "#D9A441", "#4C6A92", "#C8553D", "#7A9E7E", "#8C6E9C", "#B5A88F", "#5F7470"],
 "background": "#FFFFFF", "foreground": "#1A1A1A", "tableAccent": "#1F6F78",
 "good": "#2E7D5B", "neutral": "#D9A441", "bad": "#C8553D", "maximum": "#1F6F78", "center": "#9CC3C6", "minimum": "#F1EFE8",
 "textClasses": {"callout": {"fontSize": 26, "fontFace": F_TIT, "color": "#1A1A1A"},
                 "title": {"fontSize": 13, "fontFace": F_TIT, "color": "#1A1A1A"},
                 "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": "#1A1A1A"},
                 "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#6B6B6B"}},
 "visualStyles": {
   "*": {"*": {"background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
               "border": [{"show": False}], "dropShadow": [{"show": False}], "visualHeader": [{"show": False}],
               "padding": [{"top": 12, "bottom": 12, "left": 14, "right": 14}],
               "title": [{"show": True, "fontFamily": F_TIT, "fontSize": 13, "bold": True, "fontColor": {"solid": {"color": "#1A1A1A"}}}],
               "subTitle": [{"fontFamily": "Segoe UI", "fontSize": 9, "fontColor": {"solid": {"color": "#6B6B6B"}}}],
               "valueAxis": [{"gridlineShow": True, "gridlineColor": {"solid": {"color": "#ECEAE4"}}, "gridlineStyle": "dotted",
                              "labelColor": {"solid": {"color": "#8A8A8A"}}, "fontFamily": "Segoe UI", "fontSize": 9, "showAxisTitle": False}],
               "categoryAxis": [{"labelColor": {"solid": {"color": "#8A8A8A"}}, "fontFamily": "Segoe UI", "fontSize": 9, "showAxisTitle": False, "gridlineShow": False}],
               "legend": [{"position": "TopLeft", "labelColor": {"solid": {"color": "#6B6B6B"}}, "fontFamily": "Segoe UI", "fontSize": 9}],
               "labels": [{"color": {"solid": {"color": "#4A4A4A"}}, "fontFamily": "Segoe UI", "fontSize": 9}]}},
   "page": {"*": {"background": [{"color": {"solid": {"color": "#F5F4EF"}}, "transparency": 0}],
                  "outspace": [{"color": {"solid": {"color": "#F5F4EF"}}, "transparency": 0}]}},
   "slicer": {"*": {"items": [{"fontColor": {"solid": {"color": "#1A1A1A"}}, "fontFamily": "Segoe UI", "textSize": 9}]}},
   "tableEx": {"*": {"grid": [{"gridVertical": False, "gridHorizontalColor": {"solid": {"color": "#ECEAE4"}}}],
                     "columnHeaders": [{"fontFamily": "Segoe UI Semibold", "fontColor": {"solid": {"color": "#6B6B6B"}}, "backColor": {"solid": {"color": "#FFFFFF"}}}]}}}}
TEMA_ARQ = "TerraCodeEditorial.json"
w(RP / f"StaticResources/RegisteredResources/{TEMA_ARQ}", json.dumps(TEMA, indent=2, ensure_ascii=False))
base = RP / "StaticResources/SharedResources/BaseThemes/CY24SU10.json"
if not base.exists():
    raise SystemExit("Tema base CY24SU10.json não encontrado: salve o projeto uma vez pelo Power BI Desktop.")
ver = {"visual": "1.8.98", "report": "2.0.98", "page": "1.3.98"}
w(RP / "definition/report.json", json.dumps({
 "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
 "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": ver, "type": "SharedResources"},
                     "customTheme": {"name": TEMA_ARQ, "reportVersionAtImport": ver, "type": "RegisteredResources"}},
 "publicCustomVisuals": ["deneb7E15AEF80B9E4D4F8E12924291ECE89A"],
 "resourcePackages": [
   {"name": "SharedResources", "type": "SharedResources", "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
   {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": TEMA_ARQ, "path": TEMA_ARQ, "type": "CustomTheme"}]}],
 "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
              "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}}, indent=2))
w(ROOT / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf*\n")
print(f"modelo ok: {len(TABELAS) + 4} tabelas + Medidas ({len(MEDIDAS)} medidas), {len(RELS)} relacionamentos")
