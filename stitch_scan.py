#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Merge stitch scan reconstructions.
For more information, call this script with the help option:
    stitch_scan.py -h

"""

__author__ = ['Gianluca Iori']
__date_created__ = '2022-04-04'
__date__ = '2022-04-04'
__copyright__ = 'Copyright (c) 2022, JC|MSK'
__docformat__ = 'restructuredtext en'
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = 'Gianluca Iori'
__email__ = "gianthk.iori@gmail.com"

import os
import argparse
import logging
from tqdm import tqdm
import textwrap
import numpy as np

#################################################################################

def main():
    description = textwrap.dedent('''\
                Merge stitch scan reconstructions.
                ''')
    epilog = textwrap.dedent('''\
                EXAMPLES:
                * Merge stitch scan reconstructions:

                    stitch_scan.py "/media/gianthk/My Passport/20217193_Traviglia/recons/581681_punta_HR_stitch2_Z0.0mm_corr_phrt_EL/slices/slice_0000.tif"
                    "/media/gianthk/My Passport/20217193_Traviglia/recons/581681_punta_HR_stitch2_Z0.0mm_corr_phrt_EL/slices_transform/slice_0000.tif"
                    -si 107 112
                    -so 30
                    --translate 20 20
                    --overwrite
                ''')

    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filein', type=str, help='<Required> Input filename(s) (voxel data).')
    parser.add_argument('fileout', type=str, help='<Required> Output filename (stitched voxel data). Slices numbers will be overwritten.')
    parser.add_argument('-si', '--slicesin', type=int, default=None, nargs='+', help='Slices to be stitched (first, last).')
    parser.add_argument('-so', '--sliceout', type=int, default=None, help='First slice number after stitching.')
    parser.add_argument('-a', '--affine', type=float, default=None, nargs='+', help='2D Affine transformation matrix components (a11, a12, atx, a21, a22, aty).')
    parser.add_argument('-t', '--translate', type=float, default=None, nargs='+', help='Translation (tx, ty) as array, list or tuple.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output.')
    parser.add_argument('--overwrite', dest='overwrite', action='store_true', help='Overwrite existing files.')
    parser.set_defaults(verbose=False, overwrite=False)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # filename base
    # [fileout_base, type] = os.path.splitext(args.fileout)

    # create list of all file names contained in given folder
    stack_files = [os.path.join(os.path.dirname(args.filein), f) for f in
                   os.listdir(os.path.dirname(args.filein)) if os.path.isfile(os.path.join(os.path.dirname(args.filein), f))]
    stack_files.sort()

    # list of slices IDs
    slice_ids = [int(filename[-8:-4]) for filename in stack_files]

    # ID of the first slice to process
    slices_in_id = slice_ids.index(args.slicesin[0])

    # create list of output slice file names
    stack_files_out = [args.fileout[:-8] + str(args.sliceout + f).zfill(4) + '.tif' for f in
                       range(0, len(stack_files[slices_in_id:(slices_in_id + args.slicesin[1] - args.slicesin[0] + 1):1]))]

    # check if any of the output files already exist
    if any(os.path.exists(d) for d in stack_files_out):
        if args.overwrite:
            logging.warning('Files already exist and will be overwritten!')
        else:
            raise IOError('Files already exist. Run the code with --overwrite True.')

    # prepare transformation matrix
    if any(transformation != None for transformation in [args.affine, args.translate]):
        from skimage import transform

        if args.affine != None:
            if args.translate != None:
                logging.warning('Affine transformation given.. Translate input is ignored!')
            tform = transform.AffineTransform(matrix=np.array([[args.affine[0], args.affine[1], args.affine[2]],
                                                               [args.affine[3], args.affine[4], args.affine[5]],
                                                               [0, 0, 1]]))
        else:
            tform = transform.AffineTransform(translation=args.translate)

        tform_inverse = tform.inverse
        logging.info('Affine transformation with matrix:')
        logging.info(tform.params)

    # transform and write stack of slices with stitched slice IDs
    count = 0
    if any(transformation != None for transformation in [args.affine, args.translate]):
        import tifffile
        for filename in tqdm(stack_files[slices_in_id:(slices_in_id + args.slicesin[1] - args.slicesin[0] + 1):1]):
            data = tifffile.imread(filename)
            tf_data = transform.warp(data, tform_inverse)
            tifffile.imwrite(stack_files_out[count], tf_data)
            count = count + 1
    else:
        import shutil
        for filename in stack_files[slices_in_id:(slices_in_id + args.slicesin[1] - args.slicesin[0] + 1):1]:
            shutil.copy(filename, stack_files_out[count])
            count = count + 1

    return

if __name__ == '__main__':
    main()


