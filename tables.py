"""Funciones 24 nov """

import numpy as np 
import pandas as pd 
import datetime
from datetime import date, timedelta 

#PERDIDA MAYOR A 90

#---------------------------------------------------------------------------
#                     PROCESAMIENTO Y LIMPIEZA DE DATOS
#---------------------------------------------------------------------------

def clean_dataset(data, interno=False):
    """
    Input esperado: DataFrame correspondiente a view CASHFLOW
    Procesamiento:
    1. Aplicar formato de fecha a columnas correspondientes.
    2. Estandarizar moneda para columnas con USD y HNL.
    3. Agregar columna 'estado_mora' en base a 'dias_atraso'.
    4. Agregar columna de días de atraso para cuotas en estado 'Vencido'.
    5. Agregar columnas 'month', 'week', y 'fortnight' para columnas 'fecha_venta' y 'fecha_cuota'.
    """

    # Eliminar eben ezer y galo cell
    if interno==False:
        data = data[~data['nombre_empresa'].isin(['(ANTERIOR) INVERSIONES EBEN EZER', 'GALO CELL'])]
    
    # Formato datetime
    datetime_columns = [col for col in data.columns if "fecha" in col or "date" in col]
    for col in datetime_columns:
        data[col] = pd.to_datetime(data[col], errors='coerce')

    # Estandarización de moneda
    currency_columns = [
        "cuota_moneda", "exigible_moneda", "valor_financiamiento", "prima",
        "accesorios", "saldo_actual", "al_dia", "mora_15", "mora_30",
        "mora_45", "mora_60", "mora_75", "mora_90"
    ]
    # Asumiendo una tasa de cambio 1USD = 25HNL
    data.loc[data['pais'] == 'Honduras', currency_columns] = data.loc[data['pais'] == 'Honduras', currency_columns] / 25

    # Asignar categoría estado_mora
    def map_estado_mora(dias_atraso):
        if pd.isna(dias_atraso) or dias_atraso == 0:
            return "Al día"
        elif 1 <= dias_atraso <= 15:
            return "Mora 15"
        elif 16 <= dias_atraso <= 30:
            return "Mora 30"
        elif 31 <= dias_atraso <= 45:
            return "Mora 45"
        elif 46 <= dias_atraso <=60:
            return "Mora 60"
        elif dias_atraso > 60:
            return "Mora 60+"
        return None  # Default case, if needed

    data['estado_mora'] = data['dias_atraso'].apply(map_estado_mora)

    # Agregar días atraso para cuota
    today = pd.Timestamp.now()
    data['dias_vencido'] = data.apply(
        lambda row: (today - row['fecha_cuota']).days if row['estado'] == 'Vencido' else 0,
        axis=1
    )

    data['estado_mora_cuota'] = data['dias_vencido'].apply(map_estado_mora)


    # Agregar columnas de frecuencia
    for date_col in ['fecha_venta', 'fecha_cuota']:
        data[f'{date_col}_month'] = data[date_col].dt.to_period('M')  
        data[f'{date_col}_week'] = data[date_col].dt.to_period('W') 
        #data[f'{date_col}_fortnight'] = (data[date_col].dt.day - 1) // 15 + 1  
        data[f'{date_col}_fortnight'] = data[date_col].dt.date + pd.offsets.SemiMonthEnd()


    return data


#---------------------------------------------------------------------------
#                   FUNCIONES FILTROS ESPECIALES
#---------------------------------------------------------------------------

def filtro_pais(df, lista_paises=['El Salvador','Honduras']):

    df = df[df['pais'].isin(lista_paises)]

    return df


def filtro_generico(df, columna, seleccion):

    df = df[df[columna].isin(seleccion)]

    return df

#---------------------------------------------------------------------------
#                   FUNCIONES ANÁLISIS DE CARTERA
#---------------------------------------------------------------------------

# Indicadores de cartera total


