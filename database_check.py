import datetime
import psycopg2

# Layerbase connection string
DATABASE_URL = "postgresql://postgres:0lKJWsGszjvNna6Wli83BE7l@iot20261-gr09-lost-orbit-pooler.sage.cloud.layerbase.dev/iot20261_gr09?sslmode=require"

try:
  conn = psycopg2.connect(DATABASE_URL)
  cursor = conn.cursor()

  # 1. Fetch all user tables in the 'public' schema
  cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
  tables = cursor.fetchall()

  if not tables:
    print("No tables found in the database yet.")
  else:
    print(f"\n--- FOUND {len(tables)} TABLES IN DATABASE ---")

    # 2. Loop through each table and fetch its contents
    for (table_name,) in tables:
      print(f"\n==============================")
      print(f" TABLE: {table_name}")
      print(f"==============================")

      try:
        # Get column names
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 0;")
        col_names = [desc[0] for desc in cursor.description]
        print(f"Columns: {col_names}")

        # Fetch latest rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
        rows = cursor.fetchall()

        if not rows:
          print(" (Table is currently empty)")
        else:
          print(f" Latest {len(rows)} row(s):")
          for row in rows:
            # Clean and format any datetime objects to regular strings
            cleaned_row = []
            for val in row:
              if isinstance(val, datetime.datetime):
                cleaned_row.append(val.strftime("%Y-%m-%d %H:%M:%S"))
              else:
                cleaned_row.append(val)
            print(f"   {tuple(cleaned_row)}")

      except Exception as table_err:
        print(f" Could not read table {table_name}: {table_err}")

  cursor.close()
  conn.close()

except Exception as e:
  print(f"Database Connection Error: {e}")