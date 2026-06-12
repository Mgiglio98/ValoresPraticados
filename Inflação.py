import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(
    page_title="Inflação de Insumos - Suprimentos",
    layout="wide"
)

GRUPOS_INSUMOS = {
    "Aço": [
        "H.11.0021", "H.11.0022", "H.11.0023", "H.11.0024",
        "H.11.0025", "H.11.0026", "H.11.0027", "H.11.0031",
        "H.11.0032", "H.11.0033", "H.11.0034", "H.11.0035",
        "H.11.0036", "H.11.0037"
    ],
    "Argamassa": [
        "J.02.0001"
    ],
    "Brita": [
        "J.01.0016"
    ],
    "Areia": [
        "J.03.0015", "J.03.0001"
    ],
    "Cimento": [
        "J.05.0001"
    ]
}


def carregar_base():
    base_path = Path(__file__).parent / "ValoresPraticados.xlsx"

    df = pd.read_excel(base_path, sheet_name=0)
    df.columns = [col.strip() for col in df.columns]

    df["DATACOMPRA"] = pd.to_datetime(
        df["DATACOMPRA"],
        errors="coerce",
        dayfirst=True
    )

    df["VALOR_NUM"] = pd.to_numeric(
        df["VALORESPRATICADOS"],
        errors="coerce"
    )

    df["INSUMOCDG"] = df["INSUMOCDG"].astype(str).str.strip().str.upper()
    df["INSUMO"] = df["INSUMO"].astype(str).str.strip()
    df["UNIDADE"] = df["UNIDADE"].astype(str).str.strip().str.upper()
    df["ESTADO"] = df["ESTADO"].astype(str).str.strip().str.upper()
    df["FORNECEDOR"] = df["FORNECEDOR"].astype(str).str.strip()

    df = df[df["DATACOMPRA"].notna()].copy()
    df = df[df["VALOR_NUM"].notna()].copy()

    return df


def classificar_grupo(codigo):
    codigo = str(codigo).strip().upper()

    for grupo, codigos in GRUPOS_INSUMOS.items():
        if codigo in codigos:
            return grupo

    return None


def formatar_moeda(valor):
    if pd.isna(valor):
        return "-"

    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor):
    if pd.isna(valor):
        return "-"

    return f"{valor:.2f}%"


def calcular_variacao_grupo(df_grupo):
    if df_grupo.empty:
        return None

    df_mensal = (
        df_grupo
        .groupby(pd.Grouper(key="DATACOMPRA", freq="MS"))["VALOR_NUM"]
        .mean()
        .reset_index()
        .sort_values("DATACOMPRA")
    )

    df_mensal = df_mensal[df_mensal["VALOR_NUM"].notna()].copy()

    if len(df_mensal) < 2:
        return None

    preco_inicial = df_mensal["VALOR_NUM"].iloc[0]
    preco_final = df_mensal["VALOR_NUM"].iloc[-1]

    if preco_inicial == 0:
        return None

    variacao = ((preco_final - preco_inicial) / preco_inicial) * 100

    return {
        "preco_inicial": preco_inicial,
        "preco_final": preco_final,
        "variacao": variacao,
        "data_inicial": df_mensal["DATACOMPRA"].iloc[0],
        "data_final": df_mensal["DATACOMPRA"].iloc[-1]
    }


df = carregar_base()

df["GRUPO"] = df["INSUMOCDG"].apply(classificar_grupo)
df = df[df["GRUPO"].notna()].copy()

data_max = df["DATACOMPRA"].max()
data_min_periodo = data_max - pd.DateOffset(years=2)

df = df[df["DATACOMPRA"] >= data_min_periodo].copy()

st.title("Inflação de Insumos - Suprimentos")

periodo_min = df["DATACOMPRA"].min().strftime("%d/%m/%Y")
periodo_max = df["DATACOMPRA"].max().strftime("%d/%m/%Y")

st.markdown(f"**Período analisado:** {periodo_min} → {periodo_max}")

