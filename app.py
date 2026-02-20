import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from reportlab.platypus import Image
from reportlab.lib.units import cm
import os
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
import plotly.io as pio
pio.defaults.mathjax = None

# Janelas reais de plantio por cultura
janela_plantio = {
    "Soja": ((9, 1), (1, 31)),      # set → jan
    "Arroz": ((11, 1), (1, 31)),    # nov → jan
    "Arroz (Médio)": ((11, 1), (1, 31))
}

def dentro_janela(data, inicio, fim):
    ano = data.year
    inicio_dt = pd.Timestamp(ano, inicio[0], inicio[1])
    fim_dt = pd.Timestamp(ano + 1, fim[0], fim[1])
    return inicio_dt <= data <= fim_dt

mask = []

def fmt_int(valor):
    return f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_float(valor, casas=1):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def estilizar_figura_pdf(fig, titulo=None):

    fig.update_layout(
        title=dict(
            text=titulo,
            font=dict(size=26)  # 🔥 TÍTULO GRANDE
        ),
        font=dict(
            family="Arial",
            size=20,            # 🔥 FONTE BASE MAIOR
            color="black"
        ),
        xaxis=dict(
            title_font=dict(size=22),
            tickfont=dict(size=18),
            gridcolor="#DDDDDD"
        ),
        yaxis=dict(
            title_font=dict(size=22),
            tickfont=dict(size=18),
            gridcolor="#DDDDDD"
        ),
        legend=dict(
            font=dict(size=18),
            bgcolor="rgba(255,255,255,0.85)"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=80, r=50, t=100, b=80),
        separators=".,"
    )

    fig.update_traces(
        textfont=dict(size=18),
        marker_line_width=0
    )

    return fig



def salvar_grafico(fig, caminho):
    try:
        fig.write_image(
            caminho,
            format="png",
            width=1600,
            height=900,
            scale=2
        )
    except Exception as e:
        print("Erro ao salvar gráfico:", e)

from reportlab.lib.pagesizes import A4

def fundo_capa(canvas, doc):
    canvas.saveState()
    if os.path.exists("1.png"):
        canvas.drawImage("1.png", 0, 0, width=A4[0], height=A4[1])
    canvas.restoreState()


def fundo_interno(canvas, doc):
    canvas.saveState()
    if os.path.exists("2.png"):
        canvas.drawImage("2.png", 0, 0, width=A4[0], height=A4[1])
    canvas.restoreState()


PALETA_CORES = {
    "Soja": "#2E7D32",          # verde
    "Arroz": "#6AEA6A",         # azul
    "Arroz (Médio)": "#FBAB00"  # roxo
}

def aplicar_formato_ptbr(fig, casas_decimais=2):

    fig.update_layout(
        separators=",."
    )

    fig.update_yaxes(
        tickformat=f".,{casas_decimais}f",
        separatethousands=True
    )

    return fig



