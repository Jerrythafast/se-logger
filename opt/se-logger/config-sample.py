#!/usr/bin/env python3

#
# Copyright (C) 2020 Jerrythafast
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

# Sample config.py file.
# Copy this file to config.py and change below settings

# SETTINGS
inverter_private_key = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
db_user = "dbuser"
db_pass = "dbpassword"
db_name = "solaredge"
db_host = "localhost"
db_port = 3306

