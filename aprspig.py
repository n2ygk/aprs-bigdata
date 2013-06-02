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
if 'outputSchema' not in locals():
  from pigDecorators import *

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
  n = l.find(' ')
  if n < 0: return None
  time = l[0:n]
  l = l[n+1:]
  n = l.find('>')
  if n < 0: return None  
  from_call = l[0:n]
  l = l[n+1:]
  n = l.find(':')
  if n < 0: return None  
  digis = l[0:n].split(',')
  info = l[n+1:]
  to_call = digis[0]
  digis = digis[1:]
  if not digis: return None     # there will always be a "qAR,gateway" since this is APRS-IS
  gtype = digis[-2]
  gate = digis[-1]
  d1 = digis[0]
  digis = digis[0:-2]
  if '*' in digis:            # if there's a repeated flag set in digis, then the first hop is here.
    firsthop=d1.rstrip('*')
  else:                       # if not, then the first hop may be a hidden flood call or IGATE
    n = d1[-1] if d1[-1].isdigit() else None
    N = d1[-3] if len(d1)>3 and d1[-2] == '-' and d1[-3].isdigit() else None
    if (N or n) and N != n:
      firsthop = d1
    else:
      firsthop=gate
  return time,from_call,to_call,digis,gtype,gate,info,firsthop

