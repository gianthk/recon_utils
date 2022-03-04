import recon_utils as ru
I = ru.read_tiff_stack('./test_data/test_bbox/trab_0000.tif')
bw = I > 100
bbox_origin, bbox_size = ru.bbox(bw, offset=0, dsize=None, verbose=True)