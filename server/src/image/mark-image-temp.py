from PIL import Image, ImageDraw
import sys
import os

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

image = Image.open(outputDir + "image_log_colour_1.jpg", "r").convert("RGBA")
for x in range(140, 145):
    for y in range(80, 85):
        px = image.getpixel((x,y))
        image.putpixel((x,y), (255,255,255, 255))
        #image.putpixel((x,y), (px[0], px[1], px[2], 0))

image.save(outputDir + "image_test_colour_1.png")

