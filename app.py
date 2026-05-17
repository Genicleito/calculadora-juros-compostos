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

url_api_bcb = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod_serie}/dados?formato=json"
endpoints_bcb = {
    'ipca_acumulado': 13522,
    'ipca_mensal': 433,
    'selic_meta': 432,
    'selic_mensal': 4390,
}

def get_bcb_acumulado(cod_serie: int, meses: int = 12, data_inicial: str=None, data_final: str = None):
	"""
    Calcula o valor acumulado de uma série do Banco Central do Brasil (BCB) em percentual para um período.

    Args:
        cod_serie (int): Código da série do BCB.
        meses (int, opcional): Quantidade de meses do período. Default é 12.
        data_inicial (str, opcional): Data inicial no formato 'YYYY-MM-DD'. Se não informado, calcula a partir de 'meses'.
        data_final (str, opcional): Data final no formato 'YYYY-MM-DD'. Se não informado, usa a data atual.

    Returns:
        dict: Dicionário com o valor acumulado no período {'acumulado': valor}.
    """
	if not data_inicial:
		data_inicial = (datetime.datetime.now().date() - relativedelta(months=meses))
	elif isinstance(data_inicial, str):
		data_inicial = datetime.datetime.strptime(data_inicial, '%Y-%m-%d')

	if not data_final:
		data_final = datetime.datetime.now().date()
	elif isinstance(data_final, str):
		data_final = datetime.datetime.strptime(data_final, '%Y-%m-%d')

	data_inicial_str = data_inicial.strftime('%d/%m/%Y')
	data_final_str = data_final.strftime('%d/%m/%Y')
    
	url = url_api_bcb.format(cod_serie=cod_serie) + f"&dataInicial={data_inicial_str}&dataFinal={data_final_str}"
	df = pd.read_json(url)

	df['fator'] = (df['valor'] / 100) + 1
	fator_acumulado = df['fator'].prod()
	acumulado = (fator_acumulado - 1) * 100
	
	fator_acumulado_12meses = df['fator'].iloc[-12:].prod()
	acumulado_12meses = (fator_acumulado_12meses - 1) * 100

	return {
		"acumulado": acumulado,
		"acumulado_12meses": acumulado_12meses,
	}

def get_bcb(cod_serie: int, meses: int = 12, data_inicial: str=None, data_final: str = None):
	"""
	Obtém estatísticas de uma série do Banco Central do Brasil (BCB) para um período.
	
	Args:
		cod_serie (int): Código da série do BCB.
		meses (int, opcional): Quantidade de meses do período. Default é 12.
		data_inicial (str, opcional): Data inicial no formato 'YYYY-MM-DD'. Se não informado, calcula a partir de 'meses'.
		data_final (str, opcional): Data final no formato 'YYYY-MM-DD'. Se não informado, usa a data atual.
	
	Returns:
		dict: Dicionário com média, último valor e quantidade de meses analisados.
	"""
	if not data_inicial:
		data_inicial = (datetime.datetime.now().date() - relativedelta(months=meses))
	elif isinstance(data_inicial, str):
		data_inicial = datetime.datetime.strptime(data_inicial, '%Y-%m-%d')

	if not data_final:
		data_final = datetime.datetime.now().date()
	elif isinstance(data_final, str):
		data_final = datetime.datetime.strptime(data_final, '%Y-%m-%d')

	data_inicial_str = data_inicial.strftime('%d/%m/%Y')
	data_final_str = data_final.strftime('%d/%m/%Y')
    
	url = url_api_bcb.format(cod_serie=cod_serie) + f"&dataInicial={data_inicial_str}&dataFinal={data_final_str}"
	df = pd.read_json(url)
	df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y').dt.date
	df = df.sort_values('data')

	return {
        "media": df['valor'].mean().round(2),
        "ultimo_valor": df['valor'].iloc[-1],
        "meses": meses,
    }

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
        'Portfólio (com os juros)': valores_com_juros,
    })


@st.cache_data
def obter_taxas_juros():
	try:
		ipca_10anos = get_bcb_acumulado(endpoints_bcb['ipca_mensal'], meses = 120).get('acumulado')
		selic = get_bcb(endpoints_bcb['selic_meta'], meses = 120) # Selic dos últimos 10 anos (máximo)
	except Exception as e:
		print(f"Falha ao obter informações do BCB: {e}")
		ipca_10anos = None
		selic = dict()
	
	return selic, ipca_10anos

# Obtém a SELIC e o IPCA dos últimos 10 anos
selic, ipca_10anos = obter_taxas_juros()

