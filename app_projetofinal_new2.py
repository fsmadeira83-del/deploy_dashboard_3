import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# Configuração da página
# --------------------------------------------------
st.set_page_config(
    page_title="Dados Económico-Financeiros Economia Portuguesa 2006-2024", # O título que mostra na tab do browser
    layout="wide" # A opção "centered" coloca a página numa coluna central
)

st.title("📊 Dados Económico-Financeiros Economia Portuguesa 2006-2024")
st.markdown("Dashboard de Free Cash Flow Médio")

# --------------------------------------------------
# Carregamento dos dados
# --------------------------------------------------
# Esta linha é extremamente importante. 
# Ao ler o ficheiro a primeira vez, a app guarda os dados em memória (cache)
# Assim, sempre que houver interações com o dashboard (ex: mudar um filtro), não é necessário ler o ficheiro csv novamente
@st.cache_data 
def load_data():
    file_name = "ProjetoFinal_BaseDados.xlsx"
    df = pd.read_excel(file_name, parse_dates=["Ano"])
    return df

df = load_data()

# --------------------------------------------------
# Definir um Sidebar com filtros
# --------------------------------------------------
st.sidebar.header("Filtros")

# Filtro de Sector de Atividade
sorted_SectorAtividade = sorted(df["SectorAtividade"].unique())
SectorAtividade = st.sidebar.multiselect(
    "Sector de Atividade",
    options=sorted_SectorAtividade,
    default=sorted_SectorAtividade
)

# Filtro de Tamanho de Empresa
sorted_TamanhoEmpresa = sorted(df["TamanhoEmpresa"].unique())
TamanhoEmpresa = st.sidebar.multiselect(
    "Tamanho de Empresa",
    options=sorted_TamanhoEmpresa,
    default=sorted_TamanhoEmpresa
)

