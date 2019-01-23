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
Use this script to quickly check whether captured data is encrypted.
"""
import sys, glob

def iglob(pathname):
  success = False
  for result in glob.iglob(pathname):
    success = True
    yield result
  if not success:
    yield pathname


if len(sys.argv) < 2:
  print("%s\n\nTry running: python %s *.pcap" %
    (__doc__.strip("\r\n").replace("\r", "").replace("\n", " "), sys.argv[0]))
  sys.exit(1)

packets = 0
encrypted = 0

for filename in (x for x in sys.argv[1:] for x in iglob(x)):
  print("Reading from %s" % filename)
  f = sys.stdin if filename == "-" else open(filename, "rb")
  data = f.read()
  f.close()

  pos = -1
  while True:
    pos = data.find("\x12\x34\x56\x79", pos + 1)
    if pos == -1 or pos > len(data) - 20:
      break
    packets += 1
    if ord(data[pos+18]) + (ord(data[pos+19]) << 8) in (0x0503, 0x003d):
      encrypted += 1

if not packets:
  print("No SolarEdge data found in input.")
elif not encrypted:
  print("None of the SolarEdge data found appears to be encrypted.")
elif packets == encrypted:
  print("All SolarEdge data found is encrypted.")
else:
  print("%.1f%% of SolarEdge data found is encrypted." %
      (100. * encrypted / packets))
