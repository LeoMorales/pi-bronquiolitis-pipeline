# -*- coding: utf-8 -*-
from splot.esda import plot_moran
from splot.esda import moran_scatterplot
from splot.esda import lisa_cluster
from matplotlib import colors
from matplotlib.patches import Patch
import esda
from pysal.lib import weights
from splot.esda import moran_scatterplot, lisa_cluster
import contextily as ctx
import matplotlib.pyplot as plt
from collections import Counter

def get_spatials(
        shape, attribute,
        strategy='knn',
        k_neighbours=8,
        band_distance=500,
        use_moran_rate=False,
        moran_rate_column=None,
        use_moran_bv=False,
        moran_bv_column=None
    ):
    """
    Retona weights, moran global y moran local.
    Args:
    - strategy (str): Estrategia para obtener los pesos.
        Valor en ['queen', 'rook', 'knn', 'distance_band']
    - k_neighbours (int, default=8): Cantidad de vecinos a considerar.
        Se tiene en cuenta solo si la estrategia es knn.
    - band_distance (int, default=500): Cantidad de unidades de distancia para especificar el radio de la vecindad.
        Se tiene en cuenta solo si la estrategia es distance_band.
        Según la capa, se debe interpretar la unidad de medida (kms, millas, grados).
    - use_moran_rate (bool, default=False): Indica si se debe considerar otra columa de la capa como columna de población
    - moran_rate_column (None or str, default=None): 
        Columna de población para calcular los I de Moran.

    Returns:
    - w (pysal.lib.weights): Pesos según la capa recibida.
    - moran (esda.moran.Moran): Global Moran object.
    - lisa (esda.moran.Moran_Local): Local Moran object.
    """
    weights_selection = {
        'queen': lambda shape, attr: weights.contiguity.Queen.from_dataframe(shape),
        'rook': lambda shape, attr: weights.contiguity.Rook.from_dataframe(shape),
        'knn': lambda shape, attr: weights.KNN.from_dataframe(shape, k=attr),
        'distance_band': lambda shape, attr: weights.DistanceBand.from_dataframe(shape, attr, silence_warnings=True)
    }
    # Create the spatial weights matrix
    strategy_args = None
    if strategy == 'knn':
        strategy_args = k_neighbours
    if strategy == 'distance_band':
        strategy_args = band_distance
    
    w = weights_selection[strategy](shape, strategy_args)
    # Row standardize the matrix
    w.transform = 'R'

    if use_moran_rate:
        assert moran_rate_column is not None
        moran = esda.moran.Moran_Rate(shape[attribute], shape[moran_rate_column], w)
    elif use_moran_bv:
        assert moran_bv_column is not None
        moran = esda.moran.Moran_BV(shape[attribute], shape[moran_bv_column], w)
    else:
        moran = esda.moran.Moran(shape[attribute], w)
    lisa = None
    if not w.islands:
        if use_moran_rate:
            lisa = esda.Moran_Local_Rate(shape[attribute], shape[moran_rate_column], w)
        elif use_moran_bv:
            lisa = esda.Moran_Local_BV(shape[attribute], shape[moran_bv_column], w)
        else:
            lisa = esda.Moran_Local(shape[attribute], w)

    return w, moran, lisa


def plot_lisa_map(
        data_map,
        moran_local,
        figure_title='Hotspots / Coldspots / Outliers',
        ax=None,
        legend_title='LISA Cluster Map'
    ):
    ''' Crea el mapa de clusters.
    
    quadfilter = \
        (moran_local.p_sim <= (.05)) * (moran_local.q)
    
    # Create a dictionary where you assign each attribute value to a particular color
    spot_labels = ['Not significant', 'Hot spot', 'Donut', 'Cold spot', 'Diamond']
    label_colors = ['lightgrey', 'red', 'cornflowerblue', 'blue', 'orange']
    edge_colors = ['white', '#db0c0c', '#96b6f0', '#050568', '#f0afa7']

    tracts_palette = { label: color for label, color in zip(spot_labels, label_colors) }
    edge_palette = { label: color for label, color in zip(spot_labels, edge_colors) }

    labels = [spot_labels[i] for i in quadfilter]
    '''
    # 1. Contar las cantidades por cada cluster
    quadfilter = \
            (moran_local.p_sim <= (.05)) * (moran_local.q)
    spot_labels = ['Not significant', 'Hot spot', 'Donut', 'Cold spot', 'Diamond']
    
    label_colors = ['lightgrey', 'red', 'cornflowerblue', 'blue', 'orange']
    edge_colors = ['white', '#db0c0c', '#96b6f0', '#050568', '#f0afa7']
    edge_palette = { label: color for label, color in zip(spot_labels, edge_colors) }

    labels = [spot_labels[i] for i in quadfilter]
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

    if not ax:
        # Set up figure and axes
        f, ax = plt.subplots(figsize=(12, 12))

    pmarks = []
    for ctype, data in data_map.assign(cl=labels).groupby('cl'):
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

    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        title=legend_title,
        handles=[*handles,*pmarks],
        loc='upper right',
        prop={'size': 12}
    )
    ax.set(title=figure_title)
    ax.set_axis_off()
    return f, ax


