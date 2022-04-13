#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate HTML report from .CSV master file.
For more information, call this script with the help option:
    generate_report.py -h

"""

__author__ = ['Gianluca Iori']
__date_created__ = '2022-04-13'
__date__ = '2022-04-13'
__copyright__ = 'Copyright (c) 2022, JC|MSK'
__docformat__ = 'restructuredtext en'
__license__ = "MIT"
__version__ = "0.1.0"
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

def plot_volume(data, fileout):
    """Write screenshot of volume view.
        Trace generated using paraview version 5.9.0-RC1

        Parameters
        ----------
        data
            Input Paraview data.
        fileout : str
            Output screenshot name.
        """

    #### disable automatic camera reset on 'Show'
    paraview.simple._DisableFirstRenderCameraReset()

    # create a new 'TIFF Series Reader'
    data.CustomDataSpacing = [0.005714285714285714, 0.005714285714285714, 0.005714285714285714]

    # get active view
    renderView1 = GetActiveViewOrCreate('RenderView')

    # show data in view
    tomo__rec0Display = Show(data, renderView1, 'UniformGridRepresentation')

    # trace defaults for the display properties.
    tomo__rec0Display.Representation = 'Outline'
    tomo__rec0Display.ColorArrayName = ['POINTS', '']
    tomo__rec0Display.SelectTCoordArray = 'None'
    tomo__rec0Display.SelectNormalArray = 'None'
    tomo__rec0Display.SelectTangentArray = 'None'
    tomo__rec0Display.OSPRayScaleArray = 'Tiff Scalars'
    tomo__rec0Display.OSPRayScaleFunction = 'PiecewiseFunction'
    tomo__rec0Display.SelectOrientationVectors = 'None'
    tomo__rec0Display.ScaleFactor = 0.5182857142857143
    tomo__rec0Display.SelectScaleArray = 'Tiff Scalars'
    tomo__rec0Display.GlyphType = 'Arrow'
    tomo__rec0Display.GlyphTableIndexArray = 'Tiff Scalars'
    tomo__rec0Display.GaussianRadius = 0.025914285714285716
    tomo__rec0Display.SetScaleArray = ['POINTS', 'Tiff Scalars']
    tomo__rec0Display.ScaleTransferFunction = 'PiecewiseFunction'
    tomo__rec0Display.OpacityArray = ['POINTS', 'Tiff Scalars']
    tomo__rec0Display.OpacityTransferFunction = 'PiecewiseFunction'
    tomo__rec0Display.DataAxesGrid = 'GridAxesRepresentation'
    tomo__rec0Display.PolarAxes = 'PolarAxesRepresentation'
    tomo__rec0Display.ScalarOpacityUnitDistance = 0.024627660161461194
    tomo__rec0Display.OpacityArrayName = ['POINTS', 'Tiff Scalars']
    # tomo__rec0Display.IsosurfaceValues = [22611.5]
    tomo__rec0Display.SliceFunction = 'Plane'
    # tomo__rec0Display.Slice = 149

    # init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
    # tomo__rec0Display.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 45223.0, 1.0, 0.5, 0.0]

    # init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
    # tomo__rec0Display.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 45223.0, 1.0, 0.5, 0.0]

    # init the 'Plane' selected for 'SliceFunction'
    # tomo__rec0Display.SliceFunction.Origin = [2.5914285714285716, 1.1914285714285715, 0.8542857142857143]

    # reset view to fit data
    renderView1.ResetCamera()

    # get the material library
    materialLibrary1 = GetMaterialLibrary()

    # update the view to ensure updated data information
    renderView1.Update()

    # set scalar coloring
    ColorBy(tomo__rec0Display, ('POINTS', 'Tiff Scalars'))

    # rescale color and/or opacity maps used to include current data range
    tomo__rec0Display.RescaleTransferFunctionToDataRange(True, True)

    # change representation type
    tomo__rec0Display.SetRepresentationType('Volume')

    # get color transfer function/color map for 'TiffScalars'
    tiffScalarsLUT = GetColorTransferFunction('TiffScalars')
    tiffScalarsLUT.ApplyPreset('Viridis (matplotlib)', True)

    # get opacity transfer function/opacity map for 'TiffScalars'
    tiffScalarsPWF = GetOpacityTransferFunction('TiffScalars')

    # reset view to fit data bounds
    # renderView1.ResetCamera(0.0, 5.182857142857143, 0.0, 2.382857142857143, 0.0, 1.7085714285714286)

    # Properties modified on renderView1
    renderView1.Background = [1.0, 1.0, 1.0]

    camera = GetActiveCamera()
    camera.Roll(-20)
    # camera.Pitch(-20)
    # camera.Azimuth(-20)
    camera.Elevation(-60)

    # save screenshot
    WriteImage(fileout)

def main():
    description = textwrap.dedent('''\
                Generate HTML report from .CSV master file.
                https://www.paraview.org/
                ''')
    epilog = textwrap.dedent('''\
                EXAMPLES:

                * Generate recon report
                    generate_report.py test_data/test_ciclope_flow_2.csv
                ''')

    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filein', type=str, help='<Required> Input master file (.CSV).')
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

    # HTML string
    html_string = '''
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
            ''' + summary_table_1 + '''
            <h2>Midplanes</h2>
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

    # write HTML report
    f = open(fileout_base + type, 'w')
    f.write(html_string)
    f.close()

    # set all empty cells to None
    df = df.where(pd.notnull(df), None)

    # flow = ciclope_flow()

    parameters = df[df['run'] == 1].to_dict('list')
    del parameters['run']


    # Read tiff stack #######################################################
    # search all files in parent folder; create filenames list
    tifffiles = [os.path.join(os.path.dirname(args.filein), f) for f in os.listdir(os.path.dirname(args.filein))
                 if os.path.isfile(os.path.join(os.path.dirname(args.filein), f))]
    tifffiles.sort()

    data = TIFFSeriesReader(registrationName='tomo__rec0*', FileNames=tifffiles)
    # data = TIFFSeriesReader(FileNames=args.filein, ReadAsImageStack=True)

    plot_volume(data, fileout_base + type)

if __name__ == '__main__':
    main()
