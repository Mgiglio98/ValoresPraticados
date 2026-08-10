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
        "H.11.0024", "H.11.0034"
    ],
    "Argamassa": [
        "J.02.0001", "J.02.2000"
    ],
    "Brita": [
        "J.01.0016"
    ],
    "Areia": [
        "J.03.0015"
    ],
    "Cimento": [
        "J.05.0001"
    ]
}

PESO_UNITARIO_KG = {
    "J.02.0001": 50,      # Argamassa - saco 50 kg
    "J.03.0015": 20,      # Areia - saco 20 kg
    "J.01.0016": 20,      # Brita - saco 20 kg
    "J.05.0001": 50,      # Cimento - saco 50 kg
    "J.02.2000": 50,      # Votomassa - saco 50 kg

    "H.11.0034": 7.404,   # Aço 10mm - vara
    "H.11.0024": 1,       # Aço já comprado em KG
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
    df["EMPREENDIMENTO"] = df["EMPREENDIMENTO"].astype(str).str.strip()

    df["QUANTIDADE_NUM"] = pd.to_numeric(df["QUANTIDADE"], errors="coerce")
    
    df["PESO_UNITARIO_KG"] = df["INSUMOCDG"].map(PESO_UNITARIO_KG)
    
    df["PESO_TOTAL_COMPRA_KG"] = (df["QUANTIDADE_NUM"] * df["PESO_UNITARIO_KG"])

    df.loc[df["INSUMOCDG"] == "H.11.0034", "VALOR_NUM"] /= 7.404

    df = df[df["DATACOMPRA"].notna()].copy()
    df = df[df["VALOR_NUM"].notna()].copy()

    df = df[~df["EMPREENDIMENTO"].isin(["2514", "9992"])].copy()

    return df
    
def classificar_porte_compra(row):
    if pd.isna(row["PESO_TOTAL_COMPRA_KG"]):
        return "SEM CLASSIFICAÇÃO"

    limites = {
        "Aço": 3000,
        "Argamassa": 2000,
        "Brita": 2000,
        "Areia": 2000,
        "Cimento": 2000,
    }

    limite = limites.get(row["GRUPO"])

    if limite is None:
        return "SEM CLASSIFICAÇÃO"

    if row["PESO_TOTAL_COMPRA_KG"] >= limite:
        return "GRANDE"

    return "PEQUENA"

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
        return "-"calcular_variacao_grupo

    return f"{valor:.2f}%"

def calcular_media_ponderada(df):
    df = df[
        df["VALOR_NUM"].notna()
        & df["PESO_TOTAL_COMPRA_KG"].notna()
        & (df["PESO_TOTAL_COMPRA_KG"] > 0)
    ].copy()

    if df.empty:
        return None

    return (
        (df["VALOR_NUM"] * df["PESO_TOTAL_COMPRA_KG"]).sum()
        / df["PESO_TOTAL_COMPRA_KG"].sum()
    )

def calcular_variacao_grupo(df_grupo):
    if df_grupo.empty:
        return None

    df_grupo = df_grupo.copy()

    df_grupo["MES"] = (
        df_grupo["DATACOMPRA"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    registros = []

    for mes, grupo_mes in df_grupo.groupby("MES"):
        preco_medio = calcular_media_ponderada(grupo_mes)

        if preco_medio is not None:
            registros.append({
                "DATACOMPRA": mes,
                "VALOR_NUM": preco_medio
            })

    df_mensal = (
        pd.DataFrame(registros)
        .sort_values("DATACOMPRA")
    )

    if len(df_mensal) < 2:
        return None

    preco_inicial = df_mensal["VALOR_NUM"].iloc[0]
    preco_final = df_mensal["VALOR_NUM"].iloc[-1]

    if preco_inicial == 0:
        return None

    variacao = (
        (preco_final - preco_inicial)
        / preco_inicial
    ) * 100

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

df["PORTE_COMPRA"] = df.apply(classificar_porte_compra, axis=1)

data_max = df["DATACOMPRA"].max()
data_min_periodo = data_max - pd.DateOffset(years=1)

df = df[df["DATACOMPRA"] >= data_min_periodo].copy()

df = df[df["PORTE_COMPRA"] == "GRANDE"].copy()

st.title("Inflação de Insumos - Suprimentos")

periodo_min = df["DATACOMPRA"].min().strftime("%d/%m/%Y")
periodo_max = df["DATACOMPRA"].max().strftime("%d/%m/%Y")

st.markdown(f"**Período analisado:** {periodo_min} → {periodo_max}")

df_filtrado = df.copy()

st.subheader("Análise por grupo e estado")

def cor_variacao(valor):
    if valor > 0:
        return "#16a34a"
    elif valor < 0:
        return "#dc2626"
    return "#9ca3af"

ordem_estados = ["RJ", "SP", "SC"]

for grupo in GRUPOS_INSUMOS.keys():
    df_grupo = df_filtrado[df_filtrado["GRUPO"] == grupo].copy()

    if df_grupo.empty:
        st.info(f"Não há dados para o grupo {grupo}.")
        continue

    st.markdown(f"## {grupo}")
    
    cols_cards = st.columns(3)

    for idx, estado in enumerate(ordem_estados):
        df_grupo_estado = df_grupo[df_grupo["ESTADO"] == estado].copy()
        resultado = calcular_variacao_grupo(df_grupo_estado)

        with cols_cards[idx]:
            if df_grupo_estado.empty or resultado is None:
                st.markdown(f"""
                    <div style="padding: 10px 0;">
                        <div style="font-size: 14px;">{estado}</div>
                        <div style="font-size: 24px; font-weight: 600; color: #9ca3af;">Sem dados</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                variacao = resultado["variacao"]
                cor = cor_variacao(variacao)
                seta = "↑" if variacao > 0 else "↓" if variacao < 0 else "→"

                st.markdown(f"""
                    <div style="padding: 10px 0 20px 0;">
                        <div style="font-size: 14px; margin-bottom: 6px;">{estado}</div>
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

    df_temp = df_grupo.copy()

    df_temp["MES"] = (
        df_temp["DATACOMPRA"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    
    registros_mensais = []
    
    for (mes, estado), grupo_mes in df_temp.groupby(["MES", "ESTADO"]):
        preco_medio = calcular_media_ponderada(grupo_mes)
    
        if preco_medio is not None:
            registros_mensais.append({
                "DATACOMPRA": mes,
                "ESTADO": estado,
                "VALOR_NUM": preco_medio,
                "PESO_TOTAL_MES_KG": grupo_mes["PESO_TOTAL_COMPRA_KG"].sum()
            })
    
    df_mensal = (
        pd.DataFrame(registros_mensais)
        .sort_values("DATACOMPRA")
    )

    y_min = df_mensal["VALOR_NUM"].min()
    y_max = df_mensal["VALOR_NUM"].max()
    
    margem = (y_max - y_min) * 0.15
    
    range_y = [
        y_min - margem,
        y_max + margem
    ]
    
    cols_graficos = st.columns(3)

    for idx, estado in enumerate(ordem_estados):
        df_estado = df_mensal[df_mensal["ESTADO"] == estado].copy()

        with cols_graficos[idx]:
            if df_estado.empty:
                st.markdown(f"#### {estado}")
                st.caption("Sem dados no período")
                continue

            fig = px.line(
                df_estado,
                x="DATACOMPRA",
                y="VALOR_NUM",
                markers=True,
                text=df_estado["VALOR_NUM"].apply(lambda x: f"{x:.2f}"),
                title=estado
            )

            fig.update_xaxes(
                tickformat="%m/%Y",
                dtick="M1"
            )

            fig.update_traces(
                mode="lines+markers+text",
                textposition="top center",
                textfont=dict(size=9)
            )

            fig.update_layout(
                height=330,
                showlegend=False,
                hovermode="x unified",
                margin=dict(l=20, r=20, t=45, b=20),
                yaxis_title="Preço médio (R$)",
                xaxis_title=None,
                yaxis=dict(range=range_y)
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
            "GRUPO": "Grupo",
            "QUANTIDADE_NUM": "Quantidade",
            "PESO_UNITARIO_KG": "Peso Unitário (kg)",
            "PESO_TOTAL_COMPRA_KG": "Peso Total (kg)",
            "PORTE_COMPRA": "Porte da Compra"
        })

        colunas_exibir = [
            "Grupo",
            "Código do Insumo",
            "Insumo",
            "Preço de Compra",
            "Unidade",
            "Quantidade",
            "Peso Unitário (kg)",
            "Peso Total (kg)",
            "Porte da Compra",
            "Data da Compra",
            "Estado",
            "Fornecedor"
        ]

        st.dataframe(
            df_view[colunas_exibir],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("""
    <div style="
        border-top: 2px solid #e5e7eb;
        margin: 40px 0;
    "></div>
    """, unsafe_allow_html=True)
