import pyfits
from PIL import Image, ImageDraw
import math
import sys
import os

def printCard(header, key):
  print key,
  print header[key]
  
def printCards(header, keys):
    for key in keys:
        print key, header[key]
        
def printCardsToFile(outFile, header, keys):
    for key in keys:
        outFile.write('{0:8} {1}\n'.format(key, header[key]))

method = 'log'

if len(sys.argv) < 2:
   print "build-image.py fileName [method]"
   sys.exit(1)

fileName = sys.argv[1]
if len(sys.argv) > 2:
    method = sys.argv[2]
    
if method == 'log':
    pass
elif method == 'log10':
    pass
elif method == 'atan':
    pass
else:
    method = 'linear'

parts = os.path.splitext(fileName)
dirName = parts[0]
print "filename", fileName, dirName

magphysDir = "/Users/rob/magphys/"
outputDir = magphysDir + dirName + "/"
fileName = magphysDir + fileName

if os.path.isfile(outputDir):
   print 'Directory ', outputDir , 'exists'
   sys.exit(1)
elif os.path.isdir(outputDir):
   pass
else:
   os.mkdir(outputDir)

hdulist = pyfits.open(fileName, memmap=True)
hdulist.info()

blackRGB = (0, 0, 0)
black = (0)
white = (255)

hdu = hdulist[0]
width = hdu.header['NAXIS1']
height = hdu.header['NAXIS2']

