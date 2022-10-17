from bronchiolitis_package.report import Report

def create_report(product, upstream, KNN_VALUE):

    # instantiate report obj
    report = Report(
        title="Reporte: Bronquiolitis",
        subtitle="Puerto Madryn",
        experiment_params=[{
                'title': 'Tasas',
                'desc': 'Para este analisis las tasas fueron calculadas sobre la población indicada en el archivo de la capa de mapa',
                'value': 'radios_censales_puerto_madryn_epsg_22173.shp',
            },
            {
                'title': 'Vecinos cercanos',
                'desc': 'Para el análisis espacial se utilizaron',
                'value': f'{KNN_VALUE} vecinos mas cercanos',
            },
        ]
    )

    # add section:
    html_section = f'''
        <h2 align="left">Mapa de Necesidades Básicas Insatisfechas</h2>
        <h3 align="left">Estrategia KNN={KNN_VALUE}</h3>
    '''
    report.add_section(
        html_section,
        figure=str(upstream['get_nbi_map'])
    )

    # add section:
    html_section = f'''
        <h2 align="left">Tasa de casos sobre cantidad de habitantes</h2>
        <h3 align="left">Estrategia KNN={KNN_VALUE}</h3>
    '''
    report.add_section(
        html_section,
        figure=str(upstream['get_moranplot']['moranplot'])
    )
    report.add_section(
        '',
        figure=str(upstream['clustermap_figure'])
    )
    
    # add bivariate output
    html_section = f'''
        <h2 align="left">Análisis bi-variado: NBI vs Lag espacial de Tasa Casos</h2>
        <h3 align="left">Estrategia KNN={KNN_VALUE}</h3>
    '''
    report.add_section(
        html_section,
        figure=str(upstream['get_moranplot_bv']['moranplot'])
    )
    report.add_section(
        '',
        figure=str(upstream['clustermap_figure_bv'])
    )

    # save:
    report.build(str(product))