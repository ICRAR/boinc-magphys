#! /usr/bin/env python2.7
#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
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
Fix the table image_filters_used
"""
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy import select
from sqlalchemy.sql.expression import and_
from config import DB_LOGIN
from database.database_support_core import GALAXY, IMAGE_FILTERS_USED, FILTER

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

transaction = connection.begin()


def get_filter_id(filter_number):
    """
    Get the filter id
    """
    filter = connection.execute(select([FILTER]).where(FILTER.c.filter_number == filter_number)).first()
    return filter[FILTER.c.filter_id]


def insert_or_update(image_number, galaxy_id, red_filter, green_filter, blue_filter):
    """
    Insert or update the filter
    """

    # Get the id's before we build as SqlAlchemy flushes which will cause an error as
    filter_id_red = get_filter_id(red_filter)
    filter_id_blue = get_filter_id(blue_filter)
    filter_id_green = get_filter_id(green_filter)

    image_filters_used = connection.execute(select([IMAGE_FILTERS_USED]).where(and_(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id, IMAGE_FILTERS_USED.c.image_number == image_number))).first()
    if image_filters_used is None:
        connection.execute(IMAGE_FILTERS_USED.insert().values(image_number = image_number,
            galaxy_id = galaxy_id,
            filter_id_red = filter_id_red,
            filter_id_blue = filter_id_blue,
            filter_id_green = filter_id_green))
    else:
        connection.execute(IMAGE_FILTERS_USED.update().where(IMAGE_FILTERS_USED.c.image_filters_used_id == image_filters_used[IMAGE_FILTERS_USED.c.image_filters_used_id]).values(image_number = image_number,
            galaxy_id = galaxy_id,
            filter_id_red = filter_id_red,
            filter_id_blue = filter_id_blue,
            filter_id_green = filter_id_green))


for galaxy in connection.execute(select([GALAXY])):
    LOG.info('Processing %d - %s', galaxy[GALAXY.c.galaxy_id], galaxy[GALAXY.c.name])
    if galaxy[GALAXY.c.run_id] == 0:
        image1_filters = [232, 231, 230]
        image2_filters = [231, 230, 124]
        image3_filters = [280, 230, 124]
        image4_filters = [283, 231, 124]

    elif galaxy[GALAXY.c.run_id] == 1:
        image1_filters = [326, 325, 324]
        image2_filters = [325, 324, 323]
        image3_filters = [326, 324, 323]
        image4_filters = [327, 325, 323]

    else:
        image1_filters = [232, 231, 230]
        image2_filters = [231, 230, 229]
        image3_filters = [232, 230, 229]
        image4_filters = [233, 231, 229]

    # Insert the correct filters
    insert_or_update(1, galaxy[GALAXY.c.galaxy_id], image1_filters[0], image1_filters[1], image1_filters[2])
    insert_or_update(2, galaxy[GALAXY.c.galaxy_id], image2_filters[0], image2_filters[1], image2_filters[2])
    insert_or_update(3, galaxy[GALAXY.c.galaxy_id], image3_filters[0], image3_filters[1], image3_filters[2])
    insert_or_update(4, galaxy[GALAXY.c.galaxy_id], image4_filters[0], image4_filters[1], image4_filters[2])

transaction.commit()
