#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>
#include <PubSubClient.h>

// Wi-Fi: giữ thông tin mạng đang dùng trên máy tính.
const char* WIFI_SSID = "Pnm";
const char* WIFI_PASS = "Bangtan1204";

// Mosquitto chạy trên máy tính. Đổi IP nếu địa chỉ LAN của máy tính thay đổi.
const char* MQTT_BROKER = "192.168.1.183";
constexpr uint16_t MQTT_PORT = 1883;
const char* MQTT_TOPIC = "lab/group9/sensors";

// Chân cảm biến
constexpr uint8_t DHT_PIN = 4;
constexpr uint8_t WATER_PIN = 1;  // GPIO1 = ADC1_CH0 trên ESP32-S3
#define DHT_TYPE DHT11

// DHT11 đọc ổn định hơn với khoảng cách 2 giây.
constexpr unsigned long SENSOR_INTERVAL_MS = 2000;
constexpr unsigned long MQTT_RETRY_INTERVAL_MS = 5000;

DHT dht(DHT_PIN, DHT_TYPE);
WebServer server(80);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

float temperatureC = NAN;
float humidity = NAN;
int waterRaw = 0;
unsigned long lastReadMs = 0;
unsigned long lastMqttAttemptMs = 0;

String jsonData() {
  String json = "{";
  json += "\"temperature_c\":";
  json += isnan(temperatureC) ? "null" : String(temperatureC, 1);
  json += ",\"humidity_percent\":";
  json += isnan(humidity) ? "null" : String(humidity, 1);
  json += ",\"water_level_raw\":" + String(waterRaw);
  json += "}";
  return json;
}

void publishSensorData() {
  // Backend hiện tại chuyển hai trường DHT sang float, vì vậy chỉ publish
  // khi DHT11 trả về số hợp lệ (không gửi null cho backend).
  if (!mqttClient.connected() || isnan(temperatureC) || isnan(humidity)) {
    return;
  }

  String payload = jsonData();
  if (mqttClient.publish(MQTT_TOPIC, payload.c_str())) {
    Serial.print("MQTT published: ");
    Serial.println(payload);
  } else {
    Serial.println("MQTT publish failed");
  }
}

void readSensors() {
  humidity = dht.readHumidity();
  temperatureC = dht.readTemperature();
  waterRaw = analogRead(WATER_PIN);

  // JSON trên Serial; khi DHT lỗi, giá trị lỗi được biểu diễn bằng null.
  Serial.println(jsonData());
  publishSensorData();
}

void handleRoot() {
  const char html[] PROGMEM = R"rawliteral(
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32 Sensor JSON</title>
</head>
<body>
  <pre id="data">Đang tải...</pre>
  <script>
    async function updateData() {
      try {
        const response = await fetch('/json');
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const data = await response.json();
        document.getElementById('data').textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        document.getElementById('data').textContent = JSON.stringify({error: error.message}, null, 2);
      }
    }
    updateData();
    setInterval(updateData, 1000);
  </script>
</body>
</html>
)rawliteral";

  server.send(200, "text/html; charset=utf-8", html);
}

void handleJson() {
  server.send(200, "application/json; charset=utf-8", jsonData());
}

void connectMqttIfNeeded() {
  if (WiFi.status() != WL_CONNECTED || mqttClient.connected()) {
    return;
  }

  const unsigned long now = millis();
  if (now - lastMqttAttemptMs < MQTT_RETRY_INTERVAL_MS) {
    return;
  }
  lastMqttAttemptMs = now;

  Serial.print("Connecting to MQTT broker ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_PORT);

  if (mqttClient.connect("ESP32S3_Group9_Sensors")) {
    Serial.println("MQTT connected");
    publishSensorData();  // Gửi mẫu mới nhất sau khi kết nối lại.
  } else {
    Serial.print("MQTT connection failed, state=");
    Serial.println(mqttClient.state());
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  dht.begin();
  analogReadResolution(12);
  analogSetPinAttenuation(WATER_PIN, ADC_11db);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to Wi-Fi");
  unsigned long startMs = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startMs < 20000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("UI: http://");
    Serial.println(WiFi.localIP());
    Serial.print("JSON: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/json");

    server.on("/", handleRoot);
    server.on("/json", handleJson);
    server.begin();

    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setBufferSize(256);
  } else {
    Serial.println("Wi-Fi unavailable; JSON remains available in Serial Monitor.");
  }

  readSensors();
  lastReadMs = millis();
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    server.handleClient();
    connectMqttIfNeeded();
    mqttClient.loop();
  }

  if (millis() - lastReadMs >= SENSOR_INTERVAL_MS) {
    lastReadMs = millis();
    readSensors();
  }
}
