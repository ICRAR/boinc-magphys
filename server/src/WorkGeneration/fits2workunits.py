import math
import pyfits

MIN_LIVE_CHANNELS_PER_PIXEL = 3;
INPUT_FILE = '/Users/perh/Dropbox/Documents/Work/ThoughtWorks/Projects/ICRAR/POGS_NGC628_v3.fits';
GRID_SIZE = 5

# The file is 3840x3840. Right now only looking at a small square where there is data
START_X = 1800
START_Y = 1800
END_X = 2000
END_Y = 2000

HDULIST = pyfits.open(INPUT_FILE);
LAYER_COUNT = len(HDULIST)


## ######################################################################## ##
## 
## FUNCTIONS AND STUFF
## 
## ######################################################################## ##

class Coordinate:
	def __init__(self, x_coord, y_coord):
		self.x = x_coord
		self.y = y_coord
	def __str__(obj):
		return "<%(x)s, %(y)s>" % {'x':obj.x,'y':obj.y}

def get_pixels(pix_x, pix_y):
#	print "Getting pixels in <%(x)s, %(y)s>" % {'x':pix_x, 'y':pix_y} 
	result = []
	for x in pix_x:
		if x >= END_X:
			continue;
		for y in pix_y:
			if y >= END_Y:
				continue;

			pixels = [HDULIST[layer].data[x, y] for layer in range(LAYER_COUNT)]
			live_pixels = 0
			for p in pixels:
				if not math.isnan(p):
					live_pixels += 1

			# For now, only output pixels where MIN_LIVE_CHANNELS_PER_PIXEL or more channels have data
			# Are all channels created equally, or should different channels have different "weights" so that, for example,
			# we might discard a pixel that have data for 10 channels but is missing UV, while retaining pixels where we have
			# data for only, say, 6 pixels but that has UV? Discussion with Kevin?
			if live_pixels >= MIN_LIVE_CHANNELS_PER_PIXEL:
#				print "%(galaxy)s__%(x)d_%(y)d " % { 'galaxy':object_name, 'x':x, 'y':y}
				coords = Coordinate(x, y) #"p%(x)s,%(y)s"%{'x':x,'y':y}
				result.append({coords: pixels})
	return result
		
def squarify():
	squares = []
	for pix_y in range(START_Y, END_Y, GRID_SIZE):
		print "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-START_Y)/(END_Y-START_Y) }
		pix_x = START_X
		while pix_x < END_X:
			pixels = get_pixels([pix_x], range(pix_y, pix_y+GRID_SIZE))
			if len(pixels)>0:
				pixels.extend(get_pixels(range(pix_x+1, pix_x+GRID_SIZE), range(pix_y, pix_y+GRID_SIZE)))
				coords = Coordinate(pix_x, pix_y) #"s%(x)s,%(y)s"%{'x':pix_x,'y':pix_y}
				squares.append({coords:pixels});
				pix_x+=GRID_SIZE;
			else:
				pix_x+=1
	return squares

	
	
## ######################################################################## ##
## 
## Where it all starts
## 
## ######################################################################## ##

#Here, it might be useful to assert that there are 12 input layers/channels/HDUs
#print "List length: %(#)d" % {'#': len(HDULIST)} 

object_name = HDULIST[0].header['OBJECT']

squares = squarify()
print "Workunits for: %(object)s" % { "object":object_name } 

for square_list in squares:
	for square in square_list:
		print "  Square %(square)s has %(count)s pixels" % { 'square':square, 'count':len(square_list[square]) }
		outfile = open("observations/obs%(object)s.%(sq_x)s.%(sq_y)s" % {'object':object_name, 'sq_x':square.x, 'sq_y':square.y}, 'w')
		outfile.write("#  This workunit contains observations for object %(object)s\n" % { "object":object_name })
		outfile.write("#  Square %(square)s contains %(count)s pixels with above-threshold observations\n" % {
			'square':square, 'count':len(square_list[square]) })
		outfile.write("#\n")

		for pixel in square_list[square]:
			for p in pixel.keys():
#				print "    Pixel %(key)s => %(value)s" % { 'key':p, 'value':pixel[p]}
				outfile.write("%(object)s~%(pix_x)s~%(pix_y)s" % {'object':object_name, 'pix_x':p.x, 'pix_y':p.y})
				for one_value in pixel[p]:
					outfile.write(" %(value)s" % { 'value':one_value })
				outfile.write("\n");
		outfile.close();

print "================================ END OF OUTPUT ================================"

# Uncomment to print general information about the file to stdout
#HDULIST.info()

