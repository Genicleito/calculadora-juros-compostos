import sys
import os
import requests
import math
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

def calculadora_juros_compostos(valor_inicial, taxa_juros_ano, aporte_mensal, periodos_anos=None, periodos_meses=None, data_inicio=None):
    # # Definição das informações utilizadas para calcular juros compostos
    # valor_inicial = 0
    # taxa_juros_ano = 0.1
    # aporte_mensal = 100
    taxa_juros_mes = math.pow(1 + taxa_juros_ano, 1/12) - 1 # >> Também pode ser feito da forma: (1 + taxa_juros_ano) ** (1 / 12)
    if not data_inicio: data_inicio = datetime.datetime.today()
    assert periodos_anos != None or periodos_meses != None, "Informe pelo menos o período em meses ou o período em anos!"
    periodos_meses = periodos_anos * 12 if not periodos_meses else periodos_meses

    # Criação de listas que serão utilizadas para construir o DataFrame
    periodos = list(range(periodos_meses + 1))
    meses = []
    valores_investidos = []
    valores_com_juros = [valor_inicial]

    for i in range(periodos_meses + 1):
        # Lista de meses considerando o período informado
        meses.append(
            datetime.datetime.strptime(data_inicio.strftime('%Y-%m-01'), '%Y-%m-%d') + relativedelta(months=i)
        )
        # Valores investidos (essa informação equivale à soma dos aportes feitos)
        valores_investidos.append(valor_inicial + (aporte_mensal * i)) # valor_anterior + aporte_mensal
        if i > 0:
            # Essa lista compreende a evolução do patrimônio mês-a-mês com os juros compostos
            valores_com_juros.append(valores_com_juros[i - 1] * taxa_juros_mes + valores_com_juros[i - 1] + aporte_mensal)

    # DataFrame com a evolução dos Juros Compostos
    return pd.DataFrame({
        # 'periodo': periodos,
        'mes': meses,
        'valor_investido': valores_investidos,
        'valor_com_juros': valores_com_juros,
    })


@st.cache_data
def install_requirements():
    os.system("pip install -r requirements.txt")

install_requirements()

# @st.cache_resource
# def load_data():
#     return pd.read_json("https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json")



# with st.status('Loading data...'):
#     ts = datetime.datetime.now()
#     st.write(f"_{ts.strftime('%Y-%m-%d %H:%M:%S')} Lendo dados... Aguarde alguns instantes..._")
#     # Verifica se os dados foram atualizados a mais de um dia
#     if (pd.to_datetime(pd.read_csv(models.READ_MARKET_DATA_PATH)['date']).max() - datetime.datetime.today()).days != 0:
#         df, online_data = load_data()
#     else:
#         df = pd.read_csv(models.READ_MARKET_DATA_PATH).sort_values(['date'])
#         online_data = False



# st.write(f"### Gráfico com visualização da série do ativo no TradingView")

valor_inicial = st.number_input("Valor Inicial:")
aportes = st.number_input("Aportes mensais:")
taxa_juros_ano = st.number_input("Taxa de juros anual (%):") / 100
periodo_anos = int(st.number_input("Tempo de investimento (em anos):", format="%0.1f"))
data_inicio = st.date_input("Data de início:", datetime.datetime.today())

st.write(f"{valor_inicial}, {aportes}, {taxa_juros_ano}, {periodo_anos}: {valor_inicial and aportes and taxa_juros_ano and periodo_anos}")
# if aportes and taxa_juros_ano and periodo_anos:
df = calculadora_juros_compostos(valor_inicial, taxa_juros_ano, aportes, periodo_anos, data_inicio=data_inicio)

st.markdown(f"## Resultado")

st.dataframe(df.sort_values("mes", ascending=True), use_container_width=True, hide_index=True)
