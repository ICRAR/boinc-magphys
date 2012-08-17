#! /usr/bin/env python2.7
"""
Build a PNG image from the data in the database
"""
import argparse
import logging
import math
import numpy
import datetime
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from config import db_login
from config import django_image_dir
from image import fitsimage
from database.database_support import Galaxy, Area, PixelResult
from PIL import Image
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Build images from the POGS results')
parser.add_argument('-o','--output_dir', action=WriteableDir, nargs=1, help='where the images will be written')
parser.add_argument('names', nargs='*', help='optional the name of the galaxies to produce')
parser.add_argument('-all', action='store_true', help='build images for all the galaxies')
args = vars(parser.parse_args())

#output_directory = args['output_dir']
output_directory = django_image_dir

# First check the galaxy exists in the database
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

if len(args['names']) > 0:
    LOG.info('Building PNG files for the galaxies {0}\n'.format(args['names']))
    query = session.query(Galaxy).filter(Galaxy.name.in_(args['names']))
elif args['all']:
    LOG.info('Building PNG files for all the galaxies\n')
    query = session.query(Galaxy)
else:
    LOG.info('Building PNG files for updated galaxies\n')
    query = session.query(Galaxy).filter(Area.galaxy_id == Galaxy.galaxy_id)\
        .filter(Area.update_time >= Galaxy.image_time)

galaxies = query.all()

IMAGE_NAMES = [ 'fmu_sfh',
                'fmu_ir',
                'mu',
                'tauv',
                's_sfr',
                'm',
                'ldust',
                't_w_bc',
                't_c_ism',
                'xi_c_tot',
                'xi_pah_tot',
                'xi_mir_tot',
                'x_w_tot',
                'tvism',
                'mdust',
                'sfr',
              ]

PNG_IMAGE_NAMES = [ 'mu',
                'm',
                'ldust',
                'sfr',
              ]

# 'Fire' (Copied from Aladin cds.aladin.ColorMap.java)
FIRE_R = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,4,7,
       10,13,16,19,22,25,28,31,34,37,40,43,46,49,52,55,58,61,64,67,70,73,76,79,
       82,85,88,91,94,98,101,104,107,110,113,116,119,122,125,128,131,134,137,
       140,143,146,148,150,152,154,156,158,160,162,163,164,166,167,168,170,171,
       173,174,175,177,178,179,181,182,184,185,186,188,189,190,192,193,195,196,
       198,199,201,202,204,205,207,208,209,210,212,213,214,215,217,218,220,221,
       223,224,226,227,229,230,231,233,234,235,237,238,240,241,243,244,246,247,
       249,250,252,252,252,253,253,253,254,254,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255]

FIRE_G = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,1,3,5,7,8,10,12,14,16,19,21,24,27,29,32,35,37,40,43,46,48,
       51,54,57,59,62,65,68,70,73,76,79,81,84,87,90,92,95,98,101,103,105,107,
       109,111,113,115,117,119,121,123,125,127,129,131,133,134,136,138,140,141,
       143,145,147,148,150,152,154,155,157,159,161,162,164,166,168,169,171,173,
       175,176,178,180,182,184,186,188,190,191,193,195,197,199,201,203,205,206,
       208,210,212,213,215,217,219,220,222,224,226,228,230,232,234,235,237,239,
       241,242,244,246,248,248,249,250,251,252,253,254,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255]

FIRE_B = [0,7,15,22,30,38,45,53,61,65,69,74,78,
       82,87,91,96,100,104,108,113,117,121,125,130,134,138,143,147,151,156,160,
       165,168,171,175,178,181,185,188,192,195,199,202,206,209,213,216,220,220,
       221,222,223,224,225,226,227,224,222,220,218,216,214,212,210,206,202,199,
       195,191,188,184,181,177,173,169,166,162,158,154,151,147,143,140,136,132,
       129,125,122,118,114,111,107,103,100,96,93,89,85,82,78,74,71,67,64,60,56,
       53,49,45,42,38,35,31,27,23,20,16,12,8,5,4,3,3,2,1,1,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       4,8,13,17,21,26,30,35,42,50,58,66,74,82,90,98,105,113,121,129,136,144,
       152,160,167,175,183,191,199,207,215,223,227,231,235,239,243,247,251,255,
       255,255,255,255,255,255,255]

fimage = fitsimage.FitsImage()

for galaxy in galaxies:
    LOG.info('Working on galaxy %s\n', galaxy.name)
    array = numpy.empty((galaxy.dimension_x, galaxy.dimension_y, len(IMAGE_NAMES)), dtype=numpy.float)
    array.fill(numpy.NaN)

    # Return the rows
    for row in session.query(PixelResult).filter(PixelResult.galaxy_id == galaxy.galaxy_id).all():
        array[row.x, row.y, 0] = row.fmu_sfh
        array[row.x, row.y, 1] = row.fmu_ir
        array[row.x, row.y, 2] = row.mu
        array[row.x, row.y, 3] = row.tauv
        array[row.x, row.y, 4] = row.s_sfr
        array[row.x, row.y, 5] = row.m
        array[row.x, row.y, 6] = row.ldust
        array[row.x, row.y, 7] = row.t_w_bc
        array[row.x, row.y, 8] = row.t_c_ism
        array[row.x, row.y, 9] = row.xi_c_tot
        array[row.x, row.y, 10] = row.xi_pah_tot
        array[row.x, row.y, 11] = row.xi_mir_tot
        array[row.x, row.y, 12] = row.x_w_tot
        array[row.x, row.y, 13] = row.tvism
        array[row.x, row.y, 14] = row.mdust
        array[row.x, row.y, 15] = row.sfr

    name_count = 0

    blackRGB = (0, 0, 0)
    for name in PNG_IMAGE_NAMES:
        value = 0
        height = galaxy.dimension_x
        width = galaxy.dimension_y
        idx = 0
        if name == 'mu':
            idx = 2
        elif name == 'm':
            idx = 5
        elif name == 'ldust':
            idx = 6
        elif name == 'sfr':
            idx = 15

        values = []
        for x in range(0, width-1):
            for y in range(0, height-1):
                value =  array[x, y, idx]
                if not math.isnan(value) and value > 0:
                    values.append(value)

        values.sort()
        if len(values) > 1000:
            topCount = int(len(values)*0.005)
            topValue = values[len(values)-topCount]
        elif len(values) > 0:
            topValue = values[len(values)-1]
        else:
            topValue = 1
        if len(values) > 1:
            medianvalue = values[int(len(values)/2)]
        elif len(values) > 0:
            medianvalue = values[0]
        else:
            medianvalue = 1

        sigma = 1 / medianvalue
        mult = 255.0 / math.asinh(topValue * sigma)

        image = Image.new("RGB", (width, height), blackRGB)
        for x in range(0, width-1):
            for y in range(0, height-1):
                value = array[x, y, idx]
                if not math.isnan(value) and value > 0:
                    value = int(math.asinh(value * sigma) * mult)
                    if value > 255:
                        value = 255
                    red = FIRE_R[value]
                    green = FIRE_G[value]
                    blue = FIRE_B[value]
                    image.putpixel((width-y-1,x), (red, green, blue))
        outname = fimage.get_file_path(output_directory, '{0}_{1}_{2}.png'.format(galaxy.name, galaxy.version_number, name), True)
        image.save(outname)
        galaxy.image_time = datetime.datetime.now()
        session.commit()

LOG.info('Built images for %d galaxies\n', len(galaxies))