def indicadores_cartera(data):
    """
    Input: DataFrame limpio correspondiente a view CASHFLOW
    Output:
    1. Total esperado (suma de cuotas pendientes) por 'estado_mora'.
    2. Total cuotas pendientes (cualquier 'estado_mora').
    3. Total cuotas pagadas (cualquier 'estado_mora').
    4. Total cuotas pendientes para clientes en 'Mora 60'.
    5. Total 'valor_financiamiento' para cada cliente único.
    """
    # Filtrar por estados
    expected_mask = data['estado'].isin(['Exigible', 'Fijo', 'Vencido'])
    overdue_mask = data['estado'] == 'Vencido'
    paid_mask = data['estado'].isin(['Pagado a Tiempo', 'Pagado Retraso'])
    
    # 1. Total esperado (suma de cuotas pendientes) por 'estado_mora'
    expected_by_estado_mora = (
        data[expected_mask]
        .groupby('estado_mora')['monto_cuota']
        .sum()
        .reset_index()
        .rename(columns={'monto_cuota': 'Monto (USD)'})
    )
    expected_by_estado_mora['Indicador'] = "Cartera Total (" + expected_by_estado_mora['estado_mora'] + ")"
    
    # 2. Total cuotas pendientes (cualquier 'estado_mora')
    total_expected = data.loc[expected_mask, 'monto_cuota'].sum()
    
    # 3. Total cuotas pagadas (cualquier 'estado_mora')
    total_paid = data.loc[paid_mask, 'monto_cuota'].sum()
    
    # 4. Total cuotas pendientes para clientes en 'Mora 60'
    mora_60_expected = (
        data[expected_mask & (data['estado_mora'] == 'Mora 60')]['monto_cuota']
        .sum()
    )
    
    # 5. Total 'valor_financiamiento' 
    unique_loans = data[['id_credito', 'valor_financiamiento']].drop_duplicates()
    total_financiamiento = unique_loans['valor_financiamiento'].sum()

    # DEBUGGING TOTAL SALDO ACTUAL
    unique_loans = data[['id_credito', 'saldo_actual']].drop_duplicates()
    total_saldo_actual = unique_loans['saldo_actual'].sum()
    
    # Tabla
    summary_data = [
        {'Indicador': row['Indicador'], 'Monto (USD)': row['Monto (USD)']}
        for _, row in expected_by_estado_mora.iterrows()] + [
        {'Indicador': 'Cartera Total (Capital Pendiente)', 'Monto (USD)': total_saldo_actual},
        {'Indicador': 'Cartera Pagada', 'Monto (USD)': total_paid},
        {'Indicador': 'Cartera a Pérdida', 'Monto (USD)': mora_60_expected},
        {'Indicador': 'Capital Desembolsado', 'Monto (USD)': total_financiamiento}
    ]

    summary = pd.DataFrame(summary_data)
    
    # Porcentaje
    summary['Porcentaje'] = (summary['Monto (USD)'] / total_financiamiento * 100).round(2)

    # Formato
    summary['Monto (USD)'] = summary['Monto (USD)'].apply(lambda x: f"${x:,.2f}")
    summary['Porcentaje'] = summary['Porcentaje'].apply(lambda x: f"{x:.2f}%")

    summary.set_index('Indicador', inplace=True)

    return summary.reset_index()

#---------------------------------------------------------------------------

# Créditos otorgados

def creditos_otorgados(data):
    """
    Input: DataFrame limpio correspondiente a CASHFLOW
    Output:
    1. Cantidad de créditos únicos por 'estado_mora'.
    2. Cantidad de créditos activos (al menos una cuota en estado 'Fijo').
    3. Cantidad de créditos saldados (solo cuotas en estados 'Pagado').
    4. Cantidad de créditos a pérdida ('Mora 60').
    5. Cantidad de créditos total.
    """
    # Créditos únicos
    loans = data.groupby('id_credito')
    
    # 1. Contar por 'estado_mora'
    estado_mora_counts = (
        data.groupby('estado_mora')['id_credito']
        .nunique()
        .reset_index()
        .rename(columns={'id_credito': 'Cantidad'})
    )
    estado_mora_counts['Indicador'] = "Créditos (" + estado_mora_counts['estado_mora'] + ")"

    # 2. Contar créditos con al menos una cuota Fijo
    #active_loans = loans.filter(lambda x: (x['estado'] == 'Fijo').any()).shape[0]
    active_loans = len(data[data['estado']=='Fijo']['id_credito'].unique())

    # 3. Contar créditos con todas las cuotas pagadas
    fully_paid_loans = loans.filter(
        lambda x: x['estado'].isin(['Pagado a Tiempo', 'Pagado Retraso']).all()
    ).shape[0]

    # 4. Créditos a moraq 60
    #mora_60_loans = loans.filter(lambda x: (x['estado_mora'] == 'Mora 60').any()).shape[0]
    mora_60_loans = len(data[data['estado_mora']=='Mora 60']['id_credito'].unique())
    # 5. Créditos totales
    total_unique_loans = data['id_credito'].nunique()

    # Tabla
    summary_data = [
        {'Indicador': row['Indicador'], 'Cantidad': row['Cantidad']}
        for _, row in estado_mora_counts.iterrows()
    ] + [
        {'Indicador': 'Créditos Activos', 'Cantidad': active_loans},
        {'Indicador': 'Créditos Saldados', 'Cantidad': fully_paid_loans},
        {'Indicador': 'Créditos a pérdida', 'Cantidad': mora_60_loans},
        {'Indicador': 'Créditos Otorgados', 'Cantidad': total_unique_loans}
    ]
    summary = pd.DataFrame(summary_data)

    summary['Porcentaje'] = (summary['Cantidad'] / total_unique_loans * 100).round(2)
    summary['Porcentaje'] = summary['Porcentaje'].apply(lambda x: f"{x:.2f}%")

    summary.set_index('Indicador', inplace=True)
            
    return summary.reset_index()


