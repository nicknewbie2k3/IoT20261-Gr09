import json
import time
import paho.mqtt.client as mqtt
import psycopg2

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

DATABASE_URL = config.get("DATABASE_URL")
MQTT_BROKER = config.get("MQTT_BROKER", "localhost")
MQTT_TOPIC = config.get("MQTT_TOPIC", "lab/group9/sensors")


def init_db():
  """Creates tables without an ID column if they don't exist yet."""
  try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Table 1: DHT11 Sensor Data (No ID)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS dht11_readings (
                temperature FLOAT NOT NULL,
                humidity FLOAT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # Table 2: Water Level Sensor Data (No ID)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_level_readings (
                water_level_raw INT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables verified/created successfully (without ID).")
  except Exception as e:
    print(f"Database initialization error: {e}")


def save_to_layerbase(temp, humidity, water_raw):
  """Inserts sensor data and trims tables to keep only the latest 100 rows."""
  try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # 1. Insert DHT11 readings
    cursor.execute(
        "INSERT INTO dht11_readings (temperature, humidity) VALUES (%s, %s)",
        (temp, humidity),
    )

    # 2. Trim dht11_readings using ctid/recorded_at to keep latest 100 rows
    cursor.execute("""
            DELETE FROM dht11_readings 
            WHERE ctid NOT IN (
                SELECT ctid FROM dht11_readings 
                ORDER BY recorded_at DESC 
                LIMIT 100
            );
        """)

    # 3. Insert Water Level readings
    cursor.execute(
        "INSERT INTO water_level_readings (water_level_raw) VALUES (%s)",
        (water_raw,),
    )

    # 4. Trim water_level_readings using ctid/recorded_at to keep latest 100 rows
    cursor.execute("""
            DELETE FROM water_level_readings 
            WHERE ctid NOT IN (
                SELECT ctid FROM water_level_readings 
                ORDER BY recorded_at DESC 
                LIMIT 100
            );
        """)

    conn.commit()
    cursor.close()
    conn.close()

    print(
        "-> Successfully saved and trimmed tables to max 100 rows (no ID"
        " column)!"
    )

  except Exception as e:
    print(f"Database error during insert/trim: {e}")


def on_message(client, userdata, msg):
  payload_str = msg.payload.decode("utf-8")
  print(f"Received JSON payload: {payload_str}")

  try:
    data = json.loads(payload_str)
    temp = float(data["temperature_c"])
    humidity = float(data["humidity_percent"])
    water_raw = int(data["water_level_raw"])

    save_to_layerbase(temp, humidity, water_raw)

  except Exception as e:
    print(f"Failed to parse or save payload: {e}")


if __name__ == "__main__":
  init_db()

  client = mqtt.Client()
  client.on_message = on_message

  print(f"Connecting to MQTT broker at {MQTT_BROKER}...")
  client.connect(MQTT_BROKER, 1883, 60)
  client.subscribe(MQTT_TOPIC)

  client.loop_start()
  print("Backend worker is listening for sensor packets...")

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    client.loop_stop()