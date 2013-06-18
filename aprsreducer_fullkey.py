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
  """ 
  input: <firsthop>\t<position>  (s3://aprs-is/reduced/digipeaters.txt)
  output: <firsthop position>\t  (s3://aprs-is/reduced/digidupes.txt)
  so that a next-phase reducer can eliminate duplicate positions.
  """ 
  incounts = outcounts = 0
  for l in sys.stdin:
    if incounts%1000 == 0:
      sys.stderr.write("aprsReduceNoDedupe: %d input %d output...\n"%(incounts,outcounts))
    incounts += 1
    splits = l.split('\t')
    s = splits[1].rstrip().split(',')
    if len(s) != 3:
      sys.stderr.write("aprsReduceNoDedupe: value tuple not length 3 (%d): %s.\n"%(len(s),s))
    else:
      call,lat,lon = s
      json.dump({"f":splits[0],"p":(call,lat,lon)},sys.stdout)
      print
      outcounts += 1
  sys.stderr.write("aprsReduceNoDedupe: %d input %d output.\n"%(incounts,outcounts))

if __name__ == '__main__':

  try:
    main()
  except:
    sys.stderr.write("aprsReduceNoDedupe: Exception %s\n"%(sys.exc_info()[0]))
