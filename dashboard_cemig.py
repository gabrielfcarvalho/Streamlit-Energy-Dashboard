import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# Função para carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("Dados.xlsx", sheet_name=None)

# Carregar dados do Excel
data = load_data()

# Título do Dashboard
st.title('Consumo e Geração de Energia')


def convert_to_date(month_year_str):
    meses = {
        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
    }
    mes, ano = month_year_str.split('/')
    ano = int(ano) if len(ano) == 4 else int(ano) + 2000
    return date(year=ano, month=meses[mes], day=1)

# Depois de carregar os dados, aplique essa função para converter as datas
for key, df in data.items():
    df['Mês/Ano'] = df['Mês/Ano'].apply(convert_to_date)

# Sidebar para seleção de dados
with st.sidebar:
    st.title('Filtros para o Gráfico')
    tipo_dado = st.selectbox('Selecione o que você gostaria de saber:', ['Consumo Total em kWh', 'Energia Injetada em kWh', 'Energia Gerada em kWh', 
     'Saldo Atual de Geração', 'Consumo Pago em kWh'])
    opcoes_localidades = list(data.keys()) + ['Todas as Localidades']
    localidade_selecionada = st.selectbox('Selecione a propriedade:', opcoes_localidades)
    tipo_grafico = st.radio('Selecione o tipo de gráfico:', ('Linha', 'Barra'))

    st.write("## Filtro de Data")
    # Assume que os dados estão ordenados por data. Se não, ordene-os antes de usar.
    start_date = data[next(iter(data))]['Mês/Ano'].min()
    end_date = data[next(iter(data))]['Mês/Ano'].max()
    data_inicio, data_fim = st.date_input("Selecione o intervalo de datas:", [start_date, end_date])

    st.write("## Comparação de Localidades")
    localidades_selecionadas = st.multiselect("Selecione as localidades para comparar:", options=opcoes_localidades, default=opcoes_localidades[0])

    # Separador na sidebar
    st.write("---")  # Isso adiciona uma linha horizontal para separar visualmente as seções

    st.title('Filtro para a Distribuição de Energia Gerada')
        
    # Usar os meses conforme estão nos dados
    meses_disponiveis = data['Sapecado 1']['Mês/Ano'].unique()

    # Selectbox para escolher o mês
    selected_month = st.selectbox('Escolha o mês de referência:', meses_disponiveis)
# Tabs para diferentes visualizações
tab1, tab2 = st.tabs(["Gráficos", "Distribuição da Energia Gerada"])

# Função ajustada para plotar gráficos com os filtros aplicados
def plot_chart(df, title, y_label, chart_type, localidades, start_date, end_date):
    # Filtrar o DataFrame por localidades selecionadas e intervalo de datas
    if 'Todas as Localidades' in localidades:
        localidades = list(df.keys())

    df_filtered = pd.DataFrame()
    for loc in localidades:
        if loc in df:
            loc_df = df[loc]
            loc_df = loc_df[(loc_df['Mês/Ano'] >= start_date) & (loc_df['Mês/Ano'] <= end_date)]
            loc_df['Localidade'] = loc  # Adiciona coluna de localidade para diferenciação no gráfico
            df_filtered = pd.concat([df_filtered, loc_df])

    # Verifica se o DataFrame filtrado não está vazio
    if not df_filtered.empty:
        if chart_type == 'Linha':
            graph = px.line(df_filtered, x='Mês/Ano', y=y_label, color='Localidade', title=title)
        elif chart_type == 'Barra':
            graph = px.bar(df_filtered, x='Mês/Ano', y=y_label, color='Localidade', barmode='group', title=title)
        st.plotly_chart(graph, use_container_width=True)
    else:
        st.error("Não há dados para o intervalo de datas e localidades selecionadas.")

with tab1:
    # Exibição dos gráficos com base na seleção do usuário
    if (localidade_selecionada == 'Todas as Localidades' and all(tipo_dado in df.columns for df in data.values())) or \
    (localidade_selecionada != 'Todas as Localidades' and tipo_dado in data[localidade_selecionada].columns):
        titulo_grafico = f"{tipo_grafico} - {tipo_dado} ({localidade_selecionada})"
        plot_chart(data, titulo_grafico, tipo_dado, tipo_grafico, localidades_selecionadas, data_inicio, data_fim)
    else:
        st.error(f"Dados de '{tipo_dado}' não estão disponíveis para '{localidade_selecionada}'.")

# Função para calcular e exibir a porcentagem de energia injetada por mês e a sugestão mensal
def display_monthly_energy_distribution(data, selected_month):
    # Encontrar o mês correspondente nos dados
    month_data = data['Sapecado 1'][data['Sapecado 1']['Mês/Ano'] == selected_month]
    if month_data.empty:
        st.error(f"Não há dados disponíveis para o mês: {selected_month}")
        return
    
    total_generated = month_data['Energia Gerada em kWh'].sum()

    st.write(f"## Distribuição de Energia para o Mês: {selected_month}")

    # Inicializar o saldo do mês anterior
    previous_saldo = {loc: 0 for loc in data.keys() if 'Saldo Atual de Geração' in data[loc].columns}

    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if loc_data.empty:
            continue
        
        if 'Energia Injetada em kWh' in loc_data.columns and 'Saldo Atual de Geração' in loc_data.columns:
            injected = loc_data['Energia Injetada em kWh'].sum()
            current_saldo = loc_data['Saldo Atual de Geração'].sum()
            saldo_diff = max(0, current_saldo - previous_saldo[loc])  # Considerar apenas aumentos no saldo
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

with tab2:
    # Função para calcular e exibir a porcentagem de energia injetada por mês e a sugestão mensal
    display_monthly_energy_distribution(data, selected_month)
with st.expander("Veja mais informações"):
    st.write("Detalhes adicionais sobre os dados ou a aplicação.")