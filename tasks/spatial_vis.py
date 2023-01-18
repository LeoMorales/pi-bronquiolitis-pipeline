# -*- coding: utf-8 -*-
# +
import pandas
import geopandas
from splot.esda import plot_moran, moran_scatterplot, plot_moran_bv
import matplotlib.pyplot as plt
from matplotlib import colors
from collections import Counter
import pickle
from surnames_package import spatial_vis

from matplotlib.patches import Patch
from IPython.display import Image
from collections import Counter
from bronchiolitis_package import maps_utils
from matplotlib.lines import Line2D

from bronchiolitis_package import spatial_utils

def __launch_moranplot_creation_task(
        aMoran, aLisa,
        LABEL_BY_QUADFILTER_DICT,
        COLOR_BY_LABELNAME_DICT,
        outputFilePath,
        useBivariate=False,
        xLabel='Bronchiolitis case rate',
        yLabel='Spatial lag of bronchiolitis case rate',
        
    ):
    """
    Returns:
        - png: Moran Plot
    """
    text_annotations = [
        {'s': 'HH', 'x': 3,'y': 1.5, 'fontsize': 35, 'alpha': .25, 'color': spatial_vis.HOT_COLOR},
        {'s': 'HL', 'x': 3,'y': -1.75, 'fontsize': 35, 'alpha': .25, 'color': spatial_vis.DIAMOND_COLOR},
        {'s': 'LH', 'x': -1.23,'y': 1.5, 'fontsize': 35, 'alpha': .25, 'color': spatial_vis.DONUT_COLOR},
        {'s': 'LL', 'x': -1.23,'y': -1.75, 'fontsize': 30, 'alpha': .25, 'color': spatial_vis.COLD_COLOR},
    ]
    
    # contar las cantidades por cada cluster
    quadfilter_bv = (aLisa.p_sim <= (.05)) * (aLisa.q)
    labels = [LABEL_BY_QUADFILTER_DICT[str(i)] for i in quadfilter_bv]
    label_colors = spatial_utils.get_colors_for_labels(
        labels, COLOR_BY_LABELNAME_DICT)
    spatial_vis.create_moranplot_figure(
        aMoran, aLisa,
        xlabel=xLabel,
        ylabel=yLabel,
        outputFile=outputFilePath,
        text_annotations=text_annotations,
        use_bivariate=useBivariate,
        ordered_label_colors=label_colors
    )


def get_moranplot(
        upstream, product,
        LABEL_BY_QUADFILTER_DICT, COLOR_BY_LABELNAME_DICT
    ):
    """ 
    Returns:
        - png: Moran Plot
    """
    moran_pickle_path = str(upstream['get-moran-and-lisa']['moran'])
    lisa_pickle_path = str(upstream['get-moran-and-lisa']['lisa'])
    with open(moran_pickle_path, "rb") as infile:
        moran = pickle.load(infile)
    with open(lisa_pickle_path, "rb") as infile:
        lisa = pickle.load(infile)
        
    __launch_moranplot_creation_task(
        aMoran=moran,
        aLisa=lisa,
        LABEL_BY_QUADFILTER_DICT=LABEL_BY_QUADFILTER_DICT,
        COLOR_BY_LABELNAME_DICT=COLOR_BY_LABELNAME_DICT,
        outputFilePath=str(product),
        useBivariate=False,
        xLabel='Bronchiolitis case rate',
        yLabel='Spatial lag of bronchiolitis case rate',   
    )


def get_moranplot_bivariate_nbi_bronchiolitis(
        upstream, product,
        LABEL_BY_QUADFILTER_DICT, COLOR_BY_LABELNAME_DICT
    ):
    """ 
    Returns:
        - png: Moran Plot
    """
    moran_pickle_path = str(upstream['get-moran-and-lisa-bivariate']['moran'])
    lisa_pickle_path = str(upstream['get-moran-and-lisa-bivariate']['lisa'])
    with open(moran_pickle_path, "rb") as infile:
        moran = pickle.load(infile)
    with open(lisa_pickle_path, "rb") as infile:
        lisa = pickle.load(infile)
        
    __launch_moranplot_creation_task(
        aMoran=moran,
        aLisa=lisa,
        LABEL_BY_QUADFILTER_DICT=LABEL_BY_QUADFILTER_DICT,
        COLOR_BY_LABELNAME_DICT=COLOR_BY_LABELNAME_DICT,
        outputFilePath=str(product),
        useBivariate=True,
        xLabel='UBN',
        yLabel='Spatial lag of bronchiolitis case rate',
    )

