# -*- coding: utf-8 -*-
import pandas
import geopandas

def get_cases(upstream, product, PUERTO_MADRYN_SHAPEFILE_PATH):
    """
    Obtiene los casos de bronquiolitis para cada polígono de radio censal.
           
    Returns:

        pandas.Dataframe: 
        
                   toponimo_i  casos
            0      322017     12
            1      321999      6
            2      319126      5
    """
    # read bronchiolitis
    bronchiolitis_df = pandas.read_csv(upstream['get_bronchiolitis'])

    # create geodataframe from bronchiolitis points:
    bronchiolitis_gdf = geopandas.GeoDataFrame(
        bronchiolitis_df,
        geometry=geopandas.points_from_xy(bronchiolitis_df.longitud, bronchiolitis_df.latitud),
        crs="EPSG:4326"
    )
    
    # read shape:
    puerto_madryn_shp = geopandas.read_file(PUERTO_MADRYN_SHAPEFILE_PATH)
    
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
    pandas.DataFrame(cases_per_census_unit)\
        .sort_values(by="casos", ascending=False)\
        .reset_index(drop=True)\
        .to_parquet(str(product))