<?php
/*
 * Copyright (C) 2019 Jerrythafast
 *
 * This file is part of se-logger, which captures telemetry data from
 * the TCP traffic of SolarEdge PV inverters.
 *
 * se-logger is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at
 * your option) any later version.
 *
 * se-logger is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with se-logger.  If not, see <http://www.gnu.org/licenses/>.
 */

//Version 0.0.11
//SETTINGS
define("DB_HOST", "localhost");
define("DB_PORT", "3306");
define("DB_NAME", "solaredge");
define("DB_USERNAME", "dbuser");
define("DB_PASSWORD", "dbpassword");
define("PVO_API_KEY", "a2726abcfd6254409e725b628cfaed293745dbca");
define("PVO_SYSTEM_ID", "12345");



$db = new PDO(
  "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8", DB_USERNAME, DB_PASSWORD,
  [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
   PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);

$q = $db->query(
  'SELECT timestamp, p_active, temperature, v_dc, se_day ' .
  'FROM (' .
    'SELECT ' .
      'timestamp, p_active1+p_active2+p_active3 p_active, temperature, v_dc, ' .
      '@curdate := FROM_UNIXTIME(timestamp, "%Y%m%d") date, ' .
      '@prevsum := IF(@prevdate = @curdate, @prevsum + de_day, de_day) se_day, ' .
      '@prevdate := @curdate date2 ' .
    'FROM telemetry_inverter_3phase ' .
    'JOIN (SELECT @prevsum := 0, @curdate := NULL, @prevdate := NULL) vars ' .
    'WHERE timestamp >= (SELECT IFNULL(UNIX_TIMESTAMP(FROM_UNIXTIME(pvo_last_live, "%Y%m%d")), 0) FROM live_update) ' .
    'ORDER BY timestamp' .
  ') x ' .
  'WHERE timestamp > (SELECT pvo_last_live FROM live_update) ' .
  'LIMIT 100');
if($q === false)
  die(date("Y-m-d H:i:s  ") . "Could not get data!" . PHP_EOL);

$lastdate = 0;
$data = array();
while($row = $q->fetch()){
  array_push($data, implode(",", [
    date("Ymd", $row["timestamp"]),
    date("H:i", $row["timestamp"]),
    round($row["se_day"]),
    round($row["p_active"]),
    "",
    "",
    $row["temperature"] <= 0? "" : $row["temperature"],
    $row["v_dc"] == 0? "" : $row["v_dc"]
  ]));
  $lastdate = $row["timestamp"];
}
$data = implode(";", $data);
if(!$data)
  exit;

$c = curl_init("http://pvoutput.org/service/r2/addbatchstatus.jsp");
curl_setopt_array($c, [
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_FAILONERROR => true,
  CURLOPT_POST => true,
  CURLOPT_POSTFIELDS => "data=" . $data,
  CURLOPT_HTTPHEADER => [
    "X-Pvoutput-Apikey: " . PVO_API_KEY,
    "X-Pvoutput-SystemId: " . PVO_SYSTEM_ID
  ]
]);
if(curl_exec($c) === false)
  die(date("Y-m-d H:i:s  ") . "cURL error, exiting: " . curl_error($c) . PHP_EOL);

$db->prepare("UPDATE live_update SET pvo_last_live = ?")->execute([$lastdate]);
?>
