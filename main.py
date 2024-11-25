"""Reportería oi"""

import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
from datetime import date, timedelta 

import tables as t
import pdftest as pdf
#from pdfdescarga import reporte_cartera, reporte_cosechas

#######################################
# PAGE SETUP
#######################################

st.set_page_config(page_title="Reportes", page_icon=":bar_chart:", layout="wide")

st.title("Análisis de Cartera y Cosecha")


#######################################
# DATA LOADING
#######################################

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    return df

@st.cache_data
def clean_data(df):
    df = t.clean_dataset(df)
    return df


df = clean_data(load_data('cashflow.csv'))
original_df = df
df_sv = df[df['pais']=='El Salvador']
df_hn = df[df['pais']=='Honduras']

if "df" not in st.session_state:
    st.session_state.df = df

# if "original_df" not in st.session_state:
#     st.session_state.original_df = df 

if "term_unit" not in st.session_state:
    st.session_state.term_unit = 'month'

if "seleccion_pais" not in st.session_state:
    st.session_state.seleccion_pais = 'Todo'

if "filter_info" not in st.session_state:
    st.session_state.filter_info = 'Sin filtros'

today = datetime.date.today()

#######################################
# FILTROS
#######################################

@st.cache_data
def filtro_pais():
    if 'Todo' != st.session_state.seleccion_pais:
        st.session_state.df = original_df[original_df['pais']==st.session_state.seleccion_pais]

@st.cache_data
def filtro(df, columna, seleccion):
    df = t.filtro_generico(df, columna, seleccion)
    return df


#######################################
# LAYOUT
#######################################

def page1():
    st.divider()

    st.header('Análisis de Cartera')

    # Reporte
    # reporte_cartera = {
    #     'Indicadores de Cartera Total':t.indicadores_cartera(st.session_state.df),
    #     'Créditos Otorgados': t.creditos_otorgados(st.session_state.df),
    #     'Montos': t.montos(st.session_state.df, st.session_state.term_unit),
    #     'Mora vs Saldo Actual': t.mora_saldo(st.session_state.df),
    #     'Mora Contagiada vs Saldo Actual': t.mora_saldo(st.session_state.df, c=True),
    #     'Créditos en Mora vs Activos':t.creditos_mora_activos(st.session_state.df)
    # }

    reporte_cartera = [
        ('Indicadores de Cartera Total',t.indicadores_cartera(st.session_state.df)),
        ('Créditos Otorgados', t.creditos_otorgados(st.session_state.df)),
        ('Montos', t.montos(st.session_state.df, st.session_state.term_unit)),
        ('Mora vs Saldo Actual', t.mora_saldo(st.session_state.df)),
        ('Mora Contagiada vs Saldo Actual', t.mora_saldo(st.session_state.df, c=True)),
        ('Créditos en Mora vs Activos', t.creditos_mora_activos(st.session_state.df))
    ]

    # reporte_cartera_titulos = ['Indicadores de Cartera Total', 'Créditos Otorgados', 'Montos', 'Mora vs Saldo Actual', 'Mora Contagiada vs Saldo Actual', 'Créditos en Mora vs Activos']
    # reporte_cartera_dataframes = [t.indicadores_cartera(st.session_state.df), t.creditos_otorgados(st.session_state.df), t.montos(st.session_state.df, st.session_state.term_unit), t.mora_saldo(st.session_state.df), t.mora_saldo(st.session_state.df, c=True), t.creditos_mora_activos(st.session_state.df)]

    col1, col2 = st.columns(2)

    with col1:
        if st.radio(label='Filtrar por país', options=['Todo','El Salvador', 'Honduras'], horizontal=True, key='seleccion_pais') != 'Todo':
            st.session_state.df = df[df['pais'] == st.session_state.seleccion_pais]
            st.session_state.filter_info = f'País: {st.session_state.seleccion_pais}'
        else:
            st.session_state.df = original_df

    with col2:

        @st.cache_resource
        def generate_report1(filter_info):
            file = pdf.create_pdf_report(reporte_cartera, "reporte_cartera.pdf", filter_info)
            return file

        report = generate_report1(st.session_state.filter_info)
        
        with open("reporte_cartera.pdf", "rb") as file:
            btn = st.download_button(
                label="Descargar PDF",
                data=file,
                file_name="reporte_cartera_oi.pdf",
                mime="application/pdf"
            )
    
    st.divider()

    st.subheader('Indicadores de Cartera Total')
    st.dataframe(t.indicadores_cartera(st.session_state.df), hide_index=True)

    st.subheader('Créditos Otorgados')
    st.dataframe(t.creditos_otorgados(st.session_state.df), hide_index=True)

    st.subheader('Montos')
    st.dataframe(t.montos(st.session_state.df, st.session_state.term_unit), hide_index=True)

    st.subheader('Mora vs Saldo Actual')
    st.dataframe(t.mora_saldo(st.session_state.df), hide_index=True)

    st.subheader('Mora Contagiada vs Saldo Actual')
    st.dataframe(t.mora_saldo(st.session_state.df, c=True), hide_index=True)

    st.subheader('Créditos en Mora vs Activos')
    st.dataframe(t.creditos_mora_activos(st.session_state.df), hide_index=True)

