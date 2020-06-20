<?php
/*
 * Copyright (C) 2020 Jerrythafast
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

//Version 0.0.16
//SETTINGS
define("DB_HOST", "localhost");
define("DB_PORT", "3306");
define("DB_NAME", "solaredge");
define("DB_USERNAME", "dbuser");
define("DB_PASSWORD", "dbpassword");
define("PVO_API_KEY", "a2726abcfd6254409e725b628cfaed293745dbca");
define("PVO_SYSTEM_ID", "12345");
define("PVO_DONATED", true);  // Change 'true' to 'false' if you have not donated to PVOutput.


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
  'AND timestamp > UNIX_TIMESTAMP(NOW() - INTERVAL ' . (PVO_DONATED? '90' : '14') . ' DAY) ' .
  'LIMIT ' . (PVO_DONATED? '100' : '30'));
if($q === false)
  die(date("Y-m-d H:i:s  ") . "Could not get data!" . PHP_EOL);

$data = array();
$timestamps = array();
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
  array_push($timestamps, $row["timestamp"]);
}
$datalen = count($data);
while($datalen) {
  $c = curl_init("http://pvoutput.org/service/r2/addbatchstatus.jsp");
  curl_setopt_array($c, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => "data=" . implode(";", $data),
    CURLOPT_HTTPHEADER => [
      "X-Pvoutput-Apikey: " . PVO_API_KEY,
      "X-Pvoutput-SystemId: " . PVO_SYSTEM_ID
    ]
  ]);
  $result = curl_exec($c);
  $response = curl_getinfo($c, CURLINFO_RESPONSE_CODE);

  if($result === false)
    die(date("Y-m-d H:i:s  ") . "cURL error " . curl_errno($c) . ", exiting: " . curl_error($c) . PHP_EOL);

  if($response !== 200){
    if($response !== 400 || $result !== "Bad request 400: Moon Powered")
      die(date("Y-m-d H:i:s  ") . "PVOutput error " . $response . ", exiting: " . $result . PHP_EOL);

    // Handle 'Moon powered' error.
    if ($datalen > 1) {
      // Try sending the first half of the data again.
      $datalen = (int)($datalen / 2);
      $data = array_slice($data, 0, $datalen);
      $timestamps = array_slice($timestamps, 0, $datalen);
      continue;
    } else {
        echo(date("Y-m-d H:i:s  ") . "Skipping 'Moon powered' timestamp: " . date("Y-m-d H:i:s", $timestamps[0]) . PHP_EOL);
    }
  }

  // Update database to keep track of last sent data point.
  $db->prepare("UPDATE live_update SET pvo_last_live = ?")->execute([array_pop($timestamps)]);
  exit;
}
?>
