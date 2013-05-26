from __future__ import division
"""
parse some APRS-IS data to debug aprsd.c
you can get a live stream from telnet:noam.aprs2.net:14580
"""
import re
import sys
from collections import defaultdict
from telnetlib import Telnet
import time
import pickle
from pprint import pprint
import bz2

class Packet:
  """
  An AX.25 packet as received from an APRS-IS server.
  """
  def __init__(self,from_call='',gate='',info='',full='',clock=0,gtype='',digis='',to_call=''):
    self.from_call = from_call
    self.to_call = to_call
    self.digis = digis
    self.gate = gate
    self.gtype = gtype
    self.info = info
    self.full = full
    self.clock = clock

  def __repr__(self):
    s = 'Packet(from_call="{}",gate="{}",info="{}",full="""{}""",clock={})'
    return s.format(self.from_call,self.gate,self.info.encode('string_escape'),
                    self.full.encode('string_escape'),self.clock)

  def __eq__(self,other):
    """compare only from_call and info fields for equality"""
    return self.from_call == other.from_call and self.info == other.info

  def __ne__(self,other):
    """compare only from_call and info fields for equality"""
    return self.from_call != other.from_call or self.info != other.info

  def __str__(self):
    """pretty string representation of the packet"""
    return """Packet from: {}
         to: {}
      digis: {}
      gtype: {}
       gate: {}
({:4d}) info: "{}"
       full: "{}"
      clock: {}
""".format(self.from_call,self.to_call,self.digis,self.gtype,self.gate,len(self.info),
           self.info.encode('string_escape'),self.full.encode('string_escape'),time.ctime(self.clock))

  def pprint(self):
    """prety print"""
    print self

def parse(l,clock=None):
  """parse a packet into constituent parts and insert into call[<callsign>]
  returns from_call"""
  s = re.match('^(?P<from_call>[^>]+)>(?P<to_call>[^,]+),*(?P<digis>.*),(?P<gtype>[^,]+),(?P<gate>[^:]+)(:)(?P<info>.*)$',l)
  if s:
    fc = s.group('from_call')
    if fc not in call: print fc
    tm = int(time.time()) if clock == None else clock;
    call[fc].append(Packet(from_call=fc,gate=s.group('gate'),info=s.group('info'),
                            full=l,clock=tm,gtype=s.group('gtype'),
                           digis=s.group('digis').split(','),to_call=s.group('to_call')))
    return fc
  else:
    if l[0] != '#': print 'Eh? >>>{}<<<'.format(l)
    return None

def check(fc,quiet=False,diff=None):
  """
  check fromcall <fc> to see if there are other packets that mostly match.
  diff defines how much of a difference in length to consider for statistics-gathering
  or None to count all mismatches.
  mostly match is defined as having extra whitespace on the end of the info.
  returns (mismatches,[list of 'bad' gates])
  """
  mismatches = 0
  badgates = set()
  if fc not in call: return 0
  calls = call[fc]
  for i in range(len(calls)):
    for j in range(i,len(calls)):
      if i != j and calls[i] != calls[j]:
        a = calls[i].info
        b = calls[j].info
        lendiff = abs(len(a)-len(b))
        if a.rstrip(' \r') == b.rstrip(' \r'):
          if (not diff) or (diff and lendiff == diff):
            mismatches += 1
            if (len(a)>len(b)):
              badgates.add(calls[i].gate)
            else:
              badgates.add(calls[j].gate)
            if not quiet:
              print ''.ljust(40,'>')
              print '{}:{}'.format(i,calls[i])
              print '{}:{}'.format(j,calls[j])
              print ''.ljust(40,'<')
  return (mismatches,badgates)

def checkall(quiet=True,diff=None):
  """
  iterate over all callsigns and check for incorrectly-padded packets.
  returns (percentage,[set of bad gates])
  """
  mismatches = 0
  packets = 0
  badgates = set()
  for c in call:
    packets += len(call[c])
    (m,b) = check(c,quiet=quiet,diff=diff)
    mismatches += m
    badgates.update(b)
  print '{} mismatches of len {} out of {} packets ({:.2f}%)'.format(mismatches,diff,packets,(mismatches*100)/packets)
  print '{} bad gateways'.format(len(badgates))
  return (mismatches/packets,badgates)

def guess_gate_type(badgates):
  """
  Try to guess what type of gate is in the badgates set
  """
  for bg in badgates:
    pass

def invert():
  for c,p in call.iteritems():
    for packet in p:
      gate[packet.gate].append(packet)

def logout(tn):
  """logout of telnet session. Sends a ^D and flushes the buffer"""
  tn.write('\0x04')
  counter = 0
  out = ''
  for l in tn.read_some():
    out += l
    counter += 1
    if counter > 1000:
      break
  print out
  tn.close()

def dump(call,fn):
  pk=open(fn,'wb')
  pickle.dump(call,pk)
  pk.close()

def load(fn):
  pk=open(fn,'rb')
  r = pickle.load(pk)
  pk.close()
  return r

if __name__ == '__main__':
  call=defaultdict(list)
  gate=defaultdict(list)

  if len(sys.argv) >= 2:
    fn=sys.argv[1]      
  if len(sys.argv) == 3:
    lines = int(sys.argv[2])
  else:
    lines = None

  if len(sys.argv) >= 2:
    if 'telnet:' in fn:
      mycall,aprspass = open('.aprspass').readline().split()
      out = open('telnet.txt','a')
      if fn == 'telnet:':
        fn = 'telnet:noam.aprs2.net:14580'
        print 'connecting to North America tier 2 server'
      t = re.match('^telnet:(?P<host>[^:]+):(?P<port>.*)$',fn)
      tn = Telnet(t.group('host'),t.group('port'))
      out.write('{} '.format(int(time.time())))
      out.write(tn.read_until('\r\n'))
      tn.write('user {} pass {} filter q/rR/I\n'.format(mycall,aprspass))
      while True:
        try:
          l = tn.read_until('\n')
          tm = int(time.time())
          out.write('{} '.format(tm))
          out.write(l)
          parse(l,clock=tm)
        except:
          break
        if lines:
          lines -= 1
          if lines <= 0:
            print 'logging out'
            logout(tn)
            out.close()
            break
    else:
      if '.bz2' in fn:
        f=bz2.BZ2File(fn)
      else:
        f=open(fn)
      for l in f:
        t = re.match('^(?P<time>[\d\.]+) (?P<packet>.*$)',l)
        if t:
          parse(t.group('packet'),clock=float(t.group('time')))
        else:
          print '?Eh: {}'.format(l)
    print 'if you want to pickle the call list do this:'
    print "dump(call,'call.pickled')"
  else:
    print 'loading pickled call list'
    call = load('call.pickled')

    invert()
    (pct,badgates) = checkall()




    