def page2():

    st.divider()

    st.header('Análisis de Cosecha')

    reporte_cosechas = [
        ('Análisis de Cosecha', t.indicadores_cosecha(st.session_state.df, cohort=st.session_state.term_unit)),
        ('Mora - Monto', t.mora_monto_cosecha(st.session_state.df, cohort=st.session_state.term_unit)),
        ('Mora Contagiada - Monto', t.mora_monto_cosecha(st.session_state.df, cohort=st.session_state.term_unit, payment_type='expected')),
        ('Mora vs Saldo Actual', t.mora_saldo_cosecha(st.session_state.df, saldo='saldo_actual', cohort=st.session_state.term_unit)),
        ('Mora Contagiada vs Saldo Actual', t.mora_saldo_cosecha(st.session_state.df, saldo='saldo_actual', cohort=st.session_state.term_unit, c=True)),
        ('Mora vs Saldo Otorgado', t.mora_saldo_cosecha(st.session_state.df, saldo='valor_financiamiento', cohort=st.session_state.term_unit)),
        ('Mora Contagiada vs Saldo Otorgado', t.mora_saldo_cosecha(st.session_state.df, saldo='valor_financiamiento', cohort=st.session_state.term_unit, c=True)),
        ('Resumen', t.detailed_cohort_table(st.session_state.df, cohort=st.session_state.term_unit))
    ]


    col1, col2 = st.columns(2)

    with col1:
        if st.radio(label='Filtrar por país', options=['Todo','El Salvador', 'Honduras'], horizontal=True, key='seleccion_pais') != 'Todo':
            st.session_state.df = df[df['pais'] == st.session_state.seleccion_pais]
            st.session_state.filter_info = f'País: {st.session_state.seleccion_pais}'
        else:
            st.session_state.df = original_df
        
        frecuencia = st.radio(label='Período cosecha', options=['Mensual','Semanal', 'Quincenal'], horizontal=True)

        if frecuencia == 'Semanal':
            st.session_state.term_unit = 'week'
        elif frecuencia == 'Quincenal':
            st.session_state.term_unit = 'fortnight'
    
    with col2:

        @st.cache_resource
        def generate_report2(filter_info):
            file = pdf.create_pdf_report(reporte_cosechas, "reporte_cosechas.pdf", filter_info)
            return file

        report = generate_report2(st.session_state.filter_info)

        with open("reporte_cosechas.pdf", "rb") as file:
            btn = st.download_button(
                label="Descargar PDF",
                data=file,
                file_name="reporte_cosechas_oi.pdf",
                mime="application/pdf"
            )
    
    st.divider()

    st.subheader('Análisis de Cosecha')
    st.dataframe(t.indicadores_cosecha(st.session_state.df, cohort=st.session_state.term_unit), hide_index=True)

    st.subheader('Mora - Monto')
    st.dataframe(t.mora_monto_cosecha(st.session_state.df, cohort=st.session_state.term_unit), hide_index=True)

    st.subheader('Mora Contagiada - Monto')
    st.dataframe(t.mora_monto_cosecha(st.session_state.df, cohort=st.session_state.term_unit, payment_type='expected'), hide_index=True)

    st.subheader('Mora vs Saldo Actual')
    st.dataframe(t.mora_saldo_cosecha(st.session_state.df, saldo='saldo_actual', cohort=st.session_state.term_unit), hide_index=True)

    st.subheader('Mora Contagiada vs Saldo Actual')
    st.dataframe(t.mora_saldo_cosecha(st.session_state.df, saldo='saldo_actual', cohort=st.session_state.term_unit, c=True), hide_index=True)

    st.subheader('Mora vs Saldo Otorgado')
    st.dataframe(t.mora_saldo_cosecha(st.session_state.df, saldo='valor_financiamiento', cohort=st.session_state.term_unit), hide_index=True)
    
    st.subheader('Mora Contagiada vs Saldo Otorgado')
    st.dataframe(t.mora_saldo_cosecha(st.session_state.df, saldo='valor_financiamiento', cohort=st.session_state.term_unit, c=True), hide_index=True)

    st.subheader('Resumen')
    st.dataframe(t.detailed_cohort_table(st.session_state.df, cohort=st.session_state.term_unit), hide_index=True)


pg = st.navigation([st.Page(page1, title='Análisis de Cartera'), st.Page(page2, title='Análisis de Cosecha')])
pg.run()