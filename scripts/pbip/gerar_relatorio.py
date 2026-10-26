"""Gera as páginas, tooltips e indicadores (PBIR) do relatório TerraCode Comercial.

Uso: python gerar_relatorio.py   (rode gerar_modelo.py antes)
Apaga e recria as pastas pages/ e bookmarks/ do relatório.
"""
import json, shutil, hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DEF = BASE / "powerbi/TerraCode Comercial.Report/definition"
RP, BK = DEF / "pages", DEF / "bookmarks"
for d in (RP, BK):
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
SCHEMA_V = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"
W, H, G = 1600, 1000, 24

# ================================================================ helpers
def lit(v): return {"expr": {"Literal": {"Value": v}}}
def s(t): return lit("'" + str(t).replace("'", "''") + "'")
def num(n): return lit(f"{n}D")
def lng(n): return lit(f"{n}L")
TRUE, FALSE = lit("true"), lit("false")
def cor(h): return {"solid": {"color": lit(f"'{h}'")}}
def MREF(m): return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": m}}
def cor_medida(m): return {"solid": {"color": {"expr": MREF(m)}}}
F_TIT = "Bahnschrift, 'Segoe UI Semibold', sans-serif"
F_TXT = "'Segoe UI', wf_segoe-ui_normal, helvetica, arial, sans-serif"
F_SEMI = "'Segoe UI Semibold', wf_segoe-ui_semibold, helvetica, arial, sans-serif"
TINTA, CINZA, CLARO, LINHA, FUNDO = "#1A1A1A", "#6B6B6B", "#8A8A8A", "#DAD7CE", "#F5F4EF"
TEAL, AMBAR, ARDOSIA, TERRA, SALVIA, VERDE = "#1F6F78", "#D9A441", "#4C6A92", "#C8553D", "#7A9E7E", "#2E7D5B"
PEDRA, PEDRA_ESC = "#CFCBC0", "#9A968C"

def M(nome, display=None):
    d = {"field": MREF(nome), "queryRef": f"Medidas.{nome}", "nativeQueryRef": display or nome}
    if display: d["displayName"] = display
    return d
def C(ent, col, display=None, active=True):
    d = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": col}},
         "queryRef": f"{ent}.{col}", "nativeQueryRef": display or col}
    if display: d["displayName"] = display
    if active: d["active"] = True
    return d
def ordenar(proj, desc=True):
    return {"sort": [{"field": proj["field"], "direction": "Descending" if desc else "Ascending"}], "isDefaultSort": False}
def nid(*partes): return hashlib.md5("|".join(map(str, partes)).encode()).hexdigest()[:20]
def sel_meta(m): return {"metadata": f"Medidas.{m}"}
def sel_cat(ent, col, val):
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": col}},
                                                 "Right": {"Literal": {"Value": f"'{val}'"}}}}}]}

def vco(tit=None, sub=None, tam=13, fundo=True, pad=None, tooltip=None, tit_estilo="forte"):
    o = {"background": [{"properties": {"show": TRUE if fundo else FALSE, "color": cor("#FFFFFF"), "transparency": num(0)}}],
         "border": [{"properties": {"show": FALSE}}], "dropShadow": [{"properties": {"show": FALSE}}],
         "visualHeader": [{"properties": {"show": FALSE}}]}
    if tit:
        if tit_estilo == "forte":
            t = {"show": TRUE, "text": s(tit), "fontFamily": s(F_TIT), "fontSize": num(tam), "bold": TRUE, "fontColor": cor(TINTA)}
        else:
            t = {"show": TRUE, "text": s(tit), "fontFamily": s(F_SEMI), "fontSize": num(tam), "bold": FALSE, "fontColor": cor(CINZA)}
        t["alignment"] = s("left")
        o["title"] = [{"properties": t}]
    else:
        o["title"] = [{"properties": {"show": FALSE}}]
    if sub:
        o["subTitle"] = [{"properties": {"show": TRUE, "text": s(sub), "fontFamily": s(F_TXT), "fontSize": num(9), "fontColor": cor(CINZA)}}]
    if pad is not None:
        t, b, l, r = pad
        o["padding"] = [{"properties": {"top": num(t), "bottom": num(b), "left": num(l), "right": num(r)}}]
    if tooltip:
        o["visualTooltip"] = [{"properties": {"show": TRUE, "section": s(tooltip), "type": s("Canvas")}}]
    return o

class Pagina:
    def __init__(self, nome, display, w=W, h=H, tooltip=False):
        self.nome, self.display, self.w, self.h, self.tooltip = nome, display, w, h, tooltip
        self.z, self.vis = 0, []
    def add(self, x, y, w, h, visual, grupo=None, oculto=False, nome=None):
        self.z += 100
        n = nome or nid(self.nome, self.z)
        c = {"$schema": SCHEMA_V, "name": n,
             "position": {"x": round(x, 2), "y": round(y, 2), "z": self.z, "height": round(h, 2), "width": round(w, 2), "tabOrder": self.z}}
        if visual is None:
            c["visualGroup"] = {"displayName": grupo, "groupMode": "ScaleMode"}
        else:
            c["visual"] = visual
            if grupo: c["parentGroupName"] = grupo
        if oculto: c["isHidden"] = True
        self.vis.append((n, c))
        return n
    def salvar(self):
        d = RP / self.nome; (d / "visuals").mkdir(parents=True)
        pg = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
              "name": self.nome, "displayName": self.display,
              "displayOption": "ActualSize" if self.tooltip else "FitToPage", "height": self.h, "width": self.w,
              "objects": {"background": [{"properties": {"color": cor("#FFFFFF" if self.tooltip else FUNDO), "transparency": num(0)}}],
                          "outspace": [{"properties": {"color": cor(FUNDO), "transparency": num(0)}}]}}
        if self.tooltip:
            pg["type"] = "Tooltip"; pg["visibility"] = "HiddenInViewMode"
        (d / "page.json").write_text(json.dumps(pg, indent=2, ensure_ascii=False), encoding="utf-8")
        for n, c in self.vis:
            (d / "visuals" / n).mkdir()
            (d / "visuals" / n / "visual.json").write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8")

# ========================================================= tipos de visual
def run(t, tam, c=TINTA, fonte="Segoe UI", negrito=False):
    st = {"fontSize": f"{tam}pt", "color": c, "fontFamily": fonte}
    if negrito: st["fontWeight"] = "bold"
    return {"value": t, "textStyle": st}
