import mysql.connector
import mysql.connector.cursor
import mysql.connector.errors

CONNECTION = mysql.connector.connect(user='root', host='127.0.0.1', db='magphys_wu');

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
#	def has_all_required_fields(sellf, field_list):
#		for field in field_list: 
#			if not hasattr(sellf, field): 
#				return 0
#		return 1;

	def __init__(self, db_values):
		for key in db_values.keys():
			setattr(self, key, db_values[key])
#		if not self.has_all_required_fields(required_fields):
#			raise StandardError("Not all required fields present. Required fields: %(fields)s" % {'fields':required_fields})
		

class Object(ORMObject):
	def __str__(obj):
		return "Object[%(id)d]<%(x)s x %(y)s x %(z)s>(%(name)s): %(desc)s" % {
			'id':obj.id, 'x':obj.dimension_x,'y':obj.dimension_y,'z':obj.dimension_z,'name':obj.name,'desc':obj.description}

class Square(ORMObject):
	def getObject(self):
		return Object._getById(self.object_id)
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
	print square
	for pixel in square.getPixels():
		print pixel


for square in Square._getByQuery("wu_generated IS NULL ORDER BY size DESC, id ASC LIMIT 10"):
	create_output_file(square)

