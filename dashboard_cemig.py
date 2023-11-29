import streamlit as st
import pandas as pd
import plotly.express as px

# Função para carregar dados
@st.cache
def load_data():
    return pd.read_excel("Dados.xlsx", sheet_name=None)

# Carregar dados do Excel
data = load_data()

# Título do Dashboard
st.title('Análise Energética')

def calculate_metrics(data):
    total_consumo = sum(df['Consumo Total em kWh'].sum() for df in data.values())
    total_geracao = data['Sapecado 1']['Energia Gerada em kWh'].sum()
    return total_consumo, total_geracao

def display_metrics(total_consumo, total_geracao):
    col1, col2 = st.columns(2)
    col1.metric("Consumo Total de Energia (kWh)", "{:,.2f} kWh".format(total_consumo).replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Total de Energia Gerada (kWh)", "{:,.2f} kWh".format(total_geracao).replace(",", "X").replace(".", ",").replace("X", "."))

# Cálculo e exibição de métricas
total_consumo, total_geracao = calculate_metrics(data)
display_metrics(total_consumo, total_geracao)

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

def setup_sidebar(data):
    with st.sidebar:
        st.title('Filtros para o Gráfico')
        tipo_dado = st.selectbox('Selecione o que você gostaria de saber:', ['Consumo Total em kWh', 'Energia Injetada em kWh', 'Energia Gerada em kWh', 
            'Saldo Atual de Geração', 'Consumo Pago em kWh'])
        opcoes_localidades = list(data.keys())
        localidades_selecionadas = st.multiselect("Selecione as propriedades que deseja obter as informações:",
                                                  options=opcoes_localidades,
                                                  default=opcoes_localidades[0])
        tipo_grafico = st.radio('Selecione o tipo de gráfico:', ('Linha', 'Barra'))
        st.write("---")
        st.title('Filtro para a Distribuição de Energia Gerada')
        meses_disponiveis = data['Sapecado 1']['Mês/Ano'].unique()
        selected_month = st.selectbox('Escolha o mês de referência:', meses_disponiveis)
    return tipo_dado, localidades_selecionadas, tipo_grafico, selected_month

# Setup sidebar e captura de valores de filtro
tipo_dado, localidades_selecionadas, tipo_grafico, selected_month = setup_sidebar(data)

# Função para a distribuição mensal de energia
def display_monthly_energy_distribution(data, selected_month):
    # Processamento de dados
    month_data = data['Sapecado 1'][data['Sapecado 1']['Mês/Ano'] == selected_month]
    if month_data.empty:
        st.error(f"Não há dados disponíveis para o mês: {selected_month}")
        return
    
    total_generated = month_data['Energia Gerada em kWh'].sum()

    st.write(f"## Distribuição de Energia para o Mês: {selected_month}")

    previous_saldo = {loc: 0 for loc in data.keys() if 'Saldo Atual de Geração' in data[loc].columns}

    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if loc_data.empty:
            continue
        
        if 'Energia Injetada em kWh' in loc_data.columns and 'Saldo Atual de Geração' in loc_data.columns:
            injected = loc_data['Energia Injetada em kWh'].sum()
            current_saldo = loc_data['Saldo Atual de Geração'].sum()
            saldo_diff = max(0, current_saldo - previous_saldo[loc])
            injected_adjusted = injected + saldo_diff
            percentage_injected = (injected_adjusted / total_generated) * 100 if total_generated > 0 else 0
            st.write(f"{loc}: {percentage_injected:.2f}% de energia injetada (ajustado pelo saldo não utilizado)")
            previous_saldo[loc] = current_saldo

    # Sugestão de distribuição baseada no consumo
    st.write("### Sugestão de Distribuição Baseada no Consumo (%)")
    total_consumption_monthly = sum(data[loc][data[loc]['Mês/Ano'] == selected_month]['Consumo Total em kWh'].sum() for loc in data.keys() if 'Consumo Total em kWh' in data[loc].columns)

    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if loc_data.empty or 'Consumo Total em kWh' not in loc_data.columns:
            continue

        consumption = loc_data['Consumo Total em kWh'].sum()
        suggested_percentage = (consumption / total_consumption_monthly) * 100 if total_consumption_monthly > 0 else 0
        st.write(f"{loc}: {suggested_percentage:.2f}% sugerido com base no consumo")

# Abas para diferentes visualizações
with tab1:
    titulo_grafico = f"{tipo_dado} nas propriedades {', '.join(localidades_selecionadas)}"
    plot_chart(data, titulo_grafico, tipo_dado, tipo_grafico, localidades_selecionadas)    

with tab2:
    display_monthly_energy_distribution(data, selected_month)

