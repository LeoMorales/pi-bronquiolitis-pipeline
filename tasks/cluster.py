# -*- coding: utf-8 -*-
# + tags=[]
import pandas
import geopandas
import matplotlib.patheffects as PathEffects
from matplotlib.patches import Patch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import Point
import contextily
import matplotlib.pyplot as plt
from IPython.display import Image
import esda
from collections import Counter
from bronchiolitis_package import spatial
from matplotlib.lines import Line2D


# -

def get_colors(labels):
    # clusters map:
    spot_labels = ['Not significant', 'Hot spot', 'Donut', 'Cold spot', 'Diamond']
    label_colors = ['lightgrey', 'red', 'cornflowerblue', 'blue', 'orange']
    edge_colors = ['white', '#db0c0c', '#96b6f0', '#050568', '#f0afa7']
    
    edge_palette = { label: color for label, color in zip(spot_labels, edge_colors) }
    labels_counter = Counter(labels)

    # 2. Crear un arreglo de colores
    NS_COLOR = '#bababa'
    HOT_COLOR = '#d7191c'
    DONUT_COLOR = '#abd9e9'
    COLD_COLOR = '#2c7bb6'
    DIAMOND_COLOR = '#fdae61'

    # arreglo que posicionalmente se corresponde si tuvieramos todas las categorias:
    cluster_colors = [
        NS_COLOR,
        HOT_COLOR,
        DONUT_COLOR,
        COLD_COLOR,
        DIAMOND_COLOR,    
    ]
    
    # 3. Remover aquellos colores que no se utilicen
    spot_labels_copy = spot_labels[:]
    if labels_counter.get('Donut', 0) == 0:
        cluster_colors.pop(cluster_colors.index(DONUT_COLOR))
        spot_labels_copy.pop(spot_labels_copy.index('Donut'))
        

    if labels_counter.get('Diamond', 0) == 0:
        cluster_colors.pop(cluster_colors.index(DIAMOND_COLOR))
        spot_labels_copy.pop(spot_labels_copy.index('Diamond'))

        
    tracts_palette = { label: color for label, color in zip(spot_labels_copy, label_colors) }   
    
    return tracts_palette, edge_palette


def contextualize_map(ax, shape_crs_string, PUERTO_MADRYN_BASEMAP_TIF_PATH, SOUTH_AMERICA_BASEMAP_TIF_PATH):
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

    # basemap:
    # crs=shape.crs.to_string()
    contextily.add_basemap(
        ax,
        source=PUERTO_MADRYN_BASEMAP_TIF_PATH,
        crs=shape_crs_string
    )

    # reference map_
    ref_ax = inset_axes(
        ax,
        width="35%", height='35%',
        loc='center right',
        bbox_to_anchor=(0.078,0,1,1),
        bbox_transform=ax.transAxes
    )

    # sudamerica
    south_america.plot(color='none', figsize=(20,20), ax=ref_ax)

    # puntito de madryn en sudamerica
    geopoint_madryn.plot(color='r', markersize=100, ax=ref_ax)

    contextily.add_basemap(
        ref_ax,
        source=SOUTH_AMERICA_BASEMAP_TIF_PATH,
        crs=south_america.crs.to_string()
    )
    txt1 = ref_ax.text(
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
    
    return ax


# + tags=[]
def get_cluster(product, upstream, PUERTO_MADRYN_BASEMAP_TIF_PATH, SOUTH_AMERICA_BASEMAP_TIF_PATH):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # Casos (puntos)
    df = pandas.read_csv(str(upstream['get_bronchiolitis']))

    # Capa (+ casos)
    shape = geopandas.read_parquet(str(upstream['shape']))
    
    # create addresses geodataframe:
    addresses_gdf = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(df.longitud, df.latitud),
        crs="EPSG:4326"
    )
    addresses_gdf = addresses_gdf.to_crs(shape.crs.to_string())


    # Figura
    tracts_palette, edge_palette = get_colors(shape.label)
    
    # Set up figure and axes
    f, ax = plt.subplots(figsize=(12, 12))

    pmarks = []
    for ctype, data in shape.groupby('label'):
        # Define the color for each group using the dictionary
        color = tracts_palette[ctype]
        
        edge_color = edge_palette[ctype]
        
        # Plot each group using the color defined above
        data.plot(
            color=color,
            ax=ax,
            label=ctype,
            edgecolor=edge_color
        )

        pmarks.append(Patch(facecolor=color, label="{} ({})".format(ctype, len(data))))

    figure_title="Moran Statistics: Cases of bronchiolitis\nPuerto Madryn, Chubut, Argentina"
    ax.set(title=figure_title)

    ax = contextualize_map(
        ax,
        shape.crs.to_string(),
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH
    )
    
    # admission points
    addresses_gdf[~addresses_gdf.es_reinternacion].plot(
        ax=ax,
        marker='o',
        color='k',
        alpha=0.5,
        markersize=10,
    )

    addresses_gdf[addresses_gdf.es_reinternacion].plot(
        ax=ax,
        marker='o',
        color='r',
        alpha=0.25,
        markersize=50,
    )
    pmarks.append(
        Line2D([0], [0], marker='o', color='none', label='Admission', markerfacecolor='grey', markersize=6, alpha=0.5))
    pmarks.append(
        Line2D([0], [0], marker='o', color='None', label='Readmission', markerfacecolor='red', markersize=8, alpha=0.25))

    # legend
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        title='References:',
        handles=[*handles,*pmarks],
        loc='upper right',
        prop={'size': 12}
    )
    
    plt.xticks([])
    plt.yticks([])
    ax.ticklabel_format(style='plain')
    ax.axis('off')
    #ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()


