#/usr/bin/python
"""
 APRS parsing User Defined Functions (UDF) for Pig.
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
import re
# allow testing of this code outside the Pig context by defining a dummy decorator
if 'outputSchema' not in locals():
  def outputSchema(schema):
    def wrapper(func):
      def impl(*args, **kwargs):
        return func(*args, **kwargs)
      return impl
    return wrapper

@outputSchema("time:chararray,from_call:chararray,to_call:chararray,digis:chararray,gtype:chararray,gate:chararray,info:chararray,firsthop:chararray")
def aprs(l):
  """
  Parse APRS packet into attributes useable by Pig.
  Given an input string collected from APRS-IS (preceded by a timestamp), 
  parse into several fields, including a "firsthop" digipeater callsign.
  input:  chararray (includes timestamp followed by APRS-IS data)
  output: Parsed components of line or null if it fails to parse. 
          Beyond just parsing, the first hop digipeater is given.
  """
  s = re.match('^(?P<time>^[^ ]*) (?P<from_call>[^>]+)>(?P<to_call>[^,]+),*(?P<digis>.*),(?P<gtype>[^,]+),(?P<gate>[^:]+)(:)(?P<info>.*)$',l)
  if s:
    digis = s.group('digis')
    if '*' in digis:            # if there's a repeated flag set in digis, then the first hop is here.
      firsthop=digis.split(',')[0].rstrip('*')
    else:                       # if not, then the first hop is the IGATE
      firsthop=s.group('gate')
    return s.group('time'),s.group('from_call'),s.group('to_call'),s.group('digis'),s.group('gtype'),s.group('gate'),s.group('info'),firsthop

class Position:
  """
  A canonical APRS position.
  Methods to parse the various APRS position report formats.
  """
  def __init__(self):
    self.lat = self.lon = self.lat_a = self.lon_a = self.cse = self.spd = 0.0

  def lat2DD(self,lat,NS):
    """ convert degrees, minutes, NS compass direction to decimal degrees """
    self.lat = float(lat[0:2]) + float(lat[2:])/60.0
    if NS == 'S': self.lat = -self.lat

  def lon2DD(self,lon,EW):
    """ convert degrees, minutes, EW compass direction to decimal degrees """
    self.lon = float(lon[0:3]) + float(lon[3:])/60.0
    if EW == 'W': self.lon = -self.lon
    
  def pos(self,to_call,info):
    """
    Source: APRS101.pdf
    Section 7: Normal position reports:
   
    4903.50N/07201.75W-  where the / and - can be a variety of symbols. Special case \. means null position.
    with position ambiguity spaces in place of digits.
    4903.5 N represents latitude to nearest 1/10th of a minute. 
    4903.  N represents latitude to nearest minute.
    490 .  N represents latitude to nearest 10 minutes. 
    49  .  N represents latitude to nearest degree.
    
    optionally followed by course & speed (CSE/SPD) (and several other extensions)
    ddd/sss (e.g. 088/036)
   
    TheNet X-1J4... header is obsolete and can be skipped.
    [......] Maidenhead grid squares: skip this for now
   
    Section 8:
    Normal positions reports are identified by the info field starting with the following characters:
    ! or = without timestamp
    !4903.50N/07201.75W-comment text /A=001234
    =4903.50N/07201.75W-comment text /A=001234
    """
    if info[9]=='\\' and info[19]=='.': return None
    # "The level of ambiguity specified in the latitude will automatically apply to the longitude as well...."
    ambiguity = {0: 0.0,        # no ambiguity
                 1: 0.1/60.0,   # 4903.5 N represents latitude to nearest 1/10th of a minute. 
                 2: 1.0/60.0,   # 4903.  N represents latitude to nearest minute.
                 3: 10.0/60.0,  # 490 .  N represents latitude to nearest 10 minutes. 
                 4: 1.0,        # 49  .  N represents latitude to nearest degree.
                 5: 10.0,       # not an actual valid value!
                 6: 100.0,      # ditto
                 7: 1000.0,     # make it clear this is just stupid!
                 }
    _lat = info[1:8]
    _NS = info[8]
    _lon = info[10:18]
    _EW = info[18]
    self.lat_a = self.lon_a = ambiguity[_lat.count(' ')]
    if self.lat_a > 0.0:
      _lat = _lat.replace(' ','0')
      _lon = _lon.replace(' ','0')
    # DDMM.mm -> DD + MM.mm/60
    self.lat2DD(_lat,_NS)
    self.lon2DD(_lon,_EW)
    # TODO: CSE/SPD
    return self.value()

  def pos_ts(self,to_call,info):
    """
    position report preceded by timestamp
    / or @ with timestamp (/ = UTC, @ = local)

    /092345z4903.50N/07201.75W-comment text /A=001234
    @092345/4903.50N/07201.75W-comment text /A=001234
    """
    return self.pos(to_call,info[7:])

  def pos_cmp(self,to_call,info):
    """
    Section 9:
    Compressed position reports
    /YYYYXXXX$csT - Ugh, just read pages 37-41
    """
    pass

  def gps(self,to_call,info):
    """
    RAW NMEA position reports from a GPS
    $GPGGA,102705,5157.9762,N,00029.3256,W,1,04,2.0,75.7,M,47.6,M,,*62 
    $GPGLL,2554.459,N,08020.187,W,154027.281,A 
    $GPRMC,063909,A,3349.4302,N,11700.3721,W,43.022,89.3,291099,13.6,E*52 
    $GPVTG,318.7,T,,M,35.1,N,65.0,K*69

    """
    g = info.split(',')
    if g[0] == '$GPGGA':
      _lat = g[2]
      _NS = g[3]
      _lon = g[4]
      _EW = g[5]
    elif g[0] == '$GPGLL':
      _lat = g[1]
      _NS = g[2]
      _lon = g[3]
      _EW = g[4]
    elif g[0] == '$GPRMC':
      _lat = g[3]
      _NS = g[4]
      _lon = g[5]
      _EW = g[6]
    else:
      return None
    self.lat2DD(_lat,_NS)
    self.lon2DD(_lon,_EW)
    return self.value()

  def mic_e(self,to_call,info):
    """
    Section 10:
    Mic-E pages 42-56
    """
    pass

  def parse(self,to_call,info):
    """
    Parse the position report.
    """
    # BASICALLY, this all keys off the first character of the info field.
    # See Section 5:
    functab = {'\0x1c': self.mic_e,    # rev 0 beta
               '\0x1d': self.mic_e,    # old rev 0 beta (would that be rev -1?:-)
               '\'': self.mic_e,       # Kenwood TM-D700
               '`': self.mic_e,        # production Mic-E; Kenwood TM-D710
               '!': self.pos,          # position
               '=': self.pos,          # position (& message)
               '$': self.gps,          # raw GPS data
               '/': self.pos_ts,       # position with timestamp
               '@': self.pos_ts,       # position with timestamp (& message)
               }
    if info[0] in functab:
      return functab[info[0]](to_call,info)

  def value(self):
    """
    Return Position to match the expected Pig outputSchema:
    latitude:float,longitude:float,lat_ambiguity:float,lon_ambiguity:float,course:float,speed:float
    """
    return self.lat,self.lon,self.lat_a,self.lon_a,self.cse,self.spd

@outputSchema("latitude:float,longitude:float,lat_ambiguity:float,lon_ambiguity:float,course:float,speed:float")
def position(to_call,info):
  """
  Given an APRS to_call and information field, return canonical position or Null if none.
  Since the compressed Mic-E format encodes information in the to_call, this arg is required.

  Parses the known APRS position report formats and returns:
  latitude:float in degrees (e.g. 49.1234)
  longitude:float in degrees (e.g. -72.4321)
  lat_ambiguity:float in degrees (e.g. 1.0)
  lon_ambiguity:float in degrees (e.g. 1.0)
  course:float in degrees (0...360)
  speed:float in knots (0 = stationary)
  [altitude:float in miles???]

  """
  return Position().parse(to_call,info)

if __name__ == '__main__':
  import sys
  f = open(sys.argv[1])
  for l in f:
    print l
    r = aprs(l)
    if r:
      time,from_call,to_call,digis,gtype,gate,info,firsthop = r
      print position(to_call,info)
