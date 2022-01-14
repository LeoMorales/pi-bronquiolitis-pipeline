# -*- coding: utf-8 -*-
# + tags=[]
import pandas
import geopandas
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import Point
import contextily
import matplotlib.pyplot as plt
from IPython.display import Image
import esda

from bronchiolitis_package import spatial


# + tags=[]
def get_cluster(product, upstream):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get', 'shape']
    '''
    # Casos (puntos)
    df = pandas.read_csv(str(upstream['get']))
    df.head()

    # Capa (+ casos)
    shape = \
        geopandas.read_parquet(str(upstream['shape']))
    
    # Pesos y geodataframes de trabajo
    weights_rate, moran_rate, lisa_rate = \
        spatial.get_spatials(
            shape,
            attribute='casos',
            strategy='knn',
            k_neighbours=6,
            use_moran_rate=True,
            moran_rate_column='totalpobl'
        )

    # create addresses geodataframe:
    addresses_gdf = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(df.longitud, df.latitud),
        crs="EPSG:4326"
    )

    addresses_gdf = addresses_gdf.to_crs(shape.crs.to_string())
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    south_america = geopandas.GeoSeries(
        [world[world.continent == 'South America'].unary_union],
        crs='epsg:4326'
    )
    LAT_LNG_PM = -65.030949, -42.769679
    working_area = Point(*LAT_LNG_PM)
    geopoint_madryn = geopandas.GeoSeries(
        [working_area],
        crs='epsg:4326'
    )

    # Figura
    # clusters map:
    _, ax = spatial.plot_lisa_map(
        shape,
        lisa_rate,
        figure_title="Moran Statistics: Cases of bronchiolitis\nPuerto Madryn, Chubut, Argentina"
    )

    # basemap:
    contextily.add_basemap(
        ax,
        source="/home/lmorales/work/pi-bronquiolitis-pipeline/input/basemaps_images/puerto_madryn.tif",
        crs=shape.crs.to_string()
    )

    # reference map_
    a = inset_axes(
        ax,
        width="35%", height='35%',
        loc='center right',
        bbox_to_anchor=(0.078,0,1,1),
        bbox_transform=ax.transAxes
    )

    # sudamerica
    south_america.plot(color='none', figsize=(20,20), ax=a)

    # puntito de madryn en sudamerica
    geopoint_madryn.plot(color='r', markersize=100, ax=a)

    contextily.add_basemap(
        a,
        source='/home/lmorales/work/pi-bronquiolitis-pipeline/input/basemaps_images/south_america_stamen_terrain_background.tif',
        crs=south_america.crs.to_string()
    )
    txt1 = a.text(
        x=geopoint_madryn.x,
        y=geopoint_madryn.y+(geopoint_madryn.y*0.15),
        s='Puerto Madryn',
        fontsize=9.8
    )
    txt1.set_path_effects([PathEffects.withStroke(linewidth=4, foreground='w')])

    # 'N' indicator:
    ax.text(x=3583380, y=5261700, s='N', fontsize=30)
    arrow_length = 300
    arrow_x = 3583500
    arrow_y = 5261600 - arrow_length
    ax.arrow(
        arrow_x, arrow_y,
        0, arrow_length,
        facecolor='k',
        length_includes_head=True,
        head_width=250,
        head_length=400,
        overhang=.1
    )

    # cases points
    addresses_gdf.plot(
        ax=ax,
        marker='o',
        color='k',
        alpha=0.25,
        markersize=10
    )

    plt.xticks([])
    plt.yticks([])
    ax.ticklabel_format(style='plain')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()


# -


def get_cluster_bv(product, upstream):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    Utiliza los moran locales bivariados
    
    upstream = ['get', 'shape']
    '''
    # # Domicilios
    df = pandas.read_csv(str(upstream['get']))
    
    # # Capa (+ casos)
    shape = \
        geopandas.read_parquet(str(upstream['shape']))
    
    # # Pesos y geodataframes de trabajo
    # (solo los pesos, luego se calculan los Is Moran locales)
    weights_queen, _, _ = \
        spatial.get_spatials(
            shape,
            attribute='tasa_casos',
            strategy='queen'
        )

    # create addresses geodataframe:
    addresses_gdf = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(df.longitud, df.latitud),
        crs="EPSG:4326"
    )

    addresses_gdf = addresses_gdf.to_crs(shape.crs.to_string())

    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    south_america = geopandas.GeoSeries(
        [world[world.continent == 'South America'].unary_union],
        crs='epsg:4326'
    )
    LAT_LNG_PM = -65.030949, -42.769679
    working_area = Point(*LAT_LNG_PM)
    geopoint_madryn = geopandas.GeoSeries(
        [working_area],
        crs='epsg:4326'
    )

    # get lisa bivariate!:
    lisa_bv = esda.Moran_Local_BV(
        shape['nbi'].values,
        shape['tasa_casos'].values,
        weights_queen
    )

    # # Figura
    # clusters map:
    _, ax = spatial.plot_lisa_map(
        shape,
        lisa_bv,
        figure_title="Bivariate Moran Statistics: Cases of bronchiolitis and NBI\nPuerto Madryn, Chubut, Argentina"
    )

    # basemap:
    contextily.add_basemap(
        ax,
        source="/home/lmorales/work/pi-bronquiolitis-pipeline/input/basemaps_images/puerto_madryn.tif",
        crs=shape.crs.to_string()
    )

    # reference map_
    a = inset_axes(
        ax,
        width="35%", height='35%',
        loc='center right',
        bbox_to_anchor=(0.078,0,1,1),
        bbox_transform=ax.transAxes
    )

    # sudamerica
    south_america.plot(color='none', figsize=(20,20), ax=a)

    # puntito de madryn en sudamerica
    geopoint_madryn.plot(color='r', markersize=100, ax=a)

    contextily.add_basemap(
        a,
        source='/home/lmorales/work/pi-bronquiolitis-pipeline/input/basemaps_images/south_america_stamen_terrain_background.tif',
        crs=south_america.crs.to_string()
    )
    txt1 = a.text(
        x=geopoint_madryn.x,
        y=geopoint_madryn.y+(geopoint_madryn.y*0.15),
        s='Puerto Madryn',
        fontsize=9.8
    )
    txt1.set_path_effects([PathEffects.withStroke(linewidth=4, foreground='w')])

    # 'N' indicator:
    ax.text(x=3583380, y=5261700, s='N', fontsize=30)
    arrow_length = 300
    arrow_x = 3583500
    arrow_y = 5261600 - arrow_length
    ax.arrow(
        arrow_x, arrow_y,
        0, arrow_length,
        facecolor='k',
        length_includes_head=True,
        head_width=250,
        head_length=400,
        overhang=.1
    )

    # cases points
    addresses_gdf.plot(
        ax=ax,
        marker='o',
        color='k',
        alpha=0.25,
        markersize=10
    )

    plt.xticks([])
    plt.yticks([])
    ax.ticklabel_format(style='plain')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()