#---------------------------------------------------------------------------

# Montos

def montos(data, term_unit='month'):
    """
    Inputs:
    - DataFrame limpio correspondiente a CASHFLOW
    - Frecuencia deseada paqra mostrar número de períodos, default meses.
    Output:
    1. Capital otorgado ('valor_financiamiento') promedio (créditos únicos).
    2. Promedio de 'numero_periodos', representado en semanas, meses (default), o quincenas.
    """
    # Mapeo frecuencias
    valid_units = {'week': 2, 'fortnight': 1, 'month': 0.5}
    if term_unit not in valid_units:
        raise ValueError(f"Frecuencia inválidad '{term_unit}'. Escoger 'week', 'month', o 'fortnight'.")

    # 1. Promedio de 'valor_financiamiento' 
    unique_loans = data[['id_credito', 'valor_financiamiento']].drop_duplicates()
    avg_valor_financiamiento = unique_loans['valor_financiamiento'].mean()

    # 2. Promedio 'numero_periodos' en unidad deseada
    conversion_factor = valid_units[term_unit]
    avg_numero_periodos = data.drop_duplicates(subset=['id_credito'])['numero_periodos'].mean() * conversion_factor

    # Plazo map
    plazo_map = {'month':'mensual',
                 'week': 'semanal',
                 'fortnight': 'quincenal'}

    # Tabla
    summary = pd.DataFrame([
        {'Monto': 'Capital promedio otorgado', 'Valor': '$'+str(round(avg_valor_financiamiento, 2))},
        {'Monto': f'Plazo promedio ({plazo_map[term_unit].capitalize()})', 'Valor': avg_numero_periodos}
    ])

    summary.set_index('Monto', inplace=True)
    
    return summary.reset_index()


#---------------------------------------------------------------------------

def mora_saldo(df, c=False):

    #capital_pendiente = df[df['estado'].isin(['Vencido','Fijo','Exigible'])]['monto_cuota'].sum()
    capital_pendiente = df.drop_duplicates(subset=['id_credito'])['saldo_actual'].sum()


    if c==True:
        estados = ['Vencido','Fijo','Exigible']
        columna_mora = 'estado_mora'
        
    else:
        estados = ['Vencido']
        columna_mora = 'estado_mora_cuota'
    
    df = df[df['estado'].isin(estados)]

    #tabla = pd.DataFrame(df.groupby('estado_mora')['monto_cuota'].sum()/capital_pendiente*100)
    tabla = pd.DataFrame(df.groupby(columna_mora)['monto_cuota'].sum())
    tabla['perc'] = df.groupby(columna_mora)['monto_cuota'].sum()/capital_pendiente*100
    
    tabla.loc['Total'] = tabla.sum(axis=0)
    tabla.reset_index(col_level=0, inplace=True)
    tabla = tabla.rename(columns={str(columna_mora):'Estado Mora', 'monto_cuota':'Porcentaje'}).set_index('Estado Mora')
    #tabla['Porcentaje'] = tabla['Porcentaje'].apply(lambda x: f"{x:.2f}%")

    return tabla.reset_index(col_level=0) 


