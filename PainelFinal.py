import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title = "Painel de Preços - Suprimentos", layout = "wide")

@st.cache_data
def carregar_base():
    base_path = Path(__file__).parent / "TabelaValores.xlsx"
    df = pd.read_excel(base_path, sheet_name=0)
    df.columns = [col.strip() for col in df.columns]
    df["DATACOMPRA"] = pd.to_datetime(df["DATACOMPRA"], errors = "coerce")
    df["VALOR_NUM"] = pd.to_numeric(df["VALORESPRATICADOS"], errors="coerce")
    df["VALORESPRATICADOS"] = df["VALOR_NUM"].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else "")
    df = df.sort_values("DATACOMPRA", ascending=False)
    return df

df_valores = carregar_base()

st.title("Painel de Preços - Suprimentos")
st.subheader("Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    filtro_insumo_cdg = st.selectbox("Código do Insumo", options = ["Todos"] + sorted(df_valores["INSUMOCDG"].dropna().unique().tolist()))

with col2:
    filtro_insumo = st.selectbox("Descrição do Insumo", options = ["Todos"] + sorted(df_valores["INSUMO"].dropna().unique().tolist()))

with col3:
    filtro_estado = st.selectbox("Estado", options = ["Todos"] + sorted(df_valores["ESTADO"].dropna().unique().tolist()))

df_filtrado = df_valores.copy()

if filtro_insumo_cdg != "Todos":
    df_filtrado = df_filtrado[df_filtrado["INSUMOCDG"] == filtro_insumo_cdg]

if filtro_insumo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["INSUMO"] == filtro_insumo]

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ESTADO"] == filtro_estado]

df_recentes = df_filtrado.drop_duplicates(subset = ["INSUMOCDG", "ESTADO"], keep = "first").reset_index(drop = True)

st.subheader("Últimos valores Praticados")
st.dataframe(df_recentes, use_container_width = True)
st.subheader("Base Completa")
st.dataframe(df_filtrado.head(50))

st.subheader("Evolução de Preço (média mensal – últimos 12 meses)")

if filtro_insumo != "Todos":
    df_graf = df_filtrado.copy()
    df_graf = df_graf[df_graf["VALOR_NUM"].notna()]
    hoje = pd.Timestamp.today().normalize()
    cutoff = hoje - pd.DateOffset(months=12)
    df_graf = df_graf[df_graf["DATACOMPRA"] >= cutoff]

    if df_graf.empty:
        st.info("Não há dados nos últimos 12 meses para esse insumo.")
    else:
        df_mes = (df_graf.groupby([pd.Grouper(key = "DATACOMPRA", freq = "M"), "ESTADO"])["VALOR_NUM"].mean().reset_index().sort_values("DATACOMPRA"))
        df_pivot = df_mes.pivot(index = "DATACOMPRA", columns = "ESTADO", values = "VALOR_NUM").sort_index()
        df_pivot.index = df_pivot.index.strftime("%Y-%m")

        fig = px.line(
        df_mes,
        x="DATACOMPRA",
        y="VALOR_NUM",
        color="ESTADO",
        markers=True,
        title="Evolução de Preço (média mensal – últimos 12 meses)")
        
        fig.update_xaxes(
            tickformat="%Y-%m",
            dtick="M1")
      
        fig.update_traces(
            text=df_mes["VALOR_NUM"].round(2),
            textposition="top center",
            mode="lines+markers+text")
    
        fig.update_layout(
            height=450,
            legend_title_text="UF",
            hovermode="x unified",)
        
        st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("Selecione um insumo específico para visualizar a evolução de preços.")