def gerar_pdf(df_plantio, df_colheita, ranking, org, periodo, cenario,
              inicio_min, fim_max, inicio_medio, fim_medio):

    arquivo_pdf = "relatorio_planejamento_agricola.pdf"

    doc = SimpleDocTemplate(
        arquivo_pdf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    styles["Title"].alignment = TA_CENTER

    estilos_personalizados = ParagraphStyle(
        name='SubTitulo',
        parent=styles['Heading2'],
        spaceAfter=10
    )
    styles.add(estilos_personalizados)

    elementos = []

    # =====================================================
    # 📄 1. CAPA
    # =====================================================
    elementos.append(Spacer(1, 4*cm))
    elementos.append(Paragraph(
        "<b>RELATÓRIO DE PLANEJAMENTO AGRÍCOLA</b>",
        styles["Title"]
    ))
    elementos.append(Spacer(1, 24))

    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

    qtd_orgs = (
        df_plantio["Organizações"].nunique()
        if org == "GERAL" else 1
    )

    elementos.append(Paragraph(f"""  
        <b>Organização:</b> {org}<br/>
        <b>Quantidade de organizações:</b> {qtd_orgs}<br/>
        <b>Período analisado:</b> {periodo}<br/><br/>

        <b>Área total semeada:</b>
        {fmt_int(df_plantio['Área Semeada'].sum())} ha<br/>

        <b>Período de plantio:</b>
        {df_plantio['Primeiro Semeado'].min():%d/%m/%Y}
        a
        {df_plantio['Última Semeadura'].max():%d/%m/%Y}<br/><br/>

        <b>Data de geração do relatório:</b><br/>
        {data_geracao}
    """, styles["Normal"]))

    elementos.append(PageBreak())

    # =====================================================
    # 📄 2. ANÁLISE DE PLANTIO
    # =====================================================
    elementos.append(Paragraph(
        "<b>1. Análise de Plantio</b>",
        styles["Heading1"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"""
        O plantio analisado refere-se à organização <b>{org}</b>,
        considerando <b>{periodo}</b>. A área total semeada é de
        <b>{fmt_int(df_plantio['Área Semeada'].sum())} hectares</b>.<br/><br/>

        Observa-se concentração operacional nos períodos com maior
        volume de registros no gráfico de dispersão, refletindo
        estratégia de escalonamento produtivo.
    """, styles["Normal"]))

    elementos.append(Spacer(1, 18))

    # Gráficos Plantio
    for grafico in [
        "grafico_soja_scatter.png",
        "grafico_soja_bar.png",
        "grafico_arroz_scatter.png",
        "grafico_arroz_bar.png"
    ]:
        if os.path.exists(grafico):
            elementos.append(Image(grafico, width=16*cm, height=9*cm))
            elementos.append(Spacer(1, 18))

    # 🔽 RESUMO POR CULTURA (ABAIXO DOS GRÁFICOS)
    elementos.append(Paragraph(
        "<b>Resumo de Área Semeada por Cultura</b>",
        styles["SubTitulo"]
    ))
    elementos.append(Spacer(1, 6))

    for cultura in df_plantio["Tipo de Cultura"].unique():

        df_p = df_plantio[df_plantio["Tipo de Cultura"] == cultura]

        if df_p.empty:
            continue

        elementos.append(Paragraph(f"""
            <b>{cultura}</b><br/>
            Área semeada: <b>{fmt_int(df_p["Área Semeada"].sum())} ha</b><br/>
            Período:
            <b>{df_p["Primeiro Semeado"].min():%d/%m/%Y}</b>
            a
            <b>{df_p["Última Semeadura"].max():%d/%m/%Y}</b>
        """, styles["Normal"]))

        elementos.append(Spacer(1, 6))

    # =====================================================
    # 📄 3. ESTIMATIVA DE COLHEITA
    # =====================================================
    elementos.append(Paragraph(
        "<b>2. Estimativa de Colheita</b>",
        styles["Heading1"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"""
        A colheita foi estimada com base nas datas de semeadura
        e ciclos médios agronômicos.<br/><br/>

        <b>Soja:</b> 90 a 120 dias<br/>
        <b>Arroz:</b> 100 a 150 dias<br/><br/>

        Janela consolidada:
        <b>{inicio_min:%d/%m/%Y}</b> a
        <b>{fim_max:%d/%m/%Y}</b><br/><br/>

        Período médio de concentração:
        <b>{inicio_medio:%d/%m/%Y}</b> a
        <b>{fim_medio:%d/%m/%Y}</b>
    """, styles["Normal"]))

    elementos.append(Spacer(1, 18))

    if os.path.exists("grafico_colheita.png"):
        elementos.append(Image("grafico_colheita.png", width=16*cm, height=9*cm))
        elementos.append(Spacer(1, 18))

    # Resumo por cultura
    for cultura in df_colheita["Tipo de Cultura"].unique():

        df_c = df_colheita[df_colheita["Tipo de Cultura"] == cultura]

        if df_c.empty:
            continue

        elementos.append(Paragraph(f"""
            <b>{cultura}</b><br/>
            Janela prevista:
            <b>{df_c["Inicio_Colheita"].min():%d/%m/%Y}</b>
            a
            <b>{df_c["Fim_Colheita"].max():%d/%m/%Y}</b>
        """, styles["Normal"]))

        elementos.append(Spacer(1, 12))

    elementos.append(PageBreak())

    # =====================================================
    # 📄 4. CRONOGRAMA AGRÍCOLA
    # =====================================================
    elementos.append(Paragraph(
        "<b>3. Linha do Tempo Operacional</b>",
        styles["Heading1"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("""
        O cronograma apresenta a linha do tempo consolidada
        das fases operacionais, permitindo visualizar
        sobreposição de atividades e picos operacionais.
    """, styles["Normal"]))

    elementos.append(Spacer(1, 18))

    if os.path.exists("grafico_gantt.png"):
        elementos.append(Image("grafico_gantt.png", width=16*cm, height=9*cm))

    elementos.append(PageBreak())

    # =====================================================
    # 📄 5. RANKING
    # =====================================================
    elementos.append(Paragraph(
        "<b>4. Ranking de Clientes por Área Plantada</b>",
        styles["Heading1"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("""
        Ranking das organizações ordenadas pela maior área plantada,
        incluindo janela estimada e pico de colheita.
    """, styles["Normal"]))

    elementos.append(Spacer(1, 18))

    dados_tabela = [[
        "Pos.",
        "Organização",
        "Área (ha)",
        "Janela de Colheita",
        "Pico"
    ]]

    for _, row in ranking.iterrows():
        dados_tabela.append([
            row["Posição"],
            row["Organizações"],
            row["Área (ha)"],
            row["Janela de Colheita"],
            row["Pico da Colheita"]
        ])

    tabela = Table(dados_tabela, repeatRows=1)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.whitesmoke, colors.lightgrey])
    ]))

    elementos.append(tabela)

    doc.build(
        elementos,
        onFirstPage=fundo_capa,
        onLaterPages=fundo_interno
    )

    return arquivo_pdf

st.set_page_config(page_title="Planejamento Agrícola", layout="wide")

arquivo = st.sidebar.file_uploader("Envie o arquivo Excel (.xlsx)", type=["xlsx"])
if not arquivo:
    st.info("⬅️ Envie um arquivo Excel para iniciar")
    st.stop()

@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados(arquivo):
    xls = pd.ExcelFile(arquivo)
    dfs = []

    for aba in xls.sheet_names:
        df_temp = pd.read_excel(arquivo, sheet_name=aba)

        df_temp.columns = (
            df_temp.columns.astype(str)
            .str.strip()
            .str.replace("\n", " ")
        )

        colunas = {
            "Organizações",
            "Tipo de Cultura",
            "Área Semeada",
            "Primeiro Semeado",
            "Última Semeadura"
        }

        if colunas.issubset(df_temp.columns):
            dfs.append(df_temp)

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)

    df["Organizações"] = (
        df["Organizações"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return df

df = carregar_dados(arquivo)
if df is None:
    st.error("❌ Nenhuma aba válida encontrada no arquivo.")
    st.stop()

MESES_PT = {
    "jan": "Jan", "fev": "Feb", "mar": "Mar", "abr": "Apr",
    "mai": "May", "jun": "Jun", "jul": "Jul", "ago": "Aug",
    "set": "Sep", "out": "Oct", "nov": "Nov", "dez": "Dec"
}

def converte_data_mista(coluna):
    datas = pd.to_datetime(coluna, errors="coerce")
    mask = datas.isna() & coluna.notna()

    if mask.any():
        textos = coluna[mask].astype(str).str.lower()
        for pt, en in MESES_PT.items():
            textos = textos.str.replace(pt, en, regex=False)

        datas.loc[mask] = pd.to_datetime(
            textos, format="mixed", errors="coerce"
        )

    return datas

df["Primeiro Semeado"] = converte_data_mista(df["Primeiro Semeado"])
df["Última Semeadura"] = converte_data_mista(df["Última Semeadura"])

df["Ano"] = df["Primeiro Semeado"].dt.year

df["Mes_Num"] = df["Primeiro Semeado"].dt.month

# Ano safra (base agrícola)
df["Ano_Safra"] = df["Ano"]

df.loc[df["Mes_Num"] <= 1, "Ano_Safra"] = df["Ano"] - 1


df["Mes_Nome"] = df["Mes_Num"].map({
    1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
    7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"
})

df["Mes_Ano"] = (
    df["Mes_Nome"] + "/" +
    df["Ano"].astype(str)
)

df["Dia"] = df["Primeiro Semeado"].dt.day

def calcular_terco(dia):
    if dia <= 10:
        return "1º Terço"
    elif dia <= 20:
        return "2º Terço"
    else:
        return "3º Terço"

df["Terço"] = df["Dia"].apply(calcular_terco)

df["Mes_Ano_Terco"] = (
    df["Mes_Ano"].astype(str) + " - " + df["Terço"]
)

# ordenar corretamente
ordem_mes_ano_terco = (
    df.sort_values("Primeiro Semeado")["Mes_Ano_Terco"]
    .unique()
    .tolist()
)

df["Mes_Ano_Terco"] = pd.Categorical(
    df["Mes_Ano_Terco"],
    categories=ordem_mes_ano_terco,
    ordered=True
)

ordem_mes_ano = (
    df[["Primeiro Semeado", "Mes_Ano"]]
    .dropna()
    .sort_values("Primeiro Semeado")["Mes_Ano"]
    .unique()
    .tolist()
)

df["Mes_Ano"] = pd.Categorical(df["Mes_Ano"], categories=ordem_mes_ano, ordered=True)


ciclo_min = {"Soja": 90, "Arroz": 100, "Arroz (Médio)": 100}
ciclo_max = {"Soja": 120, "Arroz": 150, "Arroz (Médio)": 150}

orgs = sorted(df["Organizações"].dropna().unique())
org = st.sidebar.selectbox("🏢 Organização", ["GERAL"] + orgs)

anos = sorted(df["Ano"].dropna().unique())
ano_sel = st.sidebar.selectbox("📅 Ano", ["TODOS"] + anos)

df_plantio = df.copy()

if org != "GERAL":
    df_plantio = df_plantio[df_plantio["Organizações"] == org]

if ano_sel != "TODOS":
    df_plantio = df_plantio[df_plantio["Ano_Safra"] == ano_sel]

if df_plantio.empty:
    st.warning("⚠️ Nenhum dado encontrado para o filtro selecionado.")
    st.stop()

st.subheader("Indicadores")

k1, k2, k3 = st.columns(3)
k1.metric(
    "Área Total (ha)",
    fmt_int(df_plantio["Área Semeada"].sum())
)

primeiro = df_plantio["Primeiro Semeado"].min()
ultimo = df_plantio["Última Semeadura"].max()

k2.metric("Primeiro Semeado",
          primeiro.strftime("%d/%m/%Y") if pd.notna(primeiro) else "-")

k3.metric("Última Semeadura",
          ultimo.strftime("%d/%m/%Y") if pd.notna(ultimo) else "-")

area_mes_ano = (
    df_plantio
    .groupby(["Mes_Ano", "Tipo de Cultura"], observed=True)["Área Semeada"]
    .sum()
    .reset_index()
) 

area_mes_terco = (
    df_plantio
    .groupby(["Mes_Ano_Terco", "Tipo de Cultura"], observed=True)["Área Semeada"]
    .sum()
    .reset_index()
)

area_mes_terco["Mes_Ano"] = (
    area_mes_terco["Mes_Ano_Terco"]
    .str.split(" - ")
    .str[0]
)

area_mes_terco["Terço"] = (
    area_mes_terco["Mes_Ano_Terco"]
    .str.split(" - ")
    .str[1]
)

org_mes_ano = (
    df_plantio
    .groupby(["Mes_Ano", "Tipo de Cultura"], observed=True)
    .agg({
        "Área Semeada": "sum",
        "Organizações": "nunique"   # 👈 conta organizações únicas
    })
    .reset_index()
    .rename(columns={"Organizações": "Qtd_Organizações"})
)

st.subheader("Plantio por Mês/Ano")  
 
st.markdown("### Soja")


fig_soja_scatter = px.scatter(
    org_mes_ano[org_mes_ano["Tipo de Cultura"] == "Soja"],
    x="Mes_Ano",
    y="Área Semeada",
    size="Qtd_Organizações",
    color="Tipo de Cultura",
    text="Qtd_Organizações",  # 👈 ADICIONA TEXTO
    color_discrete_map={"Soja": PALETA_CORES["Soja"]},
    labels={
        "Mes_Ano": "Mês/Ano",
        "Área Semeada": "Área Semeada (ha)",
        "Qtd_Organizações": "Nº Organizações"
    },
    size_max=60,
    opacity=0.75
)

fig_soja_scatter.update_traces(
    mode="markers+text",        # 👈 ATIVA TEXTO
    textposition="middle center",
    textfont=dict(color="white", size=14),
    marker_line_width=0
)

  
fig_soja_scatter = aplicar_formato_ptbr(fig_soja_scatter, casas_decimais=2)
fig_soja_scatter = estilizar_figura_pdf(fig_soja_scatter)
st.plotly_chart(fig_soja_scatter, use_container_width=True)

#salvar_grafico(fig_soja_scatter, "grafico_soja_scatter.png")

fig_soja_bar = px.bar(
    area_mes_terco[
        area_mes_terco["Tipo de Cultura"] == "Soja"
    ],
    x="Mes_Ano",              # agora existe
    y="Área Semeada",
    color="Terço",            # agora existe
    color_discrete_map={
        "1º Terço": "#1fb469",
        "2º Terço": "#018101",
        "3º Terço": "#01660a"
    },
    barmode="group"
)

fig_soja_bar.update_layout(
    bargap=0.05,
    bargroupgap=0.02,
    xaxis_title="Mês/Ano",
    yaxis_title="Área Semeada (ha)",
    legend_title="Terço"
)

fig_soja_bar = aplicar_formato_ptbr(fig_soja_bar, casas_decimais=2)
fig_soja_bar = estilizar_figura_pdf(fig_soja_bar)

st.plotly_chart(fig_soja_bar, use_container_width=True)
#salvar_grafico(fig_soja_bar, "grafico_soja_bar.png")



st.markdown("### Arroz")

fig_arroz_scatter = px.scatter(
    org_mes_ano[
        org_mes_ano["Tipo de Cultura"].isin(["Arroz", "Arroz (Médio)"])
    ],
    x="Mes_Ano",
    y="Área Semeada",
    size="Qtd_Organizações",
    color="Tipo de Cultura",
    text="Qtd_Organizações",   # 👈 ADICIONA TEXTO
    color_discrete_map=PALETA_CORES,
    labels={
        "Mes_Ano": "Mês/Ano",
        "Área Semeada": "Área Semeada (ha)",
        "Qtd_Organizações": "Nº Organizações"
    },
    size_max=60,
    opacity=0.75
)

fig_arroz_scatter.update_traces(
    mode="markers+text",
    textposition="middle center",
    textfont=dict(color="white", size=14),
    marker_line_width=0
)


fig_arroz_scatter = aplicar_formato_ptbr(fig_arroz_scatter, casas_decimais=2)
fig_arroz_scatter = estilizar_figura_pdf(fig_arroz_scatter)
st.plotly_chart(fig_arroz_scatter, use_container_width=True)

#salvar_grafico(fig_arroz_scatter, "grafico_arroz_scatter.png")


fig_arroz_bar = px.bar(
    area_mes_terco[
        area_mes_terco["Tipo de Cultura"].isin(["Arroz", "Arroz (Médio)"])
    ],
    x="Mes_Ano",
    y="Área Semeada",
    color="Terço",
    color_discrete_map={
        "1º Terço": "#1fb469",
        "2º Terço": "#018101",
        "3º Terço": "#01660a"
    },
    barmode="group"
)

fig_arroz_bar.update_layout(
    bargap=0.05,
    bargroupgap=0.02,
    xaxis_title="Mês/Ano",
    yaxis_title="Área Semeada (ha)",
    legend_title="Terço"
)

fig_arroz_bar = estilizar_figura_pdf(fig_arroz_bar)

st.plotly_chart(fig_arroz_bar, use_container_width=True)
#salvar_grafico(fig_arroz_bar, "grafico_arroz_bar.png")


periodo = "todos os anos" if ano_sel == "TODOS" else f"o ano de {ano_sel}"

for cultura, area in df_plantio.groupby("Tipo de Cultura")["Área Semeada"].sum().items():
    df_c = df_plantio[df_plantio["Tipo de Cultura"] == cultura]

produtividade_media = {
    "Soja": 52,
    "Arroz": 180.9,
    "Arroz (Médio)": 150
}

df_plantio["Produtividade Média (sc/ha)"] = (
    df_plantio["Tipo de Cultura"].map(produtividade_media)
)


cenario = st.sidebar.selectbox(
    "Cenário de Produtividade",
    ["Conservador", "Provável", "Otimista"]
)

fator_cenario = {
    "Conservador": 0.80,
    "Provável": 1.00,
    "Otimista": 1.10
}[cenario]

df_plantio["Produtividade Ajustada (sc/ha)"] = (
    df_plantio["Produtividade Média (sc/ha)"] * fator_cenario
)

df_plantio["Produção Estimada (sacas)"] = (
    df_plantio["Área Semeada"] *
    df_plantio["Produtividade Ajustada (sc/ha)"]
)

df_colheita = (
    df_plantio
    .groupby(["Organizações", "Tipo de Cultura"], as_index=False)
    .agg({
        "Área Semeada": "sum",
        "Produtividade Ajustada (sc/ha)": "mean",
        "Produção Estimada (sacas)": "sum",
        "Última Semeadura": "max"
    })
)

# dias de ciclo (janela real)
df_colheita["Dias_Inicio"] = df_colheita["Tipo de Cultura"].map(ciclo_min)
df_colheita["Dias_Fim"]    = df_colheita["Tipo de Cultura"].map(ciclo_max)

# datas previstas por cultura/organização
df_colheita["Inicio_Colheita"] = (
    df_colheita["Última Semeadura"]
    + pd.to_timedelta(df_colheita["Dias_Inicio"], unit="D")
)

df_colheita["Fim_Colheita"] = (
    df_colheita["Última Semeadura"]
    + pd.to_timedelta(df_colheita["Dias_Fim"], unit="D")
)

def media_ponderada(datas, pesos):
    return pd.to_datetime(
        (datas.astype("int64") * pesos).sum() / pesos.sum()
    )


# janela total da safra
inicio_min = df_colheita["Inicio_Colheita"].min()
fim_max    = df_colheita["Fim_Colheita"].max()

# pico de colheita (mais representativo)
inicio_medio = media_ponderada(
    df_colheita["Inicio_Colheita"],
    df_colheita["Área Semeada"]
)

fim_medio = media_ponderada(
    df_colheita["Fim_Colheita"],
    df_colheita["Área Semeada"]
)

# 👉 SE NÃO HOUVER DADOS, PARA AQUI
if df_colheita.empty:
    st.warning("⚠️ Não há dados suficientes para calcular a colheita.")
    st.stop()

mapa_meses = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

df_colheita["Mes_Ano_Colheita"] = (
    df_colheita["Inicio_Colheita"].dt.month.map(mapa_meses)
    + "/" +
    df_colheita["Inicio_Colheita"].dt.year.astype(str)
)

assert "Inicio_Colheita" not in df_plantio.columns
assert {"Inicio_Colheita", "Fim_Colheita"}.issubset(df_colheita.columns)

st.subheader("Distribuição da Colheita por Mês/Ano")

colheita_mes = (
    df_colheita
    .groupby(["Mes_Ano_Colheita", "Tipo de Cultura"], observed=True)
    .agg({
        "Produção Estimada (sacas)": "sum",
        "Organizações": "nunique"   # 👈 conta organizações únicas
    })
    .reset_index()
    .rename(columns={"Organizações": "Qtd_Organizacoes"})
)

ordem_meses = (
    df_colheita
    .sort_values("Inicio_Colheita")["Mes_Ano_Colheita"]
    .unique()
    .tolist()
)

# Garantir que não exista NaN
colheita_mes["Qtd_Organizacoes"] = (
    colheita_mes["Qtd_Organizacoes"]
    .fillna(0)
    .astype(int)
)

fig_colheita = px.scatter(
    colheita_mes,
    x="Mes_Ano_Colheita",
    y="Produção Estimada (sacas)",
    size="Qtd_Organizacoes",
    color="Tipo de Cultura",
    text="Qtd_Organizacoes",  # 👈 ADICIONA O TEXTO
    color_discrete_map=PALETA_CORES,
    category_orders={"Mes_Ano_Colheita": ordem_meses},
    size_max=60,
    opacity=0.75,
    title=f"Distribuição da Colheita – Cenário {cenario}",
    labels={
        "Produção Estimada (sacas)": "Produção (sacas)",
        "Mes_Ano_Colheita": "Mês/Ano",
        "Qtd_Organizacoes": "Nº Organizações"
    }
)

fig_colheita.update_traces(
    mode="markers+text",              # 👈 ativa texto
    textposition="middle center",     # 👈 centraliza
    textfont=dict(color="white", size=14),
    marker_line_width=0
)

fig_colheita.update_layout(
    xaxis_title="Meses/Ano da Colheita",
    yaxis_title=""
)

fig_colheita = aplicar_formato_ptbr(fig_colheita, casas_decimais=2)
fig_colheita = estilizar_figura_pdf(fig_colheita)

st.plotly_chart(fig_colheita, use_container_width=True)
#salvar_grafico(fig_colheita, "grafico_colheita.png")



# =========================================================


# consolida por cultura (não por organização)
df_base = (
    df_plantio
    .groupby("Tipo de Cultura", as_index=False)
    .agg(
        Inicio_Plantio=("Primeiro Semeado", "min"),
        Fim_Plantio=("Última Semeadura", "max")
    )
)

gantt_rows = []

for _, row in df_base.iterrows():

    cultura = row["Tipo de Cultura"]

    inicio_plantio = pd.to_datetime(row["Inicio_Plantio"])
    fim_plantio    = pd.to_datetime(row["Fim_Plantio"])

    # ciclo mínimo e máximo
    dias_min = ciclo_min.get(cultura, 10)
    dias_max = ciclo_max.get(cultura, 70)

    # ==========================
    # COLHEITA (janela correta)
    # ==========================
    inicio_colheita = inicio_plantio + pd.Timedelta(days=dias_min)
    fim_colheita    = fim_plantio + pd.Timedelta(days=dias_max)

    # ==========================
    # VEGETATIVO CORRETO
    # ==========================

    inicio_vegetativo = inicio_plantio + pd.Timedelta(days=10)

    # limite vegetativo por cultura
    if cultura == "Soja":
        limite_vegetativo = 50
    else:  # Arroz e Arroz (Médio)
        limite_vegetativo = 70

    fim_vegetativo = inicio_plantio + pd.Timedelta(days=limite_vegetativo)

    pico_inicio = inicio_medio
    pico_fim    = fim_medio

    fases = [
        ("Plantio", inicio_plantio, fim_plantio),
        ("Vegetativo", inicio_vegetativo, fim_vegetativo),
        ("Colheita", inicio_colheita, fim_colheita),
        ("Pico Colheita", pico_inicio, pico_fim)
    ]

    for etapa, inicio, fim in fases:

        if fim <= inicio:
            fim = inicio + pd.Timedelta(days=1)

        dias_etapa = (fim - inicio).days

        gantt_rows.append({
            "Linha": f"{cultura} - {'Colheita' if etapa == 'Pico Colheita' else etapa}",
            "Etapa": etapa,
            "Inicio": inicio,
            "Fim": fim,
            "Dias": dias_etapa,   # 👈 NOVA COLUNA
            "Texto": f"{dias_etapa} dias"
        })


df_gantt = pd.DataFrame(gantt_rows)


ordem_linhas = []

for cultura in df_base["Tipo de Cultura"]:
    ordem_linhas.extend([
        f"{cultura} - Plantio",
        f"{cultura} - Vegetativo",
        f"{cultura} - Colheita"
    ])

fig_gantt = px.timeline(
    df_gantt,
    x_start="Inicio",
    x_end="Fim",
    y="Linha",
    color="Etapa",
    text="Texto",
    color_discrete_map={
        "Plantio": "#2E7D32",
        "Vegetativo": "#1E88E5",
        "Colheita": "#FBAB00",
        "Pico Colheita": "#E65100"
    }
)


fig_gantt.update_yaxes(
    categoryorder="array",
    categoryarray=ordem_linhas,
    autorange="reversed"
)

fig_gantt.update_layout(
    height=60 * len(ordem_linhas),
    bargap=0.25,
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis_title="Mês/Ano",
    yaxis_title="",
    legend_title="Fase"
)

fig_gantt.update_xaxes(
    dtick="M1",
    tickformat="%m/%Y",
    showgrid=True,
    gridcolor="#E6E6E6"
)

fig_gantt.update_traces(
    textposition="inside",   # ✅ valor válido
    textfont=dict(color="white", size=12),
    insidetextanchor="middle"
)

fig_gantt = aplicar_formato_ptbr(fig_gantt, casas_decimais=2)
fig_gantt = estilizar_figura_pdf(fig_gantt)
st.plotly_chart(fig_gantt, use_container_width=True)
#salvar_grafico(fig_gantt, "grafico_gantt.png")


st.markdown(f"""
O plantio agrícola analisado refere-se à organização **{org}**, considerando
**{periodo}**. A área total semeada é de **{fmt_int(df_plantio['Área Semeada'].sum())} hectares**
.

Observa-se concentração do plantio nos meses com maior número de pontos
no gráfico de dispersão, indicando maior intensidade operacional nesses períodos.
A distribuição mensal reflete estratégias de escalonamento para mitigação de riscos
climáticos e operacionais.
""")

for cultura in df_plantio["Tipo de Cultura"].unique():

    df_p = df_plantio[df_plantio["Tipo de Cultura"] == cultura]
    df_c = df_colheita[df_colheita["Tipo de Cultura"] == cultura]

    if df_p.empty or df_c.empty:
        continue

    st.markdown(f"""
**{cultura}**

- Área semeada: **{fmt_int(df_p["Área Semeada"].sum())} ha**
- Semeadura:
  **{df_p["Primeiro Semeado"].min():%d/%m/%Y}**
  a **{df_p["Última Semeadura"].max():%d/%m/%Y}**

- Colheita estimada (com base no último plantio):
  **{df_c["Fim_Colheita"].max():%d/%m/%Y}**
""")
    
st.markdown(f"""
Os ciclos agronômicos considerados foram:
- **Soja:** 90 a 120 dias após a semeadura  
- **Arroz:** 100 a 150 dias após a semeadura  

### Previsão de Colheita

- Janela estimada: **{inicio_min:%d/%m/%Y} a {fim_max:%d/%m/%Y}**
- Data média ponderada (pico): **{inicio_medio:%d/%m/%Y}** a **{fim_medio:%d/%m/%Y}**
""")

ranking = (
    df_colheita
    .groupby("Organizações", as_index=False)
    .agg({
        "Área Semeada": "sum",
        "Produção Estimada (sacas)": "sum",
        "Inicio_Colheita": "min",
        "Fim_Colheita": "max"
    })
)

# 🔥 calcular pico individual por cliente (INÍCIO e FIM ponderados)
picos_inicio = []
picos_fim = []

for org_nome in ranking["Organizações"]:

    df_org = df_colheita[df_colheita["Organizações"] == org_nome]

    pico_inicio = media_ponderada(
        df_org["Inicio_Colheita"],
        df_org["Área Semeada"]
    )

    pico_fim = media_ponderada(
        df_org["Fim_Colheita"],
        df_org["Área Semeada"]
    )

    picos_inicio.append(pico_inicio)
    picos_fim.append(pico_fim)

ranking["Pico_Inicio"] = picos_inicio
ranking["Pico_Fim"] = picos_fim

# ordenar pela maior área
ranking = ranking.sort_values(
    "Área Semeada",
    ascending=False
).reset_index(drop=True)

ranking = ranking.head(20)

ranking["Posição"] = ranking.index + 1

ranking["Janela de Colheita"] = (
    ranking["Inicio_Colheita"].dt.strftime("%d/%m/%Y")
    + " a " +
    ranking["Fim_Colheita"].dt.strftime("%d/%m/%Y")
)

ranking["Pico da Colheita"] = (
    ranking["Pico_Inicio"].dt.strftime("%d/%m/%Y")
    + " a " +
    ranking["Pico_Fim"].dt.strftime("%d/%m/%Y")
)

ranking["Área (ha)"] = ranking["Área Semeada"].apply(fmt_int)
ranking["Produção (sc)"] = ranking["Produção Estimada (sacas)"].apply(fmt_int)

ranking_final = ranking[[
    "Posição",
    "Organizações",
    "Área (ha)",
    "Janela de Colheita",
    "Pico da Colheita"
]]

st.subheader("Top 20 Áreas Plantadas ou por cliente específico")

st.dataframe(
    ranking_final,
    use_container_width=True,
    hide_index=True
)


import os

if st.button("📄 Gerar Relatório em PDF"):

        with st.spinner("Gerando PDF..."):

            salvar_grafico(fig_soja_scatter, "grafico_soja_scatter.png")
            salvar_grafico(fig_soja_bar, "grafico_soja_bar.png")
            salvar_grafico(fig_arroz_scatter, "grafico_arroz_scatter.png")
            salvar_grafico(fig_arroz_bar, "grafico_arroz_bar.png")
            salvar_grafico(fig_colheita, "grafico_colheita.png")
            salvar_grafico(fig_gantt, "grafico_gantt.png")

            pdf = gerar_pdf(
                df_plantio,
                df_colheita,
                ranking,
                org,
                periodo,
                cenario,
                inicio_min,
                fim_max,
                inicio_medio,
                fim_medio
            )

            with open(pdf, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=f,
                    file_name=pdf,
                    mime="application/pdf"
                )