#---------------------------------------------------------------------------

# Créditos en mora versus créditos activos

def creditos_mora_activos(data):
    """
    Input: DataFrame limpio CASHFLOW
    Output:
    - Cantidad de créditos únicos por estado mora dividido entre créditos activos
    - Valor en porcentaje
    """

    # Filtrar por estado
    active_loans_mask = data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])
    overdue_loans_mask = data['estado'] == 'Vencido'
    not_up_to_date_mask = data['estado_mora'] != 'Al día'
    
    # Créditos activos
    total_active_loans = data[active_loans_mask]['id_credito'].nunique()
    
    # 1. Créditos por estado_mora
    overdue_loans = data[overdue_loans_mask & not_up_to_date_mask]
    unique_loans_by_estado_mora = (
        overdue_loans.groupby('estado_mora')['id_credito']
        .nunique()
        .reset_index()
        .rename(columns={'id_credito': 'Cantidad'})
    )
    unique_loans_by_estado_mora['Estado Mora'] = "Créditos (" + unique_loans_by_estado_mora['estado_mora'] + ")"
    
    # 2. Total créditos en mora
    total_loans_in_debt = overdue_loans['id_credito'].nunique()
    
    summary_data = [
        {'Estado Mora': row['Estado Mora'], 'Cantidad': row['Cantidad']}
        for _, row in unique_loans_by_estado_mora.iterrows()
    ] + [
        {'Estado Mora': 'Total créditos en mora', 'Cantidad': total_loans_in_debt}
    ]
    summary = pd.DataFrame(summary_data)
    
    summary['Porcentaje'] = (summary['Cantidad'] / total_active_loans * 100).round(2)
    summary['Porcentaje'] = summary['Porcentaje'].apply(lambda x: f"{x:.2f}%")

    summary.set_index('Estado Mora', inplace=True)
    
    return summary.reset_index()

#---------------------------------------------------------------------------
#                   FUNCIONES ANÁLISIS DE COSECHA
#---------------------------------------------------------------------------

# Indicadores de cartera total