if selic and ipca_10anos:
	col1, col2, _ = st.columns([1, 1, 2])
	st.metric("Selic atual", value=f"{selic.get('selic_atual'):.2f}%")
	st.metric("IPCA acumulado (10 anos)", value=f"{ipca_10anos.get('acumulado'):.2f}%")
	st.metric("IPCA acumulado (12 meses)", value=f"{ipca_10anos.get('acumulado_12meses'):.2f}%")

# @st.cache_data
# def install_requirements():
#     os.system("pip install -r requirements.txt")

# install_requirements()


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

# Botão para mostrar/ocultar o DataFrame com o rendimento real corrigido pela inflação
if 'show_rent_real' not in st.session_state:
    st.session_state.show_rent_real = False  # Inicializando o estado

st.markdown(f"## Insira as informações abaixo para realizar o cálculo")

valor_inicial = st.number_input("Saldo Inicial:", value=None, placeholder="Insira o valor inicial que você já possui...")
aportes = st.number_input("Aplicações mensais:", value=0, placeholder="Insira o valor que você pretende investir todo mês...")
periodo_anos = st.number_input("Tempo de investimento (em anos):", min_value=1, max_value=100, step=1, placeholder="Insira por quantos anos você pretende investir...")
taxa_juros_ano = st.number_input("Taxa de juros anual (%):", value=selic.get('media'), placeholder=f"Insira a taxa de juros anual esperada." + f"Ex: {selic.get('ultimo_valor'):.2f} (Selic atual)" if selic.get('ultimo_valor') else "")
data_inicio = st.date_input("Data de início:", (datetime.datetime.now(pytz.timezone('America/Sao_Paulo')) + relativedelta(months=1)).date().replace(day=1))
inflacao_ano = st.number_input("Inflação anual esperada (opcional):", value=ipca_10anos, placeholder="Insira a inflação média anual esperada para o período [opcional]...")

