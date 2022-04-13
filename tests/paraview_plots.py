#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate plots of 3D data with Paraview.
For more information, call this script with the help option:
    paraview_plots.py -h

"""

__author__ = ['Gianluca Iori']
__date_created__ = '2022-03-04'
__date__ = '2022-03-04'
__copyright__ = 'Copyright (c) 2021, JC|MSK'
__docformat__ = 'restructuredtext en'
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = 'Gianluca Iori'
__email__ = "gianthk.iori@gmail.com"

import os
import argparse
import logging
import textwrap
import numpy as np
from paraview.simple import *
import meshio
from skimage.filters import gaussian
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
                Generate plots of 3D data with Paraview.
                https://www.paraview.org/
                ''')
    epilog = textwrap.dedent('''\
                EXAMPLES:

                * Generate screenshot of volume data.
                    paraview_plots.py test_data/test_bbox/trab_0000.tif pippo.png
                    paraview_plots.py /home/gianthk/Data/BEATS/Franceschin/tomolab/tomo_Rec_crop/tomo_rec0000.tif
                ''')

    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filein', type=str, help='<Required> Input filename (3D data).')
    parser.add_argument('-o', '--fileout', type=str, default=None, help='Output filename.')
    # parser.add_argument('-vs', '--voxelsize', type=float, default=[1., 1., 1.], nargs='+', help='Voxel size.')
    # parser.add_argument('-r', '--resampling', type=float, default=1., help='Resampling factor.')
    # parser.add_argument('-t', '--threshold', type=int, default=None, help='Threshold value.')
    # parser.add_argument('-s', '--smooth', type=float, nargs='?', const=1., default=0.,
    #                     help='Smooth image with gaussian filter of given Sigma before thresholding.')
    # parser.add_argument('--caps', type=int, default=None,
    #                     help='Add caps of given thickness to the bottom and top of the model for mesh creation.')
    # parser.add_argument('--caps_val', type=int, default=0, help='Caps grey value.')
    # parser.add_argument('--shell_mesh', dest='shell_mesh', action='store_true',
    #                     help='Write VTK mesh of outer shell generated with PyMCubes.')
    # parser.add_argument('--vol_mesh', dest='vol_mesh', action='store_true',
    #                     help='Write VTK volume mesh of tetrahedra with pygalmesh.')
    # parser.add_argument('--max_facet_distance', type=float, default=None, help='CGAL mesh parameter.')
    # parser.add_argument('--max_cell_circumradius', type=float, default=None, help='CGAL mesh parameter.')
    # parser.add_argument('--voxelfe', dest='voxelfe', action='store_true', help='Write voxel FE model (.INP) file.')
    # parser.add_argument('--template', type=str, default=None,
    #                     help='<Required by --voxelfe> Abaqus analysis template file (.INP).')
    # parser.add_argument('-m', '--mapping', default=None, nargs='+',
    #                     help='Template file for material property mapping. If more than one property is given, each property filename must followed by the corresponding GV range.')
    # parser.add_argument('--tetrafe', dest='tetrafe', action='store_true',
    #                     help='Write linear tetrahedra FE model (.INP) file.')
    # parser.add_argument('--refnode', default=None, nargs='+',
    #                     help='Reference node input. Used for kinematic coupling of Boundary Conditions in the analysis template file.'
    #                          'The REF_NODE coordinates [x,y,z] can be given. Alternatively use one of the following args [X0, X1, Y0, Y1, Z0, Z1] to generate a REF_NODE at a model boundary.')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output.')
    # parser.set_defaults(shell_mesh=False, vol_mesh=False, voxelfe=False, tetrafe=False, verbose=False)
    parser.set_defaults(verbose=False)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # filename base
    if args.fileout is None:
        [fileout_base, type] = os.path.splitext(args.filein)
        type = '.png'
    else:
        [fileout_base, type] = os.path.splitext(args.fileout)

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
