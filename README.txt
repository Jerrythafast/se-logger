VERSION 0.0.1

Installation instructions.

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
    area at the top of the script.

 5. Open 'pvo-upload.php' in a text editor and enter your database username and
    password as well as the PVOutput API key and System ID in the SETTINGS area
    at the top of the script.

 6. Open 'se-logger-service.sh' in a text editor and enter the interface name
    of the network device that connects to the inverter in the SETTINGS area at
    the top of the script.  If traffic from multiple devices is routed over
    this interface, the value of FILTER may need to be changed from 'tcp' to a
    more elaborate tcpdump filter expression to make sure only the inverter's
    communication is captured.  If you decided not to use the default
    directory, make sure to update the value of CAPTDIR accordingly.

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