def get_moranplot_bivariate_bronchiolitis_nbi(
        upstream, product,
        LABEL_BY_QUADFILTER_DICT, COLOR_BY_LABELNAME_DICT
    ):
    """ 
    Returns:
        - png: Moran Plot
    """
    moran_pickle_path = str(upstream['get-moran-and-lisa-bivariate-reverse']['moran'])
    lisa_pickle_path = str(upstream['get-moran-and-lisa-bivariate-reverse']['lisa'])
    with open(moran_pickle_path, "rb") as infile:
        moran = pickle.load(infile)
    with open(lisa_pickle_path, "rb") as infile:
        lisa = pickle.load(infile)
        
    __launch_moranplot_creation_task(
        aMoran=moran,
        aLisa=lisa,
        LABEL_BY_QUADFILTER_DICT=LABEL_BY_QUADFILTER_DICT,
        COLOR_BY_LABELNAME_DICT=COLOR_BY_LABELNAME_DICT,
        outputFilePath=str(product),
        useBivariate=True,
        xLabel='bronchiolitis case rate',
        yLabel='Spatial lag of UBN',
    )

def __create_base_clustermap(aLisa, pm_tracts_shape, LABEL_BY_QUADFILTER_DICT):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # contar las cantidades por cada cluster
    MIN_SIGNIFICANCE_LEVEL = .05
    quadfilter = (aLisa.p_sim <= (MIN_SIGNIFICANCE_LEVEL)) * (aLisa.q)
    labels = [LABEL_BY_QUADFILTER_DICT[str(i)] for i in quadfilter]

    # add label column
    pm_tracts_shape['label'] = labels
    ordered_cols = ['toponimo_i', 'label', 'geometry']
    pm_tracts_shape = pm_tracts_shape[ordered_cols]

    # Figura
    tracts_palette, edge_palette = spatial_vis.get_palettes(
        pm_tracts_shape['label'],
        LABEL_BY_QUADFILTER_DICT
    )

    # paint a map:
    ax, pmarks_map = maps_utils.plot_puerto_madryn_tract_map(
        shape=pm_tracts_shape,
        paint_by_column="label",
        tracts_palette=tracts_palette,
        edge_palette=edge_palette
    )
    return ax, pmarks_map

def __add_cases_points(point_gdf, DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS, mapAx):
    # admission and readmissions points
    point_plot_args = {
        "marker": 'o',
        "color": 'k',
        "alpha": 0.6,
        "markersize": 15
    }

    if DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS:
        admissions_gdf = \
            point_gdf[~point_gdf['es_reinternacion']]
        readmissions_gdf = \
            point_gdf[point_gdf['es_reinternacion']]
        ax, pmarks_admission_points_a = maps_utils.add_points_to_ax(
            admissions_gdf, mapAx, point_plot_args, label_title="Cases")
        
        point_plot_args = {
            "marker": '^',
            "color": 'lime',
            "alpha": 0.6,
            "markersize": 85
        }

        ax, pmarks_admission_points_r = maps_utils.add_points_to_ax(
            readmissions_gdf, ax, point_plot_args, label_title="Readmissions")
        pmarks_admission_points = [
            *pmarks_admission_points_a,
            *pmarks_admission_points_r
        ]
    else:
        ax, pmarks_admission_points = maps_utils.add_points_to_ax(
            point_gdf,
            mapAx,
            point_plot_args,
            label_title="Cases")
        
        # highlighted_cases = point_gdf[point_gdf['hc'].isin(['144586', '144874', '145769', '143367'])]
        
        # # Cajitas de nombres de los departamentos:
        # props = dict(
        #     boxstyle='round',
        #     alpha=.4
        # )

        # for point in highlighted_cases.iterrows():
        #     ax.text(
        #         point[1]['geometry'].centroid.x,
        #         point[1]['geometry'].centroid.y,
        #         f"{point[1]['hc']} - {point[1]['edad']}",
        #         horizontalalignment='left',
        #         fontsize=9,
        #         bbox=props
        #     )

        # point_plot_args = {
        #     "marker": 'o',
        #     "color": 'limegreen',
        #     "alpha": 0.9,
        #     "markersize": 19
        # }

            
        # ax, pmarks_admission_points = maps_utils.add_points_to_ax(
        #     highlighted_cases,
        #     ax,
        #     point_plot_args,
        #     label_title="A veeeeer")

    return ax, pmarks_admission_points