cards = ['MAGPHYSL', 'MAGPHYSN', 'MAGPHYSI', 'MAGPHYSF']
cards2 = ['MAGPHYSL', 'MAGPHYSN', 'MAGPHYSI', 'MAGPHYSF', 'BITPIX', 'NAXIS', 'NAXIS2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'OBJECT']

# Create Three Colour Images
image1Filters = [118, 117, 116] # i, r, g
image2Filters = [117, 116, 124] # r, g, NUV
image3Filters = [280, 116, 124] # 3.6, g, NUV
image4Filters = [283, 117, 124] # 22, r, NUV

image1 = Image.new("RGB", (width, height), blackRGB)
image2 = Image.new("RGB", (width, height), blackRGB)
image3 = Image.new("RGB", (width, height), blackRGB)
image4 = Image.new("RGB", (width, height), blackRGB)

images = [image1, image2, image3, image4]
imageFilters = [image1Filters, image2Filters, image3Filters, image4Filters]

file = 0
loCut = 0
hiCut = 999999
for hdu in hdulist:
    file = file + 1
    print hdu,
    print file
    printCards(hdu.header, cards)
    #print len(hdu.data)
    #print hdu.size()
    #print hdu.header
    #for card in hdu.header.ascardlist():
    #  print card.key,
    #  print card.value
    #for key in hdu.header:
    #   print key,
    #   print hdu.header[key]
    #print hdu.data[2000:2009, 2000:2009]
    #for x in range(2000, 2004):
    #  for y in range(2000, 2004):
    #    print x,
    #    print y,
    #    print hdu.data[y,x]
    
    width = hdu.header['NAXIS1']
    height = hdu.header['NAXIS2']
    filter = hdu.header['MAGPHYSI']
      
    # Get the Three Colour Images that require this filter.
    rImages = []
    gImages = []
    bImages = []
    for idx in range(len(imageFilters)):
        img = images[idx]
        filters = imageFilters[idx]
        if filters[0] == filter:
            rImages.append(img)
        if filters[1] == filter:
            gImages.append(img)
        if filters[2] == filter:
            bImages.append(img)
    
    xoffset = 0
    yoffset = 0        
    minorigvalue = 99999999.0
    maxorigvalue = -99999999.0
    minvalue = 9999999.0
    maxvalue = -99999999.0
    zerocount = 0
    sumsq = 0
    sum = 0
    count = 0
    for x in range(0, width-1):
        for y in range(0, height-1):
            value =  hdu.data[y + xoffset,x + xoffset]
            if not math.isnan(value):
                if value < minorigvalue:
                    minorigvalue = value
                if value > maxorigvalue:
                    maxorigvalue = value
                #if value < 0:
                #    value = 0
                if value == 0:
                    zerocount = zerocount + 1
                    continue
                if method == 'atan':
                    value = math.atan(value)
                elif method == 'log':
                    #if value < 0.001:
                    #    value = 0.001;
                    value = math.log(value)
                elif method == 'log10':
                    #if value < 0.001:
                    #    value = 0.001;
                    value = math.log(value, 10)
                elif method == 'linear':
                    if value < 0.0:
                        value = 0.0
                    #if value > math.pi/2:
                    #    value = math.pi/2
                        
                sum = sum + value
                sumsq = sumsq + (value*value)
                count = count + 1
                if value < minvalue:
                    minvalue = value
                if value > maxvalue:
                    maxvalue = value
    avg = sum / count
    print sumsq, count, avg
    stddev=0.0
    try:
        stddev = math.sqrt((sumsq/count) - (avg*avg))
    except ValueError:
        stddev=0.0
    
    valuerange = []
    for z in range(0, 256):
        valuerange.append(0)
    if method == 'linear':
        minvalue = 0.0
        hiCut = avg + (15*stddev)
        if hiCut > maxvalue:
            maxvalue = hiCut
        
    mult = 256.0 / (maxvalue - minvalue)
    sminvalue = 99999999
    smaxvalue = 0
    pixelcount = 0
        
    print 'Min-Orig', minorigvalue, 'Max-Orig', maxorigvalue, 'Min-Adj', minvalue, 'Max-Adj', maxvalue, 'Multiplier', mult, 'Zeroes', zerocount
    
    imagebw = Image.new("L", (width, height), black)
    imagewb = Image.new("L", (width, height), white)
    
    for x in range(0, width-1):
        for y in range(0, height-1):
            value =  hdu.data[y + xoffset,x + xoffset]
            if not math.isnan(value):
                #if value < 0:
                #    value = 0
                if method == 'atan':
                    value = math.atan(value)
                elif method == 'log':
                    if value == 0:
                        continue
                    #if value < 0.001:
                    #    value = 0.001;
                    value = math.log(value)
                elif method == 'log10':
                    if value == 0:
                        continue
                    #if value < 0.001:
                    #    value = 0.001;
                    value = math.log(value, 10)
                elif method == 'linear':
                    if value < 0.0:
                        value = 0.0
                adjvalue = value - minvalue
                value = int(adjvalue*mult)
                #value = int(value*256)
                if value < 0:
                    value = 0
                if value > 255:
                    value = 255
                #print math.atan(value)
                if value < sminvalue:
                    sminvalue = value
                if value > smaxvalue:
                    smaxvalue = value
                valuerange[value] = valuerange[value] + 1
                #print 'x', x, 'y', width-y-1, 'Value', value, 'Width', width, 'Height', height
                imagebw.putpixel((x,width-y-1), (value))
                imagewb.putpixel((x,width-y-1), (255-value))
                if value > 0:
                    pixelcount = pixelcount + 1
                for img in rImages:
                    px = img.getpixel((x,width-y-1))
                    img.putpixel((x,width-y-1), (value, px[1], px[2]))
                for img in gImages:
                    px = img.getpixel((x,width-y-1))
                    img.putpixel((x,width-y-1), (px[0], value, px[2]))
                for img in bImages:
                    px = img.getpixel((x,width-y-1))
                    img.putpixel((x,width-y-1), (px[0], px[1], value))
    
    print 'Scaled: Min', sminvalue, 'Max', smaxvalue
    print 'Pixel Count', pixelcount
    #print 'Count', count, 'Avg', avg, 'Std Dev', stddev
    #print 'LoCut', avg - (10*stddev), 'HiCut', avg + (15*stddev)
    
    logFile = open(outputDir +  'image_' + method + '_' + str(file) + '.txt', 'w')
    printCardsToFile(logFile, hdu.header, cards2)
    logFile.write('\n')
    logFile.write('Count {} Avg {} StdDev {} Pixels {} PercentWithValue {}\n'.format(count, avg, stddev, width*height, ((count-zerocount)*100.0)/(width*height)))
    logFile.write('Possible LoCut {} HiCut {}\n'.format(avg - (10*stddev), avg + (15*stddev)))
    logFile.write('Min-Orig {} Max-Orig {} Min-Adj {} Max-Adj {} Multiplier {} Zeroes {}\n'.format(minorigvalue, maxorigvalue, minvalue, maxvalue, mult, zerocount))
    logFile.write('\n')
    
    for z in range(0, 256):
        logFile.write('{0:3d} {1}\n'.format(z, valuerange[z]))
    logFile.close()
    imagebw.save(outputDir +  'image_' + method + '_' + str(file) + '_bw.jpg')
    imagewb.save(outputDir +  'image_' + method + '_' + str(file) + '_wb.jpg')

image1.save(outputDir + dirName + "_" + method + "_colour_1.jpg")
image2.save(outputDir + dirName + "_" + method + "_colour_2.jpg")
image3.save(outputDir + dirName + "_" + method + "_colour_3.jpg")
image4.save(outputDir + dirName + "_" + method + "_colour_4.jpg")


  
