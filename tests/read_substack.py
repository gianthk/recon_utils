from recon_utils import read_tiff_stack, plot_midplanes

input_file = '/media/gianthk/My Passport/20217193_Traviglia/recons/581681_punta_HR_stitch2_merge_corr_phrt/slices/slice_0000.tif'

data_3D = read_tiff_stack(input_file, [1340, 1400])
print('here')
