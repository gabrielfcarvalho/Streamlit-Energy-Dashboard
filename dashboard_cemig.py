import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração inicial da página
st.set_page_config(page_title="Análise Energética", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# Função para carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("Dados.xlsx", sheet_name=None)

# Carregar dados do Excel
data = load_data()

# Definição das funções para cada página
def show_metrics_page():
    st.title('Métricas')
    start_date, end_date = setup_metrics(data)
    total_consumo, total_geracao, periodo_formatado = calculate_metrics(data, start_date, end_date)
    display_metrics(total_consumo, total_geracao, periodo_formatado)

def show_charts_page():
    st.title('Gráficos')
    tipo_dado, localidades_selecionadas, tipo_grafico = setup_charts_sidebar(data)
    titulo_grafico = f"{tipo_dado} nas propriedades {', '.join(localidades_selecionadas)}"
    plot_chart(data, titulo_grafico, tipo_dado, tipo_grafico, localidades_selecionadas)

def show_distribution_page():
    st.title('Distribuição de Energia')
    selected_month = setup_distribution_sidebar(data)
    display_monthly_energy_distribution(data, selected_month)
    with st.expander(f"Visualizar Sugestão de Distribuição Baseada no Consumo do mês {selected_month}"):
        display_suggested_energy_distribution(data, selected_month)

def calculate_metrics(data, start_period, end_period):
    total_consumo = sum(df[(df['Mês/Ano'] >= start_period) & (df['Mês/Ano'] <= end_period)]['Consumo Total em kWh'].sum() for df in data.values())
    total_geracao = data['Sapecado 1'][(data['Sapecado 1']['Mês/Ano'] >= start_period) & (data['Sapecado 1']['Mês/Ano'] <= end_period)]['Energia Gerada em kWh'].sum()
    periodo_formatado = f"{start_period} - {end_period}"
    return total_consumo, total_geracao, periodo_formatado

def display_metrics(total_consumo, total_geracao, periodo_formatado):
    col1, col2, col3 = st.columns(3)
    col1.metric("Período de Referência", periodo_formatado)
    col2.metric("Consumo Total de Energia (kWh)", "{:,.2f} kWh".format(total_consumo).replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Total de Energia Gerada (kWh)", "{:,.2f} kWh".format(total_geracao).replace(",", "X").replace(".", ",").replace("X", "."))

# Função para gerar os gráficos
def plot_chart(df, title, y_label, chart_type, localidades_selecionadas):
    # Verifica se 'Energia Gerada em kWh' foi selecionada sem 'Sapecado 1'
    if y_label == 'Energia Gerada em kWh' and 'Sapecado 1' not in localidades_selecionadas:
        st.error("A 'Energia Gerada em kWh' está disponível apenas para 'Sapecado 1'. Selecione 'Sapecado 1' para visualizar esse tipo de dado.")
        return

    # Filtrar os dados
    df_filtered = pd.DataFrame()
    for localidade in localidades_selecionadas:
        if localidade in df:
            df_loc = df[localidade].copy()
            df_loc['Localidade'] = localidade
            df_filtered = pd.concat([df_filtered, df_loc])
    
    if not df_filtered.empty:
        if chart_type == 'Linha':
            fig = px.line(df_filtered, x='Mês/Ano', y=y_label, color='Localidade', title=title)
        elif chart_type == 'Barra':
            fig = px.bar(df_filtered, x='Mês/Ano', y=y_label, color='Localidade', barmode='group', title=title)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Não foram selecionadas propriedades para exibir.")

# Função de configuração da barra lateral para gráficos
def setup_charts_sidebar(data):
    with st.sidebar:
        st.title('Filtros para os Gráficos')
        tipo_dado = st.selectbox('Selecione o que você gostaria de saber:', ['Consumo Total em kWh', 'Energia Compensada em kWh', 'Energia Transferida em kWh', 'Energia Gerada em kWh', 'Saldo Atual de Geração em kWh', 'Consumo Pago em kWh'])
        opcoes_localidades = list(data.keys())
        localidades_selecionadas = st.multiselect("Selecione as propriedades que deseja obter as informações:", options=opcoes_localidades, default=opcoes_localidades[0])
        tipo_grafico = st.radio('Selecione o tipo de gráfico:', ('Linha', 'Barra'))
        return tipo_dado, localidades_selecionadas, tipo_grafico

# Função de configuração da barra lateral para distribuição de energia
def setup_distribution_sidebar(data):
    with st.sidebar:
        st.title('Filtro para a Distribuição da Energia Gerada')
        meses_disponiveis = data['Sapecado 1']['Mês/Ano'].unique()
        selected_month = st.selectbox('Escolha o mês de referência:', meses_disponiveis)
        return selected_month

# Função de configuração da barra lateral para métricas
def setup_metrics(data):
    with st.sidebar:
        st.title('Filtros para as Métricas')
        # Criar lista de meses/anos disponíveis
        all_dates = sorted(set(date for df in data.values() for date in df['Mês/Ano']))
        # Seletores para escolher o período de referência
        start_period = st.selectbox('Período Inicial', all_dates, index=0)
        end_period = st.selectbox('Período Final', all_dates, index=len(all_dates) - 1)
        return start_period, end_period

# Atualização da função para calcular a energia transferida
def calculate_energy_transferred(data, loc, selected_month_index):
    loc_data = data[loc]
    if selected_month_index == 0:
        transferred = loc_data.iloc[0]['Energia Transferida em kWh'] if 'Energia Transferida em kWh' in loc_data.columns else 0
        return transferred

    current_month_data = loc_data.iloc[selected_month_index]
    transferred = current_month_data['Energia Transferida em kWh'] if 'Energia Transferida em kWh' in current_month_data else 0
    return max(0, transferred)


def display_monthly_energy_distribution(data, selected_month):
    st.write(f"## Distribuição de Energia Transferida para o Mês: {selected_month}")

    selected_month_index = data[next(iter(data))]['Mês/Ano'].tolist().index(selected_month)
    transferred_data = [{'Localidade': loc, 'Energia Transferida': calculate_energy_transferred(data, loc, selected_month_index)} for loc in data.keys()]

    if transferred_data:
        df_transferred = pd.DataFrame(transferred_data)
        fig = px.pie(df_transferred, values='Energia Transferida', names='Localidade', title=f"Distribuição de Energia Transferida do mês {selected_month}")
        st.plotly_chart(fig)
    else:
        st.write("Não há dados de energia transferida para exibir.")

def display_suggested_energy_distribution(data, selected_month):

    consumption_data = []
    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if not loc_data.empty and 'Consumo Total em kWh' in loc_data.columns:
            consumption = loc_data['Consumo Total em kWh'].sum()
            consumption_data.append({'Localidade': loc, 'Consumo': consumption})

    if consumption_data:
        df_consumption = pd.DataFrame(consumption_data)
        fig = px.pie(df_consumption, values='Consumo', names='Localidade', title=f"Sugestão de Distribuição Baseada no Consumo Total do Mês {selected_month}")
        st.plotly_chart(fig)
    else:
        st.write("Não há dados de consumo para exibir.")

# Seletor de páginas na barra lateral
with st.sidebar:
    st.title('***O que você gostaria de analisar?***:thinking_face:')
    page = st.radio("", ("Métricas :information_source:", "Gráficos :bar_chart:", "Distribuição de Energia :battery:"))

# Exibindo a página selecionada
if page == "Métricas :information_source:":
    show_metrics_page()
elif page == "Gráficos :bar_chart:":
    show_charts_page()
elif page == "Distribuição de Energia :battery:":
    show_distribution_page()