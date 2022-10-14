# -*- coding: utf-8 -*-
# + tags=[]
import pandas
import geopandas
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from IPython.display import Image
import esda
from collections import Counter
from bronchiolitis_package import spatial, maps_utils
from matplotlib.lines import Line2D


# -

def __get_colors(labels, spot_labels):
    # clusters map:
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
    donut_index = cluster_colors.index(DONUT_COLOR)
    donut_label_name = spot_labels[donut_index]
    if labels_counter.get(donut_label_name, 0) == 0:
        cluster_colors.pop(donut_index)
        spot_labels_copy.pop(donut_index)
        

    diamond_index = cluster_colors.index(DIAMOND_COLOR)
    diamond_label_name = spot_labels[diamond_index]
    if labels_counter.get(diamond_label_name, 0) == 0:
        cluster_colors.pop(diamond_index)
        spot_labels_copy.pop(diamond_index)

        
    tracts_palette = { label: color for label, color in zip(spot_labels_copy, label_colors) }   
    
    return tracts_palette, edge_palette


def __create_map(shape, paint_by_column, tracts_palette, edge_palette):
    """ Dibuja el mapa de cluster pintado según la etiqueta de cluster """
    # Set up figure and axes
    f, ax = plt.subplots(figsize=(12, 12))

    pmarks = []
    for ctype, data in shape.groupby(paint_by_column):
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
    return ax, pmarks

def __add_admission_points(admissions_gdf, readmissions_gdf, ax):
    """ Añade al mapa de clusters los puntos con los casos de bronquiolitis """
    admissions_gdf.plot(
        ax=ax,
        marker='o',
        color='k',
        alpha=0.5,
        markersize=10,
    )

    readmissions_gdf.plot(
        ax=ax,
        marker='o',
        color='r',
        alpha=0.25,
        markersize=50,
    )
    
    pmarks = []
    # agregar la leyenda de admisiones y readmisiones
    pmarks.append(
        Line2D([0], [0],
               marker='o',
               color='none',
               label=f'Admission ({len(admissions_gdf)})',
               markerfacecolor='grey',
               markersize=6,
               alpha=0.5)
    )
    pmarks.append(
        Line2D([0], [0],
               marker='o',
               color='None',
               label=f'Readmission ({len(readmissions_gdf)})',
               markerfacecolor='red',
               markersize=8,
               alpha=0.25)
    )

    return ax, pmarks

# + tags=[]
def get_cluster_figure(
        product, upstream,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP
    ):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # Casos (puntos)
    shape = geopandas.read_parquet(str(upstream['get_moranplot']['cluster_labels']))
    
    # Figura
    tracts_palette, edge_palette = __get_colors(
        shape.label,
        list(LABEL_BY_QUADFILTER_DICT.values()))

    # paint a map:
    pmarks = []
    ax, pmarks_map = __create_map(shape, "label", tracts_palette, edge_palette)

    ax = maps_utils.annotate_map(
        ax,
        shape.crs.to_string(),
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH
    )
    
    # admission and readmissions points
    pmarks_points = []
    if PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP:
        bronchiolitis_points_gdf = geopandas.read_parquet(upstream['get_bronchiolitis_locations'])
        bronchiolitis_points_gdf = bronchiolitis_points_gdf.to_crs(shape.crs.to_string())
        admissions_gdf = bronchiolitis_points_gdf[~bronchiolitis_points_gdf.es_reinternacion]
        readmissions_gdf = bronchiolitis_points_gdf[bronchiolitis_points_gdf.es_reinternacion]
        ax, pmarks_points = __add_admission_points(admissions_gdf, readmissions_gdf, ax)

    # legend
    pmarks = [*pmarks_map, *pmarks_points]
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        title='References:',
        handles=[*handles,*pmarks],
        loc='upper right',
        prop={'size': 12}
    )

    # last tweaks
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

def get_cluster_figure_bv(
        product, upstream,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP
    ):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    Utiliza los moran locales bivariados
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # # Capa (+ casos)
    shape = geopandas.read_parquet(str(upstream['get_moranplot_bv']['cluster_labels']))

    # # Figura
    tracts_palette, edge_palette = __get_colors(
        shape.label,
        list(LABEL_BY_QUADFILTER_DICT.values()))

    ax, pmarks_map = __create_map(shape, "label", tracts_palette, edge_palette)

    ax = maps_utils.annotate_map(
        ax,
        shape.crs.to_string(),
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH
    )

    # cases points
    pmarks_points = []
    if PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP:
        bronchiolitis_points_gdf = geopandas.read_parquet(str(upstream['get_bronchiolitis_locations']))
        bronchiolitis_points_gdf = bronchiolitis_points_gdf.to_crs(shape.crs.to_string())

        # admission and readmissions points
        admissions_gdf = bronchiolitis_points_gdf[~bronchiolitis_points_gdf.es_reinternacion]
        readmissions_gdf = bronchiolitis_points_gdf[bronchiolitis_points_gdf.es_reinternacion]
        ax, pmarks_points = __add_admission_points(admissions_gdf, readmissions_gdf, ax)

    
    # legend
    pmarks = [*pmarks_map, *pmarks_points]
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
    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()

