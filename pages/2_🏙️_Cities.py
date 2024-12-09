import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
import json
import os
import inflection

# FUNÇÕES:

COUNTRIES = {
 1: "India",
 14: "Australia",
 30: "Brazil",
 37: "Canada",
 94: "Indonesia",
 148: "New Zeland",
 162: "Philippines",
 166: "Qatar",
 184: "Singapure",
 189: "South Africa",
 191: "Sri Lanka",
 208: "Turkey",
 214: "United Arab Emirates",
 215: "England",
 216: "United States of America",
 }

def country_name(country_id):
    return COUNTRIES[country_id]

MOEDAS = {
 1: "INR",
 14: "AUD",
 30: "BRL",
 37: "CAD",
 94: "IDR",
 148: "NZD",
 162: "PHP",
 166: "QAR",
 184: "SGD",
 189: "ZAR",
 191: "LKR",
 208: "TRY",
 214: "AED",
 215: "GBP",
 216: "USD",
 }

def country_moeda(country_id):
    return MOEDAS[country_id]

def rename_columns(dataframe):
    
    df = dataframe.copy()
    title = lambda x: inflection.titleize(x)
    snakecase = lambda x: inflection.underscore(x)
    spaces = lambda x: x.replace(" ", "")
    cols_old = list(df.columns)
    cols_old = list(map(title, cols_old))
    cols_old = list(map(spaces, cols_old))
    cols_new = list(map(snakecase, cols_old))
    df.columns = cols_new

    return df


def valor_unificado(row,taxas_cambio):

    taxa = taxas_cambio[(country_moeda(row['country_code']))]

    price = round((row['average_cost_for_two']/taxa),2)
    return price

COLORS = {
"3F7E00": "darkgreen",
"5BA829": "green",
"9ACD32": "lightgreen",
"CDD614": "orange",
"FFBA00": "red",
"CBCBC8": "darkred",
"FF7800": "darkred",
}

def color_name(color_code):
    return COLORS[color_code]

def create_price_tye(price_range):

    if price_range == 1:
        return "cheap"
    elif price_range == 2:
        return "normal"
    elif price_range == 3:
        return "expensive"
    else:
        return "gourmet"
    
def salvar_dados_em_json(dados, arquivo="taxas_moedas.json"):
    with open(arquivo, "w") as f:
        json.dump(dados, f)

def carregar_dados_de_json(arquivo="taxas_moedas.json"):
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f:
            return json.load(f)
    return None

def paises_nome(row):

    pais = country_name(row['country_code'])
    return pais

# Carregando os dados de atxa de converção para dólar.

taxas_cambio = carregar_dados_de_json()

# Lendo o dataframe e criando uma cópia para trabalhar e não modificar o df original

df1 = pd.read_csv(f"dataset/zomato.csv")
df = df1.copy()

df = rename_columns(df) # Renomeando as colunas

# Iniciando o processo de limpeza e tratamento dos dados

# a coluna 'switch_to_order_menu' retorna sempre um mesmo valor, como não vamos utilizar-la para a análise, vou remover-la
df = df.drop(['switch_to_order_menu'],axis=1)

df = df.dropna(subset=['cuisines']) # como a única coluna com valores é a 'Cuisines', e são apenas 15, vamos remover todas estas linhas

df = df.drop_duplicates() # removendo linhas duplicadas

# Categorizando o dataframe para que os restaurantes possuam apenas um tipo de culinária
df["cuisines"] = df.loc[:, "cuisines"].apply(lambda x: x.split(",")[0])
df['cuisines'] = df['cuisines'].str.strip()

# cirando uma coluna com valores unificados em apenas uma moeda ($ dólar) para fins de comparação
df['valor_unificado'] = df.apply(lambda row: valor_unificado(row, taxas_cambio) , axis=1 )

# retirando um super outlier da coluna valor_unificado
df = df[df['valor_unificado'] < 160000]

# Criando uma coluna convertendo os códigos de cada país e retornando uma string com o nome.
df['country'] = df.apply(lambda row: paises_nome(row) , axis=1 )

############################### INICIANDO A CONSTRUÇÃO DA PÁGINA DO STREAMLIT ########################################

st.set_page_config(page_title='Visão Cidades',page_icon='🏙️',layout='wide')

col1,col2 = st.sidebar.columns([2,3])

with col1:
    # image_path = f'/Users/thiag/Downloads/projeto_final/'
    image = Image.open( 'logo.png' )
    st.image( image , width=60)

with col2:

    st.markdown('## Fome Zero!')

