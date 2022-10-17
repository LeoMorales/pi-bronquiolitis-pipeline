# -*- coding: utf-8 -*-
# +
import pandas
import geopandas
from bronchiolitis_package import spatial
import esda
from splot.esda import plot_moran, moran_scatterplot, plot_moran_bv
import matplotlib.pyplot as plt

from matplotlib import colors
from collections import Counter


# -

def _get_moran_plot(
        moran, lisa, save_path,
        xlabel='Rate of cases of bronchiolitis',
        ylabel='Spatial lag of Rate of cases',
        label_colors=['#bababa', 'blue', 'yellow', 'orange', 'green'],
        use_plot_moran_bv=False,
        annotations={}
    ):
    """ Dibuja el gráfico de distribución de referencia + moran plot coloreado
    
    Utiliza splot.esda.plot_moran para el gráfico base.
    Utiliza splot.esda.moran_scatterplot para el gráfico Moran coloreado.
    """
    
    # dibujar la distribución (izq) junto al grafico de Moran (der)
    if use_plot_moran_bv:
        _, (ax_distribution, ax_scatterplot) = plot_moran_bv(moran, figsize=(10,4))
    else:
        _, (ax_distribution, ax_scatterplot) = plot_moran(moran, figsize=(10,4))
    
    # obtener los colores que participan en el scatterplot
    hmap = colors.ListedColormap(label_colors)
    args = {'cmap': hmap}

    # reemplazar el scatterplot sin colores por uno coloreado:
    f, ax = moran_scatterplot(
        lisa,
        p=0.05,
        ax=ax_scatterplot,
        scatter_kwds=args
    )

    # agregar los títulos a los dos graficos:
    ax_distribution.set_title("Reference\ndistribution")
    ax_scatterplot.set_title(f"Scatter plot\n Moran I: {moran.I:0.2f}")

    ax_scatterplot.set_xlabel(xlabel)
    ax_scatterplot.set_ylabel(ylabel)

    # anotar el scatterplot
    for annotation in annotations:
        ax_scatterplot.text(
            annotation['x_pos'],
            annotation['y_pos'],
            annotation['text'],
            fontsize=25
        )
        
    plt.tight_layout()
    plt.savefig(
        save_path,
        dpi=300
    )
    plt.close()


def __get_colors_for_labels(labels, color_by_labels):
    """Retorna un arreglo de colores para las etiquetas del análisis espacial.
    Existen casos en que no se presentan todas las categorías (por ejemplo no hay
    diamonds o donuts) por lo cual es necesario mantener un control con los colores
    para respetarlos en el scatter y en el mapa.
    """
    counter_dict = Counter(labels)
    painting_order = list(color_by_labels.keys())
    
    actual_labels = []
    while painting_order:
        label = painting_order.pop()
        if counter_dict[label] > 0:
            actual_labels.append(label)
    
    return [color_by_labels[label_key] for label_key in actual_labels]


