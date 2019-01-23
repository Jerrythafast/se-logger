#!/usr/bin/env python

#
# Copyright (C) 2019 Jerrythafast
#
# This file is part of se-logger, which captures telemetry data from
# the TCP traffic of SolarEdge PV inverters.
#
# se-logger is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# se-logger is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with se-logger.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Use this script to find your SolarEdge inverter's encryption key in
PCAP network traffic capture files.
"""
import sys, glob

if len(sys.argv) < 2:
  print("%s\n\nTry running: python %s *.pcap" %
    (__doc__.strip("\r\n").replace("\r", "").replace("\n", " "), sys.argv[0]))
  sys.exit(1)


def iglob(pathname):
  success = False
  for result in glob.iglob(pathname):
    success = True
    yield result
  if not success:
    yield pathname


"""
Finding: (** = checksum of packet, __ = bytes of key)
0   12 34 56 79 02 00 fd ff qq rr fd ff ff ff ss tt uu vv 12 00 39 02 ** **
1   12 34 56 79 06 00 f9 ff qq rr ss tt uu vv fd ff ff ff 90 00 __ __ __ __ 00 00 ** **
2   12 34 56 79 02 00 fd ff ww xx fd ff ff ff ss tt uu vv 12 00 3a 02 ** **
3   12 34 56 79 06 00 f9 ff ww xx ss tt uu vv fd ff ff ff 90 00 __ __ __ __ 00 00 ** **
4   12 34 56 79 02 00 fd ff yy zz fd ff ff ff ss tt uu vv 12 00 3b 02 ** **
5   12 34 56 79 06 00 f9 ff yy zz ss tt uu vv fd ff ff ff 90 00 __ __ __ __ 00 00 ** **
6   12 34 56 79 02 00 fd ff mm nn fd ff ff ff ss tt uu vv 12 00 3c 02 ** **
7   12 34 56 79 06 00 f9 ff mm nn ss tt uu vv fd ff ff ff 90 00 __ __ __ __ 00 00 ** **
"""
BARKER = "\x12\x34\x56\x79"
LEN1 = "\x02\x00\xfd\xff"
LEN2 = "\x06\x00\xf9\xff"
ID1 = "\xfd\xff\xff\xff"
CMD1 = "\x12\x00"
CMD2 = "\x90\x00"
PARAMS = ("\x39\x02", "\x3a\x02", "\x3b\x02", "\x3c\x02")
PTYPE = "\x00\x00"

seq = ""
id2 = ""
key = ""
state = 0

for filename in (x for x in sys.argv[1:] for x in iglob(x)):
  print("Reading from %s" % filename)
  if filename == "-":
    f = sys.stdin
  else:
    f = open(filename, 'rb')
  data = f.read()
  f.close()

  pos = -1
  while True:
    if state == 0:
      pos = data.find(BARKER + LEN1, pos + 1)
      if pos == -1:
        break
      if data[pos+10:pos+14] != ID1 or data[pos+18:pos+22] != CMD1 + PARAMS[0]:
        continue
      seq = data[pos+8:pos+10]
      id2 = data[pos+14:pos+18]
      state = 1
      pos += 23
    elif state in (1, 3, 5, 7):
      pos = data.find(BARKER + LEN2 + seq + id2 + ID1 + CMD2, pos + 1)
      if pos == -1:
        break
      if data[pos+24:pos+26] != PTYPE:
        continue
      key += data[pos+20:pos+24]
      state += 1
      pos += 27
    elif state in (2, 4, 6):
      pos = data.find(BARKER + LEN1, pos + 1)
      if pos == -1:
        break
      if data[pos+10:pos+22] != ID1 + id2 + CMD1 + PARAMS[state/2]:
        continue
      seq = data[pos+8:pos+10]
      state += 1
      pos += 23
    elif state == 8:
      print("Found it! Your key is '%s'" % ("".join("\\x%02x" % ord(x) for x in key)))
      sys.exit(0)

if state < 2:
  print("Sorry, your key is not in the given input file(s).")
else:
  print("Sorry, only the first part of your key is in the given input file(s).")
  print("Your key starts with '%s'" % ("".join("\\x%02x" % ord(x) for x in key)))

