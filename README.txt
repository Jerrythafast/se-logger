VERSION 0.0.13

===============================================================================
INSTALLATION INSTRUCTIONS

These instructions may assume working knowledge of managing Linux systems and
MySQL databases.  You may need to be root (i.e., 'sudo') for some of the
commands used.  Tested with Ubuntu 16.04, Python 2.7.11, MySQL 5.7.12, PHP 7.0.

 1. Install the required system packages:
    mysql-server
    php-cli
    php-mysql
    php-curl
    python-mysqldb
    python-crypto

 2. Set up the database tables using the SQL statements in 'database.txt'.

 3. Create the directory '/opt/se-logger' and copy and/or move 'liveupdate.py',
    'pvo-upload.php', and 'se-logger-service.sh' to it.  (It is also possible
    to get this running from a different directory, make sure to edit all
    scripts accordingly.)

 4. Inverters with recent firmware (presumably CPU version 3 or higher) employ
    data encryption when communicating with the SE servers.  Newly installed
    inverters send this key once within the first 2 days after connecting them
    to the internet.  They will not employ encryption until after they have
    sent the key, so you can continue with #5 now.  If your inverter is already
    connected to the internet, the encryption key has to be obtained from the
    inverter first over an RS232 or USB serial connection with the
    'get-key-by-rs232.py' script.  To use it, enter your inverter's serial
    number and the name of the serial port in the SETTINGS area of the script
    and run it.  You may need to install the python-serial system package
    (PySerial) first.

 5. Open 'liveupdate.py' in a text editor and enter your database username and
    password as well as the encryption key of your inverter in the SETTINGS
    area at the top of the script.  If your inverter is newly installed and
    the solaredge-logger will be running from the first day it is connected to
    the internet, you may not need an encryption key the first day - just leave
    it at the default value for now.  You'll know that it started encrypting
    the data when the data stops updating.  Refer to #11 when that happens.

 6. Open 'pvo-upload.php' in a text editor and enter your database username and
    password as well as the PVOutput API key and System ID in the SETTINGS area
    at the top of the script.  You may skip this step if you don't want to set
    up automatic uploading to PVOutput.

 7. Open 'se-logger-service.sh' in a text editor and enter the interface name
    of the network device that connects to the inverter in the SETTINGS area at
    the top of the script.  If traffic from multiple devices is routed over
    this interface, the value of FILTER may need to be changed from 'tcp' to a
    more elaborate tcpdump filter expression to make sure only the inverter's
    communication is captured (e.g., 'tcp and ether host 0:27:02:12:34:56').
    If you decided not to use the default directory, make sure to update the
    value of CAPTDIR accordingly.

 8. Copy and/or move the 'se-logger.service' file to the '/etc/systemd/system'
    directory.  If you decided not to use the default directory, make sure to
    update the path to 'se-logger-service.sh' accordingly.

 9. Run the following command to enable the new service:
    systemctl --now enable se-logger

10. Set up cronjobs for daily restarting the service and updating PVOutput
    every two minutes.  Run 'crontab -e' and copy the contents of 'crontab.txt'
    into your crontab.  If you decided not to install the logger in the default
    directory, make sure to update the paths to '/opt/se-logger' accordingly.
    If you don't want to set up automatic uploading to PVOutput, remove the
    line that contains 'pvo-upload.php'.

11. If your inverter was newly installed and you had not yet entered your
    inverter's encryption key in the 'liveupdate.py' script, you'll know that
    it started encrypting the data when the data stops updating.  Then, you
    can find the encryption key in the 'solaredge-###.pcap' files in the
    '/opt/se-logger' directory by using the 'find-key-in-pcap.py' script.  When
    found, update 'liveupdate.py' with your encryption key.  Then, run
    'python liveupdate.py *.pcap' to update the database and run
    'systemctl restart se-logger' to restart the service to keep it updated.

12. If anything fails to work, you may find error messages in various log files
    that appear in the '/opt/se-logger' directory.


===============================================================================
CHANGELOG

v0.0.13
  - Fixed detection of VLAN-tagged Ethernet frames.

v0.0.12
  - Added support for PCAP files with big-endian byte order.

v0.0.11
  - Added is-pcap-encrypted.py for checking whether any encryption is already
    occurring in the data you captured.
  - No longer sending negative temperatures to PVOutput.
  - Add support for FS Forth-Systeme WiFi modules (in MAC address filter).
  - Added db_port configuration setting (default: 3306).

v0.0.10
  - Added support for inverters connected using WiFi modules (DigiBoard MACs).
  - Fixed a minor issue in liveupdate.py that caused Python to display an extra
    warning if the service would crash.
  - Added date and time to error messages in pvo-upload.log.
  - The se-logger.service will now wait for mysql.service to start up.

v0.0.9
 - Fixed silly warning about 'Data loss: 0 bytes'.
 - Added support for more three-phase inverter firmware versions.
 - Fixed issue with pvo-upload.php in western hemisphere timezones.
 - Added PVOutput upload script for three-phase inverters.

v0.0.8
 - Auto-reconnect to the database if a timeout occurs, and retry connecting up
   to 5 times.
 - Added db_host configuration setting to liveupdate.py (default: 'localhost').

v0.0.7
 - Added support for three-phase inverters.
 - Added detection of non-IPv4-non-TCP traffic (and ignore it).
 - Fixed detection of VLAN-tagged Ethernet frames.
 - Fixed MySQL warnings about out-of-range FLOAT values.
 - Now committing to the database only once per telemetry packet, instead of
   after each item.

v0.0.6
 - Added support for CPU version 3.1818.

v0.0.5
 - Added support for CPU version 3.1651.
 - Added find-key-in-pcap.py to scan for the encryption key in PCAP files.
 - get-key-by-rs232.py will now print an informative error message if PySerial
   is not installed.

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