st.subheader("Filtros")

filtro_estado = st.selectbox(
    "Estado",
    options=["Todos"] + sorted(df["ESTADO"].dropna().unique().tolist())
)

df_filtrado = df.copy()

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ESTADO"] == filtro_estado]

st.subheader("Variação acumulada por grupo")

cols = st.columns(5)

def cor_variacao(valor):
    if valor > 0:
        return "#16a34a"  # verde
    elif valor < 0:
        return "#dc2626"  # vermelho
    return "#9ca3af"      # cinza


for idx, grupo in enumerate(GRUPOS_INSUMOS.keys()):
    df_grupo = df_filtrado[df_filtrado["GRUPO"] == grupo]
    resultado = calcular_variacao_grupo(df_grupo)

    with cols[idx]:
        if resultado is None:
            st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="font-size: 14px;">{grupo}</div>
                    <div style="font-size: 32px; font-weight: 700; color: #9ca3af;">-</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            variacao = resultado["variacao"]
            cor = cor_variacao(variacao)
            seta = "↑" if variacao > 0 else "↓" if variacao < 0 else "→"

            st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="font-size: 14px; margin-bottom: 6px;">{grupo}</div>
                    <div style="
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 32px;
                        font-weight: 700;
                        color: {cor};
                    ">
                        <span>{seta}</span>
                        <span>{formatar_percentual(variacao)}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.subheader("Evolução mensal por grupo")

for grupo in GRUPOS_INSUMOS.keys():
    df_grupo = df_filtrado[df_filtrado["GRUPO"] == grupo].copy()

    if df_grupo.empty:
        st.info(f"Não há dados para o grupo {grupo}.")
        continue

    df_mensal = (
        df_grupo
        .groupby([pd.Grouper(key="DATACOMPRA", freq="MS"), "UNIDADE"])["VALOR_NUM"]
        .mean()
        .reset_index()
        .sort_values("DATACOMPRA")
    )

    if df_mensal.empty:
        st.info(f"Não há dados mensais para o grupo {grupo}.")
        continue

    fig = px.line(
        df_mensal,
        x="DATACOMPRA",
        y="VALOR_NUM",
        color="UNIDADE",
        markers=True,
        title=f"{grupo} - Evolução do preço médio mensal"
    )

    fig.update_xaxes(
        tickformat="%m/%Y",
        dtick="M1"
    )

    fig.update_traces(
        mode="lines+markers+text",
        texttemplate="%{y:.2f}",
        textposition="top center"
    )

    fig.update_layout(
        height=420,
        hovermode="x unified",
        legend_title_text="Unidade",
        yaxis_title="Preço médio mensal (R$)",
        xaxis_title="Mês"
    )

    st.plotly_chart(fig, use_container_width=True)

    mostrar_base = st.checkbox(
        f"Mostrar base usada - {grupo}",
        key=f"mostrar_base_{grupo}"
    )
    
    if mostrar_base:
        df_view = df_grupo.copy()

        df_view["DATACOMPRA"] = df_view["DATACOMPRA"].dt.strftime("%d/%m/%Y")
        df_view["VALOR_NUM"] = df_view["VALOR_NUM"].apply(formatar_moeda)

        df_view = df_view.rename(columns={
            "INSUMOCDG": "Código do Insumo",
            "INSUMO": "Insumo",
            "VALOR_NUM": "Preço de Compra",
            "UNIDADE": "Unidade",
            "DATACOMPRA": "Data da Compra",
            "ESTADO": "Estado",
            "FORNECEDOR": "Fornecedor",
            "GRUPO": "Grupo"
        })

        colunas_exibir = [
            "Grupo",
            "Código do Insumo",
            "Insumo",
            "Preço de Compra",
            "Unidade",
            "Data da Compra",
            "Estado",
            "Fornecedor"
        ]

        st.dataframe(
            df_view[colunas_exibir],
            use_container_width=True,
            hide_index=True
        )
