#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
The functions used to archive tables from AWS to Pleiades
"""
import logging
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

def get_map(from_data, columns):
    """
    Build a map of the data to allow inserting or updating
    """
    map = {}

    for column in columns:
        map[column.name] = from_data[column.name]
    return map


def insert_latest(table, from_db, to_db):
    """
    Insert the data in a table from the equivalent table in a different database using the PK to find the rows to insert
    """
    columns = table.get_children()
    primary_key = None
    for column in columns:
        if column.primary_key:
            primary_key = column.name
            break

    # Find the max PK
    max_pk = to_db.execute(select([func.max(getattr(table.c, primary_key))])).first()

    select_statement = select([table])
    if max_pk is not None:
        select_statement = select_statement.where(getattr(table.c, primary_key) > max_pk[0])

    for from_data in from_db.execute(select_statement):
        map = get_map(from_data, columns)
        to_db.execute(table.insert().values(map))

def insert_only(table, from_data, to_db):
    """
    Insert the data in a table from the equivalent table in a different database
    """
    columns = table.get_children()
    map = get_map(from_data, columns)
    to_db.execute(table.insert().values(map))