st.sidebar.markdown("""___""")
st.sidebar.markdown('## Filtros')
paises = st.sidebar.multiselect(
            'Escolhas os países que deseja visualizar os restaurantes:',
            df['country'].unique(),
            default=['Brazil','England','South Africa', 'Canada','Qatar','Australia'] )

linhas_selecionadas = df["country"].isin(paises)
df = df.loc[linhas_selecionadas,:]

with st.container():

    st.title('🏙️ Visão Cidades')
    st.markdown("""___""")

with st.container():
    
    df_aux = (df.loc[:,['city','restaurant_id','country']].groupby(['country','city'])
                                                          .count()
                                                          .sort_values(by='restaurant_id', ascending=False)
                                                          .reset_index())
    df_aux = df_aux.head(10)
        
    fig = px.bar(df_aux , x='city' , y='restaurant_id' , color='country',color_discrete_sequence=px.colors.diverging.Earth_r , labels={'city':'Cidades','restaurant_id':'Restaurantes'} , text='restaurant_id' , template='plotly_dark')
    fig.update_yaxes(showticklabels=False)
    fig.update_traces(textposition='inside',texttemplate='%{text}')
    fig.update_layout(title={
        'text' : 'Top10 CIdades com mais Restaurantes Registrados',
        'y': 1,
        'x': 0.18
        },
        plot_bgcolor="#262730"
        )
    st.plotly_chart(fig,use_container_width=True)


with st.container():

    col1,col2 = st.columns([5,5])

    with col1:
        
        linhas = df['aggregate_rating'] > 4
        df_aux = df.loc[linhas,['city','aggregate_rating','country']]

        df_aux = (df_aux.groupby(['country','city'])
                        .count()
                        .sort_values(by='aggregate_rating', ascending=False)
                        .reset_index())
        
        df_aux = df_aux.head(10)

        fig = px.bar(df_aux , x='city' , y='aggregate_rating' , color='country', color_discrete_sequence=px.colors.diverging.Earth_r , labels={'city':'Cidades','aggregate_rating':'Restaurantes com nota > 4'} , text='aggregate_rating' , template='plotly_dark')
        fig.update_yaxes(showticklabels=False)
        fig.update_traces(textposition='inside',texttemplate='%{text}')
        fig.update_layout(title={
            'text' : 'Restaurantes com nota Acima de 4',
            'y': 1,
            'x': 0.05
            },
            plot_bgcolor="#262730"
            )
        st.plotly_chart(fig,use_container_width=True)

    with col2:
        
        df_aux = df.loc[(df['votes'] != 0),:]
        linhas = df_aux['aggregate_rating'] < 2.5
        df_aux = df_aux.loc[linhas,['city','aggregate_rating','votes','country']]


        df_aux = (df_aux.groupby(['country','city'])
                        .count()
                        .sort_values(by='aggregate_rating', ascending=False)
                        .reset_index())
                
        df_aux = df_aux.head(10)

        fig = px.bar(df_aux , x='city' , y='aggregate_rating' , color='country', color_discrete_sequence=px.colors.diverging.Earth_r , labels={'city':'Cidades','aggregate_rating':'Restaurantes com nota < 2.5'} , text='aggregate_rating' , template='plotly_dark')
        fig.update_yaxes(showticklabels=False)
        fig.update_traces(textposition='inside',texttemplate='%{text}')
        fig.update_layout(title={
            'text' : 'Restaurantes com nota Abaixo de 2.5',
            'y': 1,
            'x': 0.01
            },
            plot_bgcolor="#262730"
            )
        st.plotly_chart(fig,use_container_width=True)
    
    st.markdown("""___""")

with st.container():
    
    df_aux = df.loc[:,['country','cuisines','city']].groupby(['country','city']).nunique().sort_values(by='cuisines',ascending=False).reset_index()
    df_aux = df_aux.head(10)

    fig = px.bar(df_aux,x='city',y='cuisines', color='country' ,color_discrete_sequence=px.colors.diverging.Earth_r , labels={'city':'cidades','cuisines':'Quantidade de Tipos Culinários'} , text='cuisines' , template='plotly_dark')
    fig.update_yaxes(showticklabels=False)
    fig.update_layout(title={
            'text' : 'Top10 Cidades com mais Tipos Distintos de Culinária',
            'y': 1,
            'x': 0.18
            },
            plot_bgcolor="#262730"
            )
    fig.update_traces(textposition='inside',texttemplate='%{text}')
    st.plotly_chart(fig,use_container_width=True)
    st.markdown("""___""")