# + tags=[]
def get_cluster_(product, upstream):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # Casos (puntos)
    df = pandas.read_csv(str(upstream['get_bronchiolitis']))

    # Capa (+ casos)
    shape = \
        geopandas.read_parquet(str(upstream['shape']))
    
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
    tracts_palette, edge_palette = get_colors(shape.label)

    # Set up figure and axes
    f, ax = plt.subplots(figsize=(12, 12))

    pmarks = []
    for ctype, data in shape.groupby('label'):
        # Define the color for each group using the dictionary
        color = tracts_palette[ctype]
        
        edge_color = edge_palette[ctype]
        
        # Plot each group using the color defined above
        data.plot(
            color=color,
            ax=ax,
            label=ctype,
            edgecolor=edge_color
        )

        pmarks.append(
            Patch(
                facecolor=color,
                label="{} ({})".format(ctype, len(data))
            )
        )

    figure_title="Moran Statistics: Cases of bronchiolitis\nPuerto Madryn, Chubut, Argentina"

    ax.set(title=figure_title)
    ax.set_axis_off()
    

    # basemap:
    contextily.add_basemap(
        ax,
        source=PUERTO_MADRYN_BASEMAP_TIF_PATH,
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
        source=SOUTH_AMERICA_BASEMAP_TIF_PATH,
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
    addresses_gdf[~addresses_gdf.es_reinternacion].plot(
        ax=ax,
        marker='o',
        color='k',
        alpha=0.5,
        markersize=10,
    )

    addresses_gdf[addresses_gdf.es_reinternacion].plot(
        ax=ax,
        marker='o',
        color='r',
        alpha=0.25,
        markersize=50,
    )
    #pmarks.append(Patch(facecolor='grey',label="caso"))
    #pmarks.append(Patch(facecolor='red',label="reinternación"))
    pmarks.append(Line2D([0], [0], marker='o', color='k', label='Caso', markerfacecolor='grey', markersize=10))
    pmarks.append(Line2D([0], [0], marker='o', color='r', label='Reinternación', markerfacecolor='red', markersize=50))

    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        title='References',
        handles=[*handles,*pmarks],
        loc='upper right',
        prop={'size': 12}
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


def get_cluster_bv(product, upstream, PUERTO_MADRYN_BASEMAP_TIF_PATH, SOUTH_AMERICA_BASEMAP_TIF_PATH):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    Utiliza los moran locales bivariados
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # # Domicilios
    df = pandas.read_csv(str(upstream['get_bronchiolitis']))
    
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
        source=PUERTO_MADRYN_BASEMAP_TIF_PATH,
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
        source=SOUTH_AMERICA_BASEMAP_TIF_PATH,
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

