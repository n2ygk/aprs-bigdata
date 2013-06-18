#!/usr/bin/python
import sys
import json
__author__="Alan Crosswell <alan@columbia.edu>"
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Copyright (c) 2013 Alan Crosswell
"""

def main():
  """ 
  Haddop mapper for aprs-is logs reduced by aprspig.py.
  Input: firsthop\tfrom_call,latitude,longitude (s3://aprs-is/reducer/digipeaters.txt/)
  output: firsthop,from_call,latitude,longitude\t(nothing) 
  so that the reducer can eliminate duplicate positions.
  """ 
  incounts = outcounts = 0
  for l in sys.stdin:
    if incounts%1000 == 0:
      sys.stderr.write("aprsMapFullKey: %d input %d output...\n"%(incounts,outcounts))
    incounts += 1
    splits = l.split('\t')
    s = splits[1].rstrip().split(',')
    if len(s) != 3:
      sys.stderr.write("aprsMapFullKey: value tuple not length 3 (%d): %s.\n"%(len(s),s))
    else:
      call,lat,lon = s
      print "%s,%s,%f,%f\t"%(splits[0],call,float(lat),float(lon))
      outcounts += 1
  sys.stderr.write("aprsMapFullKey: %d input %d output.\n"%(incounts,outcounts))

if __name__ == '__main__':

  try:
    main()
  except:
    sys.stderr.write("aprsMapFullKey: Exception %s\n"%(sys.exc_info()[0]))