def plot_hot_cold_and_outliers(
    moran_local, shape_vis,
    ax=None,
    plot_title="Hot/Cold spots y outliers para la Región",
    legend_bbox_to_anchor=(0.5, 0.1, 1., 1.),
    x_margin=0,
    y_margin=0
    ):
    '''
    Dibuja un mapa identificando hotspots, coldspots, doughnut y diamonds según cada I de Moran local y su significancia.
    
    Args:
    - legend_bbox_to_anchor (tuple).
        (0.5, 0.1, 1., 1.)
    '''

    sig = 1 * (moran_local.p_sim < 0.05)
    hotspot = 1 * (sig * moran_local.q==1)
    coldspot = 3 * (sig * moran_local.q==3)
    doughnut = 2 * (sig * moran_local.q==2)
    diamond = 4 * (sig * moran_local.q==4)
    spots = hotspot + coldspot + doughnut + diamond
    
    spot_labels = ['0 - Not significant', '1 - Hot spot', '2 - Doughnut', '3 - Cold spot', '4 - Diamond']
    labels = [spot_labels[i] for i in spots]
    colors_labels = ['lightgrey', 'red', 'lightblue', 'blue', 'pink']
    line_labels = [.05, 1, .5, 1, .5]

    # has axes?
    if not ax:
        # Set up figure and axes
        _, ax = plt.subplots(figsize=(8, 8))

    # Define colors and line widths
    roadPalette = {label: color for label, color in zip(spot_labels, colors_labels)}
    lineWidths = {label: width for label, width in zip(spot_labels, line_labels)}

    shape_vis = shape_vis.assign(cl=labels)
    pmarks = []
    for ctype, data in shape_vis.groupby('cl'):
        color = roadPalette[ctype]
        label = ctype

        data.plot(
            color=color,
            ax=ax,
            linewidth=lineWidths[ctype],
            label=label
        )
        pmarks.append(Patch(facecolor=color, label=label))
        
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        handles=[*handles,*pmarks],
        loc='lower right',
        bbox_to_anchor=legend_bbox_to_anchor
    )
    ax.set_aspect('equal')
    ax.margins(x_margin, y_margin) 
    if len(plot_title) > 0:
        ax.set_title(plot_title)
        ax.xaxis.tick_top()
    ax.set_axis_off()
    return ax


def plot_moran_significance(shape, moran_local, ax, bbox_to_anchor = (0., 0., 0.2, 1.)):
    '''
    Dibuja un mapa de significancia para cada I de Moran local perteneciente a un item del mapa shape.
    
    Args:
    - bbox_to_anchor: Posición de la leyenda.
        (a, b, c, d) ->
            c: posiciona en el eje horizontal;
            d: posiciona en el eje vertical.

    '''
    sig = 1 * (moran_local.p_sim < 0.05)
    hmap = colors.ListedColormap(['grey','black'])
    labels = ['non-sig.', 'significant'] 
    labels = [labels[i] for i in sig]
    shape\
        .assign(cl=labels)\
        .plot(
            column='cl',
            categorical=True,
            k=2,
            cmap=hmap,
            linewidth=0.1,
            ax=ax,
            edgecolor='white',
            legend=True
        )

    ax.set_aspect('equal')
    ax.set_title("I de Moran locales: Significatividad")
    ax.get_legend().set_bbox_to_anchor(bbox_to_anchor)
    ax.set_axis_off()


def plot_moran_quadrants(shape, moran_local, ax, bbox_to_anchor = (0., 0., 0.2, 1.)):
    '''
    Dibuja un mapa de cuadrante en el que cae cada I de Moran local perteneciente a un item del mapa shape.
    
    Args:
    - bbox_to_anchor: Posición de la leyenda.
        (a, b, c, d) ->
            c: posiciona en el eje horizontal;
            d: posiciona en el eje vertical.

    '''
    q_labels = ['Q1', 'Q2', 'Q3', 'Q4']
    labels = [q_labels[i-1] for i in moran_local.q]
    hmap = colors.ListedColormap([ 'red', 'lightblue', 'blue', 'pink'])
    shape\
        .assign(cl=labels)\
        .plot(
            column='cl',
            categorical=True,
            k=2,
            cmap=hmap,
            linewidth=0.1,
            ax=ax,
            edgecolor='white',
            legend=True
        )

    ax.set_aspect('equal')
    ax.set_title("I de Moran locales: Cuadrantes")
    ax.get_legend().set_bbox_to_anchor(bbox_to_anchor)
    ax.set_axis_off()


