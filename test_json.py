import json
import sys
import re
f=open(sys.argv[1])
dd=[]
i=0
for l in f:
  i=i+1
  try:
    dd.append(json.loads(l))
  except:
    emsg = sys.exc_info()[1].message
    if '(char' in emsg:
      r = re.match(".*\(char (?P<col>\d*)",emsg)
      if r:
        start_col = int(r.group('col'))
    else:
      start_col = 0
    sc = start_col-10
    if sc < 0: sc = 0
    print "%d: %s:\n%s ...\n          ^"%(i,emsg,l[sc:sc+40])
    continue

