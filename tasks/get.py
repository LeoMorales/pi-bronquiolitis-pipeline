# -*- coding: utf-8 -*-
import pandas
import geopandas


def get_bronchiolitis_locations(
        product,
        ENV_MEDICAL_RECORDS_CSV_PATH,
        ENV_ADRESSES_AND_LATLONG_CSV_PATH
    ):
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
    
        geopandas.GeoDataframe:
        Coordenadas de los casos recolectados.
        La columna es_reinternacion se obtiene según el atributo hc se encuentre duplicado o no.

               hc     ingreso      egreso   se  edad      domicilio_definitivo  \
        0  143367  2017-01-06  2017-01-09  1.0  0.63        Manuel Castro 1230   
        1  143597  2017-01-19  2017-01-21  3.0  0.70              Cholila 1311   
        2  144173  2017-02-22  2017-02-23  8.0  0.33  Luis Federico Leloir 820   

           es_reinternacion    latitud   longitud                     geometry  
        0             False -42.759311 -65.055118  POINT (-65.05512 -42.75931)  
        1             False -42.760486 -65.057645  POINT (-65.05765 -42.76049)  
        2             False -42.786004 -65.071097  POINT (-65.07110 -42.78600) 
    """
    # A: Historias clínicas
    df_raw = pandas.read_csv(ENV_MEDICAL_RECORDS_CSV_PATH)

    df_cols = ['HC', 'INGRESO', 'EGRESO', 'SE', 'Edad', 'Domicilio definitivo']
    df = df_raw[df_cols]
    
    ## eliminar aquellos que no tienen numero de historia clinica:
    df = df.dropna(subset=['HC'])
    ## primero ordenamos por fecha de ingreso
    df = df.sort_values(by='INGRESO')
    ## después de ordenar, si se repite el nro de historia clinica, es reinternación:
    df['es_reinternacion'] = df['HC'].duplicated()
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    df = df.reset_index(drop=True)

    #
    # B: Latlong de los domicilios
    domicilio_latlong = pandas.read_csv(ENV_ADRESSES_AND_LATLONG_CSV_PATH)

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

    # mudanza problems:
    df.loc[df['domicilio_definitivo'] == "Tecka 2050", "domicilio_definitivo"] = "Simón de Alcazabar 440"
    df.loc[df['domicilio_definitivo'] == "Gualjaina 1410", "domicilio_definitivo"] = "Río Mayo 1510"
    df.loc[df['domicilio_definitivo'] == "Lago Puelo 1476", "domicilio_definitivo"] = "Rada Tilly 1280"
    df.loc[df['domicilio_definitivo'] == "Vittorio Martinelli 1230", "domicilio_definitivo"] = "Manuel Castro 1230"
    df.loc[df['domicilio_definitivo'] == "Luis María Campos 450", "domicilio_definitivo"] = "Héroes de Malvinas 850"
    df.loc\
        [df['domicilio_definitivo'] == "Ruperto Gimenez 720", "domicilio_definitivo"] = \
            "Esteban Williams 812"
    df.loc\
        [df['domicilio_definitivo'] == "Rio Pico 1710", "domicilio_definitivo"] = \
            "Trevellin 1510"

    # not found problems:
    df.loc\
        [df['domicilio_definitivo'] == "M.A. Zar 1431", "domicilio_definitivo"] = \
            "Marcos A. Zar 1431"
    df.loc\
        [df['domicilio_definitivo'] == "Manuel Alzúa 620", "domicilio_definitivo"] = \
            "Manuel Alsua 620"
    # hay dos Alzúa...
    df.loc\
        [df['domicilio_definitivo'] == "C.T. Alt 213", "domicilio_definitivo"] = \
            "Alt 213"
    df.loc\
        [df['domicilio_definitivo'] == "Italia 125", "domicilio_definitivo"] = \
            "Italia 1000"
    df.loc\
        [df['domicilio_definitivo'] == "E. Williams 995", "domicilio_definitivo"] = \
            "Esteban Williams 995" 

    # C: Combine
    output_df = pandas.merge(
        df,
        domicilio_latlong,
        on='domicilio_definitivo',
    )

    #
    # D: Create geodataframe:
    output_gdf = geopandas.GeoDataFrame(
        output_df,
        geometry=geopandas.points_from_xy(output_df.longitud, output_df.latitud),
        crs="EPSG:4326"
    )
    
    output_gdf.to_parquet(product, index=False)

def get_shape(product, PUERTO_MADRYN_SHAPEFILE_PATH):
    """
    Limpia la capa y devuelve un parquet para leer con geopandas.
    
    Returns:
        
        geopandas.GeoDataframe:
                  toponimo_i       link  totalpobl   nbi  \
            0     321973  260070401     1086.0  3.29   
            1     321976  260070402      712.0  8.23   
            2     319120  260070403      693.0  6.51   

                                                        geometry  
            0  POLYGON ((3578785.448 5264948.990, 3578901.180...  
            1  POLYGON ((3578244.850 5265535.078, 3578270.165...  
            2  POLYGON ((3578569.532 5266020.406, 3578696.315...  
    """
    pm_tracts = geopandas.read_file(PUERTO_MADRYN_SHAPEFILE_PATH)
    pm_tracts['toponimo_i'] = pm_tracts["toponimo_i"].astype('string')
    pm_tracts['link'] = pm_tracts["link"].astype('string')
    columns = ['link', 'toponimo_i', 'totalpobl', 'geometry']
    pm_tracts = pm_tracts[columns]
    
    CSV_EDADES_CHUBUT = "/home/lmorales/work/pipelines/pi-bronquiolitis/input-data/edades_chubut_censo_2010_INDEC_solo_madryn.csv"
    df_indec = pandas.read_csv(
        CSV_EDADES_CHUBUT,
        delimiter='\\t')
    
    df_indec = df_indec[df_indec['edad'] == 0]
    df_indec[["link", "menores_de_un_año"]] = df_indec[["area", "casos"]]
    df_indec["link"] = df_indec['link'].astype(str)

    pm_tracts = pandas.merge(
        pm_tracts,
        df_indec,
        on='link',
        how='left'
    )

    pm_tracts.to_parquet(product, index=False)


def get_nbi(product, PUERTO_MADRYN_SHAPEFILE_PATH):
    """
    Devuelve el valor de nbi para cada circuito (por toponimo)
    
    """
    pm_tracts = geopandas.read_file(PUERTO_MADRYN_SHAPEFILE_PATH)
    
    pm_tracts['toponimo_i'] = pm_tracts["toponimo_i"].astype('string')
    pm_tracts = pm_tracts.rename(columns={'Unidades_7': 'nbi'})
    
    columns = ['toponimo_i', 'nbi']
    pm_tracts = pm_tracts[columns]
    
    pm_tracts.to_parquet(product, index=False)


