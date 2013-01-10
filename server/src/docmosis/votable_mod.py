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
import urllib2
import os
import tempfile
import warnings

from astropy.io.vo.table import parse, parse_single_table

def getVOData(name):
   """
   Returns a map of VOData for Galaxy
   """
   map_vo = {}

   # Try NED first
   try:
      url='http://ned.ipac.caltech.edu/cgi-bin/objsearch?expand=no&objname=' + name + '&of=xml_main'
      table = getVOTable(url,0)
      map_vo['design'] = table.array['Object Name'][0]
      url='http://ned.ipac.caltech.edu/cgi-bin/objsearch?expand=no&objname=' + name + '&of=xml_posn'
      table = getVOTable(url,0)
      map_vo['ra_eqj2000'] = table.array['pos_ra_equ_J2000_d'][0]
      map_vo['dec_eqj2000'] = table.array['pos_dec_equ_J2000_d'][0]
      map_vo['ra_eqb1950'] = table.array['pos_ra_equ_B1950_d'][0]
      map_vo['dec_eqb1950'] = table.array['pos_dec_equ_B1950_d'][0]
      return map_vo
   except:
      pass

   # Try HyperLeda second
   try:
      url='http://leda.univ-lyon1.fr/G.cgi?n=101&c=o&o=' + name + '&a=x&z=d'
      table = getVOTable(url,0)
      map_vo['design'] = table.array['design'][0]
      url='http://leda.univ-lyon1.fr/G.cgi?n=113&c=o&o=' + name + '&a=x&z=d'
      table = getVOTable(url,0)
      map_vo['ra_eqj2000']=table.array['alpha'][0]
      map_vo['dec_eqj2000']=table.array['delta'][0]
      map_vo['ra_eqb1950'] = 0
      map_vo['dec_eqb1950'] = 0
      return map_vo
   except:
      raise Exception("The VOTable data is not quite right")

def getVOTable(url,table_number):
   """
   Returns VOTable from a URL and table number
   """

   tmp = tempfile.mkstemp(".xml", "pogs", None, False)
   file = tmp[0]
   os.close(file)
   xml_file = tmp[1]
   table = None
   try: 
      req = urllib2.Request(url)
      response = urllib2.urlopen(req,timeout=10)
      with open(xml_file, 'w') as file:
         file.write(response.read())
      with warnings.catch_warnings():
         warnings.simplefilter("ignore")
         table = parse_single_table(xml_file,pedantic=False,table_number=table_number)
   except:
      raise Exception("Problem contacting VOTable provider")
   finally:
      os.remove(xml_file)

   return table
