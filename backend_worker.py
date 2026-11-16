import json
import time
import paho.mqtt.client as mqtt
import psycopg2

# 1. Configuration
DATABASE_URL = (
    "postgresql://postgres:0lKJWsGszjvNna6Wli83BE7l@iot20261-gr09-lost-orbit-pooler.sage.cloud.layerbase.dev/iot20261_gr09?sslmode=require"
)
MQTT_BROKER = (  # Use "localhost" if running a local broker, or your lab broker IP
    "localhost"
)
MQTT_TOPIC = "lab/group3/dht11"


def save_to_layerbase(temp, humidity):
  """Opens a connection to Layerbase and inserts sensor data."""
  try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO dht11_readings (device_id, temperature, humidity) VALUES"
        " (%s, %s, %s)",
        ("esp32_mock_device", temp, humidity),
    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"-> Successfully saved [Temp: {temp}°C, Humid: {humidity}%] to Layerbase!")
  except Exception as e:
    print(f"Database error: {e}")


# 2. MQTT Callback when a message arrives
def on_message(client, userdata, msg):
  payload_str = msg.payload.decode("utf-8")
  print(f"Received message on topic {msg.topic}: {payload_str}")

  try:
    data = json.loads(payload_str)
    temp = float(data["temperature"])
    humidity = float(data["humidity"])
    save_to_layerbase(temp, humidity)
  except Exception as e:
    print(f"Failed to parse JSON payload: {e}")


# 3. Setup MQTT Client
client = mqtt.Client()
client.on_message = on_message

print(f"Connecting to MQTT broker at {MQTT_BROKER}...")
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC)

# Start the MQTT background network loop
client.loop_start()
print(
    "MQTT Worker is running and listening for data... Press Ctrl+C to stop."
)

try:
  while True:
    time.sleep(1)  # Keep the main thread alive
except KeyboardInterrupt:
  print("Stopping worker...")
  client.loop_stop()