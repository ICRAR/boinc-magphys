import mysql.connector
import mysql.connector.cursor
import mysql.connector.errors
import sys

if(len(sys.argv) != 2):
	print "usage:   %(me)s squares_to_process" % {'me':sys.argv[0]}
	print "example: %(me)s 15" % {'me':sys.argv[0]}
	sys.exit(-10)

SQUARES_TO_PROCESS = sys.argv[1]
CONNECTION = mysql.connector.connect(user='root', host='127.0.0.1', db='magphys_wu');
OUTPUT_DIR = '/Users/perh/Desktop/f2wu'

class ORMObject(object):
	@classmethod
	def _getById(self, id):
		result_set = fetchResultSet(CONNECTION, "SELECT * FROM %(cls_name)s WHERE id = %(obj_id)d" % { 
			'cls_name':self.__name__, 'obj_id':id })
		return self(result_set[0])
	
	@classmethod
	def _getByQuery(self, where):
		result_set = fetchResultSet(CONNECTION, "SELECT * FROM %(cls_name)s WHERE %(where_clause)s" % {
			'cls_name':self.__name__, 'where_clause':where })
		
		result = []
		for row in result_set:
			result.append(self(row))
		return result;

	def __init__(self, db_values):
		for key in db_values.keys():
			setattr(self, key, db_values[key])

class Object(ORMObject):
	def __str__(obj):
		return "Object[%(id)d]<%(x)s x %(y)s x %(z)s>(%(name)s): %(desc)s" % {
			'id':obj.id, 'x':obj.dimension_x,'y':obj.dimension_y,'z':obj.dimension_z,'name':obj.name,'desc':obj.description}

class Square(ORMObject):
	def getObject(self):
		if not hasattr(self, 'object'):
			self.object = Object._getById(self.object_id)
		return self.object
	def getPixels(self):
		return Pixel._getByQuery("square_id=%(square_id)s" % {'square_id':self.id});
	def __str__(obj):
		return "Square[%(id)d]<%(x)s, %(y)s>(%(size)d x %(size)d)" % {'id':obj.id, 'x':obj.top_x,'y':obj.top_y,'size':obj.size}

class Pixel(ORMObject):
	def __str__(obj):
		return "Pixel[%(id)d]<%(x)s, %(y)s>(square_id = %(sq_id)d, object_id = %(o_id)s" % {
			'id':obj.id, 'x':obj.x,'y':obj.y,'sq_id':obj.square_id,'o_id':obj.object_id}
	def getObject(self):
		return Object._getById(self.object_id)
	def getSquare(self):
		return Square._getById(self.square_id)


def fetchoneDict(cursor):
	row = cursor.fetchone()
	if row is None: return None
	cols = [ d[0] for d in cursor.description ]
	return dict(zip(cols, row))

def doUpdate(conn, sql):
	cursor = conn.cursor()
	return cursor.execute(sql)
	
def fetchResultSet(conn, sql):
	cursor = conn.cursor()
	cursor.execute(sql)
	rows = cursor.fetchall()
	result = []
	for row in rows:
		if row is not None:
			cols = [ d[0] for d in cursor.description ]
			result.append(dict(zip(cols, row)))
	return result

def create_output_file(square):
#	object = square.getObject().name
	pixels_in_square = len(square.getPixels())
	filename_variables = { 'output_dir':OUTPUT_DIR, 'object':square.getObject().name, 'sq_x':square.top_x, 'sq_y':square.top_y}
	filename = "%(output_dir)s/observations/obs%(object)s.%(sq_x)s.%(sq_y)s" % filename_variables
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
	print update_query
	rows_updated = doUpdate(CONNECTION, update_query)
	CONNECTION.commit()
	print "  -- Updated %(r)d rows" % {'r':rows_updated}

print "Fetching %(limit)s unprocessed squares..." % {'limit':SQUARES_TO_PROCESS}
for square in Square._getByQuery("wu_generated IS NULL ORDER BY top_x+top_y ASC LIMIT %(limit)s" % {'limit':SQUARES_TO_PROCESS}):
	create_output_file(square)

