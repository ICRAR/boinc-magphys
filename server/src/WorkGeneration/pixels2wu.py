import sys
from database_support import *

if(len(sys.argv) != 3):
	print "usage:   %(me)s squares_to_process output_directory" % {'me':sys.argv[0]}
	print "example: %(me)s 15 /Users/astrogeek/f2wu" % {'me':sys.argv[0]}
	sys.exit(-10)

SQUARES_TO_PROCESS = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

def create_output_file(square):
#	object = square.getObject().name
	pixels_in_square = len(square.getPixels())
	filename_variables = { 'output_dir':OUTPUT_DIR, 'object':square.getObject().name, 'sq_x':square.top_x, 'sq_y':square.top_y}
	filename = "%(output_dir)s/obs%(object)s.%(sq_x)s.%(sq_y)s" % filename_variables
	print "  Writing %(filename)s" % {'filename':filename}
	outfile = open(filename, 'w')
	outfile.write("#  This workunit contains observations for object %(object)s\n" % { "object":square.getObject().name })
	outfile.write("#  %(square)s contains %(count)s pixels with above-threshold observations\n" % {
		'square':square, 'count':pixels_in_square })
	outfile.write("#\n")
	
	for pixel in square.getPixels():
		outfile.write("%(object)s~%(pix_x)s~%(pix_y)s %(pixel_values)s\n" % {
			'object':square.getObject().name, 'pix_x':pixel.x, 'pix_y':pixel.y, 'pixel_values':pixel.pixel_values})
	outfile.close();
	update_query = "UPDATE square SET wu_generated=NOW() WHERE id=%(sq_id)s" % {'sq_id':square.id}
	rows_updated = doUpdate(ConnectionHolder.getConnection(), update_query)
	ConnectionHolder.getConnection().commit()

print "Fetching %(limit)s unprocessed squares..." % {'limit':SQUARES_TO_PROCESS}
for square in Square._getByQuery("wu_generated IS NULL ORDER BY top_x+top_y ASC LIMIT %(limit)s" % {'limit':SQUARES_TO_PROCESS}):
	create_output_file(square)

