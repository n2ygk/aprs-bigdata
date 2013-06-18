#!/usr/bin/python
import sys
import json
"""
Haddop reducer for aprs-is logs reduced by aprspig.py.
Input: firsthop,from_call,latitude,longitude\t(nothing)
Output: {"f": firsthop, "p": [[from,lat,lon]...]}
Assumes hadoop partitioner was used to partition all keys for the same firsthop 
to the same reducer.
"""
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
  incounts = outcounts = 0
  curhop = None
  for l in sys.stdin:
    if incounts%1000 == 0:
      sys.stderr.write("aprsReduceDedupe: %d input %d output...\n"%(incounts,outcounts))
    incounts += 1
    splits = l.split('\t')
    s = splits[0].rstrip().split(',')
    if len(s) != 4:
      sys.stderr.write("aprsReduceDedupe: key tuple not length 4 (%d): %s.\n"%(len(s),s))
    else:
      firsthop,call,lat,lon = s
      if firsthop != curhop:
        if curhop != None:
          print ']}'
        curhop = firsthop
        lastpos = None
        first = True
        print '{"f":"%s","p":['%(firsthop),
      if lastpos != (call,float(lat),float(lon)):
        if not first: 
          print ",",
        print '["%s",%f,%f]'%(call,float(lat),float(lon)),
        outcounts += 1
      lastpos = (call,float(lat),float(lon))
      first = False
  if curhop != None:
    print ']}'
  sys.stderr.write("aprsReduceDedupe: %d input %d output.\n"%(incounts,outcounts))

if __name__ == '__main__':

  try:
    main()
  except:
    sys.stderr.write("aprsReduceDedupe: Exception %s\n"%(sys.exc_info()[0]))