class Position:
  """
  A canonical APRS position.
  Methods to parse the various APRS position report formats.
  """
  def __init__(self):
    self.lat = self.lon = self.lat_a = self.lon_a = self.cse = self.spd = 0.0
    self.ambiguity = {0: 0.0,        # no ambiguity
                      1: 0.1/60.0,   # 4903.5 N represents latitude to nearest 1/10th of a minute. 
                      2: 1.0/60.0,   # 4903.  N represents latitude to nearest minute.
                      3: 10.0/60.0,  # 490 .  N represents latitude to nearest 10 minutes. 
                      4: 1.0,        # 49  .  N represents latitude to nearest degree.
                      5: 10.0,       # not an actual valid value!
                      6: 100.0,      # ditto
                      7: 1000.0,     # make it clear this is just stupid!
                      }


  def lat2DD(self,lat,NS):
    """ convert degrees, minutes, NS compass direction to decimal degrees """
    if lat[0:4].isdigit() and lat[4] == '.' and lat[5:].isdigit():
      self.lat = float(lat[0:2]) + float(lat[2:])/60.0
      if NS == 'S': self.lat = -self.lat

  def lon2DD(self,lon,EW):
    """ convert degrees, minutes, EW compass direction to decimal degrees """
    if lon[0:5].isdigit() and lon[5] == '.' and lon[6:].isdigit():
      self.lon = float(lon[0:3]) + float(lon[3:])/60.0
      if EW == 'W': self.lon = -self.lon
  
  def pos(self,to_call,info):
    """
    Source: APRS101.pdf
    Section 7: Normal position reports:
   
    4903.50N/07201.75W-  where the / and - can be a variety of symbols. Special case \. means null position.
    
    optionally followed by course & speed (CSE/SPD) (and several other extensions)
    ddd/sss (e.g. 088/036)
   
    TheNet X-1J4... header may be obsolete and can be skipped.
    [......] Maidenhead grid squares: skip this for now
   
    Section 8:
    Normal positions reports are identified by the info field starting with the following characters:
    ! or = without timestamp
    !4903.50N/07201.75W-comment text /A=001234
    =4903.50N/07201.75W-comment text /A=001234
    """
    if not info[1].isdigit(): # if first char of lat is not a digit this is a compressed position report
      return self.pos_cmp(to_call,info)
    if len(info) < 19: return None
    if info[9]=='\\' and info[19]=='.': return None
    _lat = info[1:8]
    _NS = info[8]
    _lon = info[10:18]
    _EW = info[18]
    _csespd = info[20:] if len(info) > 27 else None
    self.lat_a = self.lon_a = self.ambiguity[_lat.count(' ')]
    if self.lat_a > 0.0:
      _lat = _lat.replace(' ','0')
      _lon = _lon.replace(' ','0')
    # DDMM.mm -> DD + MM.mm/60
    self.lat2DD(_lat,_NS)
    self.lon2DD(_lon,_EW)
    # CSE/SPD
    if _csespd and len(_csespd) >= 7 and _csespd[3]=='/':
      _cse = _csespd[0:3]
      _spd = _csespd[4:7]
      if _cse.isdigit() and _spd.isdigit():
        self.cse = float(_cse)
        self.spd = float(_spd)
    return self.value()

  def pos_cmp(self,to_call,info):
    """
    Section 9:
    Compressed position reports
    !/YYYYXXXX$csT - Ugh, just read pages 37-41
    01234567890123
    """
    if len(info) < 12: return None
    _lat = info[2:6]
    _lon = info[6:10]
    _c = info[10]
    _s = info[11]
    _type = info[12]

    self.lat = 90.0 - float((ord(_lat[0])-33) * 91**3 + (ord(_lat[1])-33) * 91**2 + (ord(_lat[2])-33) * 91 + ord(_lat[3])-33)/380926.0
    self.lon = -180.0 + float((ord(_lon[0])-33) * 91**3 + (ord(_lon[1])-33) * 91**2 + (ord(_lon[2])-33) * 91 + ord(_lon[3])-33)/190463.0
    if _c == ' ' or _c == '{':
      return self.value()
    c = ord(_c) - 33
    s = ord(_s) - 33
    self.cse = c * 4.0
    self.spd = 1.08 ** s - 1.0
    return self.value()

  def pos_ts(self,to_call,info):
    """
    position report preceded by timestamp
    / or @ with timestamp (/ = UTC, @ = local)

    /092345z4903.50N/07201.75W-comment text /A=001234
    @092345/4903.50N/07201.75W-comment text /A=001234
    """
    return self.pos(to_call,info[7:])

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

  def mic_e(self,t,i):
    """
    parse position information from a Mic-E packet. 
    ignores message bits, telemetry, etc.
    See Section 10:
    Mic-E pages 42-56
    """
    if len(i) < 6: return None
    beta = i[0] in '\0x1c\0x1d'
    # check for position ambiguity (not sure this is correct)
    self.lat_a = self.lon_a = self.ambiguity[t[0:6].count('Z')]
    # latitude HHMM.SS are encoded as right nibbles of to_call.
    latDD = (ord(t[0])&0x0f)*10 + (ord(t[1])&0x0f)
    latMM = ((ord(t[3])&0x0f)*10.0+ (ord(t[3])&0x0f))/60.0
    latHH = ((ord(t[4])&0x0f)*.1 + (ord(t[5])&0x0f)*.01)/60.0
    # north and west (and other flag) bits are in the left nibbles.
    north = ord(t[3])&0x40
    west = ord(t[5])&0x40
    self.lat = float(latDD) + latMM + latHH
    if not north: self.lat = -self.lat 
    lon_offset = ord(t[4])&0x40
    lonDD = ord(i[1]) - 28;
    lonMM = float(ord(i[2]) - 28)/(60.0);
    lonHH = float((ord(i[3]) - 28)*.01)/(60.0);
    if not beta:                # this stuff is not clearly documented
      if lon_offset:
        lonDD += 100;
      if 180 <= lonDD and lonDD <= 189:
        lonDD -= 80;
      if 190 <= lonDD and lonDD <= 199:
        lonDD -= 190;
      if lonMM >= 60:
        lonMM -= 60;
    self.lon = float(lonDD) + lonMM + lonHH
    if west: self.lon = -self.lon
    sp = ord(i[4]) - 28;
    dc = ord(i[5]) - 28;
    se = ord(i[6]) - 28;
    self.spd = (sp*10.0)+(dc/10.0);
    self.cse = (dc%10)*100.0+se;
    if not beta:
      if self.spd >= 800:
	self.spd -= 800;
      if self.cse >= 400:
	self.cse -= 400;
    return self.value()

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
      print position(r['to_call'],r['info'])
