import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt
from datetime import datetime
import numpy as np
from src.pdf import listar_arquivos_docs, exportar_pdf
from src.nfe import listar_arquivos_pdfs, baixar_pdf
import src.utils as util

st.set_page_config(
    layout="wide",
    page_title="MH Refeições | Grupo Tamburi", 
    initial_sidebar_state="expanded", 
    page_icon="📊")

util.aplicar_estilo()

sidebar_logo = "https://i.postimg.cc/sgrdHyVy/tamburi.png"
main_body_logo = "https://i.postimg.cc/3xkGPmC6/streamlit02.png"
st.logo(sidebar_logo, icon_image=main_body_logo)

CODE = st.secrets["CODE"]
FILE_ID = st.secrets["FILE_ID"]

csv_url = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv"
df_elisa = pd.read_csv(csv_url, sep=",", decimal=",", thousands=".", usecols=['data', 'fazenda', 'almoco', 'janta', 'cafe', 'lanche', 'vlrCafe', 'vlrAlmoco', 'total'], index_col=None)

df_elisa['data'] = pd.to_datetime(df_elisa['data'], format='%d/%m/%Y', errors='coerce')
df_elisa['fazenda'] = df_elisa['fazenda'].astype('category')

contratos = [
    {"nome": "Safra 2025", "inicio": "2025-01-01", "fim": "2025-12-31"},
    {"nome": "Safra 2024", "inicio": "2024-01-01", "fim": "2024-12-31"},
    {"nome": "Safra 2023", "inicio": "2023-01-01", "fim": "2023-12-31"},
    {"nome": "Safra 2022", "inicio": "2022-01-01", "fim": "2022-12-31"},
]

opcoes = ["Todos os Contratos"] + [
    f"{c['nome']}"
    for c in contratos
]

opcao = st.sidebar.selectbox("Selecione o contrato:", opcoes, index=0)

if opcao == "Todos os Contratos":
    df = df_elisa.copy()
    data_menu = df['data'].min()
else:
    contrato = contratos[opcoes.index(opcao) - 1] 
    data_inicio = pd.to_datetime(contrato["inicio"])
    data_fim = pd.to_datetime(contrato["fim"])

    df = df_elisa[df_elisa['data'].between(data_inicio, data_fim)]
    data_menu = df['data'].min()

col1_side, col2_side = st.sidebar.columns([2,1])

col1_side.markdown('<h5 style="margin-bottom: -25px;">Início Apurado:', unsafe_allow_html=True)
col2_side.markdown(f'<h5 style="text-align: end; margin-bottom: -25px;">{data_menu.strftime("%d/%m/%Y")}</h5>', unsafe_allow_html=True)

col1_side.markdown('<h5 style="margin-bottom: 15px; color: #053061;">Última Atualização:</h5>', unsafe_allow_html=True)
col2_side.markdown('<h5 style="margin-bottom: 15px; text-align: end; color: #053061;">' + str(df['data'].max().strftime('%d/%m/%Y'))+ '</h5>', unsafe_allow_html=True)

if "autenticado_tab4" not in st.session_state:
    st.session_state["autenticado_tab4"] = False
if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "tab1"

tab1, tab2, tab3, tab4 = st.tabs(["📅 Fechamentos Diários",  "📊 Histórico Faturamento", "📂 Relatório (Fechamentos)", "📄 NFE's"])

########################################################################################
####### ABA FECHAMENTOS DIÁRIOS ########################################################
########################################################################################
with tab1:

    with st.container(border=True):
        col_data_ini, col_data_fim = st.columns(2)
        col1, col2, col3  = st.columns([1.775,1.7,1])   
        with col1:
            ct1 = st.container()
            ct2 = st.container(border=True )

        with col2:
            ct3 = st.container(border=True )
        with col3:
            ct4 = st.container(border=True )
    with st.container(border=True):

        colradios, col4, col5= st.columns([0.65,1.3,3])
        with colradios:
            colradio1 = st.container(border=True) 
            colradio2 = st.container(border=True)
        with col4:
            ct5 = st.container(border=True )
        with col5:
            ct6 = st.container(border=True )

########################################################################################
####### TABELA FECHAMENTO DIÁRIO #######################################################
########################################################################################

mes_atual = dt.datetime.today().month
ano_atual = dt.datetime.today().year

if df['data'].max().day < 20:
    mes_inicial_padrão = dt.date(ano_atual, mes_atual, 1)
else:
    mes_inicial_padrão = dt.date(ano_atual, mes_atual, 20)

df['data'] = pd.to_datetime(df['data'])

available_dates = set(df['data'].dt.date)

min_date = df['data'].min().date()
max_date = df['data'].max().date()

def validate_date(selected_date, available_dates):
    if selected_date in available_dates:
        return True
    else:
        st.error(f"A data {selected_date.strftime('%d/%m/%Y')} não está disponível. Por favor, selecione uma data válida.")
        return False

data_inicial = col_data_ini.date_input(
    'Data Início:', 
    max_date, 
    min_value=min_date, 
    max_value=max_date, 
    format="DD/MM/YYYY",  
    key="data_inicio_key"
)


if validate_date(data_inicial, available_dates):
    data_fim = col_data_fim.date_input(
        'Data Fim:', 
        None,
        min_value=data_inicial, 
        max_value=max_date, 
        format="DD/MM/YYYY", 
        key="data_fim_key",
    )

if data_inicial:
    data_inicial = pd.Timestamp(data_inicial)
if data_fim:
    data_fim = pd.Timestamp(data_fim)

