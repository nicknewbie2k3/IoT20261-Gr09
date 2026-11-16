import json
import time
import paho.mqtt.client as mqtt

# 1. Load configuration from config.txt
config = {}
try:
  with open("config.txt", "r") as f:
    for line in f:
      line = line.strip()
      if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip()
  print("Configuration loaded successfully from config.txt")
except FileNotFoundError:
  print("Error: 'config.txt' not found! Please create it in the project folder.")

MQTT_BROKER = config.get("MQTT_BROKER", "localhost")
MQTT_TOPIC = config.get("MQTT_TOPIC", "lab/group9/sensors")

# 2. Setup MQTT Client for the Sensor Node
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)
client.loop_start()

print(f"Sensor node started. Publishing to topic: {MQTT_TOPIC}")
print("Press Ctrl+C to stop publishing.")

try:
  while True:
    # Simulate realistic sensor readings (like your ESP32 would generate)
    sensor_payload = {
        "temperature_c": 28.5,
        "humidity_percent": 65.2,
        "water_level_raw": 1024,
    }

    # Convert dictionary to JSON string
    payload_str = json.dumps(sensor_payload)

    # Publish to the MQTT broker
    client.publish(MQTT_TOPIC, payload_str)
    print(f"-> Sent sensor payload: {payload_str}")

    # Wait 5 seconds before sending the next telemetry batch
    time.sleep(5)

except KeyboardInterrupt:
  print("\nStopping sensor publisher...")
  client.loop_stop()
  client.disconnect()