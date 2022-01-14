# -*- coding: utf-8 -*-
# %load_ext autoreload
# %autoreload 2

"""
Report con los resultados obtenidos
"""
import os
import pdfkit

# + tags=["parameters"]
upstream = ['cluster', 'cluster_bv', 'moran', 'moran_bv']
product = None
# -




# # Reporte

# +
# HTML template to add our data and plots
figure_clusters_path = str(upstream['cluster'])
figure_clusters_bv_path = str(upstream['cluster_bv'])
figure_moran_path = str(upstream['moran'])
figure_moran_bv_path = str(upstream['moran_bv'])

report_template = f'''
<!DOCTYPE html>
    <html>
      <head>
        <meta charset='utf-8'>
        <title>Bronquiolitis report</title>
        <link rel='stylesheet' href='report.css'>
          <style>
          h1 {{
          font-family: Arial;
          font-size: 300%;
          }}
          h2 {{
          font-family: Arial;
          font-size: 200%;
          }}
          @page {{
              size: 7in 9.25in;
          margin: 27mm 16mm 27mm 16mm;
          }}
          </style>                       
      </head>
      <h1 align="center">Reporte: Bronquiolitis</h1>
      <h2 align="center">Tasa casos: Casos sobre cantidad de habitantes</h2>
      <figure>
        <img src="{figure_moran_path}" width="1000" height="400">
      </figure>
      <figure>
        <img src="{figure_clusters_path}" width="1000" height="900">
      </figure>
      <h2 align="center">Análisis bi-variado: Tasa casos vs Lag espacial de NBI</h2>
      <figure>
        <img src="{figure_moran_bv_path}" width="1000" height="400">
      </figure>
      <figure>
        <img src="{figure_clusters_bv_path}" width="1000" height="900">
      </figure>
  </html>
'''
# -


# Save HTML string to file
HTML_REPORT_DIR = "tmp_report.html"
with open(HTML_REPORT_DIR, "w") as r:
    r.write(report_template)
#Use pdfkit to create the pdf report from the 
pdfkit.from_file(
    HTML_REPORT_DIR,
     str(product['data'])
)
# remove the tmp data
os.remove(HTML_REPORT_DIR)
