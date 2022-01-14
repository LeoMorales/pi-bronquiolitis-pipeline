# -*- coding: utf-8 -*-
# +
import geopandas
import matplotlib.pyplot as plt
from IPython.display import Image
from splot.esda import plot_moran
from splot.esda import moran_scatterplot

from splot.esda import plot_moran_bv
from splot.esda import moran_scatterplot
# -

from bronchiolitis_package import spatial


def get_moran(product, upstream):
    # # Capa (+ casos)
    shape = \
        geopandas.read_parquet(str(upstream['shape']))

    # # Pesos
    weights_queen, moran, lisa = \
        spatial.get_spatials(
            shape,
            attribute='tasa_casos',
            strategy='queen'
        )


    _, (ax_distribution, ax_scatterplot) = plot_moran(
        moran, figsize=(10,4))

    f, ax = moran_scatterplot(
        lisa,
        p=0.05,
        ax=ax_scatterplot)

    ax_distribution.set_title("Reference\ndistribution")
    ax_scatterplot.set_title(f"Scatter plot\n Moran I: {moran.I:0.2f}")

    ax_scatterplot.set_xlabel('Rate of cases of bronchiolitis')
    ax_scatterplot.set_ylabel('Spatial lag of Rate of cases')

    ax_scatterplot.text(4, 1.5, "HH", fontsize=25)
    ax_scatterplot.text(4, -1.25, "HL", fontsize=25)
    ax_scatterplot.text(-1.25, 1.5, "LH", fontsize=25)
    ax_scatterplot.text(-1.25, -1.25, "LL", fontsize=25)

    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()


def get_moran_bv(product, upstream):
    # # Capa (+ casos)
    shape = \
        geopandas.read_parquet(str(upstream['shape']))

    # # Pesos
    weights_queen, moran_bv, lisa_bv = \
        spatial.get_spatials(
            shape,
            attribute='tasa_casos',
            strategy='queen',
            use_moran_bv=True,
            moran_bv_column='totalpobl'
        )


    _, (ax_distribution, ax_scatterplot) = plot_moran_bv(
        moran_bv, figsize=(10,4))

    f, ax = moran_scatterplot(
        lisa_bv,
        p=0.05,
        ax=ax_scatterplot)

    ax_distribution.set_title("Reference\ndistribution")
    ax_scatterplot.set_title(f"Scatter plot\n Moran I: {moran_bv.I:0.2f}")

    ax_scatterplot.set_xlabel('Rate of cases of bronchiolitis')
    ax_scatterplot.set_ylabel('Spatial lag of UBN')

    ax_scatterplot.text(4, 1.5, "HH", fontsize=25)
    ax_scatterplot.text(4, -2, "HL", fontsize=25)
    ax_scatterplot.text(-1.5, 1.5, "LH", fontsize=25)
    ax_scatterplot.text(-1.5, -2, "LL", fontsize=25)

    plt.tight_layout()
    plt.savefig(
        str(product),
        dpi=300
    )
    plt.close()