def get_moranplot(upstream, product, LABEL_BY_QUADFILTER_DICT, COLOR_BY_LABELNAME_DICT, KNN_VALUE):
    """ Ejecuta el analisis espacial y guarda dos salidas:
        - etiquetas de cluster para cada circuito electoral y
        - el moranplot + distribución de referencia. 
    Ejecuta estas dos salidas porque aún no puedo guardar objetos en la tubería:
    Lo ideal sería guardar los objetos: Moran, LISA, Moran BV, LISA BV
    
    Se ejecutan las tareas rate y bivariada para agregar las columnas `label`y `label_bv`
    al mismo dataset de salida -> evaluar si esto es óptimo.

    Args:
        get_cases_for_each_circuit:
            Data columns (total 5 columns):
             #   Column      Non-Null Count  Dtype   
            ---  ------      --------------  -----   
             0   toponimo_i  86 non-null     string  
             1   casos       86 non-null     int64   
             2   totalpobl   86 non-null     float64 
             3   tasa_casos  86 non-null     float64 
             4   geometry    86 non-null     geometry
    
    Returns:
    
        - geopandas.Dataframe: con columnas `label`y `label_bv`
        - png: Moran Plot
        - png: Moran Plot Bi-variado
    
    """
    pm_tracts = geopandas.read_parquet(upstream["get_cases_for_each_circuit"])
    
    spatial_attrs = {
        'attribute': 'tasa_casos',
        'strategy': 'knn',
        'k_neighbours': KNN_VALUE,
        'use_moran_rate': True,
        'moran_rate_column': 'totalpobl'
    }
    # Pesos y geodataframes de trabajo
    weights, moran, lisa = spatial.get_spatials(pm_tracts, **spatial_attrs)

    # contar las cantidades por cada cluster
    MIN_SIGNIFICANCE_LEVEL = .05
    quadfilter = (lisa.p_sim <= (MIN_SIGNIFICANCE_LEVEL)) * (lisa.q)
    labels = [LABEL_BY_QUADFILTER_DICT[str(i)] for i in quadfilter]

    # add label column
    pm_tracts['label'] = labels

    ordered_cols = [
        'toponimo_i', 'label', 'geometry'
    ]
    pm_tracts = pm_tracts[ordered_cols]
    pm_tracts.to_parquet(
        str(product['cluster_labels']),
        index=False
    )
    
    label_colors = __get_colors_for_labels(labels, COLOR_BY_LABELNAME_DICT)
    annotations = [
        {'text': "HH", 'x_pos': 4, 'y_pos': 1.5},
        {'text': "HL", 'x_pos': 4, 'y_pos': -1.25},
        {'text': "LH", 'x_pos': -1.25, 'y_pos': 1.5},
        {'text': "LL", 'x_pos': -1.25, 'y_pos': -1.25},
    ]
    _get_moran_plot(
        moran, lisa, str(product['moranplot']),
        xlabel='Bronchiolitis case rate',
        ylabel='Spatial lag: Bronchiolitis case rate',
        label_colors=label_colors,
        annotations=annotations
    )


def get_moranplot_bv(upstream, product, LABEL_BY_QUADFILTER_DICT, COLOR_BY_LABELNAME_DICT, KNN_VALUE):
    """
    """
    pm_tracts = geopandas.read_parquet(upstream["get_cases_for_each_circuit"])
    
    # add nbi to shape:
    nbi_df = pandas.read_parquet(upstream["get_nbi"])
    pm_tracts = pandas.merge(
        pm_tracts,
        nbi_df,
        on='toponimo_i')

    spatial_attrs = {
        'attribute': 'nbi',
        'strategy': 'knn',
        'k_neighbours': KNN_VALUE,
        'use_moran_bv': True,
        'moran_bv_column': 'tasa_casos'
    }
    # bivariate analysis:
    weights, moran, lisa = spatial.get_spatials(pm_tracts, **spatial_attrs)

    # contar las cantidades por cada cluster
    quadfilter_bv = (lisa.p_sim <= (.05)) * (lisa.q)
    labels_bv = [LABEL_BY_QUADFILTER_DICT[str(i)] for i in quadfilter_bv]
    # add label column:
    pm_tracts['label'] = labels_bv

    ordered_cols = ['toponimo_i', 'label', 'geometry']
    pm_tracts = pm_tracts[ordered_cols]
    pm_tracts.to_parquet(
        str(product['cluster_labels']),
        index=False
    )
    
    annotations_bv = [
        {'text': "HH", 'x_pos': 3.5, 'y_pos': 1.5},
        {'text': "HL", 'x_pos': 3.5, 'y_pos': -1.25},
        {'text': "LH", 'x_pos': -1, 'y_pos': 1.5},
        {'text': "LL", 'x_pos': -1, 'y_pos': -1.25},
    ]
    label_colors_bv = __get_colors_for_labels(labels_bv, COLOR_BY_LABELNAME_DICT)
    _get_moran_plot(
        moran, lisa,
        str(product['moranplot']),
        xlabel='UBN',
        ylabel='Spatial lag: Bronchiolitis case rate',
        label_colors=label_colors_bv,
        use_plot_moran_bv=True,
        annotations=annotations_bv
    )


