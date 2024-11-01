#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Computed tomography image processing utilities.

"""

__author__ = "Gianluca Iori"
__date_created__ = "2021-03-28"
__date__ = "2024-10-28"
__copyright__ = "Copyright (c) 2024, SESAME"
__docformat__ = "restructuredtext en"
__license__ = "MIT"
__version__ = "1.4"
__maintainer__ = "Gianluca Iori"
__email__ = "gianthk.iori@gmail.com"

import numpy as np
import png
import os
import re
import logging
import matplotlib.pyplot as plt

try:
    import dxchange
except ImportError:
    logging.debug("dxchange failed to import", exc_info=True)

try:
    import tifffile
except ImportError:
    logging.debug("tifffile failed to import", exc_info=True)

try:
    import glymur
except ImportError:
    logging.debug("glymur failed to import", exc_info=True)


def average_sinogram_by_interval(
    _projs, slicer=1, remove_last_n_to_make_suited_size_for_reshape="auto"
):
    """
    remove_last_n_to_make_suited_size_for_reshape can be an index or string: None, auto
    """
    if remove_last_n_to_make_suited_size_for_reshape == "auto":
        # implement the calculation of a proper last index
        modulo = _projs.shape[0] % slicer
        if modulo != 0:
            remove_last_n_to_make_suited_size_for_reshape = -modulo

    if isinstance(remove_last_n_to_make_suited_size_for_reshape, int):
        _projs = _projs[:remove_last_n_to_make_suited_size_for_reshape, :, :]

    shape_projs = _projs.shape

    shape_projs_reduced = (
        shape_projs[0] // slicer,
        slicer,
        shape_projs[1],
        shape_projs[2],
    )

    array_reduced_by_averaging = _projs.reshape(shape_projs_reduced).astype(np.float32)
    array_reduced_by_averaging = array_reduced_by_averaging.mean(axis=1)

    array_reduced_by_averaging = array_reduced_by_averaging.astype(np.uint16)

    return array_reduced_by_averaging


def touint(
    data_3D,
    dtype="uint8",
    data_range=None,
    quantiles=None,
    numexpr=True,
    subset=True,
    nchunk=None,
):
    """Normalize and convert data to unsigned integer.

    Parameters
    ----------
    data_3D
        Input data.
    dtype
        Output data type ('uint8' or 'uint16').
    data_range : [float, float]
        Control range for data normalization.
    quantiles : [float, float]
        Define data range for data normalization through input data quantiles. If data_range is given this input is ignored.
    numexpr : bool
        Use fast numerical expression evaluator for NumPy (memory expensive).
    subset : bool
        Use subset of the input data for quantile calculation.

    Returns
    -------
    output : uint
        Normalized data.
    """

    def convertfloat(data_3D):
        return (
            data_3D.astype(np.float32, copy=False),
            np.float32(data_max - data_min),
            np.float32(data_min),
        )

    def convertint(data_3D, nchunk):
        if nchunk is not None:
            data_int = np.zeros(data_3D.shape, dtype=dtype)
            slcs = [
                np.s_[offset : offset + nchunk]
                for offset in range(0, data_3D.shape[0], nchunk)
            ]
            for slices in slcs:
                if dtype == "uint8":
                    data_int[slices] = convert8bit(data_3D[slices])
                elif dtype == "uint16":
                    data_int[slices] = convert16bit(data_3D[slices])
            return data_int

        if dtype == "uint8":
            return convert8bit(data_3D)
        elif dtype == "uint16":
            return convert16bit(data_3D)

    def convert16bit(data_3D):
        data_3D, df, mn = convertfloat(data_3D)

        if numexpr:
            import numexpr as ne

            scl = ne.evaluate("0.5+65535*(data_3D-mn)/df", truediv=True)
            ne.evaluate("where(scl<0,0,scl)", out=scl)
            ne.evaluate("where(scl>65535,65535,scl)", out=scl)
            return scl.astype(np.uint16)
        else:
            data_3D = 0.5 + 65535 * (data_3D - mn) / df
            data_3D[data_3D < 0] = 0
            data_3D[data_3D > 65535] = 65535
            return np.uint16(data_3D)

    def convert8bit(data_3D):
        data_3D, df, mn = convertfloat(data_3D)

        if numexpr:
            import numexpr as ne

            scl = ne.evaluate("0.5+255*(data_3D-mn)/df", truediv=True)
            ne.evaluate("where(scl<0,0,scl)", out=scl)
            ne.evaluate("where(scl>255,255,scl)", out=scl)
            return scl.astype(np.uint8)
        else:
            data_3D_float = 0.5 + 255 * (data_3D - mn) / df
            data_3D_float[data_3D < 0] = 0
            data_3D_float[data_3D > 255] = 255
            return np.uint8(data_3D)

    if data_range == None:
        # if quantiles is empty data is scaled based on its min and max values
        if quantiles == None:
            data_min = np.nanmin(data_3D)
            data_max = np.nanmax(data_3D)
            data_max = data_max - data_min
            return convertint(data_3D, nchunk)
        else:
            if subset:
                [data_min, data_max] = np.quantile(
                    np.ravel(data_3D[0::10, 0::10, 0::10]), quantiles
                )
            else:
                [data_min, data_max] = np.quantile(np.ravel(data_3D), quantiles)

            return convertint(data_3D, nchunk)

    else:
        # ignore quantiles input if given
        if quantiles is not None:
            print("quantiles input ignored.")

        data_min = data_range[0]
        data_max = data_range[1]
        return convertint(data_3D, nchunk)


def to01(data_3D):
    """Normalize data to 0-1 range.

    Parameters
    ----------
    data_3D
        Input data.

    Returns
    -------
    data_3D : float32
        Normalized data.
    """
    import numexpr as ne

    data_3D = data_3D.astype(np.float32, copy=False)
    data_min = np.nanmin(data_3D)
    data_max = np.nanmax(data_3D)
    df = np.float32(data_max - data_min)
    mn = np.float32(data_min)
    scl = ne.evaluate("(data_3D-mn)/df", truediv=True)
    return scl.astype(np.float32)


def writemidplanes(data_3D, fileout, slice_x=-1, slice_y=-1, slice_z=-1):
    """Plot orthogonal mid-planes through 3D dataset and save them as images.
    Uses pypng for writing .PNG files.

    Parameters
    ----------
    data
        Input 3D image data.
    fileout : str
        Output .PNG image file name.
    slice_x : int
        X-slice number.
    slice_y : int
        Y-slice number.
    slice_z : int
        Z-slice number.
    """

    if data_3D.ndim == 3:
        if slice_x == -1:
            slice_x = int(data_3D.shape[2] / 2)
        if slice_y == -1:
            slice_y = int(data_3D.shape[1] / 2)
        if slice_z == -1:
            slice_z = int(data_3D.shape[0] / 2)

        filename, ext = os.path.splitext(fileout)
        with open(filename + "_XY.png", "wb") as midplaneXY:
            pngWriter = png.Writer(
                data_3D.shape[2],
                data_3D.shape[1],
                greyscale=True,
                alpha=False,
                bitdepth=8,
            )
            pngWriter.write(midplaneXY, touint(data_3D[int(slice_z), :, :]))

        with open(filename + "_XZ.png", "wb") as midplaneXZ:
            pngWriter = png.Writer(
                data_3D.shape[2],
                data_3D.shape[0],
                greyscale=True,
                alpha=False,
                bitdepth=8,
            )
            pngWriter.write(midplaneXZ, touint(data_3D[:, int(slice_y), :]))

        with open(filename + "_YZ.png", "wb") as midplaneYZ:
            pngWriter = png.Writer(
                data_3D.shape[1],
                data_3D.shape[0],
                greyscale=True,
                alpha=False,
                bitdepth=8,
            )
            pngWriter.write(midplaneYZ, touint(data_3D[:, :, int(slice_x)]))


def writemidplanesDxchange(
    data_3D, fileout, slice_x=-1, slice_y=-1, slice_z=-1, dtype="uint8"
):
    """Plot orthogonal mid-planes through 3D dataset and save them as images.
    Uses DXchange for writing .TIFF files.

    Parameters
    ----------
    data_3D
        Input 3D image data.
    fileout : str
        Output .PNG image file name.
    slice_x : int
        X-slice number.
    slice_y : int
        Y-slice number.
    slice_z : int
        Z-slice number.
    """

    if data_3D.ndim == 3:
        if slice_x == -1:
            slice_x = int(data_3D.shape[2] / 2)
        if slice_y == -1:
            slice_y = int(data_3D.shape[1] / 2)
        if slice_z == -1:
            slice_z = int(data_3D.shape[0] / 2)

        filename, ext = os.path.splitext(fileout)
        dxchange.writer.write_tiff(
            touint(data_3D[int(slice_z), :, :]),
            fname=filename + "_XY.tiff",
            dtype=dtype,
        )
        dxchange.writer.write_tiff(
            touint(data_3D[:, int(slice_y), :]),
            fname=filename + "_XZ.tiff",
            dtype=dtype,
        )
        dxchange.writer.write_tiff(
            touint(data_3D[:, :, int(slice_x)]),
            fname=filename + "_YZ.tiff",
            dtype=dtype,
        )


def plot_midplanes(data_3D, slice_x=-1, slice_y=-1, slice_z=-1):
    """Plot orthogonal cross-sections through 3D dataset.

    Parameters
    ----------
    data_3D
        Input 3D image data.
    slice_x : int
        X-slice number.
    slice_y : int
        Y-slice number.
    slice_z : int
        Z-slice number.
    """

    if slice_x == -1:
        slice_x = int(data_3D.shape[2] / 2)
    if slice_y == -1:
        slice_y = int(data_3D.shape[1] / 2)
    if slice_z == -1:
        slice_z = int(data_3D.shape[0] / 2)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
    ax1.imshow(data_3D[slice_z, :, :])
    ax2.imshow(data_3D[:, slice_y, :])
    ax3.imshow(data_3D[:, :, slice_x])


def plot_projections(data_3D, projection="max"):
    """Plot orthogonal projections of 3D dataset.

    Parameters
    ----------
    data_3D
        Input 3D image data.
    projection : str
        Projection method. Available choices are 'max', 'min'.
    """

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)

    if projection == "max":
        ax1.imshow(np.max(data_3D, 0))
        ax2.imshow(np.max(data_3D, 1))
        ax3.imshow(np.max(data_3D, 2))
    elif projection == "min":
        ax1.imshow(np.min(data_3D, 0))
        ax2.imshow(np.min(data_3D, 1))
        ax3.imshow(np.min(data_3D, 2))


def read_tiff_stack(filename, data_range=None, zfill=4):
    """Read stack of tiff files. Searches all files in parent folder and opens them as a stack of images.

    Parameters
    ----------
    filename
        One of the stack images.
    data_range : [int, int]
        Control load slices range.
    zfill : int
        Number of leading zeros in file names.

    TO DO:
    ----------
    - check that folder contains only .TIFF files; skip the rest
    """

    # search all files in parent folder; create filenames list
    stack_files = [
        os.path.join(os.path.dirname(filename), f)
        for f in os.listdir(os.path.dirname(filename))
        if os.path.isfile(os.path.join(os.path.dirname(filename), f))
    ]
    stack_files.sort()

    if data_range is not None:
        import re

        slice_in = [
            i
            for i, item in enumerate(stack_files)
            if re.search(str(data_range[0]).zfill(4) + ".", item)
        ]
        slice_end = [
            i
            for i, item in enumerate(stack_files)
            if re.search(str(data_range[1]).zfill(4) + ".", item)
        ]

        if len(slice_in) == 1 and len(slice_end) == 1:
            stack_files = stack_files[slice_in[0] : slice_end[0]]
        else:
            import warnings

            warnings.warn(
                "Given slice range is ambiguous or non existing.. loading whole stack."
            )

    # load stack using tifffile
    return tifffile.imread(stack_files)


def write_jpeg2000_stack(
    data,
    fname="tmp/data.jp2",
    dtype=None,
    axis=0,
    digit=5,
    start=0,
    nthreads=1,
    compratio=10,
    overwrite=False,
):
    """
    Write data to stack of JPEG2000 files using glymur. Inspired by dxchange.write_tiff_stack

    Parameters
    ----------
    data : ndarray
        Array data to be saved.
    fname : str
        Base file name to which the data is saved. ``.jp2`` extension
        will be appended if it does not already have one.
    dtype : data-type, optional
        By default, the data-type is inferred from the input data.
    axis : int, optional
        Axis along which stacking is performed.
    start : int, optional
        First index of file in stack for saving.
    digit : int, optional
        Number of digits in indexing stacked files.
    nthreads : int, optional
        Number of threads for parallel write.
    compratio : int, optional
        Compression ratio.
    overwrite: bool, optional
        if True, overwrites the existing file if the file exists.
    """

    fname, data = dxchange.writer._init_write(data, fname, ".jp2", dtype, True)
    body = dxchange.writer.get_body(fname)
    ext = dxchange.writer.get_extension(fname)
    _data = np.swapaxes(data, 0, axis)
    for m in range(start, start + data.shape[axis]):
        _fname = body + "_" + "{0:0={1}d}".format(m, digit) + ext
        if not overwrite:
            _fname = dxchange.writer._suggest_new_fname(_fname, digit=1)

        glymur.set_option("lib.num_threads", nthreads)
        glymur.Jp2k(_fname, data=_data[m - start], cratios=[compratio])


def bbox(bw, pad=0, dsize=None, verbose=None):
    """Bounding BOX limits of input binary image.

    Parameters
    ----------
    bw : bool
        Binary image.
    pad : int
        Add padding of given number of pixels to the BBOX limits.
    dsize : int
        perform image close with disk structuring element of radius 'dsize' before calculating the BBOX.
    verbose
        Activate verbose graphical output

    Returns
    -------
    bbox_origin: int
        Origin [row col (slice)] of the BBOX inscribing True values in input image bw.
    bbox_size: int
        BBOX size [s_row s_col (s_slice)].
    """

    # DSIZE: remove artefacts > erode/dilate
    if dsize:
        raise IOError("dsize method not implemented yet.")

    if bw.ndim == 3:
        # project along each dimension
        maxROW = np.max(np.max(bw, 0), 1)
        maxCOL = np.max(np.max(bw, 0), 0)
        maxSLICE = np.max(np.max(bw, 1), 1)

        # find first and last True occurrences
        row0 = list(maxROW).index(True)
        row1 = len(maxROW) - list(maxROW[::-1]).index(True) - 1

        col0 = list(maxCOL).index(True)
        col1 = len(maxCOL) - list(maxCOL[::-1]).index(True) - 1

        slice0 = list(maxSLICE).index(True)
        slice1 = len(maxSLICE) - list(maxSLICE[::-1]).index(True) - 1

        # add padding
        row0 = row0 - pad
        rowd = row1 - row0 + pad
        col0 = col0 - pad
        cold = col1 - col0 + pad
        slice0 = slice0 - pad
        sliced = slice1 - slice0 + pad

        if pad > 0:
            # check if bbox exceeds image size
            if row0 < 0:
                row0 = 0
            if col0 < 0:
                col0 = 0
            if slice0 < 0:
                slice0 = 0

            bw_size = bw.shape
            if slice0 + sliced > bw_size[0]:
                sliced = bw_size[0] - slice0
            if row0 + rowd > bw_size[1]:
                rowd = bw_size[1] - row0
            if col0 + cold > bw_size[2]:
                cold = bw_size[2] - col0

        if verbose:
            fig, (ax1, ax2) = plt.subplots(1, 2)
            ax1.imshow(np.max(bw, 0))
            ax1.plot([col0, col0], [0, bw.shape[1] - 1], "r")
            ax1.plot([col0 + cold, col0 + cold], [0, bw.shape[1] - 1], "r")
            ax1.plot([0, bw.shape[2] - 1], [row0, row0], "r")
            ax1.plot([0, bw.shape[2] - 1], [row0 + rowd, row0 + rowd], "r")

            ax2.imshow(np.max(bw, 1))
            ax2.plot([col0, col0], [0, bw.shape[1] - 1], "r")
            ax2.plot([col0 + cold, col0 + cold], [0, bw.shape[1] - 1], "r")
            ax2.plot([0, bw.shape[0] - 1], [slice0, slice0], "r")
            ax2.plot([0, bw.shape[0] - 1], [slice0 + sliced, slice0 + sliced], "r")

        bbox_origin = [row0, col0, slice0]
        bbox_size = [rowd, cold, sliced]

        return bbox_origin, bbox_size

    if bw.ndim == 2:
        raise IOError("bbox method for 2D images not implemented yet.")


def crop(data_3D, crop_origin, crop_size):
    """Crop 3D image given crop origin and size.

    Parameters
    ----------
    data_3D
        Input data.
    crop_origin : [int, int, int]
        Crop origin [Z,Y,X].
    crop_size : [int, int, int]
        Crop size [Z,Y,X].

    Returns
    -------
    output
        Cropped data.
    """
    return data_3D[
        crop_origin[2] : crop_origin[2] + crop_size[2],
        crop_origin[0] : crop_origin[0] + crop_size[0],
        crop_origin[1] : crop_origin[1] + crop_size[1],
    ]
