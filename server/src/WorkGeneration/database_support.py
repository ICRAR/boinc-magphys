import mysql.connector
import mysql.connector.cursor
import mysql.connector.errors

class Database:
	@classmethod
	def getConnection(self):
		if not hasattr(self, 'c'):
			self.c = mysql.connector.connect(user='root', host='localhost', db='magphys_wu');
		return self.c
		
	@classmethod
	def commitTransaction(self):
		return self.getConnection().commit()

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
	
class ORMObject(object):
	@classmethod
	def _getById(self, id):
		result_set = fetchResultSet(Database.getConnection(), "SELECT * FROM %(cls_name)s WHERE id = %(obj_id)d" % { 
			'cls_name':self.__name__, 'obj_id':id })
		return self(result_set[0])
	
	@classmethod
	def _getByQuery(self, where):
		result_set = fetchResultSet(Database.getConnection(), "SELECT * FROM %(cls_name)s WHERE %(where_clause)s" % {
			'cls_name':self.__name__, 'where_clause':where })
		
		result = []
		for row in result_set:
			result.append(self(row))
		return result;

	def _checkForQuotes(self):
		dict = self.__dict__
		for key in dict.keys():
			value = dict[key]
			if str(value).find("\"") > -1:
				raise StandardError("Sorry; I cannot yet escape quotes in values :(");

	def _write(self):
		self._checkForQuotes()
		dict = self.__dict__
		columns = ",".join("`" + key + "`" for key in dict.keys())
		values = ",".join("\"" + str(dict[key]) + "\"" for key in dict.keys())

		sql = "INSERT INTO %(table)s(%(columns)s) VALUES(%(values)s)" % {
			'table':self.__class__.__name__, 'columns':columns, 'values':values}
#		print ">>SQL: " + sql
		rows_updated = doUpdate(Database.getConnection(), sql)
		if rows_updated != 1: raise StandardError("Something went wrong; expected exactly one updated row. Don't know how to recover, so dying")
		self.id = "<no ID>"
		return self

	def _create(self):
		self.write()
		rs = fetchResultSet(Database.getConnection(), "SELECT LAST_INSERT_ID()")
		self.id = rs[0]['LAST_INSERT_ID()']
		return self

	def _update(self):
		self._checkForQuotes()
		dict = self.__dict__

		updates = []
		for key in dict.keys():
			if key != "id": updates.append("`%(col)s`=\"%(val)s\"" % {'col':key, 'val':dict[key]})

		sql = "UPDATE %(table)s SET %(updates)s WHERE id=%(id)d" % {
			'table':self.__class__.__name__, 'updates':",".join(updates), 'id':self.id}
#		print ">>SQL: " + sql
		rows_updated = doUpdate(Database.getConnection(), sql)
		if rows_updated != 1: raise StandardError("Something went wrong; expected exactly one updated row. Don't know how to recover, so dying")
		return self

	def save(self):
		if not hasattr(self, 'id'):
			return self._create()
		return self._update()

	def write(self):
		if not hasattr(self, 'id'):
			return self._write()
		raise StandardError("Cannot write new object; appears to already have been saved")

	def __init__(self, db_values):
		for key in db_values.keys():
			setattr(self, key, db_values[key])

class Object(ORMObject):
	def __str__(obj):
		return "Object[%(id)d]<%(x)s x %(y)s x %(z)s>(%(name)s)" % {
			'id':obj.id, 'x':obj.dimension_x,'y':obj.dimension_y,'z':obj.dimension_z,'name':obj.name}

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
		return "Pixel[%(id)d]<%(x)s, %(y)s>(square_id = %(sq_id)d, object_id = %(o_id)s)" % {
			'id':obj.id, 'x':obj.x,'y':obj.y,'sq_id':obj.square_id,'o_id':obj.object_id}
	def getObject(self):
		return Object._getById(self.object_id)
	def getSquare(self):
		return Square._getById(self.square_id)