def indicadores_cosecha(data, cohort='month'):
    """
    Inputs:
    - DataFrame limpio CASHFLOW
    - Frecuencia de cosechas (semanal, quincenal o mensual, default)
    Output:
    1. Capital pendiente (suma de cuotas pendientes, USD)
    2. Capital saldado (suma de cuotas pagadas para créditos que han sido saldados, USD)
    3. Capital pagado (suma de cuotas pagadas, USD)
    4. Cuotas pendientes para créditos en mora 60 (pérdida, USD)
    5. Capital desembolsado (total valor_financiamiento para créditos únicos, USD).
    6. Suma de cuotas esperadas entre suma de cuotas totales (%)
    7. Suma de cuotas pagadas entre suma de cuotas totales (%)
    8. Cantidad de créditos activos (al menos una cuota en estado Fijo).
    9. Cantidad de créditos en Mora 60 (a pérdida)
    10. Total créditos únicos
    """
    # Mapear columnas por cosecha
    cohort_map = {
        'month': 'fecha_venta_month',
        'week': 'fecha_venta_week',
        'fortnight': 'fecha_venta_fortnight'
    }
    if cohort not in cohort_map:
        raise ValueError("Frecuencia inválida. Escoger 'week', 'fortnight', o 'month'.")

    cohort_col = cohort_map[cohort]

    def format_cohort(value):
        if cohort == 'month':
            return value.strftime('%b %Y') 
        elif cohort == 'week':
            return f"Semana {value.week} {value.start_time.strftime('%Y')}"  
        elif cohort == 'fortnight':
            return f"Quincena {value.strftime('%d %b %Y')}"

    # Cuotas pendientes
    expected = data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])]
    total_expected = expected.groupby(cohort_col)['monto_cuota'].sum()

    # Capital saldado
    fully_paid_loans = data.groupby('id_credito').filter(
        lambda x: x['estado'].isin(['Pagado a Tiempo', 'Pagado Retraso']).all()
    )
    fully_paid_total = fully_paid_loans.groupby(cohort_col)['monto_cuota'].sum()

    # Capital pagado
    total_paid = data[data['estado'].isin(['Pagado a Tiempo', 'Pagado Retraso'])].groupby(cohort_col)['monto_cuota'].sum()

    # Cartera a pérdida
    mora_60 = expected[expected['estado_mora'] == 'Mora 60']
    mora_60_total = mora_60.groupby(cohort_col)['monto_cuota'].sum()

    # valor_financiamiento promedio
    unique_loans = data[['id_credito', 'valor_financiamiento', cohort_col]].drop_duplicates()
    avg_valor_financiamiento = unique_loans.groupby(cohort_col)['valor_financiamiento'].mean()

    # Cuotas totales
    total_installments = total_expected + total_paid

    # Cartera pendiente/ cartera otorgada
    ratio_expected = (total_expected / total_installments *100).fillna(0)

    # Cartera pagada / cartera otorgada
    ratio_paid = (total_paid / total_installments *100).fillna(0)

    # Activos
    active_loans = data[data['estado'] == 'Fijo']
    active_loans_count = active_loans.groupby(cohort_col)['id_credito'].nunique()

    # Mora 60
    mora_60_loans_count = mora_60.groupby(cohort_col)['id_credito'].nunique()

    # Total únicos
    total_unique_loans = data.groupby(cohort_col)['id_credito'].nunique()

    summary = pd.DataFrame({
        'Capital Pendiente': total_expected,
        'Capital Saldado': fully_paid_total,
        'Capital Pagado': total_paid,
        'Capital a pérdida': mora_60_total,
        'Cartera Otorgada': total_installments,
        'Promedio monto capital': avg_valor_financiamiento,
        'Cartera Pendiente vs Cartera Otorgada': ratio_expected,
        'Cartera Pagada vs Cartera Otorgada': ratio_paid,
        'Créditos Activos': active_loans_count,
        'Créditos a pérdida': mora_60_loans_count,
        'Créditos Otorgados': total_unique_loans
    }).fillna(0).round(2).T  # Transpose for cohorts as columns

    # Formato
    summary.columns = [format_cohort(value) for value in summary.columns]
    summary.iloc[0] = summary.iloc[0].apply(lambda x: f"${x:,.2f}")
    summary.iloc[1] = summary.iloc[1].apply(lambda x: f"${x:,.2f}")
    summary.iloc[2] = summary.iloc[2].apply(lambda x: f"${x:,.2f}")
    summary.iloc[3] = summary.iloc[3].apply(lambda x: f"${x:,.2f}")
    summary.iloc[4] = summary.iloc[4].apply(lambda x: f"${x:,.2f}")
    summary.iloc[5] = summary.iloc[5].apply(lambda x: f"${x:,.2f}")
    summary.iloc[6] = summary.iloc[6].apply(lambda x: f"{x:.2f}%")
    summary.iloc[7] = summary.iloc[7].apply(lambda x: f"{x:.2f}%")
    summary.iloc[8] = summary.iloc[8].apply(round)
    summary.iloc[9] = summary.iloc[9].apply(round)
    summary.iloc[10] = summary.iloc[10].apply(round)

    summary.index.name= 'Indicador'

    return summary.reset_index()

#---------------------------------------------------------------------------

# Mora - Monto & Mora Contagiada - Monto

def mora_monto_cosecha(data, cohort='month', payment_type='overdue'):
    """
    Inputs:
    - DataFrame limpio CASHFLOW
    - Frecuencia de cosecha (semanal, quincenal, o mensual, default)
    - Mora o mora contagiada (overdue, default, o expected)
    Output:
    - Monto mora por cosecha por estado mroa
    """
   
    cohort_map = {
        'month': 'fecha_venta_month',
        'week': 'fecha_venta_week',
        'fortnight': 'fecha_venta_fortnight'
    }
    if cohort not in cohort_map:
        raise ValueError("Invalid cohort. Choose from 'week', 'fortnight', or 'month'.")

    if payment_type not in ['overdue', 'expected']:
        raise ValueError("Invalid payment_type. Choose from 'overdue' or 'expected'.")

    cohort_col = cohort_map[cohort]

    # Filtrar por mora o mora contagiada
    if payment_type == 'overdue':
        filtered_data = data[data['estado'] == 'Vencido']
    elif payment_type == 'expected':
        filtered_data = data[data['estado'].isin(['Vencido', 'Exigible', 'Fijo'])]

    # Group by `estado_mora` y cosecha, sumando `monto_cuota`
    mora_summary = (
        filtered_data
        .groupby(['estado_mora', cohort_col])['monto_cuota']
        .sum()
        .unstack(fill_value=0)
    )

    def format_cohort(value):
        if cohort == 'month':
            return value.strftime('%b %Y') 
        elif cohort == 'week':
            return f"Semana {value.week} {value.start_time.strftime('%Y')}"  
        elif cohort == 'fortnight':
            return f"Quincena {value.strftime('%d %b %Y')}"

    mora_summary.columns = [format_cohort(value) for value in mora_summary.columns]

    mora_summary['Total'] = mora_summary.sum(axis=1)

    mora_summary.loc['Total'] = mora_summary.sum()

    mora_summary.reset_index(col_level=0, inplace=True)
    mora_summary.set_index('estado_mora', inplace=True)

    if payment_type=='overdue':
        mora_summary.index.name = 'Estado Mora'
    else:
        mora_summary.index.name = 'Estado Mora (C)'

    for column in mora_summary.columns:
        mora_summary[column] = mora_summary[column].apply(lambda x: f"${x:,.2f}")

    return mora_summary.reset_index()

