# -*- coding: utf-8 -*-
import pandas
import geopandas


def get_hc(product):
    df_raw = pandas.read_excel(
        '/home/lmorales/work/pi-bronquiolitis/data/IRAB O2 2017 18 19 20 O31.xlsx',
        sheet_name='Hoja1'
    )

    df_cols = ['HC', 'INGRESO', 'EGRESO', 'SE', 'Edad', 'Domicilio', 'ALTERNATIVA']
    df = df_raw[df_cols]

    #df_reinternaciones = pandas.DataFrame()
    #for i, ds in df.groupby(['HC']):
    #    if len(ds) > 1:
    #        df_reinternaciones = pandas.concat([
    #            df_reinternaciones,
    #            ds
    #        ])
    #df_reinternaciones = df_reinternaciones.reset_index(drop=True)
    #print(
    #    len(df_reinternaciones.drop_duplicates(subset=['HC', 'INGRESO'])) == len(df_reinternaciones)
    #)
    #df_reinternaciones = df_reinternaciones.reset_index(drop=True)
    #df_reinternaciones.to_excel('./reinternaciones_2.xlsx', index=False)
    
    df = df.dropna(subset=['HC'])
    df['es_reinternacion'] = df.HC.duplicated()
    df.columns = df.columns.str.upper()
    df = df.sort_values(by='INGRESO')
    df = df.reset_index(drop=True)
    df.to_csv(str(product), index=False)



def get(product):
    """
    Tarea que  limpia el dataset crudo con los domicilios de casos de bronquiolitis en Perto Madryn.
    Salida: CSV con las coordenadas de los casos recolectados
    """
    df = pandas.read_csv(
        '/home/lmorales/work/pi-bronquiolitis-pipeline/input/csv/domicilio_lat_long_corregido.csv'
    )
    
    # rename columns (lowercase):
    df = df.rename(
        columns={
            column: column.lower().replace(' ', '_')
            for column
            in df.columns
        }
    )
    
    # sort from north to south, east to west:
    LAT_COLUMN = 'latitud'
    LNG_COLUMN = 'longitud'
    df = df.iloc[(df[LAT_COLUMN] ** 2 + df[LNG_COLUMN] **2).sort_values().index]

    # delete duplicates:
    df = df.drop_duplicates()

    df.to_csv(product, index=False)

def shape(product):
    """
    Limpia la capa y devuelve un parquet para leer con geopandas.
    TODO: Realizar una tarea (paso) previa que incorpora la información a la capa.
    Esto permitiria en el flujo trabajar separado datos de capa y combinar cuando resulte necesario.
    """
    pm_tracts = \
        geopandas.read_file(
            '/home/lmorales/work/pi-bronquiolitis-pipeline/input/shapes/cases_per_census_tract.geojson'
        )
    pm_tracts['toponimo_i'] = pm_tracts["toponimo_i"].astype('string')
    pm_tracts = pm_tracts.rename(columns={'Unidades_7': 'nbi'})
    pm_tracts['tasa_casos'] = (pm_tracts.casos / pm_tracts.totalpobl) * 10_000

    # pm_tracts.to_file(product, driver="GeoJSON")
    pm_tracts.to_parquet(product, index=False)
