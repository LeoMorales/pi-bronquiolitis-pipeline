# -*- coding: utf-8 -*-
import pdfkit
import PIL
import datetime
import os


# CONSTANTS:
PDF_EXPORT_OPTIONS = {
    'page-size': 'Letter',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None,
    'footer-left': "Reporte generado: <report_timestamp>",
    'footer-line':'',
    'footer-font-size':'7',
    'footer-right': '[page] of [topage]'       
}

BR = '<div style="display:block; clear:both; page-break-after:always;"></div>'

IMGS_BASEWITH = 1000


class Report:
    ''' Usage:
    
    # instantiate report obj
    report = Report(
        "Title", "Subtitle regional analysis",
        [{
            param_title: 'Tasas',
            param_desc: 'Para este reporte las tasas fueron calculadas sobre:',
            param_value: '1000',
        }]
    )

    # add section:
    report.add_section(
        '<h2 align="center">Provincial view</h2>',
        'link/to/image/file.png')
    
    # add section with page break:
    report.add_section(
        '<h2 align="center">Country view</h2>',
        'link/to/image/file-too-large.png',
        finish_with_page_break=True
    )

    # save:
    report.build(path/to/pdf/destination.pdf)  # str(product)
    '''
    
    def __init__(self, title: str, subtitle: str, experiment_params: list):
        ''' 
        experiment_params = [
            {
                param_title: 'Tasas',
                param_desc: 'Para este reporte las tasas fueron calculadas sobre:',
                param_value: '1000',
            },
        ]
        '''
        self.title = title
        self.subtitle = subtitle
        self.experiment_params = experiment_params
        
        self.tmp_files = []
        self.content = ''
        self.params = self.get_html_params()

    def get_html_params(self):
        build_params = '<h3>Parámetros:</h3>'
        if len(self.experiment_params) == 0:
            build_params += '<p>---</p>'
        
        for param in self.experiment_params:
            build_params += f'''
                <p>{param["title"]}:</p>
                <ul><li>{param["desc"]}: {param["value"]}</li></ul>
            '''

        return build_params

    def add_section(self, text: str, figure: str = None, caption = '', finish_with_page_break = True) -> None:
        '''Agrega una sección al reporte.
        Puede contener una figura: parámetro `figure`.
        
        Args:
            text (str): Título/párrafo de la sección en formato html.
            figure (str): Ruta a una imagen.
            caption (str): Texto debajo de la imagen de la sección.
            finish_with_page_break (bool): Agregar o no un espacio luego de la sección.
            
        Returns:
            None
        '''

        # add section (title, fig, caption):
        
        # > title
        report_content = f"{text}"
        
        # > figure
        if figure:
            RESIZED_IMAGE_DIR, w, h = self.__resize_image(
                figure,
                basewidth=IMGS_BASEWITH
            )
            report_content += self.__get_fig_template(RESIZED_IMAGE_DIR, w, h)
            #report_content += BR
            self.tmp_files.append(f"{os.getcwd()}/{RESIZED_IMAGE_DIR}")
        
        # > caption
        report_content += caption
        
        if finish_with_page_break:
            report_content += BR
        
        self.content += report_content

    def get_report_text(self):
        return f'''
            <!DOCTYPE html>
                <html>
                    <head>
                        <meta charset='utf-8'>
                        <title>{self.title}</title>
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
                                size: 17in 20in;
                                margin: 27mm 16mm 27mm 16mm;
                            }}
                        </style>                       
                    </head>
                    <body>
                        <div style="margin-top:150px;">
                            <h1 align="center">{self.title}</h1>
                            <h2 align="center">{self.subtitle}</h2>
                            <br>
                            <br>
                            {self.params}
                        </div>
                        <div style="display:block; clear:both; page-break-after:always;"></div>
                        {self.content}
                    </body>
                </html>
            '''
    
    def build(self, destination):
        '''Genera el PDF con el contenido del reporte'''
        # destination = str(product)
        
        # set current time
        PDF_EXPORT_OPTIONS['footer-left'] = f"Reporte generado: {str(datetime.datetime.now())}"
        # Save HTML string to file
        HTML_REPORT_DIR = "tmp_report_years.html"

        with open(HTML_REPORT_DIR, "w") as r:
            r.write(self.get_report_text())

        #Use pdfkit to create the pdf report from the 
        pdfkit.from_file(
            HTML_REPORT_DIR,
            destination,
            options=PDF_EXPORT_OPTIONS
        ) 

        # remove the tmp data
        os.remove(HTML_REPORT_DIR)
        
        for tmp_file in self.tmp_files:
            print(f"removing {tmp_file}...")
            os.remove(tmp_file)

    def __resize_image(self, image_path, basewidth):
        input_image = PIL.Image.open(image_path)
        img_width, img_height = input_image.size

        wpercent = (basewidth / float(img_width))
        hsize = int((float(img_height) * float(wpercent)))
        img = input_image.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
        base_name = image_path.split('/')[-1].rstrip('.png')
        output_image_path = f'{base_name}_{datetime.datetime.now().isoformat()}.png'
        img.save(output_image_path)
        
        return output_image_path, basewidth, hsize

    def __get_fig_template(self, fig_src: str, width: int, height: int) -> str:
        return f'''
            <figure align="center">
                <img align="center" src="{fig_src}" width="{width}" height="{height}">
            </figure>
        '''  