def textbox(paragrafos):
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paragrafos}}]},
            "visualContainerObjects": {"background": [{"properties": {"show": FALSE}}],
                                       "padding": [{"properties": {"top": num(4), "bottom": num(0), "left": num(0), "right": num(0)}}]},
            "drillFilterOtherVisuals": True}
def retangulo(h):
    return {"visualType": "shape", "objects": {
        "shape": [{"properties": {"tileShape": s("rectangle")}}],
        "fill": [{"properties": {"fillColor": cor(h), "transparency": num(0)}, "selector": {"id": "default"}}, {"properties": {"show": TRUE}}],
        "outline": [{"properties": {"show": FALSE}}]},
        "visualContainerObjects": {"background": [{"properties": {"show": FALSE}}]}, "drillFilterOtherVisuals": True}
def botao(texto, acao, tam=11, c=CINZA, negrito=False, alinh="left", contorno=None, fundo=None):
    obj = {"icon": [{"properties": {"shapeType": s("blank")}, "selector": {"id": "default"}}, {"properties": {"show": FALSE}}],
           "text": [{"properties": {"show": TRUE}},
                    {"properties": {"text": s(texto), "fontColor": cor(c), "fontSize": num(tam), "fontFamily": s(F_SEMI if negrito else F_TXT),
                                    "bold": TRUE if negrito else FALSE, "horizontalAlignment": s(alinh), "verticalAlignment": s("middle"),
                                    "leftMargin": num(8), "rightMargin": num(8), "topMargin": num(0), "bottomMargin": num(0)},
                     "selector": {"id": "default"}}],
           "outline": [{"properties": {"show": TRUE if contorno else FALSE}},
                       *([{"properties": {"lineColor": cor(contorno), "weight": num(1), "roundEdge": num(6)}, "selector": {"id": "default"}}] if contorno else [])],
           "fill": [{"properties": {"show": TRUE if fundo else FALSE}},
                    *([{"properties": {"fillColor": cor(fundo), "transparency": num(0)}, "selector": {"id": "default"}}] if fundo else [])]}
    tipo, alvo = acao
    link = {"show": TRUE, "type": s(tipo)}
    if tipo == "PageNavigation": link["navigationSection"] = s(alvo)
    if tipo == "Bookmark": link["bookmark"] = s(alvo)
    return {"visualType": "actionButton", "objects": obj,
            "visualContainerObjects": {"visualLink": [{"properties": link}], "background": [{"properties": {"show": FALSE}}],
                                       "padding": [{"properties": {"top": num(0), "bottom": num(0), "left": num(0), "right": num(0)}}]},
            "drillFilterOtherVisuals": True}
def cartao(medida, tam=26, fonte=F_TIT, cor_val=TINTA, cor_med=None, tit=None, sub=None, alinh="left",
           pad=None, tooltip=None, display=None, fundo=True, tam_tit=10):
    val = {"horizontalAlignment": s(alinh), "fontFamily": s(fonte), "fontSize": num(tam),
           "fontColor": cor_medida(cor_med) if cor_med else cor(cor_val), "labelDisplayUnits": num(1), "displayUnits": num(1)}
    return {"visualType": "cardVisual",
            "query": {"queryState": {"Data": {"projections": [M(medida, display)]}}, "sortDefinition": {"isDefaultSort": True}},
            "objects": {"value": [{"properties": val, "selector": {"id": "default"}}],
                        "label": [{"properties": {"show": FALSE}, "selector": {"id": "default"}}],
                        "layout": [{"properties": {"alignment": s("top"), "cellPadding": lng(0), "maxTiles": lng(1)}},
                                   {"properties": {"backgroundShow": FALSE, "topOuterMargin": lng(0), "bottomOuterMargin": lng(0),
                                                   "leftOuterMargin": lng(0), "rightOuterMargin": lng(0)}, "selector": {"id": "default"}}],
                        "fillCustom": [{"properties": {"show": FALSE}}],
                        "outline": [{"properties": {"show": FALSE}, "selector": {"id": "default"}}]},
            "visualContainerObjects": vco(tit, sub, tam_tit, fundo=fundo, pad=pad, tooltip=tooltip, tit_estilo="leve"),
            "drillFilterOtherVisuals": True}
def cartao_imagem(medida_valor, medida_img, tam=230):
    return {"visualType": "cardVisual",
            "query": {"queryState": {"Data": {"projections": [M(medida_valor)]}}, "sortDefinition": {"isDefaultSort": True}},
            "objects": {"value": [{"properties": {"show": FALSE}}],
                        "label": [{"properties": {"show": FALSE}, "selector": {"id": "default"}}],
                        "image": [{"properties": {"show": TRUE, "verticalAlignment": s("middle"), "position": s("Left")}, "selector": sel_meta(medida_valor)},
                                  {"properties": {"show": TRUE, "imageType": s("imageUrl"), "imageUrl": {"expr": MREF(medida_img)}, "size": lng(tam)},
                                   "selector": {"id": "default"}}],
                        "fillCustom": [{"properties": {"show": FALSE}}],
                        "outline": [{"properties": {"show": FALSE}, "selector": {"id": "default"}}]},
            "visualContainerObjects": vco(pad=(0, 0, 0, 0)), "drillFilterOtherVisuals": True}
def eixos(rotulos=True, c=None, unid=None):
    lab = {"show": TRUE if rotulos else FALSE, "color": cor("#4A4A4A"), "fontSize": num(9), "fontFamily": s(F_TXT)}
    if unid: lab.update({"labelDisplayUnits": num(unid), "labelPrecision": lng(2 if unid >= 1e6 else 0)})
    o = {"categoryAxis": [{"properties": {"showAxisTitle": FALSE, "gridlineShow": FALSE, "labelColor": cor(CLARO), "fontSize": num(9), "fontFamily": s(F_TXT)}}],
         "valueAxis": [{"properties": {"showAxisTitle": FALSE, "gridlineShow": TRUE, "gridlineStyle": s("dotted"), "gridlineColor": cor("#ECEAE4"),
                                       "labelColor": cor(CLARO), "fontSize": num(9)}}],
         "legend": [{"properties": {"show": FALSE}}], "labels": [{"properties": lab}]}
    if c: o["dataPoint"] = [{"properties": {"fill": cor(c)}}]
    return o
