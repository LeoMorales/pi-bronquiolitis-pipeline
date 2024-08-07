# -*- coding: utf-8 -*-
# +
import pandas
import geopandas
import matplotlib.pyplot as plt
from matplotlib import colors
from collections import Counter
import pickle
from bronchiolitis_package import spatial

# -
def get_moran_and_lisa(upstream, product, MORAN_ATTR, WEIGHT_STRATEGY, WEIGHT_PARAM):
    pm_tracts = geopandas.read_parquet(
        upstream["cases-for-each-circuit"])
    
    #spatial_attrs = {
    #    'attribute': 'tasa_casos',
    #    'strategy': WEIGHT_STRATEGY,
    #    'k_neighbours': WEIGHT_PARAM,
    #    'use_moran_rate': True,
    #    'moran_rate_column': 'totalpobl'
    #}
    # 'tasa_casos'
    spatial_attrs = {
        'attribute': MORAN_ATTR,
        'strategy': WEIGHT_STRATEGY,
        'strategy_args': WEIGHT_PARAM,
    }
    
    # Pesos y geodataframes de trabajo
    weights, moran, lisa = spatial.get_spatials(
        pm_tracts, **spatial_attrs)

    # Serialization
    with open(str(product["weights"]), "wb") as outfile:
        pickle.dump(weights, outfile)
    with open(str(product["moran"]), "wb") as outfile:
        pickle.dump(moran, outfile)
    with open(str(product["lisa"]), "wb") as outfile:
        pickle.dump(lisa, outfile)


def get_moran_and_lisa_bivariate(upstream, product, MORAN_ATTR, BIVARIATE_MORAN_ATTR, WEIGHT_STRATEGY, WEIGHT_PARAM):
    # combine bronchiolitis and nbi data
    pm_tracts = geopandas.read_parquet(
        upstream["cases-for-each-circuit"])
    nbi_df = pandas.read_parquet(upstream["get_nbi"])
    pm_tracts = pandas.merge(
        pm_tracts,
        nbi_df,
        on='toponimo_i')
    
    spatial_attrs = {
        'attribute': MORAN_ATTR,
        'strategy': WEIGHT_STRATEGY,
        'strategy_args': WEIGHT_PARAM,
        'use_moran_bv': True,
        'moran_bv_column': BIVARIATE_MORAN_ATTR
    }
    
    # Pesos
    weights, moran, lisa = spatial.get_spatials(
        pm_tracts, **spatial_attrs)

    # Serialization
    with open(str(product["weights"]), "wb") as outfile:
        pickle.dump(weights, outfile)
    with open(str(product["moran"]), "wb") as outfile:
        pickle.dump(moran, outfile)
    with open(str(product["lisa"]), "wb") as outfile:
        pickle.dump(lisa, outfile)


def get_moran_and_lisa_bivariate_reverse(upstream, product, MORAN_ATTR, BIVARIATE_MORAN_ATTR, WEIGHT_STRATEGY, WEIGHT_PARAM):
    # combine bronchiolitis and nbi data
    pm_tracts = geopandas.read_parquet(
        upstream["cases-for-each-circuit"])
    nbi_df = pandas.read_parquet(upstream["get_nbi"])
    pm_tracts = pandas.merge(
        pm_tracts,
        nbi_df,
        on='toponimo_i')
    
    spatial_attrs = {
        'attribute': MORAN_ATTR,
        'strategy': WEIGHT_STRATEGY,
        'strategy_args': WEIGHT_PARAM,
        'use_moran_bv': True,
        'moran_bv_column': BIVARIATE_MORAN_ATTR
    }
    
    # Pesos
    weights, moran, lisa = spatial.get_spatials(
        pm_tracts, **spatial_attrs)

    # Serialization
    with open(str(product["weights"]), "wb") as outfile:
        pickle.dump(weights, outfile)
    with open(str(product["moran"]), "wb") as outfile:
        pickle.dump(moran, outfile)
    with open(str(product["lisa"]), "wb") as outfile:
        pickle.dump(lisa, outfile)
