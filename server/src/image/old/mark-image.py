from PIL import Image
import sys
import os
from database.database_support import Galaxy, AreaUser, Area
from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if len(sys.argv) < 2:
   print "build-image.py fileName [method]"
   sys.exit(1)


fileName = sys.argv[1]

parts = os.path.splitext(fileName)
dirName = parts[0]
print "filename", fileName, dirName

magphysDir = "/Users/rob/magphys/"
outputDir = magphysDir + dirName + "/"
fileName = magphysDir + fileName

engine = create_engine(DB_LOGIN)
Session = sessionmaker(bind=engine)
session = Session()

image = Image.open(outputDir + "image_log_colour_1.jpg", "r").convert("RGBA")
galaxy_id = 1
userid = 2

stmt = session.query(Galaxy.galaxy_id).join(Area).join(AreaUser).filter(AreaUser.userid == userid).subquery()
for galaxy in session.query(Galaxy).filter(Galaxy.galaxy_id.in_(stmt)):
   print 'Galaxy', galaxy.name


areas = session.query(Area, AreaUser).filter(AreaUser.userid == userid)\
          .filter(Area.area_id == AreaUser.area_id)\
          .order_by(Area.top_x, Area.top_y).all()

for areax in areas:
    area = areax.Area;
    for x in range(area.top_x, area.bottom_x):
        for y in range(area.top_y, area.bottom_y):
            x = int(px.x)
            y = int(px.y)
            px = image.getpixel((x,y))
            image.putpixel((x,y), (px[0], px[1], px[2], 0))

for x in range(140, 145):
    for y in range(80, 93):
        px = image.getpixel((x,y))
        image.putpixel((x,y), (255,255,255))

for x in range(120, 125):
    for y in range(80, 86):
        px = image.getpixel((x,y))
        image.putpixel((x,y), (255,255,255))

image.save(outputDir + "image_test_colour_1.png")

