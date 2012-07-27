import pyfits
from PIL import Image, ImageDraw
import math

def sort_layers(hdu_list, layer_count):
        """
        Look at the layers of a HDU and order them based on the effective wavelength stored in the header
        """
        dictionary = {}

        for layer in range(layer_count):
                hdu = hdu_list[layer]
                header = hdu.header
                lamda = header['MAGPHYSL']
                if lamda is None:
                        raise LookupError('No MAGPHYS Lamda value found')
                else:
                        dictionary[lamda] = layer

        items = dictionary.items()
        items.sort()
        return [value for key, value in items]

def printCard(header, key):
  print key,
  print header[key]

hdulist = pyfits.open('POGS_NGC628_v3.fits', memmap=True)
hdulist.info()

black = (0)
white = (256)

file = 0
for hdu in hdulist:
  file = file + 1
  print hdu,
  print file
  printCard(hdu.header, 'MAGPHYSL')
  #printCard(hdu.header, 'BITPIX')
  #printCard(hdu.header, 'NAXIS')
  #printCard(hdu.header, 'NAXIS1')
  #printCard(hdu.header, 'NAXIS2')
  #printCard(hdu.header, 'CRPIX1')
  #printCard(hdu.header, 'CRPIX2')
  #printCard(hdu.header, 'CRVAL1')
  #printCard(hdu.header, 'CRVAL2')
  #printCard(hdu.header, 'OBJECT')
  #printCard(hdu.header, 'BSCALE')
  #printCard(hdu.header, 'BZERO')
  #lamda = hdu.header['MAGPHYSL')
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
  xoffset = 0
  yoffset = 0
  image = Image.new("L", (width, height), black)
  minorigvalue = 9999999
  maxorigvalue = 0
  minvalue = 9999999
  maxvalue = 0
  for x in range(0, width-1):
    for y in range(0, height-1):
      value =  hdu.data[y + xoffset,x + xoffset]
      if not math.isnan(value):
        if value < minorigvalue:
          minorigvalue = value
        if value > maxorigvalue:
          maxorigvalue = value
        if value < 0:
          value = 0
        if value > 0:
          value = math.log(value)
        if value < minvalue:
          minvalue = value
        if value > maxvalue:
          maxvalue = value
  mult = 256.0 / (maxvalue - minvalue)
  print 'Min-Orig', minorigvalue, 'Max-Orig', maxorigvalue, 'Min-Adj', minvalue, 'Max-Adj', maxvalue, 'Multiplier', mult
  sminvalue = 9999999
  smaxvalue = 0
  pixelcount = 0
  #valuerange = []
  #for z in range(0, 257):
  #    valuerange.append(0)
  for x in range(0, width-1):
    for y in range(0, height-1):
      value =  hdu.data[y + xoffset,x + xoffset]
      #blue = 0
      if not math.isnan(value):
        if value < 0:
          value = 0
        if value > 0:
          value = math.log(value)
        adjvalue = value - minvalue
        blue = int(adjvalue*mult)
        #blue = int(value*256)
        if blue < 0:
            blue = 0
        if blue > 256:
            blue = 256
        #print math.atan(value)
        if blue < sminvalue:
          sminvalue = blue
        if blue > smaxvalue:
          smaxvalue = blue
        #valuerange[blue] = valuerange[blue] + 1
        #if blue > 256:
        #  blue = 256
        #print blue
        #blue = 256 - blue
        image.putpixel((x,width-y), (blue))
        if blue > 0:
          pixelcount = pixelcount + 1
        #if pixelcount < 21:
        #  print value, adjvalue, blue
  print 'Scaled: Min', sminvalue, 'Max', smaxvalue
  print 'Pixel Count', pixelcount
  #for z in range(0, 257):
  #    print z, valuerange[z]
  filename = '/Users/rob/Magphys/fitswblog_' + str(file) + '.jpg'
  image.save(filename)


sorted = sort_layers(hdulist, len(hdulist))

#for key in sorted:
#  print key

#print sorted
  