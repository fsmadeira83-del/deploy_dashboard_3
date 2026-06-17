import streamlit as st
import pandas as pd

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
num_empresas = filtered_df["NºEmpresas"].sum()

# Vamos dividir a área em 3 colunas para mostrar os KPIs lado a lado
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Vendas Médias", f"€{media_VendasServicos:,.0f}".replace(",", "."))
col2.metric("📈 Lucro Médio", f"€{media_ResultadoLiquido:,.0f}".replace(",", "."))
col3.metric("📈 Free Cash Flow Médio", f"€{media_FreeCashFlow:,.0f}".replace(",", "."))
col4.metric("🧾 Nº de Empresas", num_empresas)

st.divider()

# --------------------------------------------------
# Gráfico 1 - Free Cash Flow Médio ao longo do tempo
# --------------------------------------------------
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

# Criar uma pivot table
freecashflow_pivot = freecashflow_over_time.pivot(
    index="Ano",
    columns="SectorAtividade",
    values="FreeCashFlow"
)

st.line_chart(freecashflow_pivot)

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
    .groupby("TamanhoEmpresa")["FreeCashFlow"]
    .mean()
)

st.bar_chart(freecashflow_by_size)

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

# --------------------------------------------------
# Rodapé
# --------------------------------------------------
st.caption("Dados: Dados Económico-Financeiros de Portugal 2006-2024")
