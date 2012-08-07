import pyfits
from PIL import Image
import math
import os, hashlib
from database.database_support import Galaxy, Area, AreaUser

class FitsImage:
    useHighCut = False
    sigma = 6
    
    def __init__(self):
        pass

    def buildImage(self, fitsFileName, imageDirName, imagePrefixName, method, createBWImages, createLog, debug):
        """
        Build Three Colour Images, and optionally black and white and white and black images for each image.
        """
        if imageDirName[-1] != "/":
            imageDirName = imageDirName + "/"
        if os.path.isfile(imageDirName):
            print 'Directory ', imageDirName , 'exists'
            return 1
        elif os.path.isdir(imageDirName):
            pass
        else:
            os.mkdir(imageDirName)

        hdulist = pyfits.open(fitsFileName, memmap=True)
        if debug:
            hdulist.info()

        blackRGB = (0, 0, 0)
        black = (0)
        white = (255)
        sigma = 6

        hdu = hdulist[0]
        width = hdu.header['NAXIS1']
        height = hdu.header['NAXIS2']

        #cards = ['MAGPHYSL', 'MAGPHYSN', 'MAGPHYSI', 'MAGPHYSF']
        cards = ['MAGPHYSL', 'MAGPHYSN', 'MAGPHYSI', 'MAGPHYSF', 'BITPIX', 'NAXIS', 'NAXIS2', 'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'BZERO', 'BSCALE', 'OBJECT']

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
            if debug:
                print hdu,
                print file

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
            valuerange = []
            avg = 0
            stddev = 0
            hiCut = 0
            for z in range(0, 256):
                valuerange.append(0)

            if self.useHighCut:
                minvalue = 0
                minorigvalue = 0
                if filter == 115:
                    hiCut = 0.000291644721334
                if filter == 116:
                    hiCut = 0.000432029634664
                if filter == 117:
                    hiCut = 0.000490767257621
                if filter == 118:
                    hiCut = 0.000740360468626
                if filter == 119:
                    hiCut = 0.00211978228098
                if filter == 123:
                    hiCut = 5.12672716825e-06
                if filter == 124:
                    hiCut = 9.56274295407e-06
                if filter == 280:
                    hiCut = 0.00868070504761
                if filter == 281:
                    hiCut = 0.0136214713233
                if filter == 282:
                    hiCut = 0.0781642428067
                if filter == 283:
                    hiCut = 0.444458113518    
                maxorigvalue = hiCut
            
                maxvalue = self.applyFunc(maxorigvalue, method)
                #if method == 'atan':
                #    maxvalue = math.atan(maxorigvalue)
                #elif method == 'log':
                #    maxvalue = math.log(maxorigvalue)
                #elif method == 'log10':
                #    maxvalue = math.log(maxorigvalue, 10)
                #elif method == 'asinh':
                #    maxvalue = math.asinh(maxorigvalue * self.sigma)
                #elif method == 'linear':
                #    maxvalue = maxorigvalue
                
                mult = 255.0 / (maxvalue - minvalue)
            else:
                values = []
                for x in range(0, width-1):
                    for y in range(0, height-1):
                        value =  hdu.data[y + xoffset,x + xoffset]
                        if not math.isnan(value):
                            if value > 0:
                                values.append(value)
                            #if value > hiCut:
                            #    value = hiCut
                            if value < minorigvalue:
                                minorigvalue = value
                            if value > maxorigvalue:
                                maxorigvalue = value
                            #if value < 0:
                            #    value = 0
                            if value == 0:
                                zerocount = zerocount + 1
                                continue
                            value = self.applyFunc(value, method)
                            #if method == 'atan':
                            #    value = math.atan(value)
                            #elif method == 'log':
                            #    #if value < 0.001:
                            #    #    value = 0.001;
                            #    value = math.log(value)
                            #elif method == 'log10':
                            #    #if value < 0.001:
                            #    #    value = 0.001;
                            #    value = math.log(value, 10)
                            #elif method == 'asinh':
                            #    #if value < 0.001:
                            #    #    value = 0.001;
                            #    value = math.asinh(value * self.sigma)
                            #    #pass
                            #elif method == 'linear':
                            #    if value < 0.0:
                            #        value = 0.0
                            #    #if value > math.pi/2:
                            #    #    value = math.pi/2
    
                            sum = sum + value
                            sumsq = sumsq + (value*value)
                            count = count + 1
                            if value < minvalue:
                                minvalue = value
                            if value > maxvalue:
                                maxvalue = value
                avg = sum / count
                if debug:
                     print sumsq, count, avg
                stddev=0.0
                try:
                    stddev = math.sqrt((sumsq/count) - (avg*avg))
                except ValueError:
                    stddev=0.0
                   
                #bottomIdx = 0
                #bottomValue = 0; 
                values.sort()
                #for val in values:
                #    bottomValue = val
                #    if bottomIdx > 20:
                #        break
                #    bottomIdx += 1
                    
                topIdx = 0
                topValue = 0;
                values.reverse()
                for val in values:
                    topValue = val
                    if topIdx > 100:
                        break
                    topIdx += 1
                    
                hiCut = topValue
                maxvalue = self.applyFunc(topValue, method)
                #if method == 'atan':
                #    #minvalue = math.atan(bottomValue)
                #    maxvalue = math.atan(topValue)
                #elif method == 'log':
                #    #minvalue = math.log(bottomValue)
                #    maxvalue = math.log(topValue)
                #elif method == 'log10':
                #    #minvalue = math.log(bottomValue, 10)
                #    maxvalue = math.log(topValue, 10)
                #elif method == 'asinh':
                #    #minvalue = math.asinh(bottomValue * self.sigma)
                #    maxvalue = math.asinh(topValue * self.sigma)
                #elif method == 'linear':
                #    #minvalue = bottomValue
                #    maxvalue = topValue

                if method == 'linear':
                    minvalue = 0.0
                    #hiCut = avg + (15*stddev)
                    #if hiCut > maxvalue:
                    #    maxvalue = hiCut
                    
                if method == 'asinh':
                    minvalue = 0.0

                mult = 255.0 / (maxvalue - minvalue)
                
            sminvalue = 99999999
            smaxvalue = 0
            pixelcount = 0
            
            #if method == 'asinh':
            #    slope = 255.0 / ((10000)/sigma)
            #     
            #    scaledMean = slope * math.asinh((avg) /sigma); 
            #    # now we can get the scale for each colour as 
            #    mult = scaledMean/avg;
            #    minvalue = 0.0
            #    #mult = 255.0 / ((maxvalue - minvalue)/sigma)

            if debug:
                print 'Min-Orig', minorigvalue, 'Max-Orig', maxorigvalue, 'Min-Adj', minvalue, 'Max-Adj', maxvalue, 'Multiplier', mult, 'Zeroes', zerocount

            if createBWImages:
                imagebw = Image.new("L", (width, height), black)
                imagewb = Image.new("L", (width, height), white)

            for x in range(0, width-1):
                for y in range(0, height-1):
                    value =  hdu.data[y + xoffset,x + xoffset]
                    if not math.isnan(value):
                        #if value < 0:
                        #    value = 0
                        value = self.applyFunc(value, method)
                        #if method == 'atan':
                        #    value = math.atan(value)
                        #elif method == 'log':
                        #    if value == 0:
                        #        continue
                        #    #if value < 0.001:
                        #    #    value = 0.001;
                        #    value = math.log(value)
                        #elif method == 'log10':
                        #    if value == 0:
                        #        continue
                        #    #if value < 0.001:
                        #    #    value = 0.001;
                        #    value = math.log(value, 10)
                        #elif method == 'asinh':
                        #    #if value < 0.001:
                        #    #    value = 0.001;
                        #    value = math.asinh(value * self.sigma)
                        #elif method == 'linear':
                        #    if value < 0.0:
                        #        value = 0.0
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
                        if createBWImages:
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

            if debug:
                print 'Scaled: Min', sminvalue, 'Max', smaxvalue
                print 'Pixel Count', pixelcount
            #print 'Count', count, 'Avg', avg, 'Std Dev', stddev
            #print 'LoCut', avg - (10*stddev), 'HiCut', avg + (15*stddev)

            if createLog:
                logFile = open(imageDirName + imagePrefixName + '_' + str(file) + '.txt', 'w')
                logFile.write('Scaling method: {}\n'.format(method))
                self.printCardsToFile(logFile, hdu.header, cards)
                logFile.write('\n')
                logFile.write('Count {} Avg {} StdDev {} Pixels {} PercentWithValue {}\n'.format(count, avg, stddev, width*height, ((count-zerocount)*100.0)/(width*height)))
                logFile.write('Possible LoCut {} HiCut {}\n'.format(avg - (10*stddev), avg + (15*stddev)))
                logFile.write('Min-Orig {} Max-Orig {} Min-Adj {} Max-Adj {} Multiplier {} Zeroes {} HiCut {}\n'.format(minorigvalue, maxorigvalue, minvalue, maxvalue, mult, zerocount, hiCut))
                logFile.write('\n')

                for z in range(0, 256):
                    logFile.write('{0:3d} {1}\n'.format(z, valuerange[z]))
                logFile.close()
            if createBWImages:
                imagebw.save(self.get_bw_image_path(imageDirName, imagePrefixName, file))
                imagewb.save(self.get_wb_image_path(imageDirName, imagePrefixName, file))

        image1.save(self.get_colour_image_path(imageDirName, imagePrefixName, 1))
        image2.save(self.get_colour_image_path(imageDirName, imagePrefixName, 2))
        image3.save(self.get_colour_image_path(imageDirName, imagePrefixName, 3))
        image4.save(self.get_colour_image_path(imageDirName, imagePrefixName, 4))

        #image1.save(imageDirName + imagePrefixName + "_colour_1.jpg")
        #image2.save(imageDirName + imagePrefixName + "_colour_2.jpg")
        #image3.save(imageDirName + imagePrefixName + "_colour_3.jpg")
        #image4.save(imageDirName + imagePrefixName + "_colour_4.jpg")

        hdulist.close()
        
    def applyFunc(self, value, method):
        if method == 'atan':
            return math.atan(value)
        elif method == 'log':
            if value == 0:
                return 0;
            else:
                return math.log(value)
        elif method == 'log10':
            return math.log(value, 10)
        elif method == 'asinh':
            return math.asinh(value * self.sigma)
        else:
           return maxorigvalue

    def filename_hash(self, name, hash_fanout):
        """
        Accepts a filename (without path) and the hash fanout.
        Returns the directory bucket where the file will reside.
        The hash fanout is typically provided by the project config file.
        """
        h = hex(int(hashlib.md5(name).hexdigest()[:8], 16) % hash_fanout)[2:]

        # check for the long L suffix. It seems like it should
        # never be present but that isn't the case
        if h.endswith('L'):
            h = h[:-1]
        return h

    def get_file_path(self, dirName, fileName):
        """
        Accepts a directory name and file name and returns the relative path to the file.
        This method accounts for file hashing and includes the directory
        bucket in the path returned.
        """
        fanout = 1024
        hashed = self.filename_hash(fileName, fanout)
        hashDirName = os.path.join(dirName,hashed)
        if os.path.isfile(hashDirName):
            pass
        elif os.path.isdir(hashDirName):
            pass
        else:
            os.mkdir(hashDirName)
        return os.path.join(dirName,hashed,fileName)

    def get_colour_image_path(self, imageDirName, imagePrefixName, colour):
        """
        Generates the relative path to the file given the directory name, image prefix
        and colour.  The file name is used to generate a hash to spread the files across
        many directories to avoid having too many files in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_colour_" + str(colour) + ".png")

    def get_bw_image_path(self, imageDirName, imagePrefixName, file):
        """
        Generates the relative path to the file given the directory name, image prefix
        and image number for the Black and White Image.  The file name is used to generate
        a hash to spread the files across many directories to avoid having too many files
        in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_" + str(file) + '_bw.png')

    def get_wb_image_path(self, imageDirName, imagePrefixName, file):
        """
        Generates the relative path to the file given the directory name, image prefix
        and image number for the White and Black Image.  The file name is used to generate
        a hash to spread the files across many directories to avoid having too many files
        in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_" + str(file) + '_wb.png')

    def markImage(self, session, inImageFileName, outImageFileName, galaxy_id, userid):
        """
        Read the image for the galaxy and generate an image that highlights the areas
        that the specified user has generated results.
        """
        image = Image.open(inImageFileName, "r").convert("RGBA")

        #pixels = session.query(PixelResult).filter("galaxy_id=:galaxyId", "user_id=:userId").params(galaxyId=galaxyId).all()
        areas = session.query(Area, AreaUser).filter(AreaUser.userid == userid)\
          .filter(Area.area_id == AreaUser.area_id)\
          .order_by(Area.top_x, Area.top_y).all()
        #print 'Areas', len(areas)
        for areax in areas:
            area = areax.Area;
            for x in range(area.top_x, area.bottom_x):
                for y in range(area.top_y, area.bottom_y):
                    self.markPixel(image, x, y)

        #for x in range(140, 145):
        #    for y in range(80, 93):
        #        self.markPixel(image, x, y)

        #for x in range(100, 113):
        #    for y in range(80, 122):
        #        self.markPixel(image, x, y)

        image.save(outImageFileName)

    def markPixel(self, image, x, y):
        """
        Mark the specified pixel to highlight the area where the user has
        generated results.
        """
        px = image.getpixel((x,y))
        #image.putpixel((x,y), (255,255,255))
        #image.putpixel((x,y), (px[0], px[1], px[2], 50))
        r = int(px[0] + ((255 - px[0]) * 0.4))
        g = int(px[1] + ((255 - px[1]) * 0.4))
        b = int(px[2] + ((255 - px[2]) * 0.4))
        #r = px[0] * 2
        #g = px[1] * 2
        #b = px[2] * 2
        if r > 255:
            r = 255
        if g > 255:
            g = 255
        if b > 255:
            b = 255
        if r < 60:
            r = 60
        if g < 60:
            g = 60
        if b < 60:
            b = 60
        image.putpixel((x,y), (r, g, b))

    def userGalaxies(self, session, userid):
        """
        Determines the galaxies that the selected user has generated results.  Returns an array of
        galaxy_ids.
        """
        stmt = session.query(Galaxy.galaxy_id).join(Area).join(AreaUser).filter(AreaUser.userid == userid).subquery()
        #print stmt
        #print session.query(Galaxy).filter(Galaxy.galaxy_id.in_(stmt))
        #adalias = aliased(PixelResult, stmt);
        return session.query(Galaxy).filter(Galaxy.galaxy_id.in_(stmt));

    def userGalaxyIds(self, session, userid):
        """
        Determines the galaxies that the selected user has generated results.  Returns an array of
        galaxy_ids.
        """
        stmt = session.query(Galaxy.galaxy_id).join(Area).join(AreaUser).filter(AreaUser.userid == userid).subquery()
        #print stmt
        #print session.query(Galaxy).filter(Galaxy.galaxy_id.in_(stmt))
        #adalias = aliased(PixelResult, stmt);
        galaxyIds = []
        for galaxy in session.query(Galaxy).filter(Galaxy.galaxy_id.in_(stmt)):
           #print 'Galaxy', galaxy.name
           galaxyIds.append(galaxy.galaxy_id)
        return galaxyIds;

    def printCardsToFile(self, outFile, header, keys):
        for key in keys:
            try:
                outFile.write('{0:8} {1}\n'.format(key, header[key]))
            except KeyError as e:
                pass