def __launch_clustermap_creation_task(
        lisa, pm_tracts_shape, bronchiolitis_points_gdf,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    ):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    # 1. clustermap
    ax, pmarks_map = __create_base_clustermap(
        lisa,
        pm_tracts_shape,
        LABEL_BY_QUADFILTER_DICT
    )
        
    # 2. contextualize clustermap
    ax = maps_utils.annotate_map(
        ax,
        pm_tracts_shape.crs.to_string(),
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH
    )

    # 3. add cases points?
    pmarks_admission_points = []
    if PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP:
        ax, pmarks_admission_points = __add_cases_points(
            bronchiolitis_points_gdf,
            DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS,
            ax
        )
 
    # legend
    pmarks = [*pmarks_map, *pmarks_admission_points]
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        title='References:',
        handles=[*handles,*pmarks],
        loc='upper right',
        prop={'size': 12}
    )

    # last tweaks
    ax.ticklabel_format(style='plain')
    ax.axis('off')

    return ax

def create_clustermap_figure(
        product, upstream,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    ):
    ''' Genera la figura de HS, CS, y outliers + puntos de domicilios de las internaciones.
    
    upstream = ['get_bronchiolitis', 'shape']
    '''
    lisa_pickle_path = str(upstream['get-moran-and-lisa']['lisa'])
    with open(lisa_pickle_path, "rb") as infile:
        lisa = pickle.load(infile)
        
    # Casos (puntos)
    pm_tracts_shape = geopandas.read_parquet(
        upstream["cases-for-each-circuit"])
    bronchiolitis_points_gdf = geopandas.read_parquet(
        upstream['get_bronchiolitis_locations'])
    bronchiolitis_points_gdf = bronchiolitis_points_gdf.to_crs(
        pm_tracts_shape.crs.to_string())

    mainAx = __launch_clustermap_creation_task(
        lisa, pm_tracts_shape, bronchiolitis_points_gdf,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    )

    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()


def create_clustermap_figure_bivariate(
        product, upstream,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    ):
    '''
    '''
    lisa_pickle_path = str(upstream['get-moran-and-lisa-bivariate']['lisa'])
    with open(lisa_pickle_path, "rb") as infile:
        lisa = pickle.load(infile)

     # Casos (puntos)
    pm_tracts_shape = geopandas.read_parquet(
        upstream["cases-for-each-circuit"])
    bronchiolitis_points_gdf = geopandas.read_parquet(
        upstream['get_bronchiolitis_locations'])
    bronchiolitis_points_gdf = bronchiolitis_points_gdf.to_crs(
        pm_tracts_shape.crs.to_string())

    mainAx = __launch_clustermap_creation_task(
        lisa, pm_tracts_shape, bronchiolitis_points_gdf,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    )

    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()


def create_clustermap_figure_bivariate_brq_nbi(
        product, upstream,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    ):
    '''
    '''
    lisa_pickle_path = str(upstream['get-moran-and-lisa-bivariate-reverse']['lisa'])
    with open(lisa_pickle_path, "rb") as infile:
        lisa = pickle.load(infile)

     # Casos (puntos)
    pm_tracts_shape = geopandas.read_parquet(
        upstream["cases-for-each-circuit"])
    bronchiolitis_points_gdf = geopandas.read_parquet(
        upstream['get_bronchiolitis_locations'])
    bronchiolitis_points_gdf = bronchiolitis_points_gdf.to_crs(
        pm_tracts_shape.crs.to_string())

    mainAx = __launch_clustermap_creation_task(
        lisa, pm_tracts_shape, bronchiolitis_points_gdf,
        PUERTO_MADRYN_BASEMAP_TIF_PATH,
        SOUTH_AMERICA_BASEMAP_TIF_PATH,
        LABEL_BY_QUADFILTER_DICT,
        PAINT_BRONCHIOLITIS_LOCATIONS_IN_MAP,
        DIFFERENTIATE_ADMISSIONS_AND_READMISSIONS
    )

    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()
