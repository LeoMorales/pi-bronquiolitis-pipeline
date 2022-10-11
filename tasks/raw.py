# -*- coding: utf-8 -*-
import pandas
import geopandas
from bronchiolitis_package import spatial
import esda


def get_bronchiolitis(product, MEDICAL_RECORDS_CSV_PATH, ADRESSES_AND_LATLONG_CSV_PATH):
    """
    Tarea que combina los datos crudos de casos de bronquiolitis con el dataset de domicilios.
    El dataset crudo tiene las siguientes columnas:
    
       'HC', 'FN', 'MESES', 'Edad', 'Vaginal', 'Cesarea', 'Sexo', 'SE',
       'INGRESO', 'EGRESO', 'Días I', 'Lugar E', 'DE CIE-10', 'Virus',
       'Domicilio', 'ALTERNATIVA', 'Domicilio definitivo', 'Unnamed: 17',
       'Barrio', 'Circunscripción', 'Sector', 'Unnamed: 21',
       'Nombre del Barrio'
    
    Solo se trabaja con las columnas: 'HC', 'INGRESO', 'EGRESO', 'SE', 'Edad', 'Domicilio definitivo'.
    La última columna se utiliza para combinar con el dataset de domicilios que tiene los siguientes
    primeros tres registros:
    
          domicilio_definitivo    latitud   longitud
        0              Alt 213 -42.760519 -65.040279
        1             Mitre 41 -42.765109 -65.037430
        2   Marcos A. Zar 1898 -42.782798 -65.027143
       
    
    Returns:
    
        CSV con las coordenadas de los casos recolectados.
        La columna es_reinternacion se obtiene según el atributo hc se encuentre duplicado o no.

            hc      ingreso     egreso      se      edad    domicilio_definitivo        es_reinternacion    latitud     longitud
        0   143367  2017-01-06  2017-01-09  1.0     0.63    Manuel Castro 1230          False               -42.759311  -65.055118
        1   143597  2017-01-19  2017-01-21  3.0     0.70    Cholila 1311                False               -42.760486  -65.057645
        2   144173  2017-02-22  2017-02-23  8.0     0.33    Luis Federico Leloir 820    False               -42.786004  -65.071097
        3   144546  2017-03-27  2017-04-01  13.0    4.00    Mitre 41                    False               -42.765109  -65.037430
        4   144189  2017-03-29  2017-04-01  13.0    1.00    El Hoyo 1310                False               -42.758420  -65.062481
        """
    # A: Historias clínicas
    df_raw = pandas.read_csv(MEDICAL_RECORDS_CSV_PATH)

    df_cols = ['HC', 'INGRESO', 'EGRESO', 'SE', 'Edad', 'Domicilio definitivo']
    df = df_raw[df_cols]
    
    ## eliminar aquellos que no tienen numero de historia clinica:
    df = df.dropna(subset=['HC'])
    ## primero ordenamos por fecha de ingreso
    df = df.sort_values(by='INGRESO')
    ## después de ordenar, si se repite el nro de historia clinica, es reinternación:
    df['es_reinternacion'] = df.HC.duplicated()
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    df = df.reset_index(drop=True)

    #
    # B: Latlong de los domicilios
    domicilio_latlong = pandas.read_csv(ADRESSES_AND_LATLONG_CSV_PATH)

    ## rename columns (lowercase):
    domicilio_latlong = domicilio_latlong.rename(
        columns={
            column: column.lower().replace(' ', '_')
            for column
            in domicilio_latlong.columns
        }
    )

    ## sort from north to south, east to west:
    LAT_COLUMN = 'latitud'
    LNG_COLUMN = 'longitud'
    sorted_index_values = (domicilio_latlong[LAT_COLUMN] ** 2 + domicilio_latlong[LNG_COLUMN] **2).sort_values().index
    domicilio_latlong = domicilio_latlong.iloc[sorted_index_values]

    ## delete duplicates:
    domicilio_latlong = domicilio_latlong.drop_duplicates()
    domicilio_latlong = domicilio_latlong.reset_index(drop=True)

    #
    # C: Combine
    output_df = pandas.merge(
        df,
        domicilio_latlong,
        on='domicilio_definitivo',
    )
    output_df.to_csv(product, index=False)

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
    
    columns = ['toponimo_i', 'link', 'totalpobl', 'nbi', 'casos', 'geometry', 'tasa_casos']
    pm_tracts = pm_tracts[columns]
    
    # Pesos y geodataframes de trabajo
    weights, moran_rate, lisa_rate = \
        spatial.get_spatials(
            pm_tracts,
            attribute='casos',
            strategy='knn',
            k_neighbours=6,
            use_moran_rate=True,
            moran_rate_column='totalpobl'
        )

    # 1. Contar las cantidades por cada cluster
    quadfilter = \
            (lisa_rate.p_sim <= (.05)) * (lisa_rate.q)
    spot_labels = ['Not significant', 'Hot spot', 'Donut', 'Cold spot', 'Diamond']
    labels = [spot_labels[i] for i in quadfilter]
    pm_tracts['label'] = labels
    
    # get lisa bivariate!:
    #weights_queen, _, _ = \
    #    spatial.get_spatials(
    #        pm_tracts,
    #        attribute='tasa_casos',
    #        strategy='queen'
    #    )

    lisa_bv = esda.Moran_Local_BV(
        pm_tracts['nbi'].values,
        pm_tracts['tasa_casos'].values,
        weights
    )
    # Contar las cantidades por cada cluster
    quadfilter_bv = \
            (lisa_bv.p_sim <= (.05)) * (lisa_bv.q)
    labels_bv = [spot_labels[i] for i in quadfilter_bv]
    pm_tracts['label_bv'] = labels_bv
    
    
    
    # pm_tracts.to_file(product, driver="GeoJSON")
    pm_tracts.to_parquet(product, index=False)


