import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title = "Painel de Preços - Suprimentos", layout = "wide")

@st.cache_data
def carregar_base():
    base_path = Path(__file__).parent / "TabelaValores.xlsx"
    df = pd.read_excel(base_path, sheet_name=0)
    df.columns = [col.strip() for col in df.columns]
    df["DATACOMPRA"] = pd.to_datetime(df["DATACOMPRA"], errors = "coerce")
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