#---------------------------------------------------------------------------

# Mora versus saldo actual/ saldo otorgado por cosecha

def mora_saldo_cosecha(df, saldo='saldo_actual', cohort='month', c=False):

    df_expected = df[df['estado'].isin(['Vencido','Fijo','Exigible'])]
    df_vencido = df[df['estado']=='Vencido']
    df_unique = df[df['num_cuota']==1]

    cohort_map = {
        'month': 'fecha_venta_month',
        'week': 'fecha_venta_week',
        'fortnight': 'fecha_venta_fortnight'
    }

    cohort_col = cohort_map[cohort]

    saldo_cosecha = df_unique.pivot_table(index='estado_mora',columns=cohort_col, values=saldo, aggfunc='sum')
    saldo_cosecha.loc['Total'] = saldo_cosecha.sum(axis=0)

    if c==True:
        mora_saldo = df_expected.pivot_table(index='estado_mora', columns=cohort_col, values='monto_cuota', aggfunc='sum')
    else:
        mora_saldo = df_vencido.pivot_table(index='estado_mora', columns=cohort_col, values='monto_cuota', aggfunc='sum')

    mora_saldo.loc['Total'] = mora_saldo.sum(axis=0)

    tabla = mora_saldo/saldo_cosecha.loc['Total']*100

    def format_cohort(value):
        if cohort == 'month':
            return value.strftime('%b %Y') 
        elif cohort == 'week':
            return f"Semana {value.week} {value.start_time.strftime('%Y')}"  
        elif cohort == 'fortnight':
            return f"Quincena {value.strftime('%d %b %Y')}"

    tabla.columns = [format_cohort(value) for value in tabla.columns]
    tabla.fillna(0, inplace=True)
    tabla.index.name = 'Estado Mora'

    for column in tabla.columns:
        tabla[column] = tabla[column].apply(lambda x: f"{x:.2f}%")


    return tabla.reset_index()

#---------------------------------------------------------------------------

# Rendimientos estimados por cosecha 

