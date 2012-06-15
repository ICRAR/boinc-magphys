import sys
from database_support import *

if(len(sys.argv) != 3):
	print "usage:   %(me)s squares_to_process output_directory" % {'me':sys.argv[0]}
	print "example: %(me)s 15 /home/ec2-user/f2wu" % {'me':sys.argv[0]}
	sys.exit(-10)

SQUARES_TO_PROCESS = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def create_output_file(square):
	pixels_in_square = len(square.getPixels())
	filename_variables = { 'output_dir':OUTPUT_DIR, 'square':square.id}
	filename = "%(output_dir)s/wu%(square)s" % filename_variables
	print "  Writing %(filename)s" % {'filename':filename}
	outfile = open(filename, 'w')
	outfile.write("#  This workunit contains observations for object %(object)s. " % { "object":square.getObject().name })
	outfile.write("%(square)s contains %(count)s pixels with above-threshold observations\n" % {
		'square':square, 'count':pixels_in_square })

	row_num = 0
	for pixel in square.getPixels():
		outfile.write("pix%(id)s %(pixel_redshift)s %(pixel_values)s\n" % {
			'id':baseN(pixel.id, 62), 'pixel_redshift':pixel.redshift, 'pixel_values':pixel.pixel_values})
		row_num += 1
	outfile.close();
	update_query = "UPDATE square SET wu_generated=NOW() WHERE id=%(sq_id)s" % {'sq_id':square.id}
	rows_updated = doUpdate(Database.getConnection(), update_query)
	Database.commitTransaction()

print "Fetching %(limit)s unprocessed squares..." % {'limit':SQUARES_TO_PROCESS}
for square in Square._getByQuery("wu_generated IS NULL ORDER BY top_x+top_y ASC LIMIT %(limit)s" % {'limit':SQUARES_TO_PROCESS}):
	create_output_file(square)

