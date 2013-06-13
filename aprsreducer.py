#!/usr/bin/python
import sys
import json
"""
Haddop reducer for aprs-is logs reduced by aprspig.py.
Input: firsthop\tfrom_call,latitude,longitude
Output: {"firsthop": "firsthop", "pos": [{"from": "from","lat": lat, "lon":, lon}]}
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
if __name__ == '__main__':

  curhop = None
  posits = None
  for l in sys.stdin:
    splits = l.split('\t')
    firsthop = splits[0]
    if firsthop != curhop:
      if posits:
        json.dump({"f":curhop,"p":list(posits)},sys.stdout)
        print
      curhop = firsthop
      posits=set()
    call,lat,lon = splits[1].rstrip().split(',')
    posits.add((call,float(lat),float(lon)))
  if posits: 
    json.dump({"f":curhop,"p":list(posits)},sys.stdout)
    print
   
    