df['data'] = pd.to_datetime(df['data'])

filtered_df = df[(df['data'] == data_inicial)]

if data_inicial is not None:
    dia_start = str(data_inicial.day).zfill(2)
    mes_start = str(data_inicial.month).zfill(2)
    ano_start = str(data_inicial.year)
if data_fim is not None:
    dia_end = str(data_fim.day).zfill(2)
    mes_end = str(data_fim.month).zfill(2)
    ano_end = str(data_fim.year)

if data_inicial and data_fim:
    if data_inicial > data_fim:
        st.warning('Data de início é maior que data de término!')
    else:
        filtered_df = df[(df['data'] >= data_inicial) & (df['data'] <= data_fim)] 

        if data_inicial == data_fim:
            periodo = dia_start + "/" + mes_start + "/" + ano_start                
        else:
            periodo = dia_start + "/" + mes_start + "/" + ano_start + " A " + dia_end + "/" + mes_end + "/" + ano_end
elif data_inicial:
    periodo = dia_start + "/" + mes_start + "/" + ano_start
    filtered_df = df[(df['data'] == data_inicial)]
elif data_fim:
    periodo = dia_end + "/" + mes_end + "/" + ano_end
    filtered_df = df[(df['data'] == data_fim)]

lista_fazenda = df['fazenda'].unique().tolist()

qtd_almoco = filtered_df.groupby("fazenda", observed=True)[["almoco"]].sum(numeric_only=True)
qtd_janta = filtered_df.groupby("fazenda", observed=True)[["janta"]].sum(numeric_only=True)
qtd_cafe = filtered_df.groupby("fazenda", observed=True)[["cafe"]].sum(numeric_only=True)
qtd_lanche = filtered_df.groupby("fazenda", observed=True)[["lanche"]].sum(numeric_only=True)

qtd_almoco = qtd_almoco.reindex(lista_fazenda)
qtd_janta = qtd_janta.reindex(lista_fazenda)
qtd_cafe = qtd_cafe.reindex(lista_fazenda)
qtd_lanche = qtd_lanche.reindex(lista_fazenda)

lista_almoco = qtd_almoco["almoco"].tolist()
lista_janta = qtd_janta["janta"].tolist()
lista_cafe = qtd_cafe["cafe"].tolist()
lista_lanche = qtd_lanche["lanche"].tolist()

lista_almoco_display = ['-' if v == 0 else v for v in lista_almoco]
lista_janta_display = ['-' if v == 0 else v for v in lista_janta]
lista_cafe_display = ['-' if v == 0 else v for v in lista_cafe]
lista_lanche_display = ['-' if v == 0 else v for v in lista_lanche]

data = {
    "Fazenda": lista_fazenda,
    "Café": lista_cafe_display,
    "Almoço": lista_almoco_display,
    "Lanche": lista_lanche_display,
    "Janta": lista_janta_display
}

data_frame = pd.DataFrame(data)

data_frame = data_frame.dropna(subset=["Café", "Almoço", "Lanche", "Janta"], how='all')

soma_colunas = {
    "Fazenda": "<b>TOTAL</b>",
    "Café": f"<b>{int(qtd_cafe.sum(numeric_only=True).iloc[0]):,}".replace(',', '.') + "</b>",
    "Almoço": f"<b>{int(qtd_almoco.sum(numeric_only=True).iloc[0]):,}".replace(',', '.') + "</b>",
    "Lanche": f"<b>{int(qtd_lanche.sum(numeric_only=True).iloc[0]):,}".replace(',', '.') + "</b>",
    "Janta": f"<b>{int(qtd_janta.sum(numeric_only=True).iloc[0]):,}".replace(',', '.') + "</b>"
}

soma_colunas_df = pd.DataFrame([soma_colunas])

data_frame = pd.concat([data_frame, soma_colunas_df], ignore_index=True)

fill_colors = [
    ['#176f87'] * len(data_frame), 
    ['white'] * len(data_frame), 
    ['#e2e7ed'] * len(data_frame), 
    ['white'] * len(data_frame), 
    ['#e2e7ed'] * len(data_frame),
]
font_colors = [
    ['white'] * len(data_frame),
    ['black'] * len(data_frame),
    ['black'] * len(data_frame),
    ['black'] * len(data_frame),
    ['black'] * len(data_frame)
]

for i, col in enumerate(data_frame.columns):
    for j, cell_value in enumerate(data_frame[col]):
        if '<b>' in str(cell_value):  
            fill_colors[i][j] = '#2d5480'  
            font_colors[i][j] = 'white'  

fig_tabela_dia = go.Figure(data=[go.Table(
    header=dict(
        values=list(data_frame.columns),
        fill_color='#244366',
        line_color="lightgrey",
        font_color="white",
        font=dict(size=14.5),
        align='center',
        height=28  
    ),
    cells=dict(
        values=[data_frame[col] for col in data_frame.columns],
        fill=dict(color=fill_colors),
        line_color="lightgrey",
        font=dict(color=font_colors, size=13),
        align='center',
        height=29  
    ))
])

fig_tabela_dia.update_layout(
                            yaxis=dict(
                                domain=[0.3, 1]  
                            ),
                            height=139,
                            margin=dict(r=0, t=20,b=0)
)

data_frame['Café'] = pd.to_numeric(data_frame['Café'], errors='coerce')
data_frame['Almoço'] = pd.to_numeric(data_frame['Almoço'], errors='coerce')
data_frame['Lanche'] = pd.to_numeric(data_frame['Lanche'], errors='coerce')
data_frame['Janta'] = pd.to_numeric(data_frame['Janta'], errors='coerce')