# Filtro de Ano
years = sorted(df["Ano"].dt.year.unique())
year_range = st.sidebar.slider(
    "Ano",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

# Aplicar filtros
filtered_df = df[
    (df["SectorAtividade"].isin(SectorAtividade)) &
    (df["TamanhoEmpresa"].isin(TamanhoEmpresa)) &
    (df["Ano"].dt.year.between(year_range[0], year_range[1]))
]

# --------------------------------------------------
# Parte superior com KPIs
# --------------------------------------------------
media_VendasServicos = filtered_df["VendasServicos"].mean()
media_ResultadoLiquido = filtered_df["RL"].mean()
media_FreeCashFlow = filtered_df["FreeCashFlow"].mean()
media_empresas = int(filtered_df["NºEmpresas"].mean())

# Vamos dividir a área em 3 colunas para mostrar os KPIs lado a lado
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Vendas Médias", f"k€ {media_VendasServicos:,.0f}".replace(",", "."))
col2.metric("📈 Lucro Médio", f"k€ {media_ResultadoLiquido:,.0f}".replace(",", "."))
col3.metric("📈 Free Cash Flow Médio", f"k€ {media_FreeCashFlow:,.0f}".replace(",", "."))
col4.metric("🧾 N.º Médio de Empresas", media_empresas)

st.divider()

# --------------------------------------------------
# Gráfico 1 - Free Cash Flow Médio ao longo do tempo
# --------------------------------------------------
# Agrupar a média de Free Cash Flow em cada ano por Sector de Atividade
st.subheader("📅 Free Cash Flow Médio ao longo do tempo por Sector de Atividade")

# Agrupar a média de Free Cash Flow em cada ano por Sector de Atividade
freecashflow_over_time = (
    filtered_df
    .groupby(
        [pd.Grouper(key="Ano", freq="ME"), "SectorAtividade"]
    )["FreeCashFlow"]
    .mean()
    .reset_index()
)

fig = px.line(
    freecashflow_over_time,
    x="Ano",
    y="FreeCashFlow",
    color="SectorAtividade"
)

# Calcular o intervalo do eixo Y com base nos dados
y_min = freecashflow_over_time["FreeCashFlow"].min()
y_max = freecashflow_over_time["FreeCashFlow"].max()

fig.update_yaxes(
    tickformat=".0f",
    dtick=10000,
    range=[
        (y_min // 10000) * 10000,
        (y_max // 10000 + 1) * 10000
    ]
)

fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="left",
        x=0
    )
)

st.plotly_chart(fig)

# -------------------------------------------------------
# Gráfico 2 - Free Cash Flow Médio por Tamanho da Empresa
# -------------------------------------------------------
st.subheader("🌍 Free Cash Flow Médio por Tamanho da Empresa")

# Agrupar a média de Free Cash Flow por Tamanho da Empresa
ordem = ["Microempresas", "Pequenas empresas", "Médias empresas", "Grandes empresas"]
filtered_df["TamanhoEmpresa"] = pd.Categorical(
    filtered_df["TamanhoEmpresa"],
    categories=ordem,
    ordered=True
)

freecashflow_by_size = (
    filtered_df
    .groupby("TamanhoEmpresa", observed=True)["FreeCashFlow"]
    .mean()
    .reset_index()
)

fig = px.bar(
    freecashflow_by_size,
    x="TamanhoEmpresa",
    y="FreeCashFlow"
)

fig.update_yaxes(tickformat=".0f")

st.plotly_chart(fig)

st.divider()

# --------------------------------------------------------------------
# Table - Top Sectores de Atividade com Maiores Free Cash Flows Médios
# --------------------------------------------------------------------
st.subheader("🏆 Top 10 Sectores por Free Cash Flow (Médias Anuais)")

# Agrupar a média de Free Cash Flow por Setor de Atividade, ordenar e mostrar os top 10
top_sectores = (
    filtered_df
    .groupby("SectorAtividade")["FreeCashFlow"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .round(0)
)

st.dataframe(top_sectores)

st.divider()

# ------------------------------------------------------------------
# Gráfico 3 - Decomposição do Free Cash Flow por Componente
# ------------------------------------------------------------------
st.subheader("🔍 Decomposição do Free Cash Flow Médio por Dimensão de Empresa")
st.markdown("Comparação entre os fluxos operacionais, de investimento e de financiamento face ao Free Cash Flow líquido.")

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Excluir anos sem dados de fluxos de caixa (registos a zero)
df_fluxos = filtered_df[filtered_df["FluxosCaixa_AtividadesOperacionais"] != 0].copy()

ordem = ["Microempresas", "Pequenas empresas", "Médias empresas", "Grandes empresas"]
df_fluxos["TamanhoEmpresa"] = pd.Categorical(
    df_fluxos["TamanhoEmpresa"],
    categories=ordem,
    ordered=True
)

# Agregação média por Tamanho de Empresa e Ano
cols_fluxos = [
    "TamanhoEmpresa", "Ano",
    "FluxosCaixa_AtividadesOperacionais",
    "FluxosCaixa_AtividadesInvestimento",
    "FluxosCaixa_AtividadesFinanciamento",
    "FreeCashFlow",
]
df_agg = (
    df_fluxos[cols_fluxos]
    .groupby(["TamanhoEmpresa", pd.Grouper(key="Ano", freq="ME")], observed=True)
    .mean()
    .reset_index()
)

# Transformar para formato longo
df_long = df_agg.melt(
    id_vars=["TamanhoEmpresa", "Ano"],
    value_vars=[
        "FluxosCaixa_AtividadesOperacionais",
        "FluxosCaixa_AtividadesInvestimento",
        "FluxosCaixa_AtividadesFinanciamento",
    ],
    var_name="Componente",
    value_name="Valor",
)

df_long["Componente"] = df_long["Componente"].map({
    "FluxosCaixa_AtividadesOperacionais":  "Fluxos Operacionais",
    "FluxosCaixa_AtividadesInvestimento":  "Fluxos de Investimento",
    "FluxosCaixa_AtividadesFinanciamento": "Fluxos de Financiamento",
})

mapa_cores = {
    "Fluxos Operacionais":     "#2196F3",
    "Fluxos de Investimento":  "#FF7043",
    "Fluxos de Financiamento": "#66BB6A",
}

tamanhos_disponiveis = [t for t in ordem if t in df_agg["TamanhoEmpresa"].cat.categories and t in df_agg["TamanhoEmpresa"].values]
n = len(tamanhos_disponiveis)

fig3 = make_subplots(
    rows=n,
    cols=1,
    shared_xaxes=True,
    subplot_titles=tamanhos_disponiveis,
    vertical_spacing=0.06,
)

legenda_adicionada = set()

for i, tamanho in enumerate(tamanhos_disponiveis, start=1):
    df_t    = df_long[df_long["TamanhoEmpresa"] == tamanho]
    df_fcf  = df_agg[df_agg["TamanhoEmpresa"] == tamanho]

    for componente, cor in mapa_cores.items():
        df_c = df_t[df_t["Componente"] == componente]
        mostrar_legenda = componente not in legenda_adicionada
        if mostrar_legenda:
            legenda_adicionada.add(componente)
        fig3.add_trace(go.Bar(
            name=componente,
            x=df_c["Ano"],
            y=df_c["Valor"],
            marker_color=cor,
            opacity=0.85,
            legendgroup=componente,
            showlegend=mostrar_legenda,
            hovertemplate=(
                f"<b>{componente}</b><br>"
                "Ano: %{x|%Y}<br>"
                "Valor médio: %{y:,.0f} k€<extra></extra>"
            ),
        ), row=i, col=1)

    mostrar_legenda_fcf = "Free Cash Flow" not in legenda_adicionada
    if mostrar_legenda_fcf:
        legenda_adicionada.add("Free Cash Flow")
    fig3.add_trace(go.Scatter(
        name="Free Cash Flow",
        x=df_fcf["Ano"],
        y=df_fcf["FreeCashFlow"],
        mode="lines+markers",
        line=dict(color="#212121", width=2.5, dash="dot"),
        marker=dict(size=6),
        legendgroup="Free Cash Flow",
        showlegend=mostrar_legenda_fcf,
        hovertemplate=(
            "<b>Free Cash Flow</b><br>"
            "Ano: %{x|%Y}<br>"
            "Valor médio: %{y:,.0f} k€<extra></extra>"
        ),
    ), row=i, col=1)

    fig3.add_hline(y=0, line_width=1, line_color="grey", opacity=0.5, row=i, col=1)
    fig3.update_yaxes(title_text="Média (k€)", tickformat=".0f", row=i, col=1)

fig3.update_xaxes(title_text="Ano", row=n, col=1)

fig3.update_layout(
    barmode="group",
    height=320 * n,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.05,
        xanchor="left",
        x=0,
    ),
    plot_bgcolor="#FAFAFA",
    margin=dict(t=60, b=80, l=80, r=40),
)

st.plotly_chart(fig3, use_container_width=True)

with st.expander("ℹ️ Como interpretar este gráfico"):
    st.markdown("""
- **Fluxos Operacionais** — caixa gerada pela atividade corrente da empresa. Valor positivo e crescente é o sinal mais saudável.
- **Fluxos de Investimento** — tipicamente negativo em empresas que investem. Um valor positivo pode indicar desinvestimento.
- **Fluxos de Financiamento** — entradas e saídas de dívida e capital. Valores muito negativos refletem reembolso de dívida.
- **Free Cash Flow** *(linha pontilhada)* — resultado após subtrair o investimento aos fluxos operacionais.

> ⚠️ **Sinal de alerta:** FCF positivo com Fluxos de Investimento também positivos pode indicar que a empresa vende ativos para sustentar a liquidez.
""")
# --------------------------------------------------
# Rodapé
# --------------------------------------------------
st.caption("Dados: Dados Económico-Financeiros de Portugal 2006-2024")
