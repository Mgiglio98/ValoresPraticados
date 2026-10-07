from pathlib import Path
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

GRUPOS = {
    'Aço': ['H.11.0024', 'H.11.0034'],
    'Argamassa': ['J.02.0001', 'J.02.2000'],
    'Brita': ['J.01.0016'], 'Areia': ['J.03.0015'], 'Cimento': ['J.05.0001'],
}
PESOS = {'H.11.0024': 1, 'H.11.0034': 7.404, 'J.02.0001': 50,
         'J.02.2000': 50, 'J.01.0016': 20, 'J.03.0015': 20, 'J.05.0001': 50}
LIMITES = {'Aço': 3000, 'Argamassa': 2000, 'Brita': 2000, 'Areia': 2000, 'Cimento': 2000}
ESTADOS = ['RJ', 'SP']
CARGAS = ['Carga Completa', 'Carga Fracionada']
CORES = {'RJ': '#2563eb', 'SP': '#9333ea'}
COLUNAS = ['INSUMOCDG', 'INSUMO', 'VALORESPRATICADOS', 'UNIDADE',
           'QUANTIDADE', 'DATACOMPRA', 'ESTADO', 'FORNECEDOR', 'EMPREENDIMENTO']


def moeda(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def preparar_base(df):
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    faltantes = sorted(set(COLUNAS) - set(df.columns))
    if faltantes:
        raise ValueError('Colunas ausentes: ' + ', '.join(faltantes))
    for c in ['INSUMOCDG', 'UNIDADE', 'ESTADO']:
        df[c] = df[c].astype('string').str.strip().str.upper()
    for c in ['INSUMO', 'FORNECEDOR', 'EMPREENDIMENTO']:
        df[c] = df[c].astype('string').str.strip()
    df['EMPREENDIMENTO'] = df['EMPREENDIMENTO'].str.replace(r'\.0$', '', regex=True)
    mapa = {codigo: grupo for grupo, codigos in GRUPOS.items() for codigo in codigos}
    df['GRUPO'] = df['INSUMOCDG'].map(mapa)
    df = df.loc[df['GRUPO'].notna() & df['ESTADO'].isin(ESTADOS)
                & ~df['EMPREENDIMENTO'].isin(['2514', '9992'])].copy()
    df['DATACOMPRA'] = pd.to_datetime(df['DATACOMPRA'], errors='coerce', dayfirst=True)
    df['VALOR_NUM'] = pd.to_numeric(df['VALORESPRATICADOS'], errors='coerce')
    df['QUANTIDADE_NUM'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce')
    df['PESO_UNITARIO_KG'] = df['INSUMOCDG'].map(PESOS)
    df['PESO_TOTAL_COMPRA_KG'] = df['QUANTIDADE_NUM'] * df['PESO_UNITARIO_KG']
    df.loc[df['INSUMOCDG'].eq('H.11.0034'), 'VALOR_NUM'] /= 7.404
    validos = (df['DATACOMPRA'].notna() & np.isfinite(df['VALOR_NUM'])
               & np.isfinite(df['PESO_TOTAL_COMPRA_KG']) & df['PESO_TOTAL_COMPRA_KG'].gt(0))
    descartados = int((~validos).sum())
    df = df.loc[validos].copy()
    df['TIPO_CARGA'] = np.where(df['PESO_TOTAL_COMPRA_KG'].ge(df['GRUPO'].map(LIMITES)),
                                CARGAS[0], CARGAS[1])
    # Janela global definida após excluir SC, antes dos filtros da interface.
    if not df.empty:
        ultima = df['DATACOMPRA'].max()
        df = df.loc[df['DATACOMPRA'].ge(ultima - pd.DateOffset(years=1))].copy()
    return df, descartados


@st.cache_data(show_spinner=False)
def carregar_base(caminho, modificacao):
    # A data de modificação invalida o cache quando o Excel é atualizado.
    return preparar_base(pd.read_excel(caminho, sheet_name=0))


def resumo_mensal(df):
    temp = df.assign(MES=df['DATACOMPRA'].dt.to_period('M').dt.to_timestamp(),
                     VALOR_PONDERADO=df['VALOR_NUM'] * df['PESO_TOTAL_COMPRA_KG'])
    mensal = temp.groupby(['MES', 'ESTADO', 'TIPO_CARGA'], as_index=False).agg(
        SOMA_PONDERADA=('VALOR_PONDERADO', 'sum'),
        PESO_KG=('PESO_TOTAL_COMPRA_KG', 'sum'), REGISTROS=('INSUMOCDG', 'size'))
    mensal['PRECO_MEDIO'] = mensal['SOMA_PONDERADA'] / mensal['PESO_KG']
    return mensal.sort_values('MES')


def mostrar_card(serie, estado, carga):
    st.markdown(f'**{estado} · {carga}**')
    if serie.empty:
        st.caption('Sem compras no período.')
        return
    inicio, fim = serie.iloc[0], serie.iloc[-1]
    if len(serie) < 2 or inicio['PRECO_MEDIO'] == 0:
        st.markdown(f"### {moeda(fim['PRECO_MEDIO'])}")
        st.caption('Dados insuficientes para calcular a variação.')
        st.caption(f"Último mês: {fim['MES']:%m/%Y}")
        return
    variacao = (fim['PRECO_MEDIO'] / inicio['PRECO_MEDIO'] - 1) * 100
    cor = '#dc2626' if variacao > 0 else '#16a34a' if variacao < 0 else '#64748b'
    texto = 'Aumento' if variacao > 0 else 'Redução' if variacao < 0 else 'Estável'
    st.markdown(f'<div style="font-size:32px;font-weight:700;color:{cor}">{f'{variacao:+.2f}'.replace('.', ',')}%</div>',
                unsafe_allow_html=True)
    st.caption(texto + ' no período comparado')
    st.markdown(
        f'<div style="font-size:18px;font-weight:500;margin:12px 0;">'
        f'{html.escape(moeda(inicio["PRECO_MEDIO"]))} → '
        f'{html.escape(moeda(fim["PRECO_MEDIO"]))}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"{inicio['MES']:%m/%Y} → {fim['MES']:%m/%Y} · {len(serie)} meses com compras")


def main():
    st.set_page_config(page_title='Inflação de Insumos | Suprimentos', layout='wide')
    st.markdown('''<style>
    .block-container {padding-top:2rem;padding-bottom:2rem;max-width:1500px;}
    </style>''', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center;">Inflação de Insumos</h1>', unsafe_allow_html=True)
    caminho = Path(__file__).resolve().parent / 'BaseInflação.xlsx'
    if not caminho.exists():
        st.error('Coloque BaseInflação.xlsx na mesma pasta do painel.')
        st.stop()
    try:
        df, descartados = carregar_base(str(caminho), caminho.stat().st_mtime_ns)
    except (ValueError, OSError, ImportError) as erro:
        st.error(f'Não foi possível carregar a base: {erro}')
        st.stop()
    if df.empty:
        st.info('Não há registros válidos para RJ e SP nos insumos analisados.')
        st.stop()
    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    primeira_data = df['DATACOMPRA'].min()
    periodo = f'{meses_pt[primeira_data.month - 1]}/{primeira_data.year}'
    st.markdown(
        f'<div style="text-align:center;opacity:0.7;margin-bottom:28px;">'
        f'Suprimentos · Evolução dos preços praticados em RJ e SP desde {periodo}</div>',
        unsafe_allow_html=True,
    )
    a, b, c = st.columns([1.2, 1, 1.4])
    with a:
        grupo = st.selectbox('Tipo de insumo', list(GRUPOS))
    with b:
        estados = st.multiselect('Estado', ESTADOS, default=ESTADOS)
    with c:
        cargas = st.multiselect('Tipo de carga', CARGAS, default=CARGAS)
    if not estados or not cargas:
        st.info('Selecione pelo menos um estado e um tipo de carga.')
        st.stop()
    filtrado = df.loc[df['GRUPO'].eq(grupo) & df['ESTADO'].isin(estados)
                      & df['TIPO_CARGA'].isin(cargas)].copy()
    mensal = resumo_mensal(filtrado)
    st.markdown(
        f'<h2 style="text-align:center;margin-top:20px;">{html.escape(grupo)} · Variação dos preços</h2>'
        '<div style="text-align:center;opacity:0.7;margin-bottom:22px;">'
        'Variação entre o primeiro e o último mês com compras de cada combinação. '
        'Os meses comparados podem diferir.</div>',
        unsafe_allow_html=True,
    )
    combinacoes = [(e, c) for e in ESTADOS if e in estados for c in CARGAS if c in cargas]
    cards = st.columns(len(combinacoes))
    for coluna, (estado, carga) in zip(cards, combinacoes):
        with coluna:
            with st.container(border=True):
                serie = mensal.loc[mensal['ESTADO'].eq(estado) & mensal['TIPO_CARGA'].eq(carga)]
                mostrar_card(serie, estado, carga)
    if mensal.empty:
        st.info('Não há compras para essa seleção.')
    else:
        st.subheader('Evolução mensal do preço médio ponderado')
        unidade = 'R$/kg' if grupo == 'Aço' else 'R$/saco'
        fig = go.Figure()
        meses = pd.date_range(df['DATACOMPRA'].min().to_period('M').to_timestamp(),
                              df['DATACOMPRA'].max().to_period('M').to_timestamp(), freq='MS')
        for estado, carga in combinacoes:
            serie = mensal.loc[mensal['ESTADO'].eq(estado) & mensal['TIPO_CARGA'].eq(carga)]
            if serie.empty:
                continue
            serie = serie.set_index('MES').reindex(meses)
            fig.add_trace(go.Scatter(
                x=serie.index, y=serie['PRECO_MEDIO'], name=f'{estado} · {carga}',
                mode='lines+markers', connectgaps=False,
                line=dict(color=CORES[estado], width=3, dash='solid' if carga == CARGAS[0] else 'dot'),
                marker=dict(size=9, symbol='circle' if carga == CARGAS[0] else 'diamond'),
                customdata=serie[['PESO_KG', 'REGISTROS']].to_numpy(),
                hovertemplate='%{x|%m/%Y}<br>Preço médio: R$ %{y:.2f}<br>Peso: %{customdata[0]:,.0f} kg<br>Registros: %{customdata[1]:.0f}<extra>%{fullData.name}</extra>'))
        fig.update_layout(height=520, template='plotly_white', hovermode='x unified',
                          margin=dict(l=20, r=20, t=20, b=30),
                          legend=dict(orientation='h', y=1.12, x=0),
                          yaxis_title=f'Preço médio ponderado ({unidade})', xaxis_title=None,
                          separators=',.')
        fig.update_xaxes(dtick='M1', tickformat='%m/%Y', showgrid=False)
        fig.update_yaxes(tickprefix='R$ ', tickformat=',.2f', rangemode='normal')
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Meses sem compras ficam sem pontos e interrompem as linhas. Passe o mouse para ver preços e volumes.')
    with st.expander('Ver compras utilizadas na análise'):
        view = filtrado.sort_values('DATACOMPRA', ascending=False)[[
            'DATACOMPRA', 'ESTADO', 'TIPO_CARGA', 'INSUMOCDG', 'INSUMO', 'UNIDADE',
            'QUANTIDADE_NUM', 'VALORESPRATICADOS', 'VALOR_NUM', 'PESO_TOTAL_COMPRA_KG',
            'FORNECEDOR', 'EMPREENDIMENTO']].rename(columns={
                'DATACOMPRA': 'Data', 'ESTADO': 'Estado', 'TIPO_CARGA': 'Tipo de carga',
                'INSUMOCDG': 'Código', 'INSUMO': 'Insumo', 'UNIDADE': 'Unidade',
                'QUANTIDADE_NUM': 'Quantidade', 'VALORESPRATICADOS': 'Preço original (R$)',
                'VALOR_NUM': 'Preço utilizado (R$)', 'PESO_TOTAL_COMPRA_KG': 'Peso total (kg)',
                'FORNECEDOR': 'Fornecedor', 'EMPREENDIMENTO': 'Obra'})
        st.caption(f'{len(view)} registros da seleção atual')
        st.dataframe(view, hide_index=True, use_container_width=True,
                     column_config={'Data': st.column_config.DateColumn(format='DD/MM/YYYY'),
                                    'Preço original (R$)': st.column_config.NumberColumn(format='%.2f'),
                                    'Preço utilizado (R$)': st.column_config.NumberColumn(format='%.2f')})
    with st.expander('Como os indicadores são calculados'):
        st.write('A média mensal é ponderada pelo peso comprado. A carga é classificada por registro: '
                 'a partir de 3.000 kg para aço e 2.000 kg para os demais grupos, considera-se Carga Completa.')
        st.write('Aço em vara (H.11.0034): 7,404 kg por vara, com preço dividido por 7,404. '
                 'Os demais pesos e preços por saco seguem o cadastro do código original.')
        st.write('A janela cobre um ano anterior à última compra válida de RJ/SP. '
                 'As obras 2514 e 9992 ficam excluídas. Nenhum preço discrepante é removido automaticamente.')
        st.write('A variação representa os preços das compras realizadas e pode refletir mudanças na composição '
                 'dos insumos e fornecedores. A classificação de carga usa o peso de cada linha, não o total da OF.')
        if descartados:
            st.caption(f'{descartados} registros de RJ/SP desconsiderados por data/preço inválido ou peso não positivo.')


if __name__ == '__main__':
    main()
