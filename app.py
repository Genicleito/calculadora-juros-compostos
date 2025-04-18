import pandas as pd
import numpy as np
import datetime
import pytz
import os
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

def calculadora_juros_compostos(valor_inicial, taxa_juros_ano, aporte_mensal, periodos_anos=None, periodos_meses=None, data_inicio=None):
    # # Definição das informações utilizadas para calcular juros compostos
    # valor_inicial = 0
    # taxa_juros_ano = 0.1
    # aporte_mensal = 100
    taxa_juros_mes = ((1 + taxa_juros_ano) ** (1 / 12)) - 1 # >> Também pode ser feito da forma: math.pow(1 + taxa_juros_ano, 1/12) - 1
    if not data_inicio: data_inicio = (datetime.datetime.today() + relativedelta(months=1)).replace(day=1)
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
            (datetime.datetime.strptime(data_inicio.strftime('%Y-%m-01'), '%Y-%m-%d') + relativedelta(months=i)).date()
        )
        # Valores investidos (essa informação equivale à soma dos aportes feitos)
        valores_investidos.append(valor_inicial + (aporte_mensal * i)) # valor_anterior + aporte_mensal
        if i > 0:
            # Essa lista compreende a evolução do patrimônio mês-a-mês com os juros compostos
            valores_com_juros.append(valores_com_juros[i - 1] * taxa_juros_mes + valores_com_juros[i - 1] + aporte_mensal)

    # DataFrame com a evolução dos Juros Compostos
    return pd.DataFrame({
        # 'periodo': periodos,
        'Mês': meses,
        'Valor investido': valores_investidos,
        'Valor resultado (com os juros)': valores_com_juros,
    })


@st.cache_data
def install_requirements():
    os.system("pip install -r requirements.txt")

install_requirements()

# @st.cache_resource
# def load_data():
#     selic_hist = pd.read_json("https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json")
#     selic_hist["data"] = pd.to_datetime(selic_hist['data'], format="%d/%m/%Y")
#     return selic_hist.sort_values("data").iloc[-30:]


# with st.status('Loading data...'):
#     ts = datetime.datetime.now()
#     st.write(f"_{ts.strftime('%Y-%m-%d %H:%M:%S')} Lendo dados... Aguarde alguns instantes..._")
#     df_selic = load_data()
#     st.write(f"SELIC atual: {df_selic.sort_values("data")['valor'].round(2).iloc[-1] * 100}%")

st.set_page_config(
    page_title="Calculadora de Juros Compostos",
    page_icon=":chart_with_upwards_trend:"
)

st.markdown(f"## Insira as informações abaixo para realizar o cálculo")

valor_inicial = st.number_input("Saldo Inicial:", placeholder="Insira o valor inicial que você já possui...")
aportes = st.number_input("Aplicações mensais:", value=None, placeholder="Insira o valor que você pretende investir todo mês...")
periodo_anos = st.number_input("Tempo de investimento (em anos):", min_value=1, max_value=100, step=1, placeholder="Insira por quantos anos você pretende investir...")
taxa_juros_ano = st.number_input("Taxa de juros anual (%):", value=None, placeholder="Insira a taxa de juros anual dos seus investimentos...")
data_inicio = st.date_input("Data de início:", (datetime.datetime.now(pytz.timezone('America/Sao_Paulo')) + relativedelta(months=1)).date().replace(day=1))

if aportes and periodo_anos and taxa_juros_ano:
    df = calculadora_juros_compostos(valor_inicial, taxa_juros_ano / 100, aportes, periodo_anos, data_inicio=data_inicio)

    df = df.assign(**{
        "Total em juros": (df["Valor resultado (com os juros)"] - df["Valor investido"]).round(2)
    })

    st.markdown(f"## Resultado")

    portfolio_final = df.sort_values("Mês")['Valor resultado (com os juros)'].round(2).iloc[-1]
    total_em_aportes = df.sort_values("Mês")['Valor investido'].round(2).iloc[-1]
    total_em_juros = portfolio_final - total_em_aportes

    st.markdown(f"> Em {periodo_anos} ano{'s' if periodo_anos > 1 else ''} você terá **R\$ {portfolio_final:.2f}**.")
    st.markdown(f"""
    - Deste valor, saíram do seu bolso, como investimento, apenas R\$ {total_em_aportes:.2f}.
    - R\$ {round(total_em_juros, 2)} foi o que você teve de rendimento com os juros do investimento.
    """)
    
    st.markdown(f"""
    **As configurações utilizadas para gerar esses valores foram:**

    - Saldo inicial: \t\t**R\$ {valor_inicial:.2f}**
    - Aplicações mensais: \t\t**R\$ {aportes:.2f}**
    - Taxa de juros (ao ano): \t**{taxa_juros_ano:.2f}%**
    - Tempo de investimento: \t**{periodo_anos} ano{'s' if periodo_anos > 1 else ''}**
    """)

    st.markdown(f"---")

    st.markdown(f"### Gráficos dos resultados")

    # st.markdown(f"\n> Gráfico de pizza")
    fig_pie = px.pie(
        pd.DataFrame({'Valor': [total_em_aportes, total_em_juros], 'Origem': ['Valor investido', 'Rendimento']}),
        values='Valor',
        names='Origem',
        title='Distribuição dos valores aportados e rendimentos'
    )
    st.plotly_chart(fig_pie, use_container_width=True)


    fig_bars = px.bar(
        df.assign(Ano=pd.to_datetime(df['Mês']).dt.year).sort_values("Mês", ascending=False).drop_duplicates(subset=["Ano"]),
        x='Ano',
        y=['Valor investido', 'Total em juros'],
        text_auto=True,
        title="Distribuição dos rendimentos por ano"
    )
    st.plotly_chart(fig_bars, use_container_width=True)

    st.markdown(f"---")

    st.markdown(f"\n### Tabela com os resultados mês a mês")

    st.dataframe(
        # df.round(2).style.format({'Valor investido': 'R$ {:.2f}', 'Valor resultado (com os juros)': 'R$ {:.2f}'}).sort_values("Mês"),
        df.round(2).sort_values("Mês").style.format({
            "Valor investido": lambda x: f"R$ {x:,.2f}".replace(',', ''),
            "Total em juros": lambda x: f"R$ {x:,.2f}".replace(',', ''),
            "Valor resultado (com os juros)": lambda x: f"R$ {x:,.2f}".replace(',', ''),
        }),
        use_container_width=True,
        hide_index=True
    )

    # TODO: adicionar botão para exportar o dataframe com os valores mensais em excel onde cada ano terá uma aba específica

# st.components.v1.html(adsense_code)
