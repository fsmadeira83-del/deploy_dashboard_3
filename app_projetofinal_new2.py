import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------
# Configuração da página
# --------------------------------------------------
st.set_page_config(
    page_title="Dados Económico-Financeiros Economia Portuguesa 2006-2024",
    layout="wide"
)

st.title("📊 Dados Económico-Financeiros Economia Portuguesa 2006-2024")
st.markdown("Dashboard de Free Cash Flow Médio")

# --------------------------------------------------
# Carregamento dos dados
# --------------------------------------------------
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

sorted_SectorAtividade = sorted(df["SectorAtividade"].unique())
SectorAtividade = st.sidebar.multiselect(
    "Sector de Atividade",
    options=sorted_SectorAtividade,
    default=sorted_SectorAtividade
)

sorted_TamanhoEmpresa = sorted(df["TamanhoEmpresa"].unique())
TamanhoEmpresa = st.sidebar.multiselect(
    "Tamanho de Empresa",
    options=sorted_TamanhoEmpresa,
    default=sorted_TamanhoEmpresa
)

years = sorted(df["Ano"].dt.year.unique())
year_range = st.sidebar.slider(
    "Ano",
    min_value=2010,
    max_value=int(max(years)),
    value=(2010, int(max(years)))
)

filtered_df = df[
    (df["SectorAtividade"].isin(SectorAtividade)) &
    (df["TamanhoEmpresa"].isin(TamanhoEmpresa)) &
    (df["Ano"].dt.year.between(year_range[0], year_range[1]))
]
filtered_df = filtered_df[filtered_df["FreeCashFlow"] != 0]

# --------------------------------------------------
# Parte superior com KPIs
# --------------------------------------------------
media_VendasServicos = filtered_df["VendasServicos"].mean()
media_ResultadoLiquido = filtered_df["RL"].mean()
media_FreeCashFlow = filtered_df["FreeCashFlow"].mean()
media_empresas = int(filtered_df["NºEmpresas"].mean())

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Vendas Médias", f"k€ {media_VendasServicos:,.0f}".replace(",", "."))
col2.metric("📈 Lucro Médio", f"k€ {media_ResultadoLiquido:,.0f}".replace(",", "."))
col3.metric("📈 Free Cash Flow Médio", f"k€ {media_FreeCashFlow:,.0f}".replace(",", "."))
col4.metric("🧾 N.º Médio de Empresas", media_empresas)

st.divider()

# --------------------------------------------------
# Gráfico 1 - Area Chart: FCF Médio ao longo do tempo
# --------------------------------------------------
st.subheader("📅 Free Cash Flow Médio ao longo do tempo por Sector de Atividade")

freecashflow_over_time = (
    filtered_df
    .groupby(
        [pd.Grouper(key="Ano", freq="ME"), "SectorAtividade"]
    )["FreeCashFlow"]
    .mean()
    .reset_index()
)

fig = px.area(
    freecashflow_over_time,
    x="Ano",
    y="FreeCashFlow",
    color="SectorAtividade",
    line_group="SectorAtividade",
)

fig.update_traces(opacity=0.45)

fig.update_yaxes(tickformat=".0f")

fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="left",
        x=0
    )
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------
# Gráfico 2 - Linhas por Tamanho da Empresa ao longo do tempo
# -------------------------------------------------------
st.subheader("🏢 Free Cash Flow Médio por Tamanho da Empresa")

ordem = ["Microempresas", "Pequenas empresas", "Médias empresas", "Grandes empresas"]
filtered_df["TamanhoEmpresa"] = pd.Categorical(
    filtered_df["TamanhoEmpresa"],
    categories=ordem,
    ordered=True
)

freecashflow_by_size_year = (
    filtered_df
    .groupby(["Ano", "TamanhoEmpresa"], observed=True)["FreeCashFlow"]
    .mean()
    .reset_index()
)

mapa_cores = {
    "Microempresas":     "#185FA5",
    "Pequenas empresas": "#0F6E56",
    "Médias empresas":   "#BA7517",
    "Grandes empresas":  "#993556",
}

fig2 = go.Figure()

for tamanho in ordem:
    df_t = freecashflow_by_size_year[freecashflow_by_size_year["TamanhoEmpresa"] == tamanho]
    fig2.add_trace(go.Scatter(
        name=tamanho,
        x=df_t["Ano"],
        y=df_t["FreeCashFlow"],
        mode="lines+markers",
        line=dict(color=mapa_cores[tamanho], width=2.5),
        marker=dict(size=6, color=mapa_cores[tamanho]),
        hovertemplate=(
            f"<b>{tamanho}</b><br>"
            "Ano: %{x|%Y}<br>"
            "FCF Médio: %{y:,.0f} k€<extra></extra>"
        ),
    ))