def barras(tipo, cat, medidas, tit, sub, c=TEAL, desc=True, rotulos=True, ordenar_por=None, tooltip=None, unid=None):
    v = {"visualType": tipo, "query": {"queryState": {"Category": {"projections": [cat]}, "Y": {"projections": medidas}}},
         "objects": eixos(rotulos, c, unid), "visualContainerObjects": vco(tit, sub, tooltip=tooltip), "drillFilterOtherVisuals": True}
    if ordenar_por is not False:
        v["query"]["sortDefinition"] = ordenar(ordenar_por or medidas[0], desc)
    return v
def legenda(v):
    v["objects"]["legend"] = [{"properties": {"show": TRUE, "position": s("TopRight"), "labelColor": cor(CINZA), "fontSize": num(9)}}]
    return v
def combo(cat, colunas, linhas, tit, sub, cores, eixo2=False, tooltip=None):
    o = eixos(False)
    o["dataPoint"] = [{"properties": {"fill": cor(cores[0])}, "selector": {"metadata": colunas[0]["queryRef"]}},
                      {"properties": {"fill": cor(cores[1])}, "selector": {"metadata": linhas[0]["queryRef"]}}]
    o["lineStyles"] = [{"properties": {"strokeWidth": lng(3), "showMarker": TRUE, "markerSize": num(4)}}]
    o["valueAxis"][0]["properties"]["secShow"] = TRUE if eixo2 else FALSE
    if eixo2: o["valueAxis"][0]["properties"].update({"secLabelColor": cor(CLARO), "secFontSize": num(9), "secShowAxisTitle": FALSE})
    v = {"visualType": "lineClusteredColumnComboChart",
         "query": {"queryState": {"Category": {"projections": [cat]}, "Y": {"projections": colunas}, "Y2": {"projections": linhas}},
                   "sortDefinition": ordenar(cat, False)},
         "objects": o, "visualContainerObjects": vco(tit, sub, tooltip=tooltip), "drillFilterOtherVisuals": True}
    return legenda(v)

def meta_realizado(tooltip):
    """Linhas acumuladas no ano + colunas Meta / Realizado / Diferença no mesmo eixo (tabela 'Eixo Meta')."""
    cat = C("Eixo Meta", "Período", "Mês")
    cols = ["MR Meta", "MR Realizado", "MR Base", "MR Acima", "MR Abaixo"]
    lns = ["MR YTD meta", "MR YTD realizado", "MR Linha meta", "MR Linha realizado"]
    pts = ["MR Pt meta", "MR Pt realizado", "MR Pt diferença"]
    cores = {"MR Meta": PEDRA, "MR Realizado": TEAL, "MR Base": "#FFFFFF", "MR Acima": VERDE, "MR Abaixo": TERRA,
             "MR YTD meta": PEDRA_ESC, "MR YTD realizado": TEAL, "MR Linha meta": PEDRA_ESC, "MR Linha realizado": TEAL}
    o = eixos(True, unid=1000000)
    o["valueAxis"][0]["properties"].update({"show": FALSE, "secShow": FALSE, "gridlineShow": FALSE, "start": num(0), "end": {"expr": MREF("MR eixo")}})
    o["categoryAxis"][0]["properties"].update({"fontSize": num(10), "labelColor": cor(CINZA)})
    o["dataPoint"] = [{"properties": {"fill": cor(c)}, "selector": sel_meta(m)} for m, c in cores.items()]
    o["dataPoint"].append({"properties": {"fillTransparency": num(100)}, "selector": sel_meta("MR Base")})
    o["labels"][0]["properties"].update({"labelPosition": s("Above"), "fontSize": num(10), "fontFamily": s(F_SEMI), "color": cor(TINTA)})
    for m in cols + lns:
        o["labels"].append({"properties": {"showSeries": FALSE}, "selector": sel_meta(m)})
    o["labels"].append({"properties": {"labelDisplayUnits": num(1)}, "selector": sel_meta("MR Pt diferença")})
    o["labels"].append({"properties": {"color": cor_medida("MR Cor diferença")},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "Medidas.MR Pt diferença"}})
    o["lineStyles"] = [{"properties": {"strokeWidth": lng(2), "showMarker": TRUE, "markerSize": num(4)}}]
    for m in pts:
        o["lineStyles"].append({"properties": {"strokeWidth": lng(0), "showMarker": FALSE}, "selector": sel_meta(m)})
    for m in ("MR Linha meta", "MR Linha realizado"):
        o["lineStyles"].append({"properties": {"strokeWidth": lng(1), "lineStyle": s("dotted"), "showMarker": FALSE}, "selector": sel_meta(m)})
    o["legend"] = [{"properties": {"show": FALSE}}]
    return {"visualType": "lineStackedColumnComboChart",
            "query": {"queryState": {"Category": {"projections": [cat], "showAll": True},
                                     "Y": {"projections": [M(m) for m in cols]}, "Y2": {"projections": [M(m) for m in lns + pts]}},
                      "sortDefinition": ordenar(cat, False)},
            "objects": o,
            "visualContainerObjects": vco("Desempenho meta vs realizado",
                "Linhas: acumulado no ano (meta em cinza). Colunas: total do período e a diferença. Passe o mouse num mês para comparar", tooltip=tooltip),
            "drillFilterOtherVisuals": True}

