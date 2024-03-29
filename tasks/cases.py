# -*- coding: utf-8 -*-
import pandas
import geopandas

def get_cases_for_each_circuit(upstream, product):
    """
    Obtiene los casos de bronquiolitis (mas la tasa según la población) para cada
    polígono de radio censal.
           
    Returns:

        geopandas.GeoDataframe: 
        
                   toponimo_i  totalpobl casos   tasa_casos
            0      322017      X         12      X
            1      321999      X         6       X
            2      319126      X         5       X
    """
    # read bronchiolitis
    bronchiolitis_gdf = geopandas.read_parquet(upstream['get_bronchiolitis_locations'])

    # read shape:
    puerto_madryn_shp = geopandas.read_parquet(upstream['get_shape'])
    COL_YOUNG_POPULATION = 'menores_de_un_año'
    COL_TOTAL_POPULATION = 'totalpobl'
    # use same crs:
    bronchiolitis_gdf = bronchiolitis_gdf.to_crs(puerto_madryn_shp.crs.to_string())

    # count:
    cases_per_census_unit = []
    for _, census_unit in puerto_madryn_shp.iterrows():
        # count intersections vs all se points
        intersections = []
        for _, point in bronchiolitis_gdf.iterrows():
            intersections.append(census_unit.geometry.intersects(point.geometry))

        cases_per_census_unit.append(
            {
                'toponimo_i': census_unit.toponimo_i,
                'casos': len(list(filter(bool, intersections)))
            }
        )
    # -

    # save:
    cases_df = pandas.DataFrame(cases_per_census_unit)\
        .sort_values(by="casos", ascending=False)\
        .reset_index(drop=True)
    
    cases_df['toponimo_i'] = cases_df["toponimo_i"].astype('string')
    
    output_gdf = pandas.merge(
        puerto_madryn_shp[['link', 'toponimo_i', COL_TOTAL_POPULATION, COL_YOUNG_POPULATION, 'geometry']],
        cases_df,
        on='toponimo_i'
    )
    
    # add rates:
    output_gdf['tasa_casos'] = (output_gdf['casos'] / output_gdf[COL_TOTAL_POPULATION]) * 10_000
    output_gdf['tasa_casos_menores'] = (output_gdf['casos'] / output_gdf[COL_YOUNG_POPULATION]) * 10_000
    

    columns = [
        'link', 'toponimo_i',
        'casos',
        COL_TOTAL_POPULATION, 'tasa_casos',
        COL_YOUNG_POPULATION, 'tasa_casos_menores',
        'geometry'
    ]
    output_gdf = output_gdf[columns]
    
    # save geodataframe
    output_gdf.to_parquet(str(product), index=False)