categorias = ['Café', 'Almoço', 'Lanche', 'Janta']
valores = [
    data_frame['Café'].sum(numeric_only=True),
    data_frame['Almoço'].sum(numeric_only=True),
    data_frame['Lanche'].sum(numeric_only=True),
    data_frame['Janta'].sum(numeric_only=True)
]

fig_barras = go.Figure(data=go.Bar(
    x=categorias,
    y=valores,
    text=valores,
    textposition='auto',
    texttemplate='%{y:.0f}',  
    marker_color=["#2d5480", "#176f87", "#2d5480", "#176f87"],  
    textangle = 0

))

fig_barras.update_layout(
    height=301,
    margin=dict(l=0, r=0, t=23, b=0),
    yaxis=dict(showticklabels=False),
    title_text=f'-QUANTIDADE TOTAL DE REFEIÇÕES ({periodo})',
    title_x=0,
    title_y=0.98,
    title_font_color="rgb(98,83,119)",
    title_font_size=15,
)
fig_barras.update_yaxes(showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey')
fig_barras.update_xaxes(showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey')

ct1.plotly_chart(fig_tabela_dia, use_container_width=True, automargin=True)
ct3.plotly_chart(fig_barras, use_container_width=True)

########################################################################################
####### GRÁFICO PIZZA FECHAMENTO DIÁRIO ################################################
########################################################################################
fazenda_total = filtered_df.groupby("fazenda", observed=True)[["total"]].sum(numeric_only=True).reset_index()

fazenda_total = fazenda_total[fazenda_total['total'] > 0]

total_geral = fazenda_total['total'].sum(numeric_only=True)
fazenda_total['porcentagem'] = fazenda_total['total'] / total_geral * 100

fazenda_total['porcentagem_formatada'] = fazenda_total['porcentagem'].apply(lambda x: f"{x:.2f}%")

fig_venda_fazenda = px.pie(fazenda_total, names='fazenda', values='porcentagem', 
                        color='fazenda', 
                        color_discrete_sequence= [util.barra_vermelha, util.barra_azul, util.barra_verde_escuro],
                        hover_data=['porcentagem_formatada'])

fig_venda_fazenda.update_traces(
    texttemplate='%{label}<br>%{value:.2f}%', 
    textposition='inside'
)

fig_venda_fazenda.update_layout(
    height=301, 
    margin=dict(l=0, t=35, b=0, r=0), 
    legend=dict(
        orientation="h",
        yanchor="top",
        y=0,
        xanchor="center",
        x=0.5,
        font=dict(size=12),
        itemsizing='constant',
        itemwidth=30,
        entrywidthmode='pixels'
    ),
    title={
        'text': f"-DISTRIBUIÇÃO ({periodo})",
        'y': 0.965,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {
            'color': "rgb(98,83,119)",
            'size': 15
        }
    },
)

ct4.plotly_chart(fig_venda_fazenda, use_container_width=True)


########################################################################################
####### GRAFICO BOX PLOT MENSAL ########################################################
########################################################################################
df_filtrado = df[(pd.to_datetime(df['data']).dt.month == data_inicial.month) &
                (pd.to_datetime(df['data']).dt.year == data_inicial.year)]

df_agrupado = df_filtrado.groupby(['data', 'fazenda', ], observed=True).sum(numeric_only=True).reset_index()

df_agrupado = df_agrupado.rename(columns={'cafe': 'Café', 'almoco': 'Almoço', 'lanche': 'Lanche', 'janta': 'Janta'})  

df_long = df_agrupado.melt(id_vars=['data', 'fazenda'], value_vars=['Café', 'Almoço', 'Lanche', 'Janta'], 
                        var_name='Refeição', value_name='Valor')

fazendas_com_valor = df_long[df_long['Valor'] > 0]['fazenda'].unique()
opcoes_fazenda = np.append(['Todas'], fazendas_com_valor)

with colradio1:
    fazenda_selecionada = st.radio("FAZENDA:", options=opcoes_fazenda, index=0, key="fazenda_selecionada")

if fazenda_selecionada != 'Todas':
    df_filtrado_fazenda = df_long[(df_long['fazenda'] == fazenda_selecionada) & (df_long['Valor'] >= 0)]
else:
    df_filtrado_fazenda = df_long[df_long['Valor'] >= 0]


df_filtrado_valor_radio = df_filtrado_fazenda[df_filtrado_fazenda['Valor'] > 0]

tipos_com_valor = df_filtrado_valor_radio['Refeição'].unique()

with colradio2:
    tipo_refeicao = st.radio("TIPO REFEIÇÃO:", options=tipos_com_valor, index=list(tipos_com_valor).index("Almoço") if "Almoço" in tipos_com_valor else 0, key="tipo_selecionado")

df_selecionado = df_filtrado_fazenda[df_filtrado_fazenda['Refeição'] == tipo_refeicao]

if fazenda_selecionada == 'Todas':
    df_selecionado = df_selecionado.groupby('data').sum(numeric_only=True).reset_index()

fig_box = go.Figure()

colors = {"Café": "#2d5480", "Almoço": "#2d5480", "Lanche": "#2d5480", "Janta": "#2d5480"}
color = colors.get(tipo_refeicao, "#b3112e") 

fig_box.add_trace(go.Box(
    y=df_selecionado['Valor'],
    name=tipo_refeicao,
    marker=dict(color="#2d5480"), 
    line=dict(color=color),  
    boxpoints="all",  
    hovertext=df_selecionado['data'].dt.strftime('%d/%m/%y')   
))

fig_box.update_layout(
    height=284,
    margin=dict(l=0, r=0, t=30, b=0),
    title_text=f'-BOX PLOT QTD. DE REFEIÇÕES ({util.mapa_meses[data_inicial.month].upper()}/{data_inicial.year})',
    title_font_color="rgb(98,83,119)",
    title_font_size=15,
    showlegend=False,
    title_x=0,
    title_y=1,
)

fig_box.update_yaxes(
        zerolinecolor='lightgrey',
        autorange=True,
        dtick=20,
        showline=False, 
        linecolor="Grey", 
        linewidth=0.1, 
        gridcolor='lightgrey', 
        showticklabels=True, 
        title_text='Quantidade',
)

fig_box.update_xaxes(showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey', title_text=f'{fazenda_selecionada}')
fig_box.update_traces(marker=dict(size=4.5),
                    boxmean='sd',)

ct5.plotly_chart(fig_box, use_container_width=True)

########################################################################################
####### GRÁFICO MENSAL QUANTIDADES POR DIA ##########################################
########################################################################################

df["data"] = pd.to_datetime(df["data"], errors='coerce')
df["Almoço | Janta"] = df["almoco"] + df["janta"]
df["Café | Lanche"] = df["cafe"] + df["lanche"]
df["ano"] = df["data"].dt.year
df["mes"] = df["data"].dt.month
df["dia"] = df["data"].dt.day

data_inicial = pd.Timestamp(data_inicial)  
data_selecionada = data_inicial

data_inicio = data_selecionada - pd.Timedelta(days=28)
data_fim = data_selecionada

df_filtrado = df[(df["data"] >= data_inicio) & (df["data"] <= data_fim)]

if fazenda_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['fazenda'] == fazenda_selecionada]

df_grouped = df_filtrado.groupby(["ano", "mes", "dia"]).sum(numeric_only=True).reset_index()

df_grouped["Dia/Mês"] = df_grouped.apply(lambda row: f"{str(int(row['dia'])).zfill(2)}/{str(int(row['mes'])).zfill(2)}", axis=1)

dia_selecionado = data_selecionada.day

linhas_verticais = []
for day in range(dia_selecionado, df_grouped['dia'].min() - 1, -7):
    if day in df_grouped['dia'].values:
        day_label = df_grouped[df_grouped['dia'] == day]["Dia/Mês"].values[0]
        linhas_verticais.append(day_label)
        
for day in range(dia_selecionado + 7, df_grouped['dia'].max() + 1, 7):
    if day in df_grouped['dia'].values:
        day_label = df_grouped[df_grouped['dia'] == day]["Dia/Mês"].values[0]
        linhas_verticais.append(day_label)

fig = go.Figure()

def should_show_text(x_value):
    return x_value in linhas_verticais

fig.add_trace(go.Bar(
    x=df_grouped["Dia/Mês"],
    y=df_grouped["Almoço | Janta"],
    name="Almoço | Janta",
    marker_color="#81a8b4",
    showlegend=True,  
    text=df_grouped.apply(lambda row: f"<b>{int(row['Almoço | Janta'])}</b>" if row["Dia/Mês"] in linhas_verticais else "", axis=1),
    textposition='outside',
    textangle=-45,
    textfont=dict(
        color=util.barra_verde_escuro,
    )    
))

fig.add_trace(go.Bar(
    x=df_grouped["Dia/Mês"],
    y=df_grouped["Café | Lanche"],
    name="Café | Lanche",
    marker_color="#6882a0",
    showlegend=True,  
    text=df_grouped.apply(lambda row: f"<b>{int(row['Café | Lanche'])}</b>" if row["Dia/Mês"] in linhas_verticais else "", axis=1),
    textposition='outside',
    textangle=-45,
    textfont=dict(
        color=util.barra_azul_escuro,
    )   
))

for day_label in linhas_verticais:
    fig.add_shape(
        type="line",
        x0=day_label,
        x1=day_label,
        y0=0,
        y1=df_grouped[["Almoço | Janta", "Café | Lanche"]].max().max(),
        line=dict(color="#b3112e", width=1, dash="dot")
    )

ultimo_dia_almoco_janta = df_grouped["Almoço | Janta"].iloc[-1]
ultimo_dia_cafe_lanche = df_grouped["Café | Lanche"].iloc[-1]

fig.add_shape(
    type="line",
    x0=df_grouped["Dia/Mês"].iloc[0],
    x1=df_grouped["Dia/Mês"].iloc[-1],
    y0=ultimo_dia_almoco_janta,
    y1=ultimo_dia_almoco_janta,
    line=dict(color="#176f87", width=1.5, dash="dashdot") 
)

fig.add_shape(
    type="line",
    x0=df_grouped["Dia/Mês"].iloc[0],
    x1=df_grouped["Dia/Mês"].iloc[-1],
    y0=ultimo_dia_cafe_lanche,
    y1=ultimo_dia_cafe_lanche,
    line=dict(color="#2d5480", width=1.5, dash="dashdot")
)

if len(df_grouped) < 21:
    tickvals = df_grouped["Dia/Mês"].tolist()
else:
    tickvals = linhas_verticais

fig.update_yaxes(showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey', dtick=30, range=[0, df_grouped["Almoço | Janta"].max() + 12])
fig.update_xaxes(
    showline=True, 
    linecolor="Grey", 
    linewidth=0.1, 
    gridcolor='lightgrey',
    tickmode='array',
    tickvals=tickvals,
    tickformat="%d/%m"
)
fig.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),
    height=284,
    title=" ",
    title_text = (
        f"-DISTRIBUIÇÃO DE REFEIÇÕES AGRUPADAS "
        f"({data_inicio.day:02d}/{data_inicio.month:02d}/{data_inicio.year} "
        f"A {data_fim.day:02d}/{data_fim.month:02d}/{data_fim.year})"
    ),
    title_x=0,
    title_y=1,
    title_font_color="rgb(98,83,119)",
    title_font_size=15,
    barmode='group',  
    yaxis=dict(showticklabels=False),
    xaxis_title="Período",
    legend=dict(x=0.7315, y=1.115, orientation='h')  
)

ct6.plotly_chart(fig, use_container_width=True, automargin=True)

########################################################################################
####### GRAFICO AREA HISTORICO QUANTIDADES #############################################
########################################################################################

df["Almoço | Janta"] = df["almoco"] + df["janta"]
df["Café | Lanche"] = df["cafe"] + df["lanche"]
df["ano"] = df["data"].dt.year
df["mes"] = df["data"].dt.month

df_grouped_area = df.groupby(["ano", "mes"]).sum(numeric_only=True).reset_index()
df_grouped_area["Mês/Ano"] = df_grouped_area.apply(lambda row: f"{util.mapa_meses[int(row['mes'])]}/{int(row['ano'])}", axis=1)

data_inicial_area = pd.Timestamp(df['data'].min())
data_fim_area = pd.Timestamp(df['data'].max())
periodo_area = f"{util.mapa_meses[data_inicial_area.month].upper()}/{data_inicial_area.year} A {util.mapa_meses[data_fim_area.month].upper()}/{data_fim_area.year}"

current_month = pd.Timestamp.now().month
current_year = pd.Timestamp.now().year
previous_month = current_month - 1 if current_month != 1 else 12
previous_year = current_year if current_month != 1 else current_year - 1

filtered_df = df_grouped_area[(df_grouped_area["ano"] == previous_year) & (df_grouped_area["mes"] == previous_month)]

if not filtered_df.empty:
    previous_almoco_janta_value = filtered_df["Almoço | Janta"].values[0]
    previous_cafe_lanche_value = filtered_df["Café | Lanche"].values[0]
else:
    previous_almoco_janta_value = 0 
    previous_cafe_lanche_value = 0   

fig_area = go.Figure()

fig_area.add_trace(go.Scatter(
    x=df_grouped_area["Mês/Ano"],
    y=df_grouped_area["Almoço | Janta"],
    mode='lines+markers+text',
    name="Almoço | Janta",
    fill='tozeroy',
    marker_color=util.barra_verde,
))

fig_area.add_trace(go.Scatter(
    x=df_grouped_area["Mês/Ano"],
    y=df_grouped_area["Café | Lanche"],
    mode='lines+markers+text',
    name="Café | Lanche",
    fill='tozeroy',
    marker_color=util.barra_azul,
    fillcolor="#6c87a6"
))

fig_area.add_shape(
    type="line",
    x0=df_grouped_area["Mês/Ano"].iloc[0],
    x1=df_grouped_area["Mês/Ano"].iloc[-1],
    y0=previous_almoco_janta_value,
    y1=previous_almoco_janta_value,
    line=dict(color="#0e7089", width=1.5, dash="dashdot")
)

fig_area.add_shape(
    type="line",
    x0=df_grouped_area["Mês/Ano"].iloc[0],
    x1=df_grouped_area["Mês/Ano"].iloc[-1],
    y0=previous_cafe_lanche_value,
    y1=previous_cafe_lanche_value,
    line=dict(color="#145073", width=1.5, dash="dashdot")
)

previous_month_years = df_grouped_area[df_grouped_area["mes"] == previous_month]["ano"].values
linhas_verticais = []
for year in previous_month_years:
    month_year_label = f"{util.mapa_meses[previous_month]}/{year}"
    linhas_verticais.append(month_year_label)
    fig_area.add_shape(
        type="line",
        x0=month_year_label,
        x1=month_year_label,
        y0=0,
        y1=df_grouped_area["Almoço | Janta"].max(),
        line=dict(color="#b3112e", width=1, dash="dot")
    )

tickvals = linhas_verticais

fig_area.update_yaxes(showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey', dtick=2000)
fig_area.update_xaxes(showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey', tickmode='array', tickvals=tickvals)
fig_area.update_layout(
    margin=dict(l=5, r=0, t=28, b=0),
    height=145.5,
    title=f"-HISTÓRICO REFEIÇÕES AGRUPADAS ({periodo_area})",
    title_font_color="rgb(98,83,119)",
    title_font_size=15,
    legend=dict(x=0.722, y=1.09, orientation='h'),
    title_x=0,
    title_y=1,
    yaxis=dict(showticklabels=False),
    showlegend=False
)

ct2.plotly_chart(fig_area, use_container_width=True, automargin=True)


########################################################################################
####### ABA HISTORICO FATURAMENTO ######################################################
########################################################################################
with tab2:

    with st.container(border=True):
        col_filtro_mes, col_filtro_ano = st.columns(2) 

        col6, col2000 = st.columns([5,1])
        with col6:
            ctt6 = st.container(border=True )
        with col2000:

            c2000 = st.container()  
            c2001 = st.container()  

            c2002 = st.container()  
            c2003 = st.container()

    with st.container(border=True):
        col8, col7 = st.columns([2,4])

        with col8:
            ctt8 = st.container(border=True )
        with col7:
            ctt7 = st.container(border=True )  

    with st.container(border=True):
        ctt9 = st.container(border=True )              


    ########################################################################################
    ####### GRAFICO VISAO GERAL MENSAL #####################################################
    ########################################################################################
        
    mes_atual = util.mapa_meses[dt.datetime.now().month]
    ano_atual = dt.datetime.now().year

    anos_disponiveis = util.anos_disponiveis(df)

    ano_selecionado = col_filtro_ano.selectbox(
        'Selecione o Ano:',
        anos_disponiveis,
        index=len(anos_disponiveis)-1,
        key="tabela_ano"
    )
    meses_nomes_disponiveis = util.atualiza_meses_disponiveis(ano_selecionado, df)

    mes_selecionado = col_filtro_mes.selectbox(
        'Selecione um Mês:',
        meses_nomes_disponiveis,
        index=len(meses_nomes_disponiveis)-1,
        key="tabela_mes"
    )

    linha_mais_recente = df.sort_values(by='data', ascending=False).iloc[0]
    valor_refeicao = "R$ {:,.2f}".format(linha_mais_recente['vlrAlmoco']).replace(".", "@").replace(",", ".").replace("@", ",")
    valor_lanche = "R$ {:,.2f}".format(linha_mais_recente['vlrCafe']).replace(".", "@").replace(",", ".").replace("@", ",")

    c2000.success(f"Refeição: {valor_refeicao}", icon=":material/attach_money:")

    c2001.success(f"Lanche:  {valor_lanche}", icon=":material/attach_money:")


    mes_selecionado = [key for key, value in util.mapa_meses.items() if value == mes_selecionado][0]

    df_mes_filtrado = df[(df['data'].dt.month == mes_selecionado) & (df['data'].dt.year == ano_selecionado)]

    venda_total = df_mes_filtrado.groupby("data")[["total"]].sum(numeric_only=True).reset_index()

    primeira_quinzena = venda_total[venda_total['data'].dt.day <= 15]['total'].sum()
    segunda_quinzena = venda_total[venda_total['data'].dt.day >= 16]['total'].sum()

    primeira_quinzena_formatado = f"R$ {primeira_quinzena:,.2f}".replace('.', '@').replace(',', '.').replace('@', ',')
    segunda_quinzena_formatado = f"R$ {segunda_quinzena:,.2f}".replace('.', '@').replace(',', '.').replace('@', ',')

    if primeira_quinzena > 0:
        c2002.info(f"1º Fechamento: {primeira_quinzena_formatado}")

    if segunda_quinzena > 0:
        c2003.info(f"2º Fechamento:  {segunda_quinzena_formatado}")


    venda_total['total_formatado'] = venda_total['total'].apply(lambda x: f"R$ {x:,.2f}".replace('.', '@').replace(',', '.').replace('@', ','))

    venda_total['data_formatada'] = venda_total['data'].dt.strftime('%d/%m/%y')

    fig_venda_mes = px.bar(
        venda_total, 
        x='data_formatada', 
        y='total', 
        orientation='v',
        text=venda_total['total'].apply(util.formata_para_brl),
        color_discrete_sequence=[util.barra_azul],

    )

    fig_venda_mes.update_yaxes(title_text="", showline=True, linecolor="Grey",linewidth=0.1, gridcolor='lightgrey')
    fig_venda_mes.update_xaxes(title_text="", showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey')
    fig_venda_mes.update_traces(textposition='inside')
    fig_venda_mes.update_layout(margin=dict(t=30, b=0, l=0),height=301,yaxis_title="Receita", xaxis_title="Período", title=f"-FATURAMENTO DIÁRIO ({util.mapa_meses[mes_selecionado].upper()}/{ano_selecionado})", title_font_color="rgb(98,83,119)", title_font_size=15)

    ctt6.plotly_chart(fig_venda_mes, use_container_width=True)


    ########################################################################################
    ####### GRAFICO VISAO GERAL ANUAL ######################################################
    ########################################################################################

    df['mes_num'] = df['data'].dt.month
    df['ano'] = df['data'].dt.year

    df_filtrado = df[df['ano'] == ano_selecionado]

    venda_total_mensal = df_filtrado.groupby(['mes_num', 'ano'])[['total']].sum(numeric_only=True).reset_index()

    venda_total_mensal = venda_total_mensal.sort_values(by='mes_num')

    venda_total_mensal['mes'] = venda_total_mensal['mes_num'].map(util.mapa_meses)
    venda_total_mensal['mes_ano'] = venda_total_mensal['mes'] + '/' + venda_total_mensal['ano'].astype(str)

    venda_total_mensal['total_formatado'] = venda_total_mensal['total'].apply(lambda x: f"R$ {x:,.2f}".replace('.', '@').replace(',', '.').replace('@', ','))

    fig_venda_ano = px.bar(
        venda_total_mensal,
        height=301,
        x='mes', 
        y='total', 
        orientation='v',
        text='total_formatado',
        color_discrete_sequence=[util.barra_verde_escuro],

    )

    fig_venda_ano.update_yaxes(title_text="", showline=True, linecolor="Grey",linewidth=0.1, gridcolor='lightgrey')
    fig_venda_ano.update_xaxes(title_text="", showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey')
    fig_venda_ano.update_traces(textposition='inside')
    fig_venda_ano.update_layout(margin=dict(t=30, b=0, l=0),height=301,yaxis_title="Receita", xaxis_title="Período", title=f"-FATURAMENTO MENSAL ({ano_selecionado})", title_font_color="rgb(98,83,119)", title_font_size=15)

    ctt7.plotly_chart(fig_venda_ano, use_container_width=True)

    ########################################################################################
    ####### GRAFICO HISTORICO ANUAL ########################################################
    ########################################################################################

    df['ano'] = df['data'].dt.year.astype(str)

    venda_total_anual = df.groupby('ano')[['total']].sum(numeric_only=True).reset_index()

    venda_total_anual['total_formatado'] = venda_total_anual['total'].apply(lambda x: f"R$ {x:,.2f}".replace('.', '@').replace(',', '.').replace('@', ','))

    fig_venda_ano.update_yaxes(
        showline=True,
        linecolor = "Grey",
        linewidth=0.5
    )

    fig_hist_ano = px.bar(
        venda_total_anual, 
        x='ano', 
        y='total', 
        orientation='v',
        text='total_formatado',
        color_discrete_sequence=[util.barra_verde],
    )

    fig_hist_ano.update_yaxes(
        title_text="",
        showline=True,
        linecolor="Grey",
        linewidth=0.1,
        gridcolor='lightgrey'
    )

    fig_hist_ano.update_xaxes(
        title_text="",
        showline=True,
        linecolor="Grey",
        linewidth=0.1,
        gridcolor='lightgrey',
        type='category'   
    )

    fig_hist_ano.update_traces(textposition='inside')

    fig_hist_ano.update_layout(
        margin=dict(t=30, b=0, l=0),
        height=301,
        yaxis_title="Receita",
        xaxis_title="Período",
        title="-FATURAMENTO ANUAL",
        title_font_color="rgb(98,83,119)",
        title_font_size=15
    )
    ctt8.plotly_chart(fig_hist_ano, use_container_width=True)

    ########################################################################################
    ####### GRAFICO COMPARATIVO FATURAMENTO ANUAL ##########################################
    ########################################################################################
    df['ano_mes'] = df['data'].dt.to_period('M')

    current_month = pd.Timestamp.now().to_period('M')
    
    df_filtered = df[df['ano_mes'] != current_month]
    
    venda_total_mensal = df_filtered.groupby('ano_mes')[['total']].sum(numeric_only=True).reset_index()
    venda_total_mensal['Anos'] = venda_total_mensal['ano_mes'].dt.year.astype(str)
    venda_total_mensal['mes'] = venda_total_mensal['ano_mes'].dt.month.astype(int)
    venda_total_mensal['nome_mes'] = venda_total_mensal['mes'].map(util.mapa_meses)
    venda_total_mensal['total_formatado'] = venda_total_mensal['total'].apply(lambda x: f"R$ {x:,.2f}".replace('.', '@').replace(',', '.').replace('@', ','))

    colors = px.colors.diverging.RdBu

    fig_comparativo_anual = px.bar(
        venda_total_mensal, 
        x='nome_mes', 
        y='total', 
        color="Anos",
        barmode='group',
        orientation='v',
        color_discrete_sequence=px.colors.sequential.Bluyl_r,
        text='total_formatado',
    )

    fig_comparativo_anual.update_yaxes(title_text="", showline=True, linecolor="Grey",linewidth=0.1, gridcolor='lightgrey')
    fig_comparativo_anual.update_xaxes(title_text="", showline=True, linecolor="Grey", linewidth=0.1, gridcolor='lightgrey')
    fig_comparativo_anual.update_traces(textposition='inside')
    fig_comparativo_anual.update_layout(margin=dict(t=50, b=0, l=0),height=301,yaxis_title="Receita", xaxis_title="Período", title=f"-COMPARATIVO FATURAMENTO ANUAL", title_font_color="rgb(98,83,119)", title_font_size=15)

    ctt9.plotly_chart(fig_comparativo_anual, use_container_width=True)

########################################################################################
####### ABA RELATÓRIOS E FECHAMENTOS ###################################################
########################################################################################
with tab3:
    arquivos = listar_arquivos_docs()

    if not arquivos:
        st.warning("Nenhum arquivo DOC encontrado na pasta.")
    else:
        # Lista apenas nomes
        nomes = [f["name"] for f in arquivos]

        # Extrair ano e mês do padrão AAAAMM-SEQ
        anos_meses = sorted(
            {(n[:4], n[4:6]) for n in nomes if len(n) >= 6},
            key=lambda x: (x[0], x[1])
        )

        # Pegar último ano/mês disponível
        ultimo_ano, ultimo_mes = anos_meses[-1]


        with st.container(border=True):
           col_ano, col_mes, col_drop, col_convert, col_download = st.columns([2, 2, 3, 2, 2])
        

        with col_ano:
            anos_disp = sorted({a for a, m in anos_meses})
            ano_sel = st.selectbox(
                "Selecione o Ano:",
                anos_disp,
                index=anos_disp.index(ultimo_ano),
                key="ano_docs"
            )

        with col_mes:
            meses_disp = sorted({m for a, m in anos_meses if a == ano_sel})
            # Converter meses para extenso
            meses_labels = [util.mapa_meses[int(m)] for m in meses_disp]
            mes_idx_default = meses_disp.index(ultimo_mes) if ano_sel == ultimo_ano else 0

            mes_sel_label = st.selectbox(
                "Selecione o Mês:",
                meses_labels,
                index=mes_idx_default,
                key="mes_docs"
            )

            # Converter de volta para número (com zero à esquerda)
            mes_sel = f"{list(util.mapa_meses.keys())[list(util.mapa_meses.values()).index(mes_sel_label)]:02d}"

        # Filtrar documentos pelo ano/mês selecionado
        nomes_filtrados = [
            n for n in nomes if n.startswith(f"{ano_sel}{mes_sel}")
        ]

        with col_drop:
            escolha = st.selectbox(
                "Selecione um Fechamento: (aaaamm-seq)",
                nomes_filtrados,
                key="drop_docs"
            )

        # Botão de exportar PDF
        with col_convert:
            st.markdown("<div style='margin-top: 27.8px;'>", unsafe_allow_html=True)
            if st.button("⬇️ Exportar como PDF", key="export_pdf_tab3", use_container_width=True):
                idx = nomes.index(escolha)
                file_id = arquivos[idx]["id"]
                nome_arquivo = arquivos[idx]["name"]
                fh, nome_pdf = exportar_pdf(file_id, nome_arquivo)
                download_data = fh.getvalue()
            st.markdown("</div>", unsafe_allow_html=True)

        # Botão de download PDF
        with col_download:
            st.markdown("<div style='margin-top: 27.8px;'>", unsafe_allow_html=True)
            if "download_data" in locals() and download_data and nome_pdf:
                st.download_button(
                    label="📥 Download PDF",
                    data=download_data,
                    file_name=nome_pdf,
                    mime="application/pdf",
                    key="download_pdf_tab3",
                    use_container_width=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # Exibir Google Doc original
        idx = nomes.index(escolha)
        file_id = arquivos[idx]["id"]
        doc_url = f"https://docs.google.com/document/d/{file_id}/preview"
        with st.container(border=True):
            st.components.v1.iframe(src=doc_url, height=450, scrolling=True)
            
########################################################################################
####### ABA NFE ########################################################################
########################################################################################
with tab4:
    st.session_state["aba_ativa"] = "tab4"

    if not st.session_state["autenticado_tab4"]:
        with st.container(border=True):
            placeholder4 = st.empty()  

            with st.form("form_tab4", clear_on_submit=False):
                codigo4 = st.text_input("Digite o Código de Acesso:", type="password", key="codigo_tab4")
                submit4 = st.form_submit_button("Entrar")

            if submit4:
                if codigo4 == CODE:
                    st.session_state["autenticado_tab4"] = True
                    st.session_state["aba_ativa"] = "tab4"
                    st.rerun()
                else:
                    placeholder4.error("Código Incorreto ❌")
            else:
                placeholder4.warning("Digite o Código para acessar NFE's")

    else:
    
        arquivos = listar_arquivos_pdfs()

        if not arquivos:
            st.warning("Nenhum arquivo PDF encontrado na pasta.")
        else:
            nomes = [f["name"] for f in arquivos]

            anos_meses = sorted(
                {(n[:4], n[4:6]) for n in nomes if len(n) >= 6},
                key=lambda x: (x[0], x[1])
            )

            ultimo_ano, ultimo_mes = anos_meses[-1]

            with st.container(border=True):
                col_ano_pdf, col_mes_pdf, col_drop_pdf, col_download_pdf = st.columns([2, 2, 3, 2])

            with col_ano_pdf:
                anos_disp = sorted({a for a, m in anos_meses})
                ano_sel = st.selectbox(
                    "Selecione o Ano:",
                    anos_disp,
                    index=anos_disp.index(ultimo_ano),
                    key="ano_pdf"
                )

            with col_mes_pdf:
                meses_disp = sorted({m for a, m in anos_meses if a == ano_sel})
                meses_labels = [util.mapa_meses[int(m)] for m in meses_disp]
                mes_idx_default = meses_disp.index(ultimo_mes) if ano_sel == ultimo_ano else 0

                mes_sel_label = st.selectbox(
                    "Selecione o Mês:",
                    meses_labels,
                    index=mes_idx_default,
                    key="mes_pdf"
                )

                mes_sel = f"{list(util.mapa_meses.keys())[list(util.mapa_meses.values()).index(mes_sel_label)]:02d}"

            nomes_filtrados = [n for n in nomes if n.startswith(f"{ano_sel}{mes_sel}")]
        
            with col_drop_pdf:
                escolha = st.selectbox(
                    "Selecione um Fechamento: (aaaamm-seq)",
                    nomes_filtrados,
                    key="drop_pdf"
                )

            with col_download_pdf:
                st.markdown("<div style='margin-top: 27.8px;'>", unsafe_allow_html=True)
                idx = nomes.index(escolha)
                file_id = arquivos[idx]["id"]
                fh = baixar_pdf(file_id)
                st.download_button(
                    label="📥 Download NFE",
                    data=fh.getvalue(),
                    file_name=escolha,
                    mime="application/pdf",
                    key="download_pdf_tab4",
                    use_container_width=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

            idx = nomes.index(escolha)
            file_id = arquivos[idx]["id"]
            pdf_url = f"https://drive.google.com/file/d/{file_id}/preview"
            with st.container(border=True):
                st.components.v1.iframe(src=pdf_url, height=450, scrolling=True)


st.markdown(
    """
    <div style="
        position: fixed; 
        bottom: 0;
        left: 0;
        right: 0; 
        width: 100%; 
        background-color: #c6d0d2; 
        padding: 2.5px; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        color: #2d5480; 
        font-size: 14px;
        gap: 8px;
    ">
        <span>Developed by </span>
        <a href="https://github.com/rafa-trindade" target="_blank">
            <img src="https://img.shields.io/badge/-Rafael%20Trindade-2D5480?style=flat-square&logo=github&logoColor=E4E3E3" alt="GitHub Badge">
        </a>
    </div>

    """,
    unsafe_allow_html=True
)