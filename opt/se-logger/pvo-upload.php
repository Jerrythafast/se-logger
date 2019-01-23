<?php
//Version 0.0.10
//SETTINGS
define("DB_HOST", "localhost");
define("DB_NAME", "solaredge");
define("DB_USERNAME", "dbuser");
define("DB_PASSWORD", "dbpassword");
define("PVO_API_KEY", "a2726abcfd6254409e725b628cfaed293745dbca");
define("PVO_SYSTEM_ID", "12345");



$db = new PDO(
  "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8", DB_USERNAME, DB_PASSWORD,
  [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
   PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);

$q = $db->query(
  'SELECT timestamp, p_active, temperature, v_ac, se_day ' .
  'FROM (' .
    'SELECT ' .
      'timestamp, p_active, temperature, v_ac, ' .
      '@curdate := FROM_UNIXTIME(timestamp, "%Y%m%d") date, ' .
      '@prevsum := IF(@prevdate = @curdate, @prevsum + de_day, de_day) se_day, ' .
      '@prevdate := @curdate date2 ' .
    'FROM telemetry_inverter ' .
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
    $row["temperature"] == 0? "" : $row["temperature"],
    $row["v_ac"] == 0? "" : $row["v_ac"]
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
