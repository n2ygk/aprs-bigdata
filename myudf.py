#/usr/bin/python
import re 
"""
 Pig Latin APRS parsing UDF.
 Given an input string, parse into several fields, including a "firstheard" digipeater callsign.
"""
@outputSchema("time:chararray,from_call:chararray,to_call:chararray,digis:chararray,gtype:chararray,gate:chararray,info:chararray,firstheard:chararray")
def aprs(l):
  s = re.match('^(?P<time>^[^ ]*) (?P<from_call>[^>]+)>(?P<to_call>[^,]+),*(?P<digis>.*),(?P<gtype>[^,]+),(?P<gate>[^:]+)(:)(?P<info>.*)$',l)
  if s:
    digis = s.group('digis')
    if '*' in digis:
      firstheard=digis.split(',')[0]
    else:
      firstheard=s.group('gate')
    return s.group('time'),s.group('from_call'),s.group('to_call'),s.group('digis'),s.group('gtype'),s.group('gate'),s.group('info'),firstheard

