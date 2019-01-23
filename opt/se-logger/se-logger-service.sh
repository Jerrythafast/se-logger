#!/bin/bash

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