fig2.update_yaxes(tickformat=".0f")

fig2.update_layout(
    xaxis=dict(title="Ano"),
    yaxis=dict(title="FCF Médio (k€)", tickformat=".0f"),
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="left",
        x=0,
    ),
    plot_bgcolor="#FAFAFA",
    margin=dict(t=20, b=80, l=80, r=40),
)

st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --------------------------------------------------------------------
# Ranking - Top 10 Sectores com Barras Horizontais
# --------------------------------------------------------------------
st.subheader("🏆 Top 10 Sectores por Free Cash Flow (Médias Anuais)")

top_sectores = (
    filtered_df
    .groupby("SectorAtividade")["FreeCashFlow"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .round(0)
    .reset_index()
)
top_sectores.columns = ["SectorAtividade", "FreeCashFlow"]
top_sectores_sorted = top_sectores.sort_values("FreeCashFlow", ascending=True)

fig_ranking = go.Figure(go.Bar(
    x=top_sectores_sorted["FreeCashFlow"],
    y=top_sectores_sorted["SectorAtividade"],
    orientation="h",
    marker=dict(
        color=top_sectores_sorted["FreeCashFlow"],
        colorscale="Blues",
        showscale=False,
    ),
    text=top_sectores_sorted["FreeCashFlow"].apply(lambda v: f"{v:,.0f} k€"),
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>FCF Médio: %{x:,.0f} k€<extra></extra>",
))

fig_ranking.update_layout(
    xaxis=dict(title="FCF Médio (k€)", tickformat=".0f"),
    yaxis=dict(title=""),
    plot_bgcolor="#FAFAFA",
    margin=dict(l=20, r=100, t=20, b=40),
    height=400,
)

st.plotly_chart(fig_ranking, use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# Gráfico 3 - Decomposição do FCF por Componente
# ------------------------------------------------------------------
st.subheader("🔍 Decomposição do Free Cash Flow Médio por Dimensão de Empresa")
st.markdown("Comparação entre os fluxos operacionais, de investimento e de financiamento face ao Free Cash Flow líquido.")

ordem = ["Microempresas", "Pequenas empresas", "Médias empresas", "Grandes empresas"]
df_fluxos = filtered_df[filtered_df["FluxosCaixa_AtividadesOperacionais"] != 0].copy()
df_fluxos["TamanhoEmpresa"] = pd.Categorical(
    df_fluxos["TamanhoEmpresa"].astype(str),
    categories=ordem,
    ordered=True
)

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

tamanhos_disponiveis = [t for t in ordem if t in df_agg["TamanhoEmpresa"].values]
n = len(tamanhos_disponiveis)

if n == 0:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
else:
    fig3 = make_subplots(
        rows=n,
        cols=1,
        shared_xaxes=True,
        subplot_titles=tamanhos_disponiveis,
        vertical_spacing=0.06,
    )

    legenda_adicionada = set()

    for i, tamanho in enumerate(tamanhos_disponiveis, start=1):
        df_t   = df_long[df_long["TamanhoEmpresa"] == tamanho]
        df_fcf = df_agg[df_agg["TamanhoEmpresa"] == tamanho]

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

    # ALTERAÇÃO PRINCIPAL: barmode="relative" em vez de "group"
    fig3.update_layout(
        barmode="relative",
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
- **Fluxos de Financiamento** — entradas e saídas de dívida e capital. Valores muito negativos refletem reembolso de dívida. Valores positivos podem refletir um aumento do endividamento.
- **Free Cash Flow** *(linha pontilhada)* — resultado após subtrair os fluxos de investimento e de financiamento aos fluxos operacionais. Valor negativo demonstra que a empresa não está a criar valor para os seus stakeholders.

> ⚠️ **Sinal de alerta:** FCF positivo com Fluxos de Investimento também positivos pode indicar que a empresa vende ativos para sustentar a liquidez.
""")

st.divider()

# ------------------------------------------------------------------
# Gráfico 4 - Relação entre RCP e Free Cash Flow
# ------------------------------------------------------------------
st.subheader("📊 Relação entre Rendibilidade dos Capitais Próprios (RCP) e Free Cash Flow")
st.markdown("Análise da relação entre a rendibilidade gerada para os acionistas e a capacidade de geração de caixa, por dimensão de empresa ao longo do tempo.")

df_rcp_fcf = filtered_df[
    (filtered_df["RCP"].notna()) &
    (filtered_df["FreeCashFlow"].notna())
].copy()

ordem = ["Microempresas", "Pequenas empresas", "Médias empresas", "Grandes empresas"]
df_rcp_fcf["TamanhoEmpresa"] = pd.Categorical(
    df_rcp_fcf["TamanhoEmpresa"],
    categories=ordem,
    ordered=True
)

df_agg_rcp = (
    df_rcp_fcf
    .groupby(["TamanhoEmpresa", pd.Grouper(key="Ano", freq="ME")], observed=True)[["RCP", "FreeCashFlow"]]
    .mean()
    .reset_index()
)

tamanhos_disponiveis_rcp = [t for t in ordem if t in df_agg_rcp["TamanhoEmpresa"].values]
n_rcp = len(tamanhos_disponiveis_rcp)

if n_rcp == 0:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
else:
    fig4 = make_subplots(
        rows=n_rcp,
        cols=1,
        shared_xaxes=True,
        subplot_titles=tamanhos_disponiveis_rcp,
        vertical_spacing=0.06,
        specs=[[{"secondary_y": True}]] * n_rcp,
    )

    legenda_adicionada_rcp = set()

    for i, tamanho in enumerate(tamanhos_disponiveis_rcp, start=1):
        df_t = df_agg_rcp[df_agg_rcp["TamanhoEmpresa"] == tamanho].sort_values("Ano")

        mostrar_fcf = "Free Cash Flow" not in legenda_adicionada_rcp
        if mostrar_fcf:
            legenda_adicionada_rcp.add("Free Cash Flow")
        fig4.add_trace(go.Bar(
            name="Free Cash Flow",
            x=df_t["Ano"],
            y=df_t["FreeCashFlow"],
            marker_color="#2196F3",
            opacity=0.75,
            legendgroup="Free Cash Flow",
            showlegend=mostrar_fcf,
            hovertemplate=(
                "<b>Free Cash Flow</b><br>"
                "Ano: %{x|%Y}<br>"
                "Valor médio: %{y:,.0f} k€<extra></extra>"
            ),
        ), row=i, col=1, secondary_y=False)

        mostrar_rcp = "RCP" not in legenda_adicionada_rcp
        if mostrar_rcp:
            legenda_adicionada_rcp.add("RCP")
        fig4.add_trace(go.Scatter(
            name="RCP",
            x=df_t["Ano"],
            y=df_t["RCP"],
            mode="lines+markers",
            line=dict(color="#FF7043", width=2.5),
            marker=dict(size=6),
            legendgroup="RCP",
            showlegend=mostrar_rcp,
            hovertemplate=(
                "<b>RCP</b><br>"
                "Ano: %{x|%Y}<br>"
                "Valor médio: %{y:.2%}<extra></extra>"
            ),
        ), row=i, col=1, secondary_y=True)

        fig4.add_hline(y=0, line_width=1, line_color="grey", opacity=0.5, row=i, col=1)

        fig4.update_yaxes(title_text="FCF Médio (k€)", tickformat=".0f",
                          row=i, col=1, secondary_y=False)
        fig4.update_yaxes(title_text="RCP (%)", tickformat=".1%",
                          row=i, col=1, secondary_y=True)

    fig4.update_xaxes(title_text="Ano", row=n_rcp, col=1)

    fig4.update_layout(
        barmode="group",
        height=320 * n_rcp,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="left",
            x=0,
        ),
        plot_bgcolor="#FAFAFA",
        margin=dict(t=60, b=80, l=80, r=80),
    )

    st.plotly_chart(fig4, use_container_width=True)

    with st.expander("ℹ️ Como interpretar este gráfico"):
        st.markdown("""
- **Free Cash Flow** *(barras azuis)* — caixa gerada após investimento. Reflete a capacidade real de geração de liquidez.
- **RCP — Rendibilidade dos Capitais Próprios** *(linha laranja, eixo direito)* — mede o retorno gerado para os acionistas em proporção do capital investido.

**Padrões a observar:**
- **RCP elevado + FCF positivo** → empresa rentável e com boa geração de caixa. Situação ideal.
- **RCP elevado + FCF negativo** → rentabilidade contabilística não se traduz em caixa. Pode indicar problemas de cobranças ou investimento intensivo.
- **RCP negativo + FCF positivo** → empresa com prejuízo mas que ainda gera caixa. Situação de alerta a monitorizar.
- **Ambos negativos** → sinal de forte pressão financeira.
""")

st.divider()

# --------------------------------------------------
# Rodapé
# --------------------------------------------------
st.caption("Dados: Dados Económico-Financeiros de Portugal 2006-2024")
