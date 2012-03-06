import math
import pyfits

input_file = 'POGS_NGC628_v3.fits';

hdulist = pyfits.open(input_file);

#Here, it might be useful to assert that there are 12 input layers/channels/HDUs
print "List length: %(#)d" % {'#': len(hdulist)}

layer_count = len(hdulist)
object_name = hdulist[0].header['OBJECT']

# Uncomment to print general information about the file to stdout
#hdulist.info()

# Here, find out dimensions of the layers. Currently, it is assumed the file is 3840x3840

for pix_x in range(3840):
	for pix_y in range(3840):
		pixels = [hdulist[layer].data[pix_y, pix_x] for layer in range(layer_count)]
		live_pixels = 0
		pixel_string = ""
		for p in pixels:
			if not math.isnan(p):
				live_pixels += 1
			pixel_string+= `p` + " "
# For now, only output pixels where 2 or more channels have data
# Should perhaps be configurable – this is something we need to discuss before going live
# Are all channels created equally, or should different channels have different "weights" so that, for example,
# we might discard a pixel that have data for 10 channels but is missing UV, while retaining pixels where we have
# data for only, say, 6 pixels but that has UV? Discussion with Kevin?
		if live_pixels > 2:
			print "%(galaxy)s__%(x)d_%(y)d %(values)s" % { 'galaxy':object_name, 'x':pix_x, 'y':pix_y, 'values':pixel_string }
