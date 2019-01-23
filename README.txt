VERSION 0.0.4

===============================================================================
INSTALLATION INSTRUCTIONS

These instructions may assume working knowledge of managing Linux systems and
MySQL databases.  You may need to be root (i.e., 'sudo') for some of the
commands used.  Tested with Ubuntu 16.04, MySQL 5.7.12, PHP 7.0.


 1. Install the required system packages:
    mysql-server
    php-mysql
    php-curl
    python-mysqldb
    python-crypto

 2. Set up the database tables using the SQL statements in 'database.txt'.

 3. Create the directory '/opt/se-logger' and copy and/or move 'liveupdate.py',
    'pvo-upload.php', and 'se-logger-service.sh' to it.  (It is also possible
    to get this running from a different directory, make sure to edit all
    scripts accordingly.)

 4. Open 'liveupdate.py' in a text editor and enter your database username and
    password as well as the encryption key of your inverter in the SETTINGS
    area at the top of the script.  The encryption key can be obtained from the
    inverter using an RS232 or USB connection with the 'getkey.py' script.  To
    use it, enter your inverter's serial number and the name of the serial port
    in the SETTINGS area of 'getkey.py' and run it.

 5. Open 'pvo-upload.php' in a text editor and enter your database username and
    password as well as the PVOutput API key and System ID in the SETTINGS area
    at the top of the script.

 6. Open 'se-logger-service.sh' in a text editor and enter the interface name
    of the network device that connects to the inverter in the SETTINGS area at
    the top of the script.  If traffic from multiple devices is routed over
    this interface, the value of FILTER may need to be changed from 'tcp' to a
    more elaborate tcpdump filter expression to make sure only the inverter's
    communication is captured (e.g., 'tcp and ether host 0:27:02:12:34:56').
    If you decided not to use the default directory, make sure to update the
    value of CAPTDIR accordingly.

 7. Copy and/or move the 'se-logger.service' file to the '/etc/systemd/system'
    directory.  If you decided not to use the default directory, make sure to
    update the path to 'se-logger-service.sh' accordingly.

 8. Run the following command to enable the new service:
    systemctl --now enable se-logger

 9. Set up cronjobs for daily restarting the service and updating PVOutput
    every two minutes.  Run 'crontab -e' and copy the contents of 'crontab.txt'
    into your crontab.  If you decided not to install the logger in the default
    directory, make sure to update the paths to '/opt/se-logger' accordingly.

10. If anything fails to work, you may find error messages in various log files
    that appear in the '/opt/se-logger' directory.


===============================================================================
CHANGELOG

v0.0.4
 - liveupdate.py will no longer try to fill gaps in TCP streams that have been
   terminated by the RST flag.

v0.0.3
 - Added 'uptime' column to the 'telemetry_optimizers' database table.  This is
   the uptime in seconds (approximately) of each optimizer since last wake-up.
   The 'e_day' value is reset to zero when the optimizer wakes up, which may
   happen mid-day in case of very dark rainy periods.
 - Added 'last_telemetry' column to the 'live_update' database table.  This
   field will contain the system time of the moment on which the most recent
   telemetry message was received from the inverter by liveupdate.py.
 - Fixed incomplete reporting of skipped 'mysterious bytes' in liveupdate.py.
 - Improved robustness of liveupdate.py by only parsing the data sent by the
   inverter.  This is detected by looking for the SolarEdge ethernet MAC
   address prefix 00:27:02.
 - Greatly improved robustness of liveupdate.py by recognising and reordering
   out-of-order TCP segments and retransmissions.
 - liveupdate.py will now correctly identify truncated and damaged messages by
   checking the checksums and seeking for another message barker if the
   checksums don't match.

v0.0.2
 - Fixed bug in the detection of mid-day inverter restarts in pvo-upload.php.
 - Changed gmdate("...") + date("Z") to date("...") in pvo-upload.php.
 - Added script that reads the encryption key from the inverter.

v0.0.1
 - Initial version.
