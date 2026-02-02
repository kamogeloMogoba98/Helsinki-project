import requests
import json
from datetime import datetime
import boto3
from google.transit import gtfs_realtime_pb2
import time

# -----------------------------
# CONFIG
# -----------------------------
S3_BUCKET = ""
S3_REGION = ""
ATHENA_DB = ""
ATHENA_TABLE = ""
ATHENA_OUTPUT = "s3://"  # ✅ real bucket for Athena results

# Vehicle IDs to track
TRACK_VEHICLES = ["22/1023", "22/1265", "18/634", "22/915"]

# -----------------------------
# AWS CLIENTS
# -----------------------------
s3 = boto3.client("s3", region_name=S3_REGION)
athena = boto3.client("athena", region_name=S3_REGION)

# -----------------------------
# Athena helper functions
# -----------------------------
def run_athena_query(query):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": ATHENA_DB},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
    )
    exec_id = response["QueryExecutionId"]

    # Wait until query finishes
    while True:
        stats = athena.get_query_execution(QueryExecutionId=exec_id)
        state = stats["QueryExecution"]["Status"]["State"]
        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        time.sleep(1)

    if state != "SUCCEEDED":
        raise Exception(f"Athena query failed: {state}")
    return exec_id

def drop_and_create_table():
    drop_query = f"DROP TABLE IF EXISTS {ATHENA_TABLE}"
    create_query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {ATHENA_TABLE} (
        vehicle_id string,
        line string,
        latitude double,
        longitude double,
        speed double,
        current_status string,
        event_timestamp string
    )
    PARTITIONED BY (year int, month int, day int, hour int)
    ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
    LOCATION 's3://{S3_BUCKET}/';
    """
    print("Dropping and creating Athena table...")
    run_athena_query(drop_query)
    run_athena_query(create_query)
    print("Table ready.")

def add_partitions():
    """Repair table partitions after uploading data"""
    query = f"MSCK REPAIR TABLE {ATHENA_TABLE};"
    run_athena_query(query)
    print("Partitions updated in Athena.")

# -----------------------------
# Fetch GTFS-RT feed
# -----------------------------
URL = "https://realtime.hsl.fi/realtime/vehicle-positions/v2/hsl"

def fetch_and_store():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(URL)
    feed.ParseFromString(response.content)

    uploaded_hours = set()  # track which hours we upload to

    for entity in feed.entity:
        if entity.HasField("vehicle"):
            v = entity.vehicle
            vehicle_id = v.vehicle.id

            # Track only selected vehicles
            if vehicle_id not in TRACK_VEHICLES:
                continue

            record = {
                "vehicle_id": vehicle_id,
                "line": v.trip.route_id,
                "latitude": v.position.latitude,
                "longitude": v.position.longitude,
                "speed": getattr(v.position, "speed", 0.0),
                "current_status": v.current_status,
                "event_timestamp": str(v.timestamp) if hasattr(v, "timestamp") else "",
            }

            now = datetime.utcnow()
            key = (
                f"year={now.year}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}/"
                f"{vehicle_id.replace('/', '-')}-{now.strftime('%H%M%S%f')}.json"
            )

            s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(record))
            print(f"Saved vehicle {vehicle_id} to S3: {key}")

            uploaded_hours.add((now.year, now.month, now.day, now.hour))

    # Add partitions for the hours uploaded
    if uploaded_hours:
        add_partitions()

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    drop_and_create_table()
    print("Fetching vehicle positions and storing to S3...")
    fetch_and_store()
    print("Done!")


#we need to have a staging table to bring the latest data and and then adding to the existing athena table instead of drop the whole athena table and lossing data
#we need to cron job the script to run every 5 minutes where it loads mqqt data that runs for 3 minutes and adds the data to the staging tables and suppsiquent tables 