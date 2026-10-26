"""
Gerador de dados sintéticos da TerraCode Academy (empresa fictícia).

Simula a operação comercial de uma escola de tecnologia com três pipelines
(Online, Presencial e Pós-graduação) entre jan/2024 e dez/2025.

Nenhum dado real é lido ou reproduzido aqui. Os parâmetros abaixo são
aproximações arredondadas e propositalmente alteradas, pensadas para gerar
um comportamento plausível de funil B2C (conversão, ciclo de venda,
sazonalidade, motivos de perda), não para espelhar uma empresa específica.

Saída: CSVs (UTF-8, separador vírgula, decimal ponto, datas ISO) em ../data
       e Parquet também, se o pyarrow estiver instalado
Uso:   python gerar_dados.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

INICIO = pd.Timestamp("2024-01-01")
FIM = pd.Timestamp("2025-12-31 23:59:59")
DATA_REFERENCIA = FIM  # "hoje" do dataset: o que fecharia depois disso fica em aberto

OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Dimensões estáticas
# ---------------------------------------------------------------------------
pipelines = pd.DataFrame({
    "id_pipeline": [1, 2, 3],
    "pipeline": ["Online", "Presencial", "Pós-graduação"],
    "ordem": [1, 2, 3],
})
MIX_PIPELINE = {1: 0.46, 2: 0.36, 3: 0.18}

# Etapas por pipeline (ordem = profundidade no funil)
ETAPAS_ABERTAS = {
    1: ["Novo lead", "Tentativa de contato", "Contatado", "Diagnóstico", "Objeção", "Fechamento"],
    2: ["Novo lead", "Tentativa de contato", "Apresentação", "Follow-up", "Negociação", "Fechamento"],
    3: ["Novo lead", "Tentativa de contato", "Contatado", "Diagnóstico", "Objeção", "Fechamento"],
}
linhas = []
for pid, etapas in ETAPAS_ABERTAS.items():
    for i, e in enumerate(etapas, start=1):
        linhas.append((pid, e, i, "Em aberto"))
    linhas += [(pid, "Ganho", 90, "Ganho"), (pid, "Perdido", 91, "Perdido"),
               (pid, "Desqualificado", 92, "Perdido")]
etapas = pd.DataFrame(linhas, columns=["id_pipeline", "etapa", "ordem_etapa", "status"])
# Fase genérica do funil, comparável entre pipelines (as etapas têm nomes diferentes em cada um)
FASES = {1: "1. Novo lead", 2: "2. Tentativa de contato", 3: "3. Contato feito",
         4: "4. Descoberta", 5: "5. Negociação", 6: "6. Fechamento"}
etapas["fase_funil"] = etapas.ordem_etapa.map(FASES).fillna(etapas.etapa)
etapas.insert(0, "id_etapa", range(1, len(etapas) + 1))
ID_ETAPA = {(r.id_pipeline, r.etapa): r.id_etapa for r in etapas.itertuples()}

# Vendedores fictícios, com entradas e saídas ao longo do período
vendedores = pd.DataFrame([
    # id, nome, pipeline, entrada, saída
    (1, "Ana Ribeiro", 1, "2024-01-01", None),
    (2, "Bruno Tavares", 1, "2024-01-01", "2024-09-30"),
    (3, "Carla Mendes", 1, "2024-01-01", None),
    (4, "Diego Santana", 1, "2024-01-01", None),
    (5, "Elisa Fonseca", 1, "2024-03-01", None),
    (6, "Felipe Araújo", 1, "2024-10-01", None),
    (7, "Gabriela Lins", 1, "2025-04-01", None),
    (8, "Henrique Paiva", 2, "2024-01-01", None),
    (9, "Isabela Duarte", 2, "2024-01-01", "2025-02-28"),
    (10, "João Pedro Castro", 2, "2024-01-01", None),
    (11, "Karina Moraes", 2, "2024-06-01", None),
    (12, "Lucas Prado", 2, "2025-03-01", None),
    (13, "Mariana Vieira", 3, "2024-01-01", None),
    (14, "Nicolas Barreto", 3, "2024-01-01", None),
    (15, "Olívia Campos", 3, "2025-01-01", None),
], columns=["id_vendedor", "vendedor", "id_pipeline", "data_entrada", "data_saida"])
vendedores["data_entrada"] = pd.to_datetime(vendedores["data_entrada"])
vendedores["data_saida"] = pd.to_datetime(vendedores["data_saida"])
vendedores["ativo"] = vendedores["data_saida"].isna()
# Desempenho relativo de cada vendedor (multiplica a chance de ganho)
PERFORMANCE = dict(zip(vendedores.id_vendedor, rng.normal(1.0, 0.18, len(vendedores)).clip(0.65, 1.4)))

# Fontes de entrada: nome técnico (como viria do CRM) + canal agrupado
fontes = pd.DataFrame([
    (1, "[CRM] Formulário site - levantada de mão", "Formulário do site", 1.0),
    (2, "[CRM] Plataforma gratuita - usuários engajados", "Plataforma gratuita", 0.35),
    (3, "[CRM] Inbound WhatsApp", "WhatsApp", 2.2),
    (4, "[CRM] Materiais ricos - envio para vendas", "Material rico", 0.45),
    (5, "[CRM] Carrinho abandonado", "Carrinho abandonado", 2.6),
    (6, "[CRM] Nutrição trial 7 dias", "Trial", 1.4),
    (7, "[B2C] Lista de renovação", "Renovação", 1.9),
    (8, "[CRM] Aula aberta / evento", "Evento", 0.8),
    (9, "[CRM] Formulário pós-graduação", "Formulário do site", 1.0),
    (10, "Criado manualmente pelo vendedor", "Criado pelo vendedor", 4.5),
    (11, "Fluxo sem nome", "Não identificado", 0.9),
], columns=["id_fonte", "fonte_crm", "canal", "_mult_ganho"])
MULT_FONTE = dict(zip(fontes.id_fonte, fontes._mult_ganho))
fontes = fontes.drop(columns="_mult_ganho")

MIX_FONTE = {  # por pipeline
    1: {1: .30, 2: .22, 3: .10, 4: .06, 5: .07, 6: .06, 7: .03, 8: .04, 10: .07, 11: .05},
    2: {1: .52, 2: .14, 3: .07, 4: .04, 7: .05, 8: .07, 10: .06, 11: .05},
    3: {9: .55, 3: .14, 4: .06, 8: .10, 10: .09, 11: .06},
}

motivos = pd.DataFrame([
    (1, "Parou de responder", "Sem resposta"),
    (2, "Nunca respondeu o contato", "Sem resposta"),
    (3, "Interesse futuro", "Timing"),
    (4, "Não é o momento", "Timing"),
    (5, "Comprou sozinho pelo site", "Autonomia / concorrência"),
    (6, "Fechou com concorrente", "Autonomia / concorrência"),
    (7, "Financeiro inviável", "Financeiro"),
    (8, "Achou caro", "Financeiro"),
    (9, "Sem interesse em seguir", "Fit"),
    (10, "Não tem graduação", "Fit"),
    (11, "Produto não atende", "Fit"),
    (12, "Lead duplicado", "Qualidade do dado"),
    (13, "Contato inválido", "Qualidade do dado"),
], columns=["id_motivo", "motivo", "categoria_motivo"])
MIX_MOTIVO_PERDA = {
    1: {1: .38, 2: .05, 3: .30, 4: .04, 5: .11, 6: .02, 7: .03, 8: .02, 9: .04, 11: .01},
    2: {1: .18, 2: .42, 3: .17, 4: .03, 5: .06, 6: .02, 7: .03, 8: .02, 9: .05, 11: .02},
    3: {1: .45, 2: .22, 3: .05, 4: .03, 7: .05, 8: .04, 9: .09, 10: .05, 12: .01, 13: .01},
}
MIX_MOTIVO_DESQ = {9: .45, 11: .20, 12: .20, 13: .15}

produtos = pd.DataFrame([
    (1, "Formação Full Stack", 1, 2290.0),
    (2, "Formação Dados & IA", 1, 2490.0),
    (3, "Trilha Fundamentos", 1, 1190.0),
    (4, "Assinatura Anual", 1, 1890.0),
    (5, "Bootcamp Presencial Web", 2, 2390.0),
    (6, "Bootcamp Presencial Dados", 2, 2590.0),
    (7, "Imersão de Fim de Semana", 2, 990.0),
    (8, "Pós em Engenharia de Software", 3, 7200.0),
    (9, "Pós em IA Aplicada", 3, 7900.0),
    (10, "MBA em Liderança Tech", 3, 8900.0),
], columns=["id_produto", "produto", "id_pipeline", "preco_lista"])
MIX_PRODUTO = {1: {1: .35, 2: .25, 3: .15, 4: .25}, 2: {5: .5, 6: .3, 7: .2}, 3: {8: .45, 9: .40, 10: .15}}
DESCONTOS = np.array([0, .05, .10, .15, .20])
P_DESCONTO = np.array([.40, .15, .25, .12, .08])

formas_pgto = pd.DataFrame([
    (1, "Cartão de crédito"), (2, "Pix"), (3, "Boleto parcelado"),
    (4, "Link de pagamento"), (5, "Recorrência mensal"),
], columns=["id_forma_pagamento", "forma_pagamento"])
MIX_PGTO = {1: {1: .55, 2: .18, 3: .07, 4: .05, 5: .15}, 2: {1: .60, 2: .22, 3: .08, 4: .10},
            3: {1: .40, 2: .10, 3: .35, 4: .05, 5: .10}}

# ---------------------------------------------------------------------------
# Calendário (com feriados nacionais para dias úteis)
# ---------------------------------------------------------------------------
FERIADOS = pd.to_datetime([
    "2024-01-01", "2024-02-12", "2024-02-13", "2024-03-29", "2024-04-21", "2024-05-01",
    "2024-05-30", "2024-09-07", "2024-10-12", "2024-11-02", "2024-11-15", "2024-11-20", "2024-12-25",
    "2025-01-01", "2025-03-03", "2025-03-04", "2025-04-18", "2025-04-21", "2025-05-01",
    "2025-06-19", "2025-09-07", "2025-10-12", "2025-11-02", "2025-11-15", "2025-11-20", "2025-12-25",
])
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
datas = pd.date_range(INICIO.normalize(), FIM.normalize(), freq="D")
cal = pd.DataFrame({"data": datas})
cal["ano"] = cal.data.dt.year
cal["mes"] = cal.data.dt.month
cal["nome_mes"] = cal.mes.map(lambda m: MESES[m - 1])
cal["mes_abrev"] = cal.nome_mes.str[:3]
cal["ano_mes"] = cal.data.dt.strftime("%Y-%m")
cal["inicio_mes"] = cal.data.dt.to_period("M").dt.to_timestamp()
cal["trimestre"] = "T" + cal.data.dt.quarter.astype(str)
cal["semana_iso"] = cal.data.dt.isocalendar().week.astype(int)
cal["dia"] = cal.data.dt.day
cal["dia_semana_num"] = cal.data.dt.dayofweek + 1
cal["dia_semana"] = cal.data.dt.dayofweek.map(lambda d: DIAS[d])
cal["dia_semana_abrev"] = cal.dia_semana.str[:3]
# Semana do mês (começando na segunda), usada no visual de calendário
offset = cal.data.dt.to_period("M").dt.to_timestamp().dt.dayofweek
cal["semana_mes"] = (cal.dia + offset - 1) // 7 + 1
cal["feriado"] = cal.data.isin(FERIADOS)
cal["dia_util"] = (cal.dia_semana_num <= 5) & ~cal.feriado

# ---------------------------------------------------------------------------
# Volume diário de leads (tendência + sazonalidade + dia da semana)
# ---------------------------------------------------------------------------
SAZON_MES = {1: 1.10, 2: .85, 3: .85, 4: 1.10, 5: 1.08, 6: 1.00, 7: 1.08,
             8: .80, 9: .90, 10: .95, 11: 1.30, 12: .70}
PESO_DIA_SEMANA = np.array([1.12, 1.15, 1.12, 1.08, 1.05, .60, .62])
BASE_DIA_2024 = 62.0
CRESC_ANUAL = 0.18

dias_corridos = (cal.data - INICIO).dt.days.values
tendencia = BASE_DIA_2024 * (1 + CRESC_ANUAL) ** (dias_corridos / 365)
lam = tendencia * cal.mes.map(SAZON_MES).values * PESO_DIA_SEMANA[cal.data.dt.dayofweek.values]
lam[(cal.mes == 11) & (cal.dia >= 20) & (cal.dia <= 30)] *= 1.6   # campanha de Black Friday
lam[cal.feriado.values] *= 0.5
qtd_dia = rng.poisson(lam)

PESO_HORA = np.array([.024, .013, .010, .014, .004, .006, .010, .019, .085, .070, .080, .065,
                      .058, .050, .060, .068, .064, .048, .042, .048, .049, .045, .042, .031])
PESO_HORA = PESO_HORA / PESO_HORA.sum()

n = int(qtd_dia.sum())
criacao = np.repeat(cal.data.values, qtd_dia)
segundos = rng.choice(24, n, p=PESO_HORA) * 3600 + rng.integers(0, 3600, n)
criacao = pd.to_datetime(criacao) + pd.to_timedelta(segundos, unit="s")

def amostra(mapa, tamanho):
    chaves = np.array(list(mapa.keys()))
    p = np.array(list(mapa.values()), dtype=float)
    return rng.choice(chaves, tamanho, p=p / p.sum())

df = pd.DataFrame({"data_criacao": criacao})
df["id_pipeline"] = amostra(MIX_PIPELINE, n)

# Fonte por pipeline
df["id_fonte"] = 0
for pid, mix in MIX_FONTE.items():
    m = df.id_pipeline == pid
    df.loc[m, "id_fonte"] = amostra(mix, m.sum())

# Vendedor: sorteado entre os ativos do pipeline no mês de criação
df["mes_ref"] = df.data_criacao.dt.to_period("M")
df["id_vendedor"] = 0
for (pid, mes), idx in df.groupby(["id_pipeline", "mes_ref"]).groups.items():
    ref = mes.to_timestamp() + pd.Timedelta(days=14)
    v = vendedores[(vendedores.id_pipeline == pid) & (vendedores.data_entrada <= ref)
                   & (vendedores.data_saida.isna() | (vendedores.data_saida >= ref))]
    df.loc[idx, "id_vendedor"] = rng.choice(v.id_vendedor.values, len(idx))

# ---------------------------------------------------------------------------
# Desfecho final de cada negócio
# ---------------------------------------------------------------------------
BASE_GANHO = {1: .075, 2: .055, 3: .07}
BASE_DESQ = {1: .20, 2: .22, 3: .05}
p_ganho = (df.id_pipeline.map(BASE_GANHO) * df.id_fonte.map(MULT_FONTE)
           * df.id_vendedor.map(PERFORMANCE)).clip(0, .75).values
p_desq = df.id_pipeline.map(BASE_DESQ).values
u = rng.random(n)
desfecho = np.where(u < p_ganho, "Ganho", np.where(u < p_ganho + p_desq, "Desqualificado", "Perdido"))
df["desfecho"] = desfecho

# Lead score condicionado ao desfecho (lognormal)
MED_SCORE = {"Ganho": 5200, "Perdido": 850, "Desqualificado": 600}
med = df.desfecho.map(MED_SCORE).values
df["lead_score"] = np.round(np.exp(np.log(med) + rng.normal(0, 1.05, n)) / 5) * 5
df.loc[df.id_fonte == 10, "lead_score"] = np.nan  # criados à mão não passam pelo scoring
df["lead_score"] = df.lead_score.clip(10, 60000)

# Tempo até o fechamento (dias, lognormal por desfecho e pipeline)
CICLO = {  # (mediana em dias, sigma)
    ("Ganho", 1): (1.2, 1.9), ("Ganho", 2): (1.0, 1.7), ("Ganho", 3): (1.5, 1.6),
    ("Perdido", 1): (55, 1.0), ("Perdido", 2): (28, 1.0), ("Perdido", 3): (14, .8),
    ("Desqualificado", 1): (3, 1.2), ("Desqualificado", 2): (3, 1.2), ("Desqualificado", 3): (2, 1.0),
}
ciclo = np.empty(n)
for (d, pid), (mediana, sigma) in CICLO.items():
    m = ((df.desfecho == d) & (df.id_pipeline == pid)).values
    ciclo[m] = np.exp(np.log(mediana) + rng.normal(0, sigma, m.sum()))
ciclo = np.clip(ciclo, 0.01, 400)
fechamento = df.data_criacao + pd.to_timedelta(ciclo, unit="D")
# Fechamentos caem em horário comercial e quase nunca no fim de semana
fechamento = fechamento.dt.normalize() + pd.to_timedelta(rng.integers(9 * 3600, 19 * 3600, n), unit="s")
fim_de_semana = fechamento.dt.dayofweek >= 5
fechamento[fim_de_semana] += pd.to_timedelta(7 - fechamento[fim_de_semana].dt.dayofweek, unit="D")
fechamento = fechamento.where(fechamento > df.data_criacao, df.data_criacao + pd.Timedelta(minutes=20))
df["data_fechamento"] = fechamento

# O que fecharia depois da data de referência ainda está em aberto
aberto = df.data_fechamento > DATA_REFERENCIA
# Uma parcela pequena fica "esquecida" em aberto (negócios parados no CRM)
aberto |= (rng.random(n) < 0.015) & (df.desfecho == "Perdido")
df["status"] = np.where(aberto, "Em aberto", np.where(df.desfecho == "Ganho", "Ganho", "Perdido"))
df.loc[aberto, "data_fechamento"] = pd.NaT

# Etapa atual (abertos) e etapa máxima atingida (todos)
PESO_ETAPA_ABERTO = np.array([.08, .55, .14, .10, .08, .05])
PESO_ETAPA_PERDA = np.array([.06, .52, .16, .12, .10, .04])
etapa_atual, etapa_max = [], []
for st, d, pid in zip(df.status.values, df.desfecho.values, df.id_pipeline.values):
    lista = ETAPAS_ABERTAS[pid]
    if st == "Em aberto":
        e = rng.choice(lista, p=PESO_ETAPA_ABERTO)
        etapa_atual.append(e); etapa_max.append(e)
    elif d == "Ganho":
        etapa_atual.append("Ganho"); etapa_max.append("Fechamento")
    elif d == "Desqualificado":
        etapa_atual.append("Desqualificado"); etapa_max.append(rng.choice(lista[:2], p=[.4, .6]))
    else:
        etapa_atual.append("Perdido"); etapa_max.append(rng.choice(lista, p=PESO_ETAPA_PERDA))
df["id_etapa"] = [ID_ETAPA[(p, e)] for p, e in zip(df.id_pipeline, etapa_atual)]
df["id_etapa_maxima"] = [ID_ETAPA[(p, e)] for p, e in zip(df.id_pipeline, etapa_max)]
df["ordem_etapa_maxima"] = df.id_etapa_maxima.map(dict(zip(etapas.id_etapa, etapas.ordem_etapa)))

# Motivo de perda (principal) e quantidade de motivos marcados
df["id_motivo_perda"] = pd.array([pd.NA] * n, dtype="Int64")
for pid, mix in MIX_MOTIVO_PERDA.items():
    m = (df.status == "Perdido") & (df.desfecho == "Perdido") & (df.id_pipeline == pid)
    df.loc[m, "id_motivo_perda"] = amostra(mix, m.sum())
m = (df.status == "Perdido") & (df.desfecho == "Desqualificado")
df.loc[m, "id_motivo_perda"] = amostra(MIX_MOTIVO_DESQ, m.sum())
df["qtd_motivos_perda"] = np.where(df.id_motivo_perda.notna(), 1 + (rng.random(n) < .07), 0)

# Produto, valor e forma de pagamento (só ganhos)
ganho = df.status == "Ganho"
df["id_produto"] = pd.array([pd.NA] * n, dtype="Int64")
df["id_forma_pagamento"] = pd.array([pd.NA] * n, dtype="Int64")
for pid in (1, 2, 3):
    m = ganho & (df.id_pipeline == pid)
    df.loc[m, "id_produto"] = amostra(MIX_PRODUTO[pid], m.sum())
    df.loc[m, "id_forma_pagamento"] = amostra(MIX_PGTO[pid], m.sum())
preco = df.id_produto.map(dict(zip(produtos.id_produto, produtos.preco_lista))).astype(float)
desconto = rng.choice(DESCONTOS, n, p=P_DESCONTO)
df["desconto_pct"] = np.where(ganho, desconto, np.nan)
df["valor"] = np.where(ganho, np.round(preco * (1 - desconto), 2), np.nan)
# Reajuste de preço em 2025
df.loc[ganho & (df.data_criacao.dt.year == 2025), "valor"] = (df.valor * 1.06).round(2)

df = df.sort_values("data_criacao").reset_index(drop=True)
df.insert(0, "id_negocio", ["NEG-" + str(i).zfill(6) for i in range(1, len(df) + 1)])
df["ciclo_dias"] = ((df.data_fechamento - df.data_criacao).dt.total_seconds() / 86400).round(2)

fato_negocios = df[["id_negocio", "data_criacao", "data_fechamento", "status", "id_pipeline",
                    "id_vendedor", "id_fonte", "id_etapa", "id_etapa_maxima", "ordem_etapa_maxima", "lead_score",
                    "id_motivo_perda", "qtd_motivos_perda", "id_produto", "id_forma_pagamento",
                    "desconto_pct", "valor", "ciclo_dias"]].copy()

# ---------------------------------------------------------------------------
# Metas mensais por vendedor (com ano)
# Meta = média móvel dos 3 meses anteriores do vendedor * fator de desafio
# ---------------------------------------------------------------------------
g = fato_negocios[fato_negocios.status == "Ganho"].copy()
g["inicio_mes"] = g.data_fechamento.dt.to_period("M").dt.to_timestamp()
real = g.groupby(["id_vendedor", "inicio_mes"]).valor.sum()
metas = []
for v in vendedores.itertuples():
    fim = v.data_saida if pd.notna(v.data_saida) else FIM
    meses = pd.date_range(v.data_entrada.to_period("M").to_timestamp(), fim, freq="MS")
    media_pipe = g[g.id_pipeline == v.id_pipeline].groupby("inicio_mes").valor.sum().mean() / \
        vendedores[vendedores.id_pipeline == v.id_pipeline].shape[0] * 1.3
    hist = []
    for mes in meses:
        base = np.mean(hist[-3:]) if len(hist) >= 2 else media_pipe * .6
        fator = rng.uniform(1.0, 1.25)
        if mes.month == 11: fator *= 1.25
        meta = max(15000, round(base * fator / 5000) * 5000)
        metas.append((mes, v.id_vendedor, v.id_pipeline, meta))
        hist.append(real.get((v.id_vendedor, mes), 0))
fato_metas = pd.DataFrame(metas, columns=["inicio_mes", "id_vendedor", "id_pipeline", "meta"])

# ---------------------------------------------------------------------------
# Conversas de atendimento por hora (canal de mensagens)
# ---------------------------------------------------------------------------
PICO_HORA = np.array([.010, .008, .003, .003, .002, .003, .006, .012, .030, .060, .085, .095,
                      .080, .060, .062, .090, .075, .068, .045, .035, .030, .016, .012, .010])
PICO_HORA = PICO_HORA / PICO_HORA.sum()
leads_dia = pd.Series(qtd_dia, index=cal.data)
conv = []
for d, q in leads_dia.items():
    total = q * rng.uniform(1.4, 1.9)
    if d.dayofweek == 0:  # segunda tem disparo de campanha às 15h
        pesos = PICO_HORA.copy(); pesos[15] *= 2.5; pesos /= pesos.sum()
    else:
        pesos = PICO_HORA
    qtd = rng.poisson(total * pesos)
    conv += [(d, h, int(c)) for h, c in enumerate(qtd) if c > 0]
fato_conversas = pd.DataFrame(conv, columns=["data", "hora", "qtd_conversas"])

# ---------------------------------------------------------------------------
# Exportação
# ---------------------------------------------------------------------------
tabelas = {
    "dim_calendario": cal,
    "dim_pipeline": pipelines,
    "dim_etapa": etapas,
    "dim_vendedor": vendedores,
    "dim_fonte": fontes,
    "dim_motivo_perda": motivos,
    "dim_produto": produtos,
    "dim_forma_pagamento": formas_pgto,
    "fato_negocios": fato_negocios,
    "fato_metas": fato_metas,
    "fato_conversas": fato_conversas,
}
try:
    import pyarrow  # noqa: F401
    GERA_PARQUET = True
except ImportError:
    GERA_PARQUET = False

# Colunas de data pura saem sem horário
SO_DATA = {"dim_calendario": ["data", "inicio_mes"], "dim_vendedor": ["data_entrada", "data_saida"],
           "fato_metas": ["inicio_mes"], "fato_conversas": ["data"]}
for nome, cols in SO_DATA.items():
    for c in cols:
        tabelas[nome][c] = pd.to_datetime(tabelas[nome][c]).dt.date

for nome, t in tabelas.items():
    t.to_csv(OUT / f"{nome}.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    if GERA_PARQUET:
        t.to_parquet(OUT / f"{nome}.parquet", index=False)
    print(f"{nome:22s} {len(t):>7,} linhas")