def plot_choropleth(shape, column_var, ax, plot_title="Plot", bbox_to_anchor = (0., 0., 0.2, 1.)):
    '''
    Dibuja un mapa pintado por una columna.
    
    Args:
    - bbox_to_anchor: Posición de la leyenda.
        (a, b, c, d) ->
            c: posiciona en el eje horizontal;
            d: posiciona en el eje vertical.

    '''
    shape.plot(
        column=column_var,
        cmap='viridis',
        scheme='quantiles',
        k=5,
        edgecolor='white',
        linewidth=0.1,
        alpha=0.75,
        legend=True,
        ax=ax
    )
    ax.set_aspect('equal')
    ax.set_title(plot_title)
    # Adjust legend location
    ax.get_legend().set_bbox_to_anchor(bbox_to_anchor)
    ax.set_axis_off()


def plot_moran_global_and_local(moran_global, moran_local, shape, var_name='Indicator'):
    '''
    Dibuja el resumen de los indicadores I de Moran global y los locales.
    '''
    fig1, (ax1_A, ax1_B) = plot_moran(moran_global, zstandard=True, figsize=(14, 4))
    ax1_B.set_xlabel(var_name)

    fig2, (ax2_A, ax2_B) = plt.subplots(1, 2, figsize=(12, 5))
    moran_scatterplot(moran_local, p=0.05, ax=ax2_A)
    ax2_A.set_xlabel(var_name)
    ax2_A.set_ylabel(f'Spatial Lag del {var_name}')

    #lisa_cluster(lisa, shape_patagonia, p=0.05, ax=ax2)
    #plot_hot_cold_and_outliers(moran_local, shape.copy(), ax2_B)
    plot_lisa_map(shape, moran_local, ax=ax2_B)
    # Get the bounding box of the original legend
    bb = ax2_B.get_legend().get_bbox_to_anchor().transformed(ax2_B.transAxes.inverted())

    # Change to location of the legend. 
    xy_offset = .95
    bb.x0 += xy_offset
    bb.x1 += xy_offset
    xy_offset -= .45
    bb.y0 -= xy_offset 
    bb.y1 -= xy_offset
    ax2_B.get_legend().set_bbox_to_anchor(bb, transform = ax2_B.transAxes)
    ax2_B.set_title(f"Hotspots / Coldspots / Outliers: {var_name} labels")


    plt.tight_layout()
    plt.show()


def plot_local_moran_maps(shape, lisa, fig_title='Regional'):
    '''
    Dibuja 4 mapas:
        - Mapa pintado por el valor del I de Morán Local.
        - Cuadrantes para cada I de Moran Local.
        - Significatividad para cada I de Moran Local.
        - Hot spots, cold spots y outliers espaciales.
    '''
    shape_vis = shape.copy()
    shape_vis['Is'] = lisa.Is
    
    # Set up figure and axes
    f, axs = plt.subplots(nrows=2, ncols=2, figsize=(12, 12))
    # Make the axes accessible with single indexing
    axs = axs.flatten()

    # Subplot 1 #
    plot_choropleth(shape_vis, 'Is', axs[0], plot_title="I de Moran locales")
    # Subplot 2 #
    plot_moran_quadrants(shape_vis, lisa, axs[1])
    # Subplot 3 #
    plot_moran_significance(shape_vis, lisa, axs[2])
                                
    # Subplot 4 #
    plot_hot_cold_and_outliers(lisa, shape_vis, axs[3])
    
    # Display the figure
    f.suptitle(fig_title, fontsize=14)
    plt.show()


def plot_neighborhood(shape, highlighted_ids, w,
                      attr='department_id',
                      ax=None,
                      plot_title="Alcance de la vecindad"):
    '''
    Dibuja el alcance de la vecindad considerada en los pesos `w` recibidos.
    
    Args:
    - shape (geopandas.geodataframe.GeoDataFrame)
    - highlighted_ids (str or list): Id del item resaltado.
    - w (pysal.lib.weights.distance.KNN): Pesos.
    
    Returns:
    - ax (matplotlib.axes._subplots.AxesSubplot): Retorna los ejes para seguir personalizando el dibujo.
    '''
    # obtener el eje si no se recibió por parámetro
    if not ax:
        _, ax = plt.subplots(figsize=(12, 12), constrained_layout=True)

    if not isinstance(highlighted_ids, list):
        highlighted_ids = [highlighted_ids]

    shape.plot(ax=ax, facecolor='k', linewidth=0.1)

    for highlighted_id in highlighted_ids:
        focus_id = shape.loc[shape[attr] == highlighted_id].index[0]
        focus = shape.loc[[focus_id], ['geometry']]
        # highlighted in red:
        focus.plot(facecolor='red', alpha=1, linewidth=0, ax=ax)
        # neighborhood in green:
        neighborhood = shape.loc[w[focus_id], :]
        neighborhood.plot(ax=ax, facecolor='lime', linewidth=0)

    ax.set_axis_off()
    ax.set_title(plot_title)
    
    return ax