def comparativo(tab, suf, base_ant, base_atu, cor_var, tit, rotulos_cat):
    """Duas colunas ligadas por hastes até uma linha, com a variação no meio (barras de erro)."""
    cat = C(tab, "Período", " ")
    val, linha, var, ant, atu = (f"Cmp {suf} valor", f"Cmp {suf} linha", f"Cmp {suf} variação", f"Cmp {suf} anterior", f"Cmp {suf} atual")
    o = {"categoryAxis": [{"properties": {"show": TRUE, "fontSize": num(9), "labelColor": cor(CINZA), "showAxisTitle": FALSE, "gridlineShow": FALSE,
                                          "innerPadding": num(12)}}],
         "valueAxis": [{"properties": {"show": FALSE, "showAxisTitle": FALSE, "gridlineShow": FALSE, "secShow": FALSE,
                                       "start": num(0), "end": {"expr": MREF(f"Cmp {suf} eixo")}}}],
         "dataPoint": [{"properties": {"fill": cor(PEDRA_ESC)}, "selector": sel_cat(tab, "Período", rotulos_cat[0])},
                       {"properties": {"fill": cor(TEAL)}, "selector": sel_cat(tab, "Período", rotulos_cat[1])},
                       *[{"properties": {"fill": cor(PEDRA_ESC)}, "selector": sel_meta(m)} for m in (linha, var, ant, atu)]],
         "labels": [{"properties": {"show": TRUE, "labelPosition": s("InsideEnd"), "color": cor("#FFFFFF"), "fontSize": num(9),
                                    "fontFamily": s(F_SEMI), "labelDisplayUnits": num(1000), "labelPrecision": lng(0), "enableBackground": FALSE}},
                    {"properties": {"showSeries": FALSE}, "selector": sel_meta(linha)},
                    {"properties": {"showSeries": FALSE}, "selector": sel_meta(ant)},
                    {"properties": {"showSeries": FALSE}, "selector": sel_meta(atu)},
                    {"properties": {"showSeries": TRUE, "labelPosition": s("Above"), "enableBackground": TRUE, "backgroundColor": cor("#FFFFFF"),
                                    "backgroundTransparency": num(0), "fontSize": num(10), "bold": TRUE}, "selector": sel_meta(var)},
                    {"properties": {"color": cor_medida(cor_var)}, "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"Medidas.{var}"}}],
         "legend": [{"properties": {"show": FALSE}}],
         "lineStyles": [{"properties": {"strokeWidth": lng(2), "showMarker": TRUE, "markerColor": cor(PEDRA_ESC)}},
                        {"properties": {"markerShape": s("circle"), "markerSize": num(5)}, "selector": sel_meta(var)},
                        {"properties": {"markerShape": s("shortDash"), "markerSize": num(1)}, "selector": sel_meta(linha)},
                        {"properties": {"markerShape": s("circle"), "markerSize": num(1)}, "selector": sel_meta(ant)},
                        {"properties": {"markerShape": s("circle"), "markerSize": num(1)}, "selector": sel_meta(atu)}],
         "error": [
            {"properties": {"enabled": TRUE, "barColor": cor(PEDRA_ESC), "barBorderColor": cor(PEDRA_ESC), "tooltipShow": FALSE,
                            "markerShow": FALSE, "barBorderSize": lng(0), "barWidth": num(2)}, "selector": sel_meta(ant)},
            {"properties": {"errorRange": {"kind": "ErrorRange", "explicit": {"isRelative": FALSE, "lowerBound": {"expr": MREF(base_ant)}}}},
             "selector": {"data": [{"roles": ["Rows", "Category"]}], "metadata": f"Medidas.{ant}", "highlightMatching": 1}},
            {"properties": {"errorRange": {"kind": "ErrorRange", "explicit": {"isRelative": FALSE, "upperBound": {"expr": MREF(base_atu)}}}},
             "selector": {"data": [{"roles": ["Rows", "Category"]}], "metadata": f"Medidas.{atu}", "highlightMatching": 1}},
            {"properties": {"enabled": TRUE, "barColor": cor(PEDRA_ESC), "barBorderSize": lng(0), "markerShow": TRUE, "barWidth": num(2),
                            "markerShape": s("longDash"), "tooltipShow": FALSE, "markerSize": num(6)}, "selector": sel_meta(atu)}]}
    return {"visualType": "lineStackedColumnComboChart",
            "query": {"queryState": {"Category": {"projections": [cat]}, "Y": {"projections": [M(val, "Receita")]},
                                     "Y2": {"projections": [M(linha), M(var, "Variação"), M(ant), M(atu)]}},
                      "sortDefinition": ordenar(cat, False)},
            "objects": o, "visualContainerObjects": vco(tit, tam=10, pad=(4, 2, 4, 4)), "drillFilterOtherVisuals": True}

def tabela(colunas, tit, sub, ordem=None):
    v = {"visualType": "tableEx", "query": {"queryState": {"Values": {"projections": colunas}}},
         "objects": {"grid": [{"properties": {"gridVertical": FALSE, "gridHorizontal": TRUE, "gridHorizontalColor": cor("#ECEAE4"), "rowPadding": num(6), "textSize": num(10)}}],
                     "columnHeaders": [{"properties": {"fontColor": cor(CINZA), "backColor": cor("#FFFFFF"), "fontFamily": s(F_SEMI), "fontSize": num(9), "wordWrap": TRUE}}],
                     "values": [{"properties": {"fontColorPrimary": cor(TINTA), "backColorPrimary": cor("#FFFFFF"), "fontColorSecondary": cor(TINTA),
                                                "backColorSecondary": cor("#FAF9F6"), "fontFamily": s(F_TXT), "fontSize": num(10)}}],
                     "total": [{"properties": {"totals": TRUE, "fontFamily": s(F_SEMI), "fontColor": cor(TINTA), "backColor": cor("#FFFFFF")}}]},
         "visualContainerObjects": vco(tit, sub), "drillFilterOtherVisuals": True}
    if ordem: v["query"]["sortDefinition"] = ordenar(ordem)
    return v
def larguras(v, mapa):
    v["objects"]["columnWidth"] = [{"properties": {"value": num(w)}, "selector": {"metadata": q}} for q, w in mapa.items()]
    return v
def gradiente(valor, cmin, cmax):
    return {"solid": {"color": {"expr": {"FillRule": {"Input": valor["field"], "FillRule": {"linearGradient2": {
        "min": {"color": {"Literal": {"Value": f"'{cmin}'"}}}, "max": {"color": {"Literal": {"Value": f"'{cmax}'"}}},
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'noColor'"}}}}}}}}}}
def mapa_calor(linhas, colunas, valor, tit, sub, cmax=TEAL, cor_por=None, tam=9, esconder_linhas=False, tooltip=None, pad_linha=5):
    vals = [{"properties": {"fontSize": num(tam), "fontColorPrimary": cor(TINTA), "fontColorSecondary": cor(TINTA), "fontFamily": s(F_TXT),
                            "wordWrap": TRUE, "backColorPrimary": cor("#FFFFFF"), "backColorSecondary": cor("#FFFFFF")}},
            {"properties": {"backColor": gradiente(cor_por or valor, "#F4F2EC", cmax)},
             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": valor["queryRef"]}}]
    rh = {"fontColor": cor("#FFFFFF" if esconder_linhas else TINTA), "backColor": cor("#FFFFFF"), "fontSize": num(1 if esconder_linhas else 9)}
    return {"visualType": "pivotTable",
            "query": {"queryState": {"Rows": {"projections": [linhas]}, "Columns": {"projections": [colunas]}, "Values": {"projections": [valor]}}},
            "objects": {"subTotals": [{"properties": {"columnSubtotals": FALSE, "rowSubtotals": FALSE}}],
                        "grid": [{"properties": {"gridVertical": TRUE, "gridVerticalColor": cor("#FFFFFF"), "gridVerticalWeight": lng(3),
                                                 "gridHorizontal": TRUE, "gridHorizontalColor": cor("#FFFFFF"), "gridHorizontalWeight": lng(3),
                                                 "rowPadding": num(pad_linha), "textSize": num(tam)}}],
                        "columnHeaders": [{"properties": {"fontColor": cor(CINZA), "backColor": cor("#FFFFFF"), "fontSize": num(9), "alignment": s("Center")}}],
                        "rowHeaders": [{"properties": rh}], "values": vals},
            "visualContainerObjects": vco(tit, sub, tooltip=tooltip), "drillFilterOtherVisuals": True}
def segmentador(ent, col, grupo, padrao=None, horizontal=False, unico=False, tit=None, suspensa=False):
    o = {"data": [{"properties": {"mode": s("Dropdown" if suspensa else "Basic")}}],
         "general": [{"properties": {"orientation": num(1 if horizontal else 0), "outlineWeight": num(0)}}],
         "header": [{"properties": {"show": FALSE}}],
         "items": [{"properties": {"fontColor": cor(TINTA), "background": cor("#FFFFFF"), "textSize": num(10), "fontFamily": s(F_TXT),
                                   "outlineColor": cor(LINHA), "outlineStyle": lng(1 if horizontal else 0), "padding": num(4)}}],
         "selection": [{"properties": {"singleSelect": TRUE if unico else FALSE, "strictSingleSelect": TRUE if unico else FALSE,
                                       "selectAllCheckboxEnabled": FALSE}}]}
    if padrao is not None:
        o["general"][0]["properties"]["filter"] = {"filter": {"Version": 2, "From": [{"Name": "c", "Entity": ent, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": col}}],
                                            "Values": [[{"Literal": {"Value": padrao}}]]}}}]}}
    v = {"visualType": "slicer",
         "query": {"queryState": {"Values": {"projections": [C(ent, col)]}}, "sortDefinition": {"isDefaultSort": True}},
         "objects": o, "visualContainerObjects": vco(tit, tam=10, fundo=False, tit_estilo="leve")}
    if grupo: v["syncGroup"] = {"groupName": grupo, "fieldChanges": True, "filterChanges": True}
    v["drillFilterOtherVisuals"] = True
    return v
def deneb(cat, valor, rotulo, tit, sub, cores=("#DCEBEC", TEAL), tooltip=None):
    spec = {
      "data": {"name": "dataset"},
      "transform": [{"filter": "datum.Categoria != null && datum.Valor != null"},
                    {"joinaggregate": [{"op": "max", "field": "Valor", "as": "maximo"}]},
                    {"calculate": "datum.maximo * 1.3", "as": "limite"}],
      "encoding": {"y": {"field": "Categoria", "type": "nominal", "sort": {"field": "Valor", "order": "descending"},
                         "axis": {"title": None, "labelLimit": 170, "labelFontSize": 11, "labelColor": "#4A4A4A", "labelPadding": 8}}},
      "layer": [
        {"mark": {"type": "point", "opacity": 0}, "encoding": {"x": {"field": "limite", "type": "quantitative", "axis": None}}},
        {"mark": {"type": "bar", "cornerRadiusEnd": 6, "height": {"band": 0.62}, "tooltip": True},
         "encoding": {"x": {"field": "Valor", "type": "quantitative", "axis": None},
                      "opacity": {"condition": {"test": {"field": "__selected__", "equal": "off"}, "value": 0.3}, "value": 1}}},
        {"mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 6, "fontSize": 11, "color": TINTA},
         "encoding": {"x": {"field": "Valor", "type": "quantitative", "axis": None}, "text": {"field": "Rotulo"}}}]}
    config = {"view": {"stroke": "transparent"}, "font": "Segoe UI",
              "bar": {"color": {"x1": 0, "x2": 1, "y1": 0, "y2": 0, "gradient": "linear",
                                "stops": [{"offset": 0, "color": cores[0]}, {"offset": 1, "color": cores[1]}]}},
              "axis": {"ticks": False, "grid": False, "domain": False}, "padding": {"right": 8, "left": 4, "top": 4, "bottom": 4}}
    return {"visualType": DENEB,
            "query": {"queryState": {"dataset": {"projections": [C(*cat, display="Categoria", active=False), M(valor, "Valor"), M(rotulo, "Rotulo")]}}},
            "objects": {"vega": [{"properties": {"provider": s("vegaLite"), "jsonSpec": s(json.dumps(spec, indent=2, ensure_ascii=False)),
                                                 "jsonConfig": s(json.dumps(config, indent=2)), "enableTooltips": TRUE, "enableContextMenu": TRUE,
                                                 "enableHighlight": TRUE, "enableSelection": TRUE, "selectionMaxDataPoints": num(50), "version": s("6.1.0")}}]},
            "visualContainerObjects": vco(tit, sub, tooltip=tooltip), "drillFilterOtherVisuals": True}

# ============================================== cabeçalho, abas e filtros
PAGINAS = [("visaogeral", "Visão geral"), ("funil", "Funil e canais"), ("time", "Time comercial"),
           ("perdas", "Perdas e atendimento"), ("calendario", "Calendário")]
bookmarks = []
TOPO, FIM = 196, H - G
DIR = G + 1026
LD = W - G - DIR

def painel_filtros(p):
    grp = nid(p.nome, "painel")
    larg = 380
    p.add(W - larg, 0, larg, H, None, grupo="Painel de filtros", oculto=True, nome=grp)
    filhos = [grp]
    # no PBIR a posição dos filhos de um grupo é relativa ao grupo
    def f(x, y, w, h, v): filhos.append(p.add(x, y, w, h, v, grupo=grp))
    abrir, fechar = nid(p.nome, "bk_abrir"), nid(p.nome, "bk_fechar")
    f(0, 0, larg, H, retangulo("#FFFFFF"))
    f(0, 0, 2, H, retangulo(LINHA))
    f(24, 18, 220, 80, textbox([{"textRuns": [run("Filtros", 18, TINTA, "Bahnschrift", True)]},
                                {"textRuns": [run("Valem para todas as páginas", 9, CINZA)]}]))
    f(larg - 134, 26, 110, 42, botao("Fechar  ✕", ("Bookmark", fechar), 10, TINTA, True, "center", contorno=LINHA))
    f(24, 110, larg - 48, 80, segmentador("Calendario", "Ano", "ano", "2025L", horizontal=True, tit="Ano"))
    f(24, 202, larg - 48, 136, segmentador("Pipeline", "Pipeline", "pipeline", tit="Pipeline"))
    f(24, 350, larg - 48, 300, segmentador("Vendedor", "Vendedor", "vendedor", tit="Vendedor"))
    f(24, 662, larg - 48, 250, segmentador("Fonte", "Canal", "canal", tit="Canal de entrada"))
    f(24, H - 72, larg - 48, 46, botao("Limpar filtros", ("ClearAllSlicers", None), 10, TINTA, alinh="center", contorno=LINHA))
    for b, oculto, nome_b in ((abrir, False, f"Filtros abertos ({p.display})"), (fechar, True, f"Filtros fechados ({p.display})")):
        bookmarks.append((b, {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/2.1.0/schema.json",
            "displayName": nome_b, "name": b,
            "options": {"applyOnlyToTargetVisuals": True, "targetVisualNames": filhos, "suppressData": True, "suppressActiveSection": True},
            "explorationState": {"version": "1.3", "activeSection": p.nome,
                                 "sections": {p.nome: {"visualContainers": {}, "visualContainerGroups": {grp: {"isHidden": oculto}}}},
                                 "objects": {}}}))
    return abrir

def cabecalho(p, titulo_pagina):
    p.add(G, 4, 900, 84, textbox([{"textRuns": [run("TERRACODE ACADEMY  ·  PAINEL COMERCIAL", 9, CINZA, "Segoe UI Semibold")]},
                                  {"textRuns": [run(titulo_pagina, 24, TINTA, "Bahnschrift", True)]}]))
    p.add(G, 68, 1252, 58, cartao("Resumo do período", 13, F_TXT, cor_val="#3A3A3A", pad=(8, 0, 12, 12)))
    x = G
    for nome, disp in PAGINAS:
        larg = len(disp) * 8.5 + 36
        ativo = nome == p.nome
        p.add(x, 140, larg, 40, botao(disp, ("PageNavigation", nome), 11, TINTA if ativo else CLARO, negrito=ativo, alinh="center"))
        if ativo: p.add(x + 10, 178, larg - 20, 3, retangulo(TEAL))
        x += larg + 2
    p.add(G, 181, W - 2 * G, 1, retangulo(LINHA))
    p.add(1287, 126, 289, 54, cartao("Texto rodapé", 9, F_TXT, cor_val=CLARO, alinh="right", pad=(10, 0, 4, 4), fundo=False))
    p.add(1426, 22, 150, 46, botao("☰   Filtros", ("PageNavigation", p.nome), 11, TINTA, True, "center", contorno=LINHA, fundo="#FFFFFF"),
          nome=nid(p.nome, "btn_filtros"))

def finalizar(p):
    abrir = painel_filtros(p)   # painel por último: fica por cima de tudo
    for n, c in p.vis:
        if n == nid(p.nome, "btn_filtros"):
            c["visual"]["visualContainerObjects"]["visualLink"][0]["properties"] = {"show": TRUE, "type": s("Bookmark"), "bookmark": s(abrir)}
    p.salvar()

def kpis(p, itens, y=TOPO, h_val=110, h_sub=40):
    n, gap = len(itens), 16
    larg = (W - 2 * G - gap * (n - 1)) / n
    for i, it in enumerate(itens):
        x = G + i * (larg + gap)
        p.add(x, y, larg, 3, retangulo(it["cor"]))
        p.add(x, y + 3, larg, h_val, cartao(it["medida"], 26, tit=it["nome"], tooltip=it.get("tooltip"), pad=(10, 2, 14, 14)))
        if it.get("texto"):
            p.add(x, y + 3 + h_val - 8.5, larg, h_sub + 8.6, cartao(it["texto"], 9, F_SEMI, cor_med=it.get("cor_texto"), cor_val=CINZA, pad=(0, 10, 14, 14)))
        else:
            p.add(x, y + 3 + h_val, larg, h_sub, retangulo("#FFFFFF"))
    return y + 3 + h_val + h_sub + 16

def campo(p, x, y, w, medida, rotulo, tam=17, cor_med=None, fonte=F_TIT, h=72):
    """Campo de tooltip: rótulo pequeno em cima, valor embaixo."""
    p.add(x, y, w, h, cartao(medida, tam, fonte, cor_med=cor_med, tit=rotulo, pad=(4, 0, 6, 6), tam_tit=9))
    return y + h

MES = C("Calendario", "Mês abrev.", "Mês")

# ================================================================ tooltips
def tt_cabecalho(tt, medida, w):
    tt.add(0, 0, w, 50, cartao(medida, 13, F_TIT, pad=(12, 0, 14, 14)))
    tt.add(14, 50, w - 28, 1, retangulo(LINHA))
def tt_campo(tt, x, y, w, medida, rotulo, tam=15, cor_med=None, fonte=F_TIT, h=70):
    tt.add(x, y, w, h, cartao(medida, tam, fonte, cor_med=cor_med, tit=rotulo, pad=(6, 0, 14, 4), tam_tit=9))
    return y + h

tt = Pagina("tt_meta", "Tooltip meta", 470, 280, tooltip=True)
tt_cabecalho(tt, "Período (texto)", 470)
y = tt_campo(tt, 0, 58, 230, "Receita", "Realizado")
y = tt_campo(tt, 0, y, 230, "Meta", "Meta")
tt_campo(tt, 0, y, 246, "Texto gap da meta", "Diferença", 10, cor_med="Cor gap da meta", fonte=F_SEMI, h=68)
tt.add(208, 7, 248, 265, cartao_imagem("% da meta", "SVG meta", 212))
tt.salvar()

def tt_comparativo(nome, display, campos, tab, suf, base_ant, cor_var, rotulos, rodape=None, y_graf=25):
    w, h = 500, 300 if rodape else 278
    tt = Pagina(nome, display, w, h, tooltip=True)
    tt_cabecalho(tt, "Período (texto)", w)
    y = 58
    for med, rot in campos:
        y = tt_campo(tt, 0, y, 170, med, rot)
    tt.add(170, y_graf, w - 178, 214, comparativo(tab, suf, base_ant, "Receita", cor_var, None, rotulos))
    if rodape:
        tt.add(170, y_graf + 214, w - 178, 44, cartao(rodape[0], 9, F_SEMI, cor_med=rodape[1], alinh="center", pad=(4, 0, 4, 4)))
    tt.salvar()

tt_comparativo("tt_mes", "Tooltip mês", [("Receita", "Receita"), ("Vendas", "Vendas"), ("Conversão da coorte", "Conversão dos leads")],
               "Comparativo", "mês", "Receita mês anterior", "Cor var mês anterior", ("Mês anterior", "Mês atual"),
               rodape=("Texto var receita", "Cor var receita"))
tt_comparativo("tt_dia", "Tooltip dia", [("Receita", "Receita"), ("Vendas", "Vendas"), ("Leads", "Leads criados")],
               "Comparativo Dia", "dia", "Receita dia anterior", "Cor var dia anterior", ("Dia anterior", "Dia"), y_graf=32)

# ========================================================== 1. Visão geral
p = Pagina("visaogeral", "Visão geral")
cabecalho(p, "Desempenho comercial")
y = kpis(p, [
    {"nome": "Receita", "medida": "Receita", "cor": TEAL, "texto": "Texto var receita", "cor_texto": "Cor var receita"},
    {"nome": "% da meta", "medida": "% da meta", "cor": AMBAR, "texto": "Texto gap da meta", "cor_texto": "Cor gap da meta", "tooltip": "tt_meta"},
    {"nome": "Vendas", "medida": "Vendas", "cor": ARDOSIA, "texto": "Texto var vendas", "cor_texto": "Cor var vendas"},
    {"nome": "Ticket médio", "medida": "Ticket médio", "cor": SALVIA, "texto": "Texto var ticket", "cor_texto": "Cor var ticket"},
    {"nome": "Leads", "medida": "Leads", "cor": TERRA, "texto": "Texto var leads", "cor_texto": "Cor var leads"},
    {"nome": "Conversão dos leads", "medida": "Conversão da coorte", "cor": TEAL, "texto": "Texto var conversão", "cor_texto": "Cor var conversão"}])
h = (FIM - y - 16) / 2
p.add(G, y, 1010, h, meta_realizado("tt_mes"))
p.add(DIR, y, LD, h, deneb(("Pipeline", "Pipeline"), "Receita", "Rótulo receita", "Receita por pipeline", "Clique numa barra para filtrar a página"))
y2 = y + h + 16
p.add(G, y2, 1010, FIM - y2, combo(MES, [M("Leads")], [M("Conversão da coorte", "Conversão")], "Leads e conversão por mês de criação",
      "Meses recentes ainda têm negócios em aberto, então a conversão tende a subir", (ARDOSIA, TERRA), eixo2=True))
p.add(DIR, y2, LD, FIM - y2, deneb(("Produto", "Produto"), "Receita", "Rótulo receita", "Receita por produto", "Mix de vendas no período",
      ("#E3ECDF", SALVIA)))
finalizar(p)

# ======================================================= 2. Funil e canais
p = Pagina("funil", "Funil e canais")
cabecalho(p, "Funil e canais de entrada")
y = kpis(p, [
    {"nome": "Leads criados", "medida": "Leads", "cor": TERRA, "texto": "Texto var leads", "cor_texto": "Cor var leads"},
    {"nome": "Ainda em aberto", "medida": "Em aberto", "cor": AMBAR, "texto": "Texto em aberto"},
    {"nome": "Win rate", "medida": "Win rate", "cor": TEAL},
    {"nome": "Ciclo de venda (mediana, dias)", "medida": "Ciclo de venda (mediana, dias)", "cor": ARDOSIA}])
h = (FIM - y - 16) / 2
v = barras("funnel", C("Fase Funil", "Fase"), [M("Negócios na fase")], "Funil da coorte",
           "Leads criados no período que chegaram a cada fase", TEAL, ordenar_por=False)
v["objects"]["labels"] = [{"properties": {"show": TRUE, "color": cor("#FFFFFF"), "fontSize": num(10), "fontFamily": s(F_SEMI), "bold": TRUE,
                                          "labelDisplayUnits": num(1), "labelPosition": s("InsideCenter")}}]
v["objects"]["categoryAxis"][0]["properties"].update({"fontSize": num(10), "labelColor": cor(TINTA)})
p.add(G, y, 620, h, v)
p.add(G + 636, y, 450, h, barras("clusteredColumnChart", C("Negocios", "Faixa de score"), [M("Conversão da coorte", "Conversão")],
      "Conversão por faixa de lead score", "Quanto mais quente o lead, maior a chance de venda", AMBAR, ordenar_por=False))
p.add(G + 1102, y, W - 2 * G - 1102, h, barras("clusteredColumnChart", C("Negocios", "Hora de criação"), [M("Leads")],
      "Leads por hora de criação", "Horário em que os leads entram no CRM", ARDOSIA, rotulos=False, ordenar_por=False))
y2 = y + h + 16
cols = [C("Fonte", "Canal", active=False), M("Leads"), M("Vendas da coorte", "Vendas"), M("Conversão da coorte", "Conversão"), M("Receita")]
p.add(G, y2, 1010, FIM - y2, larguras(tabela(cols, "Canais de entrada",
      "Negócios criados pelo vendedor costumam nascer no momento da venda e inflam a conversão do canal", ordem=M("Leads")),
      {"Fonte.Canal": 330, "Medidas.Leads": 150, "Medidas.Vendas da coorte": 150, "Medidas.Conversão da coorte": 150, "Medidas.Receita": 170}))
p.add(DIR, y2, LD, FIM - y2, deneb(("Pipeline", "Pipeline"), "Conversão da coorte", "Rótulo conversão",
      "Conversão por pipeline", "Leads criados no período que viraram venda", ("#F3E3C1", AMBAR)))
finalizar(p)

# ======================================================= 3. Time comercial
p = Pagina("time", "Time comercial")
cabecalho(p, "Time comercial")
y = kpis(p, [
    {"nome": "Receita", "medida": "Receita", "cor": TEAL, "texto": "Texto var receita", "cor_texto": "Cor var receita"},
    {"nome": "Meta", "medida": "Meta", "cor": AMBAR},
    {"nome": "% da meta", "medida": "% da meta", "cor": AMBAR, "texto": "Texto gap da meta", "cor_texto": "Cor gap da meta", "tooltip": "tt_meta"},
    {"nome": "Ticket médio", "medida": "Ticket médio", "cor": SALVIA, "texto": "Texto var ticket", "cor_texto": "Cor var ticket"}])
cols = [C("Vendedor", "Vendedor", active=False), C("Pipeline", "Pipeline", active=False), M("Receita"), M("Meta"), M("% da meta"),
        M("Gap da meta"), M("Vendas"), M("Ticket médio"), M("Conversão da coorte", "Conversão"), M("Ciclo de venda (mediana, dias)", "Ciclo (dias)")]
p.add(G, y, W - 2 * G, 290, larguras(tabela(cols, "Desempenho por vendedor",
      "Receita e vendas pela data de fechamento; conversão pela coorte de leads", ordem=M("Receita")),
      {"Vendedor.Vendedor": 220, "Pipeline.Pipeline": 160, "Medidas.Receita": 150, "Medidas.Meta": 150, "Medidas.% da meta": 120,
       "Medidas.Gap da meta": 150, "Medidas.Vendas": 110, "Medidas.Ticket médio": 130, "Medidas.Conversão da coorte": 120,
       "Medidas.Ciclo de venda (mediana, dias)": 120}))
y2 = y + 306
p.add(G, y2, 1010, FIM - y2, larguras(mapa_calor(C("Vendedor", "Vendedor"), MES, M("% da meta"), "Atingimento de meta por mês",
      "Quanto mais escuro, mais perto (ou acima) da meta", tooltip="tt_meta"), {"Medidas.% da meta": 66}))
p.add(DIR, y2, LD, FIM - y2, deneb(("Vendedor", "Vendedor"), "Receita", "Rótulo receita", "Receita por vendedor", "Passe o mouse para ver detalhes"))
finalizar(p)

# ================================================ 4. Perdas e atendimento
p = Pagina("perdas", "Perdas e atendimento")
cabecalho(p, "Perdas e atendimento")
y = TOPO; h = (FIM - y - 16) / 2
p.add(G, y, 500, h, barras("clusteredBarChart", C("Motivo Perda", "Categoria do motivo"), [M("Perdidos")],
      "Perdas por categoria", "Negócios perdidos ou desqualificados no período", TERRA))
p.add(G + 516, y, 510, h, deneb(("Motivo Perda", "Motivo"), "% das perdas", "Rótulo % perdas",
      "Principais motivos", "Participação no total de perdas", ("#F2D9D2", TERRA)))
v = barras("hundredPercentStackedBarChart", C("Pipeline", "Pipeline"), [M("Leads")], "Desfecho dos leads por pipeline",
           "Situação atual dos leads criados no período", None, ordenar_por=False)
v["query"]["queryState"]["Series"] = {"projections": [C("Negocios", "Status")]}
v["objects"]["dataPoint"] = [{"properties": {"fill": cor(c)}, "selector": sel_cat("Negocios", "Status", st)}
                             for st, c in {"Ganho": TEAL, "Perdido": "#D9D5CB", "Em aberto": AMBAR}.items()]
p.add(DIR + 16, y, LD - 16, h, legenda(v))
y2 = y + h + 16
p.add(G, y2, 1010, FIM - y2, mapa_calor(C("Calendario", "Dia da semana"), C("Conversas", "Hora"), M("Conversas"),
      "Quando os leads conversam", "Conversas iniciadas por dia da semana e hora", ARDOSIA))
p.add(DIR, y2, LD, FIM - y2, barras("clusteredColumnChart", MES, [M("Conversas")],
      "Conversas por mês", "Volume no canal de mensagens", ARDOSIA, rotulos=False, ordenar_por=False))
finalizar(p)

# =========================================================== 5. Calendário
p = Pagina("calendario", "Calendário")
cabecalho(p, "Calendário de vendas")
p.add(G, TOPO, 260, 70, segmentador("Calendario", "Mês/ano", None, "'Dez/25'", unico=True, tit="Mês", suspensa=True))
v = mapa_calor(C("Calendario", "Semana do mês", "Semana"), C("Calendario", "Dia sem."), M("Calendário célula", "Receita do dia"),
               "Receita por dia", "Número do dia e receita fechada. Passe o mouse para comparar com o dia anterior",
               cor_por=M("Receita"), cmax="#7FB3B8", tam=13, esconder_linhas=True, tooltip="tt_dia", pad_linha=18)
p.add(G, TOPO + 78, 1010, FIM - TOPO - 78, larguras(v, {"Medidas.Calendário célula": 126, "Calendario.Semana do mês": 60}))
p.add(DIR, TOPO, LD, 3, retangulo(TEAL))
p.add(DIR, TOPO + 3, LD, 110, cartao("Receita", 26, tit="Receita no mês", tooltip="tt_mes", pad=(10, 2, 14, 14)))
p.add(DIR, TOPO + 104.5, LD, 48.6, cartao("Texto var mês anterior", 9, F_SEMI, cor_med="Cor var mês anterior", pad=(0, 10, 14, 14)))
y = TOPO + 169; h = (FIM - y - 16) / 2
p.add(DIR, y, LD, h, deneb(("Produto", "Produto"), "Receita", "Rótulo receita", "Receita por produto", "Mix de vendas no mês", ("#E3ECDF", SALVIA)))
p.add(DIR, y + h + 16, LD, FIM - y - h - 16, deneb(("Forma Pagamento", "Forma de pagamento"), "Receita", "Rótulo receita",
      "Receita por forma de pagamento", None, ("#DDE3EC", ARDOSIA)))
finalizar(p)

# ============================================================== metadados
(RP / "pages.json").write_text(json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": [n for n, _ in PAGINAS] + ["tt_meta", "tt_mes", "tt_dia"], "activePageName": "visaogeral"}, indent=2), encoding="utf-8")
for b, conteudo in bookmarks:
    (BK / f"{b}.bookmark.json").write_text(json.dumps(conteudo, indent=2, ensure_ascii=False), encoding="utf-8")
(BK / "bookmarks.json").write_text(json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json",
    "items": [{"name": b} for b, _ in bookmarks]}, indent=2), encoding="utf-8")
print(f"relatório ok: {len(list(RP.glob('*/page.json')))} páginas, {sum(1 for _ in RP.rglob('visual.json'))} visuais, {len(bookmarks)} indicadores")
