import geopandas
from shapely.geometry import Point
import contextily
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.patheffects as PathEffects
from matplotlib.lines import Line2D
2


def annotate_map(
        ax, shape_crs_string,
        PUERTO_MADRYN_BASEMAP_TIF_PATH=None,
        SOUTH_AMERICA_BASEMAP_TIF_PATH=None
    ):
    """ Agrega anotaciones al mapa:
        - Referencia de Puerto Madryn en América Latina
        - Flecha apuntando al norte
        - Capas base
    """
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
    if PUERTO_MADRYN_BASEMAP_TIF_PATH:
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

    if SOUTH_AMERICA_BASEMAP_TIF_PATH:
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
    ref_ax.set_xticks([])
    ref_ax.set_yticks([])
    return ax


def add_points_to_ax(point_gdf, ax, point_plot_args={}, label_title="Admissions"):
    """ Añade al mapa de clusters los puntos con los casos de bronquiolitis

    Args:
        point_plot_args (dict):
            Atributos:
                - "marker": 'o',
                - "color": 'r',
                - "alpha": 0.25,
                - "markersize": 50
        
    """
    
    point_gdf.plot(
        ax=ax,
        **point_plot_args
    )
    
    pmarks = []
    # agregar la leyenda de admisiones y readmisiones
    pmarks.append(
        Line2D([0], [0],
               marker=point_plot_args['marker'],
               color='none',
               label=f'{label_title} ({len(point_gdf)})',
               markerfacecolor=point_plot_args['color'],
               markersize=(point_plot_args['markersize']/10) * (2 - (2*(point_plot_args['markersize']/10)/100)),
               alpha=point_plot_args['alpha'])
    )

    return ax, pmarks

