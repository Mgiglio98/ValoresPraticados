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

st.subheader("Evolução de Preço")

periodo = st.radio("", ("3 meses", "6 meses", "12 meses"), horizontal = True)

if periodo == "3 meses":
    cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(months=3)
elif periodo == "6 meses":
    cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(months=6)
else:
    cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(months=12)

if filtro_insumo != "Todos":
    
    df_graf = df_filtrado.copy()
    df_graf = df_graf[df_graf["VALOR_NUM"].notna()]
    df_graf = df_graf[df_graf["DATACOMPRA"] >= cutoff]
    
    if df_graf.empty:
        st.info(f"Não há dados nos últimos {periodo} para esse insumo.")
    else:
        df_tmp = df_graf.sort_values("DATACOMPRA")
        if len(df_tmp) >= 2:
            preco_inicial = df_tmp["VALOR_NUM"].iloc[0]
            preco_final = df_tmp["VALOR_NUM"].iloc[-1]
            variacao = ((preco_final - preco_inicial) / preco_inicial) * 100

            st.metric(
                label = f"Variação de Preço nos últimos {periodo}",
                value = f"{preco_final:.2f}",
                delta = f"{variacao:.2f}%")
        else:
            st.info("Não há dados suficientes para calcular a variação.")

        df_mes = (df_graf.groupby([pd.Grouper(key = "DATACOMPRA", freq = "M"), "ESTADO"])["VALOR_NUM"].mean().reset_index().sort_values("DATACOMPRA"))
        df_pivot = df_mes.pivot(index = "DATACOMPRA", columns = "ESTADO", values = "VALOR_NUM").sort_index()
        df_pivot.index = df_pivot.index.strftime("%Y-%m")

        fig = px.line(df_mes, x = "DATACOMPRA", y = "VALOR_NUM", color = "ESTADO", markers = True, title = f"Evolução de Preço – Média Mensal ({periodo})")
        
        fig.update_xaxes(tickformat = "%Y-%m", dtick = "M1")
      
        fig.update_traces(mode = "lines+markers+text", texttemplate = "%{y:.2f}", textposition = "top center")
    
        fig.update_layout(height = 450, legend_title_text = "UF", hovermode = "x unified", yaxis_title = "Preço médio (R$)")
        
        st.plotly_chart(fig, use_container_width = True)
    
else:
    st.info("Selecione um insumo específico para visualizar a evolução de preços.")
