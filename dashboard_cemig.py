import streamlit as st
import pandas as pd
import plotly.express as px

# Função para carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("Dados.xlsx", sheet_name=None)

# Carregar dados do Excel
data = load_data()

# Título do Dashboard
st.title('Consumo e Geração de Energia')

# Sidebar para seleção de dados
with st.sidebar:
    st.title('Filtros para o Gráfico')
    tipo_dado = st.selectbox('Selecione o que você gostaria de saber:', ['Consumo Total em kWh', 'Energia Injetada em kWh', 'Energia Gerada em kWh', 
     'Saldo Atual de Geração', 'Consumo Pago em kWh'])
    opcoes_localidades = list(data.keys()) + ['Todas as Localidades']
    localidade_selecionada = st.selectbox('Selecione a propriedade:', opcoes_localidades)
    tipo_grafico = st.radio('Selecione o tipo de gráfico:', ('Linha', 'Barra'))

    # Separador na sidebar
    st.write("---")  # Isso adiciona uma linha horizontal para separar visualmente as seções

    st.title('Filtro para a Distribuição de Energia Gerada')
        
    # Usar os meses conforme estão nos dados
    meses_disponiveis = data['Sapecado 1']['Mês/Ano'].unique()

    # Selectbox para escolher o mês
    selected_month = st.selectbox('Escolha o mês de referência:', meses_disponiveis)
# Tabs para diferentes visualizações
tab1, tab2 = st.tabs(["Gráficos", "Distribuição da Energia Gerada"])

# Função para plotar gráficos de linha ou barra
def plot_chart(df, title, y_label, chart_type, localidade):
    if localidade == 'Todas as Localidades':
        df_melted = pd.DataFrame()
        for loc in df.keys():
            if y_label in df[loc].columns:
                melted = df[loc].melt(id_vars=['Mês/Ano'], value_vars=[y_label])
                melted['Localidade'] = loc
                df_melted = pd.concat([df_melted, melted])
        if not df_melted.empty:
            if chart_type == 'Linha':
                graph = px.line(df_melted, x='Mês/Ano', y='value', color='Localidade', title=title)
            elif chart_type == 'Barra':
                graph = px.bar(df_melted, x='Mês/Ano', y='value', color='Localidade', barmode='group', title=title)
        else:
            st.error(f"Os dados de '{y_label}' não estão disponíveis para todas as localidades.")
            return
    else:
        if chart_type == 'Linha':
            graph = px.line(df[localidade], x='Mês/Ano', y=y_label, color='Localidade', title=title)
        elif chart_type == 'Barra':
            graph = px.bar(df[localidade], x='Mês/Ano', y=y_label, color='Localidade', barmode='group', title=title)

    st.plotly_chart(graph, use_container_width=True)

with tab1:
    # Exibição dos gráficos com base na seleção do usuário
    if (localidade_selecionada == 'Todas as Localidades' and all(tipo_dado in df.columns for df in data.values())) or \
    (localidade_selecionada != 'Todas as Localidades' and tipo_dado in data[localidade_selecionada].columns):
        titulo_grafico = f"{tipo_grafico} - {tipo_dado} ({localidade_selecionada})"
        plot_chart(data, titulo_grafico, tipo_dado, tipo_grafico, localidade_selecionada)
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