"""Valida o PBIP gerado: campos e medidas existem no modelo, nomes não se repetem num visual,
navegação/indicadores/tooltips apontam para alvos que existem, e nenhum termo da empresa original aparece."""
import json, glob, re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[2]
SM = BASE / "powerbi/TerraCode Comercial.SemanticModel/definition/tables"
DEF = BASE / "powerbi/TerraCode Comercial.Report/definition"
medidas = set(re.findall(r"^\tmeasure '?([^'=]+?)'? =", (SM / "Medidas.tmdl").read_text(encoding="utf-8"), re.M))
cols = {}
for f in SM.glob("*.tmdl"):
    t = f.read_text(encoding="utf-8"); tab = re.search(r"^table '?([^'\n]+)'?", t, re.M).group(1)
    cols[tab] = set(re.findall(r"^\tcolumn '?([^'\n]+?)'?$", t, re.M))
# TMDL: objetos filhos (formatStringDefinition) precisam vir depois das propriedades da medida
_lin = (SM / "Medidas.tmdl").read_text(encoding="utf-8").split("\n")
erros_tmdl = [i + 1 for i, l in enumerate(_lin) if l.startswith("\t\tformatStringDefinition")
              and any(x.startswith("\t\t") and not x.startswith("\t\t\t") for x in _lin[i + 1:i + 3])]
paginas = {p.parent.name for p in (DEF / "pages").glob("*/page.json")}
bks = {b.name[:-14] for b in (DEF / "bookmarks").glob("*.bookmark.json")}
erros = [f"Medidas.tmdl linha {n}: propriedade depois de formatStringDefinition" for n in erros_tmdl]
def walk(o, f):
    if isinstance(o, dict):
        m = o.get("Measure")
        if isinstance(m, dict) and m.get("Expression", {}).get("SourceRef", {}).get("Entity") == "Medidas" and m["Property"] not in medidas:
            erros.append(f"medida inexistente {m['Property']} em {f}")
        c = o.get("Column")
        if isinstance(c, dict) and "Entity" in c.get("Expression", {}).get("SourceRef", {}):
            e = c["Expression"]["SourceRef"]["Entity"]
            if c["Property"] not in cols.get(e, ()): erros.append(f"coluna inexistente {e}.{c['Property']} em {f}")
        for v in o.values(): walk(v, f)
    elif isinstance(o, list):
        for v in o: walk(v, f)
for f in (DEF / "pages").glob("*/visuals/*/visual.json"):
    v = json.loads(f.read_text(encoding="utf-8")); rel = f.relative_to(DEF); walk(v, rel)
    qs = v.get("visual", {}).get("query", {}).get("queryState", {})
    nomes = [p["nativeQueryRef"] for k in qs.values() for p in k.get("projections", [])]
    dup = {n for n in nomes if nomes.count(n) > 1}
    if dup: erros.append(f"nomes repetidos {dup} em {rel}")
    s = json.dumps(v, ensure_ascii=False)
    for chave, alvo_ok in (("navigationSection", paginas), ("bookmark", bks), ("section", paginas)):
        for alvo in re.findall(rf"\"{chave}\": {{\"expr\": {{\"Literal\": {{\"Value\": \"'([^']+)'", s):
            if alvo not in alvo_ok: erros.append(f"{chave} aponta para {alvo} inexistente em {rel}")
    if "parentGroupName" in v:
        gf = f.parent.parent / v["parentGroupName"] / "visual.json"
        if not gf.exists():
            erros.append(f"grupo inexistente em {rel}")
        else:  # posição dos filhos é relativa ao grupo e precisa caber nele
            g = json.loads(gf.read_text(encoding="utf-8"))["position"]; pos = v["position"]
            if pos["x"] + pos["width"] > g["width"] + 1 or pos["y"] + pos["height"] > g["height"] + 1:
                erros.append(f"elemento fora do grupo (posição deve ser relativa) em {rel}")
# Termos da empresa original ficam num arquivo local, fora do Git (um por linha)
_arq = Path(__file__).with_name("termos_proibidos.txt")
proibidos = [l.strip() for l in _arq.read_text(encoding="utf-8").splitlines() if l.strip()] if _arq.exists() else []
if not proibidos:
    print("AVISO: termos_proibidos.txt ausente; checagem de termos da empresa original desativada.")
for f in list((BASE / "powerbi").rglob("*.json")) + list((BASE / "powerbi").rglob("*.tmdl")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for p in proibidos:
        if re.search(rf"\b{re.escape(p)}\b", t) and "CY24SU10" not in f.name:
            if f.name == "expressions.tmdl":
                print(f"AVISO: o caminho padrão dos dados contém '{p}'. Mova a pasta do projeto e ajuste PASTA_PADRAO antes de publicar.")
            else:
                erros.append(f"termo '{p}' em {f.relative_to(BASE)}")
print("\n".join(erros) if erros else f"ok: {len(paginas)} páginas, {len(medidas)} medidas, nenhuma referência quebrada")
sys.exit(1 if erros else 0)