if valor_inicial and periodo_anos and taxa_juros_ano:
    # Realiza o calculo dos juros compostos
    df = calculadora_juros_compostos(valor_inicial, taxa_juros_ano / 100, aportes, periodo_anos, data_inicio=data_inicio)

    if inflacao_ano:
        rentabilidade_real = (1 + (taxa_juros_ano / 100)) / (1 + (inflacao_ano / 100)) - 1
        # Realiza o cálculo do resultado real corrigido pela inflação
        df_real = calculadora_juros_compostos(valor_inicial, rentabilidade_real, aportes, periodo_anos, data_inicio=data_inicio)
        df_real = df_real.assign(**{"Total em juros": df_real["Portfólio (com os juros)"] - df_real["Valor investido"]})

    df = df.assign(**{
        "Total em juros": (df["Portfólio (com os juros)"] - df["Valor investido"]).round(2)
    })

    st.markdown(f"## Resultado (desconsiderando a inflação)")

    portfolio_final = df.sort_values("Mês")['Portfólio (com os juros)'].round(2).iloc[-1]
    total_em_aportes = df.sort_values("Mês")['Valor investido'].round(2).iloc[-1]
    total_em_juros = portfolio_final - total_em_aportes

    st.success(f"> Em {periodo_anos} ano{'s' if periodo_anos > 1 else ''} ({df.sort_values('Mês')['Mês'].iloc[-1].year}) você terá **R\\$ {portfolio_final:.2f}**.")
    st.success(f"""
    > - Deste valor, você investiu **R\\$ {total_em_aportes:.2f}** com aportes.
    > - **R\\$ {total_em_juros:.2f}** foi o que você obteve de rendimento com os juros compostos do investimento.
    """)
    
    st.markdown(f"""
    ### **Informações completas sobre a simulação:**

    - **Valor final** ({df.sort_values('Mês')['Mês'].iloc[-1].year}): \t\t**R\\$ {portfolio_final:.2f}**
        - Total investido: \t\t**R\\$ {total_em_aportes:.2f}** ({total_em_aportes / portfolio_final:.2%})
        - Total em juros: **R$ \t{total_em_juros:.2f}** ({total_em_juros / portfolio_final:.2%})
    - Saldo inicial: \t\t**R\\$ {valor_inicial:.2f}**
    - Aplicações mensais: \t\t**R\\$ {aportes:.2f}**
    - Tempo de investimento: \t**{periodo_anos} ano{'s' if periodo_anos > 1 else ''}**
    - Taxa de juros (ao ano): \t**{taxa_juros_ano:.2f}%**
        - Taxa de juros mensal: \t**{((1 + (taxa_juros_ano / 100)) ** (1 / 12)) - 1:.3%}**
    """)

    if inflacao_ano:
        # Valor final real corrigido pela inflação
        portfolio_final_real = df_real.sort_values('Mês')['Portfólio (com os juros)'].iloc[-1]
        valor_total_real_aportes = df_real.sort_values("Mês")['Valor investido'].iloc[-1]
        total_em_juros_real = portfolio_final_real - valor_total_real_aportes

        st.markdown(f"""
        ### **Valores corrigidos pela inflação:**

    - Valor final corrigido pela inflação ({df_real.sort_values('Mês')['Mês'].iloc[-1].year}): \t\t**R\\$ {portfolio_final_real:.2f}**
        - Total investido: \t\t**R\\$ {valor_total_real_aportes:.2f}** ({valor_total_real_aportes / portfolio_final_real:.2%})
        - Total em juros: **R$ \t{total_em_juros_real:.2f}** ({total_em_juros_real / portfolio_final_real:.2%})
    - Inflação projetada ao ano: \t**{inflacao_ano:.2f}%**
    - Taxa de juros real (a.a.): \t**{rentabilidade_real:.2%}**
        - Taxa de juros real mensal: \t**{((1 + rentabilidade_real) ** (1 / 12)) - 1:.2%}**
    """)

    # # TODO: Montar tabela como o exemplo abaixo:
    # | Indicador                        | Valor                |
    # | -------------------------------- | -------------------- |
    # | **Valor final corrigido (2064)** | **R\$ X.XXX.XXX,XX** |
    # | **Rendimento real acumulado**    | **R\$ X.XXX.XXX,XX** |
    # | **Total aportado** (300×468)     | **R\$ XXX.XXX,XX**   |
    # | **Patrimônio inicial**           | R\$ X.XXX,XX         |
    # | **Total investido**              | R\$ XXX.XXX,XX       |
    # | **Rentabilidade real anual**     | **X,XX% a.a.**       |
    # | **Rentabilidade real mensal**    | **X,XXX% a.m.**      |


    st.markdown(f"---")

    st.markdown(f"### Gráficos dos resultados (desconsiderando a inflação)")

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

    st.markdown(f"\n### Tabela com os resultados mês a mês (desconsiderando a inflação)")

    st.dataframe(
        # df.round(2).style.format({'Valor investido': 'R$ {:.2f}', 'Portfólio (com os juros)': 'R$ {:.2f}'}).sort_values("Mês"),
        df[
            ["Mês", "Valor investido", "Total em juros", "Portfólio (com os juros)"]
        ].sort_values("Mês").style.format({
            "Valor investido": lambda x: f"R$ {x:,.2f}".replace(',', ''),
            "Total em juros": lambda x: f"R$ {x:,.2f}".replace(',', ''),
            "Portfólio (com os juros)": lambda x: f"R$ {x:,.2f}".replace(',', ''),
        }),
        use_container_width=True,
        hide_index=True
    )

    if inflacao_ano:
        def toggle_df():
            st.session_state.show_rent_real = not st.session_state.show_rent_real

        st.markdown("---")
        st.button("**Ocultar tabela com o rendimento real**" if st.session_state.show_rent_real else "**Mostrar tabela com o rendimento real**", on_click=toggle_df)

        # Mostrar o DataFrame com o rendimento real se o estado for True
        if st.session_state.show_rent_real:
            st.markdown(f"### Tabela com o rendimento real considerando inflação de {inflacao_ano / 100:.2%} a.a.")
            st.dataframe(
            # df.round(2).style.format({'Valor investido': 'R$ {:.2f}', 'Portfólio (com os juros)': 'R$ {:.2f}'}).sort_values("Mês"),
            df_real.rename(columns={'Total em juros': 'Total em juros reais', 'Portfólio (com os juros)': 'Portfólio (com juros reais)'})[[
                "Mês", "Valor investido", "Total em juros reais", "Portfólio (com juros reais)"
            ]].sort_values("Mês").style.format({
                "Valor investido": lambda x: f"R$ {x:,.2f}".replace(',', ''),
                "Total em juros reais": lambda x: f"R$ {x:,.2f}".replace(',', ''),
                "Portfólio (com juros reais)": lambda x: f"R$ {x:,.2f}".replace(',', ''),
            }),
            use_container_width=True,
            hide_index=True
        )

    # TODO: adicionar botão para exportar o dataframe com os valores mensais em excel onde cada ano terá uma aba específica

# st.components.v1.html(adsense_code)
