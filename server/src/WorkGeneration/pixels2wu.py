import mysql.connector
import mysql.connector.cursor
import mysql.connector.errors

CONNECTION = mysql.connector.connect(user='root', host='127.0.0.1', db='magphys_wu');

class ORMObject(object):
#	def has_all_required_fields(sellf, field_list):
#		for field in field_list: 
#			if not hasattr(sellf, field): 
#				return 0
#		return 1;

#	def __init__(self, db_values, required_fields):
	def __init__(self, db_values):
		for key in db_values.keys():
			setattr(self, key, db_values[key])
#		if not self.has_all_required_fields(required_fields):
#			raise StandardError("Not all required fields present. Required fields: %(fields)s" % {'fields':required_fields})
		

class Square(ORMObject):
#	def __init__(self, db_values):
#		super(Square, self).__init__(db_values, ['id', 'object_id', 'top_x', 'top_y', 'size', 'wu_generated'])
	def __str__(obj):
		return "Square[%(id)d]<%(x)s, %(y)s>(%(size)d x %(size)d)" % {'id':obj.id, 'x':obj.top_x,'y':obj.top_y,'size':obj.size}

class Pixel(ORMObject):
#	def __init__(self, db_values):
#		super(Pixel, self).__init__(db_values, ['id', 'object_id', 'square_id', 'top_x', 'top_y', 'size', 'wu_generated'])
	def __str__(obj):
		return "Pixel[%(id)d]<%(x)s, %(y)s>(square_id = %(sq_id)d, object_id = %(o_id)s" % {
			'id':obj.id, 'x':obj.x,'y':obj.y,'sq_id':obj.square_id,'o_id':obj.object_id}


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

result_set = fetchResultSet(CONNECTION, "SELECT * FROM square WHERE wu_generated IS NULL ORDER BY size DESC, id ASC LIMIT 10")

for result in result_set:
	square = Square(result)
	print square
	sq_result_set = fetchResultSet(CONNECTION, "SELECT * FROM pixel WHERE square_id = %(square)s" % { 'square':square.id } )
	for sq_result in sq_result_set:
		print Pixel(sq_result)