def detailed_cohort_table(data, cohort='month'):

    # ANUALIZAR ((VAR1 / VAR2)-1) *12)

    """
    Inputs:
    - DataFrame limpio CASHFLOW
    - Frecuencia de cosecha
    Output:
    - Cartera pagada total
    - Monto total esperado
    - Cartera saldado
    - Cartera por estado mora
    - Margen saldado
    - Margen saldado por estado mora (acumulado)
    - Plazo promedio
    - Rendimiento saldado
    - Rendimiento saldado por estado mora (acumulado)
    """

    cohort_map = {
        'month': 'fecha_venta_month',
        'week': 'fecha_venta_week',
        'fortnight': 'fecha_venta_fortnight'
    }
    if cohort not in cohort_map:
        raise ValueError("Invalid cohort. Choose from 'week', 'fortnight', or 'month'.")
    
    cohort_col = cohort_map[cohort]

    total_paid = data[data['estado'].isin(['Pagado a Tiempo', 'Pagado Retraso'])].groupby(cohort_col)['monto_cuota'].sum()

    total_expected = data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])].groupby(cohort_col)['monto_cuota'].sum()

    loans_without_fijo = data.groupby('id_credito').filter(lambda x: not (x['estado'] == 'Fijo').any())
    total_paid_no_fijo = loans_without_fijo.groupby(cohort_col)['monto_cuota'].sum()

    estado_mora_totals = (
        data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])]
        .groupby(['estado_mora', cohort_col])['monto_cuota']
        .sum()
        .unstack(fill_value=0)
    )

    # Llenar valores vacíos para estado mora
    all_estado_mora = ['Al día', 'Mora 15', 'Mora 30', 'Mora 45', 'Mora 60']
    # for mora in all_estado_mora:
    #     if mora not in estado_mora_totals.index:
    #         estado_mora_totals.loc[mora] = 0

    # # Margen Saldado
    unique_loans = data[['id_credito', 'valor_financiamiento', cohort_col]].drop_duplicates()
    valor_financiamiento_sum = unique_loans.groupby(cohort_col)['valor_financiamiento'].sum()
    unique_loans_precio = data[['id_credito', 'precio_venta', cohort_col]].drop_duplicates()
    precio_venta_sum = unique_loans_precio.groupby(cohort_col)['precio_venta'].sum()

    margen_rows = {'Margen Saldado':(total_paid/precio_venta_sum-1)*100}

    margen = ['Margen Saldado']
    sumados_margen = []

    for estado in all_estado_mora:
        sumados_margen.append(estado)
        name = margen[-1]+' + '+estado
        margen.append(name)
        plus = data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])][data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])]['estado_mora'].isin(sumados_margen)].groupby(cohort_col)['monto_cuota'].sum()

        margen_rows[name] = ((total_paid+plus)/precio_venta_sum-1)*100

    # Período promedio en frecuencia seleccionada
    avg_terms = (data[data['num_cuota']==1].groupby(cohort_col)['numero_periodos'].mean() * {'month': 0.5, 'week': 2, 'fortnight': 1}[cohort]).round(2)

    # # Rendimiento Saldado
    unique_loans_precio = data[['id_credito', 'precio_venta', cohort_col]].drop_duplicates()
    precio_venta_sum = unique_loans_precio.groupby(cohort_col)['precio_venta'].sum()

    rendimiento_rows = {'Rendimiento Saldado':(total_paid/precio_venta_sum-1)*avg_terms/12*100}
    rendimiento = ['Rendimiento Saldado']
    sumados_rendimiento = []

    for estado in all_estado_mora:
        sumados_rendimiento.append(estado)
        name = rendimiento[-1]+' + '+estado
        rendimiento.append(name)
        plus = data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])][data[data['estado'].isin(['Fijo', 'Exigible', 'Vencido'])]['estado_mora'].isin(sumados_rendimiento)].groupby(cohort_col)['monto_cuota'].sum()

        rendimiento_rows[name] = ((total_paid+plus)/precio_venta_sum-1)*avg_terms/12*100
    

    table_data = {
        'Cartera Pagada (USD)': total_paid,
        'Cartera Esperada (USD)': total_expected,
        'Cartera Saldada (USD)': total_paid_no_fijo,
        **{f"Capital Pendiente {mora} (USD)": estado_mora_totals.loc[mora] for mora in all_estado_mora},
        'Períodos promedio': avg_terms,
    }

    for row in margen_rows:
        table_data[row] = margen_rows[row]
    
    for row in rendimiento_rows:
        table_data[row] = rendimiento_rows[row]

    result_table = pd.DataFrame(table_data).T.fillna(0)#.round(2).T  # Transpose to have rows as requested
    for row in result_table.index:
        if '(USD)' in row.split(' '):
            result_table.loc[row] = result_table.loc[row].apply(lambda x: f"${x:.2f}")
        elif 'Saldado' in row.split(' '):
            result_table.loc[row] = result_table.loc[row].apply(lambda x: f"{x:.2f}%")
        else:
            result_table.loc[row] = result_table.loc[row].apply(round)
    
    result_table.index.name = 'Indicador'
    result_table.columns.name = 'Cosecha'

    def format_cohort(value):
        if cohort == 'month':
            return value.strftime('%b %Y') 
        elif cohort == 'week':
            return f"Semana {value.week} {value.start_time.strftime('%Y')}"  
        elif cohort == 'fortnight':
            return f"Quincena {value.strftime('%d %b %Y')}"

    result_table.columns = [format_cohort(value) for value in result_table.columns]

    return result_table.reset_index(col_level=0)

