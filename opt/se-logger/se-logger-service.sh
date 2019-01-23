#!/bin/bash

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


# SETTINGS
INTERFACE=eth0
FILTER=tcp
CAPTDIR=/opt/se-logger/
PREFIX=solaredge-


rm ${CAPTDIR}tcpdump.log
rm ${CAPTDIR}liveupdate.log

# wait for the time to get set
while [ `date -u +%Y` == "1970" ]
do
	echo "Waiting for correct time" >> ${CAPTDIR}tcpdump.log
	sleep 1
done

/usr/bin/stdbuf -i0 -o0 -e0 /usr/sbin/tcpdump -i $INTERFACE -U -w - ${FILTER} 2>> ${CAPTDIR}tcpdump.log | \
	tee $CAPTDIR$PREFIX`date -u +%Y%m%d%H%M%S`.pcap | \
	/usr/bin/python -u ${CAPTDIR}liveupdate.py - 2>> ${CAPTDIR}liveupdate.log
