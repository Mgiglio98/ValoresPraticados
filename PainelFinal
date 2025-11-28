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
    return df

df_valores = carregar_base()

st.subheader("Prévia da base de valores")
st.dataframe(df_valores.head(20))
st.write("Colunas:", list(df_valores.columns))
