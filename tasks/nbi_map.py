# -*- coding: utf-8 -*-
# +
import pandas
import geopandas
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import contextily as ctx

from bronchiolitis_package import maps_utils
puerto_madryn_basemap_file = "/home/lmorales/work/pipelines/pi-bronquiolitis-pipeline/input-data/basemaps_images/puerto_madryn.tif"
south_america_basemap_file = '/home/lmorales/work/pipelines/pi-bronquiolitis-pipeline/input-data/basemaps_images/south_america_stamen_terrain_background.tif'


# + tags=[]
def get_nbi_clusters(upstream, product):
    """
    Asigna una etiqueta de cluster según el valor de nbi
    
    Returns:
    
        pandas.Dataframe
        
              toponimo_i    nbi     cluster
        0     321973        3.29   0 - 4,99%
        1     321976        8.23  5 - 14,99%
        2     319120        6.51  5 - 14,99%

    """
    nbi_df = pandas.read_parquet(upstream['get_nbi'])

    higher_25_mask = nbi_df.nbi > 25
    higher_15_mask = nbi_df.nbi > 15
    higher_5_mask = nbi_df.nbi > 5
    lower_5_mask = nbi_df.nbi < 5

    nbi_df.loc[higher_25_mask, 'cluster'] = "+ 25%"
    nbi_df.loc[higher_15_mask & ~higher_25_mask, 'cluster'] = "15 - 24,99%"
    nbi_df.loc[higher_5_mask & ~higher_15_mask, 'cluster'] = "5 - 14,99%"
    nbi_df.loc[lower_5_mask, 'cluster'] = "0 - 4,99%"

    nbi_df.to_parquet(str(product))


# -

def get_nbi_map(upstream, product):
    shape = geopandas.read_parquet(upstream["get_shape"])
    nbi_df = pandas.read_parquet(upstream['get_nbi_clusters'])
    
    nbi_shape = pandas.merge(shape, nbi_df, on="toponimo_i")
    
    ordered_category_labels = ['0 - 4,99%', '5 - 14,99%', '15 - 24,99%', '+ 25%']
    colors = ['white', 'yellow', 'orange', 'red']
    cluster_palette = { label: color for label, color in zip(ordered_category_labels, colors) }

    fig, ax = plt.subplots(figsize=(12, 12))
    pmarks = []
    data_n = { label: 0 for label in ordered_category_labels }

    for i, (ctype, cluster_slice) in enumerate(nbi_shape.groupby('cluster')):

        color=cluster_palette[ctype]

        # Plot each group using the color defined above
        cluster_slice.plot(
            color=color,
            ax=ax,
            label=ctype,
            alpha=.65,
            #edgecolor=edge_color
        )

        data_n[ctype] = len(cluster_slice)


    for ctype in ordered_category_labels:
        pmarks.append(
            Patch(
                facecolor=cluster_palette[ctype],
                label="{} ({})".format(ctype, data_n[ctype])
            )
        )

    nbi_shape.plot(
        color='none',
        edgecolor='grey',
        ax=ax
    )

    ctx.add_basemap(
        ax,
        source=puerto_madryn_basemap_file,
        crs=nbi_shape.crs.to_string()
    )

    ax = maps_utils.annotate_map(
        ax, nbi_shape.crs,
        puerto_madryn_basemap_file,
        south_america_basemap_file
    )
    
    
    bronchiolitis_points_gdf = geopandas.read_parquet(upstream['get_bronchiolitis_locations'])
    bronchiolitis_points_gdf = bronchiolitis_points_gdf.to_crs(shape.crs.to_string())
    admissions_gdf = bronchiolitis_points_gdf[~bronchiolitis_points_gdf.es_reinternacion]
    readmissions_gdf = bronchiolitis_points_gdf[bronchiolitis_points_gdf.es_reinternacion]
    
    point_plot_args = {
        "marker": 'o',
        "color": 'k',
        "alpha": 0.5,
        "markersize": 10
    }
    ax, pmarks_admission_points = maps_utils.add_points_to_ax(
        admissions_gdf, ax, point_plot_args, label_title="Admissions")

    point_plot_args = {
        "marker": 'o',
        "color": 'r',
        "alpha": 0.25,
        "markersize": 50
    }
    ax, pmarks_readmission_points = maps_utils.add_points_to_ax(
        readmissions_gdf, ax, point_plot_args, label_title="Readmissions")

    pmarks = [*pmarks, *pmarks_admission_points, *pmarks_readmission_points]
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        title='Census Radios NBI 3 (2010)',
        handles=[*handles,*pmarks],
        loc='upper right',
        prop={'size': 12}
    )
    ax.set(title='Puerto Madryn NBI and bronchiolitis cases')
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()



