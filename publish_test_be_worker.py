import json
import paho.mqtt.client as mqtt

# Load configuration dynamically from config.txt
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
  print(
      "Error: 'config.txt' not found! Please create it in the project folder."
  )

# Assign configuration variables (with fallbacks if missing)
MQTT_BROKER = config.get("MQTT_BROKER", "localhost")
MQTT_TOPIC = config.get("MQTT_TOPIC", "lab/group9/sensors")

# Connect to the MQTT broker using the config file settings
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)

# Create the test payload matching your multi-sensor JSON format
payload = json.dumps(
    {"temperature_c": 29.9, "humidity_percent": 76.0, "water_level_raw": 0}
)

# Publish to the topic read from config.txt
client.publish(MQTT_TOPIC, payload)
client.disconnect()

print(f"Multi-sensor test payload published successfully to '{MQTT_TOPIC}'!")