# TODO: BORRAR. Esta funcion de dibujado tenia que ver para comparar analisis espaciales rate vs no rate.
# y lo usé con los orígenes.
# new since origin analysis:
def plot_moran_clusters(
    region_shape,
    moran, moran_rate,
    lisa, lisa_rate,
    region_name_subtitle='Region',
    var_label='Origin_name',
    legend_x_offset=.39,
    annotation_y_offset=0.1,
    moran_rate_column='total_population',
    figsize=(18, 9),
    only_save_figure=False,
    figure_name='',
    ):
    """
    Dibuja dos mapas de clusters hotspots+coldspots+outliers:
    A la izquierda el mapa de clusters considerando solo los valores de la variable cantidad de personas para un origen de apellidos.
    A la derecha el mapa similar, solo que considerando una columna de total de población para utilizar como tasa.
    Anota cada mapa con el valor del indicador de Moran global.
    
    Si se especifica "solo guardar la figura" (`only_save_figure=True`),
    se guarda la figura con el `figure_name` especificado y no se retornan los ejes (par de elementos vacíos).
    """
    # Set up figure and axes
    f, axs = plt.subplots(nrows=1, ncols=2, figsize=figsize, constrained_layout=True)
    # Make the axes accessible with single indexing
    axs = axs.flatten()

    #########
    ax_one = axs[0]
    plot_lisa_map(region_shape, lisa, ax=ax_one)

    # change to location of the legend. 
    # -> get the bounding box of the original legend
    bb = (
        ax_one
            .get_legend()
            .get_bbox_to_anchor()
            .transformed(ax_one.transAxes.inverted())
    )
    xOffset = legend_x_offset
    bb.x0 += xOffset
    bb.x1 += xOffset
    yOffset = .5
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    # -> move the legend
    ax_one\
        .get_legend()\
        .set_bbox_to_anchor(
            bb, transform=ax_one.transAxes
        )

    # set title
    ax_one.set_title(
        f"Hotspots / Coldspots / Outliers (Moran)\n{region_name_subtitle}\nLabel: {var_label}",
        fontdict=dict(fontsize=18)
    )

    # write Global Moran I info
    y_min, y_max = ax_one.get_ylim()
    _, x_max = ax_one.get_xlim()
    ax_one.text(
        x_max,
        y_min-((y_min-y_max)*annotation_y_offset),
        f"Global Moran I: {moran.I:0.2f}\np-value: {moran.p_sim}",
        backgroundcolor='#ffff0045' if (moran.p_sim < 0.05) else 'white',
        fontsize='x-large' if (moran.p_sim < 0.05) else 'medium',
        fontweight='demibold' if (moran.p_sim < 0.05) else 'normal',
    )

    ##########
    ax_two = axs[1]
    plot_lisa_map(region_shape, lisa_rate, ax=ax_two)

    # change to location of the legend. 
    # -> get the bounding box of the original legend
    bb = (
        ax_two
            .get_legend()
            .get_bbox_to_anchor()
            .transformed(ax_two.transAxes.inverted())
    )
    bb.x0 += xOffset
    bb.x1 += xOffset
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    # -> move the legend
    ax_two\
        .get_legend()\
        .set_bbox_to_anchor(
            bb, transform=ax_two.transAxes
        )

    # set the title
    ax_two.set_title(
        f"Hotspots / Coldspots / Outliers (Moran Rate)\n{region_name_subtitle}\nLabel: {var_label}",
        fontdict=dict(fontsize=18)
    )
    y_min, y_max = ax_two.get_ylim()
    _, x_max = ax_two.get_xlim()

    # write Global Moran I info
    ax_two.text(
        x_max,
        y_min-((y_min-y_max)*annotation_y_offset),
        f"Global Moran I: {moran_rate.I:0.2f}\np-value: {moran_rate.p_sim}",
        backgroundcolor='#ffff0045' if (moran_rate.p_sim < 0.05) else 'white',
        fontsize='x-large' if (moran_rate.p_sim < 0.05) else 'medium',
        fontweight='demibold' if (moran_rate.p_sim < 0.05) else 'normal',
    )
    
    if only_save_figure:
        plt.ioff()
        plt.savefig(figure_name)
        plt.close()
        
        return None, None
    
    return ax_one, ax_two
