#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate HTML report from .CSV master file.
For more information, call this script with the help option:
    generate_report.py -h

"""

__author__ = ['Gianluca Iori']
__date_created__ = '2022-04-15'
__date__ = '2022-04-13'
__copyright__ = 'Copyright (c) 2022, JC|MSK'
__docformat__ = 'restructuredtext en'
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = 'Gianluca Iori'
__email__ = "gianthk.iori@gmail.com"

import os
import argparse
import logging
import textwrap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import recon_utils

#################################################################################

def read_report_template(filein):
    """Read HTML report template to string.

        Parameters
        ----------
        filein
            Input file (HTML).
        template : str
            HTML template string.
        """

    with open(filein, "r") as f:
        template = f.read()

    return template

def basic_report():
    """Return basic report HTML template."""
    return '''
        <html>
            <head>
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">
                <style>
                body{ margin:0 100; background:whitesmoke; }
                /* Three image containers (use 25% for four, and 50% for two, etc) */
                .column {
                  float: left;
                  width: 33.33%;
                  padding: 5px;
                }
                
                /* Clear floats after image containers */
                .row::after {
                  content: "";
                  clear: both;
                  display: table;
                } 
                </style>
            </head>
            <body>
                <h1>2014 technology and CPG stock prices</h1>
    
                <!-- *** Section 1 *** --->
                <h2>Section 1: Apple Inc. (AAPL) stock in 2014</h2>
                <p>Apple stock price rose steadily through 2014.</p>
    
                <!-- *** Section 2 *** --->
                <h2>Section 2: AAPL compared to other 2014 stocks</h2>
                <p>GE had the most predictable stock price in 2014. IBM had the highest mean stock price. \
        The red lines are kernel density estimations of each stock price - the peak of each red lines \
        corresponds to its mean stock price for 2014 on the x axis.</p>
                <h3>Summary table: 2014 stock statistics</h3>
                <!-- summary --->
                <h2>Midplanes</h2>
                <!-- midplanes --->
                <div class="row">
                  <div class="column">
                    <img src="/home/gianthk/Data/TOMCAT/Manfrini/1000_B_360_01_/cropped_rescale_025_00_XY.png" alt="XY" style="width:100%">
                  </div>
                  <div class="column">
                    <img src="/home/gianthk/Data/TOMCAT/Manfrini/1000_B_360_01_/cropped_rescale_025_00_XZ.png" alt="XZ" style="width:100%">
                  </div>
                  <div class="column">
                    <img src="/home/gianthk/Data/TOMCAT/Manfrini/1000_B_360_01_/cropped_rescale_025_00_YZ.png" alt="YZ" style="width:100%">
                  </div>
                </div> 
            </body>
        </html>'''

def midplanes_string(filein):
    """Generate 3x1 midplane images HTML string.

            Parameters
            ----------
            filein
                Input midplane image file.
            """
    name, type = os.path.splitext(filein)

    return '''
    <div class="row">
      <div class="column">
        <img src="''' + name[:-2]+"XY"+type + '''" alt="XY plane" style="width:100%">
      </div>
      <div class="column">
        <img src="''' + name[:-2]+"XZ"+type + '''" alt="XZ plane" style="width:100%">
      </div>
      <div class="column">
        <img src="''' + name[:-2]+"YZ"+type + '''" alt="YZ plane" style="width:100%">
      </div>
    </div>
    '''

def main():
    description = textwrap.dedent('''\
                Generate HTML report from .CSV master file.
                ''')
    epilog = textwrap.dedent('''\
                EXAMPLES:

                * Generate recon report
                    generate_report.py test_data/test_ciclope_flow_2.csv
                ''')

    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filein', type=str, help='<Required> Input master file (.CSV).')
    parser.add_argument('-t', '--template', type=str, default=None, help='Template report (.HTML file).')
    parser.add_argument('-o', '--fileout', type=str, default=None, help='Output (.HTML) filename.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output.')
    parser.set_defaults(verbose=False)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # filename base
    if args.fileout is None:
        [fileout_base, type] = os.path.splitext(args.filein)
        type = '.html'
    else:
        [fileout_base, type] = os.path.splitext(args.fileout)

    # load master table
    df = pd.read_csv(args.filein)

    # filter only rows selected for run
    df_selected = df[df['run'] == 1]

    # summary table
    # summary_table_1 = df_selected.describe()
    # summary_table_1 = summary_table_1.to_html().replace('<table border="1" class="dataframe">', '<table class="table table-striped">')  # use bootstrap styling
    summary_table_1 = df_selected.to_html().replace('<table border="1" class="dataframe">', '<table class="table table-striped">')  # use bootstrap styling

    # load template report string
    html_string = read_report_template(args.template)

    # insert report title
    html_string = html_string.replace("Title", os.path.splitext(os.path.basename(args.filein))[0])

    # insert summary table
    html_string = html_string.replace("<!-- summary --->", summary_table_1)

    # insert midplanes for each reconstructed sample
    html_string_midplanes = ""
    for index, row in df_selected.iterrows():
        # html_string_midplanes += '''<h4>''' + row['filein'] + '''</h4>'''
        html_string_midplanes += row.to_frame().transpose().to_html().replace('<table border="1" class="dataframe">', '<table class="table table-striped">')  # use bootstrap styling
        html_string_midplanes += midplanes_string(row['midplanes'])
        # html_string_midplanes += '''<hr style = "height:2px;border-width:0;color:gray;background-color:gray" >'''

    # for sample in df_selected.midplanes:
    #     html_string_midplanes += midplanes_string(sample)
    html_string = html_string.replace("<!-- midplanes --->", html_string_midplanes)

    # write HTML report
    f = open(fileout_base + type, 'w')
    f.write(html_string)
    f.close()

    # set all empty cells to None
    # df = df.where(pd.notnull(df), None)

if __name__ == '__main__':
    main()
