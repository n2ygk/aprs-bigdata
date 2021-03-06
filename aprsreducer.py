#!/usr/bin/python
import sys
import json
"""
Haddop reducer for aprs-is logs reduced by aprspig.py.
Input: firsthop\tfrom_call,latitude,longitude
Output: {"f": firsthop, "p": [[from,lat,lon]...]}
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
  curhop = None
  posits = None
  incounts = outcounts = 0
  for l in sys.stdin:
    incounts += 1
    if incounts%100 == 0:
      sys.stderr.write("aprsReduce: %d input %d output...\n"%(incounts,outcounts))
    splits = l.split('\t')
    firsthop = splits[0]
    if firsthop != curhop:
      if posits:
        json.dump({"f":curhop,"p":list(posits)},sys.stdout)
        print
        outcounts += 1
      curhop = firsthop
      posits=set()
    call,lat,lon = splits[1].rstrip().split(',')
    posits.add((call,float(lat),float(lon)))
  if posits: 
    json.dump({"f":curhop,"p":list(posits)},sys.stdout)
    print
    outcounts += 1
  sys.stderr.write("aprsReduce: %d input %d output.\n"%(incounts,outcounts))

if __name__ == '__main__':

  try:
    main()
  except:
    sys.stderr.write("aprsReduce: Exception %s\n"%(sys.exc_info()[0]))

