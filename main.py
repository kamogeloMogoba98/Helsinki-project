# from fastapi import FastAPI
# from fastapi.responses import JSONResponse
# import pyodbc
# from azure.identity import DefaultAzureCredential

# app = FastAPI()

# # --- Database connection ---
# def get_connection():
#     # Get AAD token for Fabric SQL Endpoint
#     credential = DefaultAzureCredential()
#     token = credential.get_token("https://database.windows.net/.default").token
    
#     return pyodbc.connect(
#         "Driver={ODBC Driver 18 for SQL Server};"
#         "Server=tcp:kdf3tskeg22e3ith7kcn6l2m5m-6m7b7l6z6pze5kkmqls2jwwuay.datawarehouse.fabric.microsoft.com;"
#         "Database=vehcile_events_2;"
#         "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
#         attrs_before={1256: token}  # 1256 = SQL_COPT_SS_ACCESS_TOKEN
#     )

# # --- API endpoint ---
# @app.get("/buses")
# def get_buses():
#     conn = get_connection()
#     cursor = conn.cursor()

#     query = """
#     WITH Latest AS (
#         SELECT vehicle_id, line, latitude, longitude, timestamp,
#                ROW_NUMBER() OVER(PARTITION BY vehicle_id ORDER BY timestamp DESC) AS rn
#         FROM vehcile_events_2
#     )
#     SELECT vehicle_id, line, latitude, longitude, timestamp
#     FROM Latest
#     WHERE rn = 1;
#     """
#     cursor.execute(query)
#     rows = cursor.fetchall()

#     # Convert rows → GeoJSON
#     features = []
#     for r in rows:
#         features.append({
#             "type": "Feature",
#             "geometry": {
#                 "type": "Point",
#                 "coordinates": [float(r.longitude), float(r.latitude)]
#             },
#             "properties": {
#                 "vehicle_id": r.vehicle_id,
#                 "line": r.line,
#                 "timestamp": str(r.timestamp)
#             }
#         })

#     return JSONResponse(content={
#         "type": "FeatureCollection",
#         "features": features
#     })


# import pyodbc

# SQL_SERVER = "kdf3tskeg22e3ith7kcn6l2m5m-6m7b7l6z6pze5kkmqls2jwwuay.datawarehouse.fabric.microsoft.com,1433"
# DATABASE = "helsinki_lakehouse"

# try:
#     conn = pyodbc.connect(
#         f"Driver={{ODBC Driver 18 for SQL Server}};"
#         f"Server={SQL_SERVER};Database={DATABASE};Encrypt=yes;TrustServerCertificate=no;"
#     )
#     cursor = conn.cursor()
#     cursor.execute("SELECT TOP 5 * FROM vehicle_events_2")
#     print(cursor.fetchall())
#     conn.close()
# except Exception as e:
#     print(e)


# from azure.identity import DefaultAzureCredential
# import pyodbc

# # ---------- CONFIG ----------
# SQL_SERVER = "kdf3tskeg22e3ith7kcn6l2m5m-6m7b7l6z6pze5kkmqls2jwwuay.datawarehouse.fabric.microsoft.com,1433"
# DATABASE = "helsinki_lakehouse"
# TABLE = "vehicle_events_2"   # check spelling!
# # -----------------------------

# def get_connection():
#     credential = DefaultAzureCredential()
#     token = credential.get_token("https://database.windows.net/.default").token

#     conn_str = (
#         f"Driver={{ODBC Driver 18 for SQL Server}};"
#         f"Server={SQL_SERVER};"
#         f"Database={DATABASE};"
#         "Encrypt=yes;"
#         "TrustServerCertificate=no;"
#         "Connection Timeout=30;"
#     )

#     return pyodbc.connect(conn_str, attrs_before={1256: token})

# try:
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute(f"SELECT TOP 5 * FROM {TABLE}")
#     rows = cursor.fetchall()
#     for row in rows:
#         print(row)
#     conn.close()
# except Exception as e:
#     print(f"Error connecting to Fabric: {e}")


# async def refresh_bus_data():
#     global bus_cache
#     while True:
#         try:
#             conn = get_connection()
#             cursor = conn.cursor()
#             cursor.execute(f"""
#                 SELECT vehicle_id, line, direction, latitude, longitude, timestamp, speed
#                 FROM {TABLE}
#                 ORDER BY timestamp DESC
#             """)
#             rows = cursor.fetchall()
#             columns = [col[0] for col in cursor.description]
#             bus_cache = [dict(zip(columns, row)) for row in rows]
#             conn.close()
#         except Exception as e:
#             print(f"Error refreshing bus data: {e}")
#         await asyncio.sleep(REFRESH_INTERVAL)

# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(refresh_bus_data())

# @app.get("/stream")
# async def stream_buses():
#     async def bus_stream():
#         while True:
#             yield f"data: {json.dumps(bus_cache)}\n\n"
#             await asyncio.sleep(1)
#     return EventSourceResponse(bus_stream())

# from fastapi import FastAPI
# from sse_starlette.sse import EventSourceResponse
# from azure.identity import DefaultAzureCredential
# import pyodbc
# import asyncio
# import json
# from contextlib import asynccontextmanager

# SQL_SERVER = "kdf3tskeg22e3ith7kcn6l2m5m-6m7b7l6z6pze5kkmqls2jwwuay.datawarehouse.fabric.microsoft.com,1433"
# DATABASE = "helsinki_lakehouse"
# TABLE = "vehicle_events_2"
# REFRESH_INTERVAL = 2  # seconds

# bus_cache = []

# def get_connection():
#     credential = DefaultAzureCredential()
#     token = credential.get_token("https://database.windows.net/.default").token
#     conn_str = (
#         f"Driver={{ODBC Driver 18 for SQL Server}};"
#         f"Server={SQL_SERVER};"
#         f"Database={DATABASE};"
#         "Encrypt=yes;"
#         "TrustServerCertificate=no;"
#         "Connection Timeout=30;"
#     )
#     return pyodbc.connect(conn_str, attrs_before={1256: token})

# async def refresh_bus_data():
#     global bus_cache
#     while True:
#         try:
#             conn = get_connection()
#             cursor = conn.cursor()
#             cursor.execute(f"SELECT TOP 10 * FROM {TABLE} ORDER BY timestamp DESC")
#             rows = cursor.fetchall()
#             bus_cache = [dict(zip([c[0] for c in cursor.description], row)) for row in rows]
#             print(bus_cache)
#             conn.close()
#         except Exception as e:
#             print(f"Error refreshing bus data: {e}")
#         await asyncio.sleep(REFRESH_INTERVAL)

# async def bus_stream():
#     while True:
#         yield f"data: {json.dumps(bus_cache)}\n\n"
#         await asyncio.sleep(REFRESH_INTERVAL)

# # Lifespan event handler
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code
#     asyncio.create_task(refresh_bus_data())
#     yield
#     # Shutdown code (if needed)
#     print("App is shutting down...")

# app = FastAPI(lifespan=lifespan)

# @app.get("/stream")
# async def stream_buses():
#     return EventSourceResponse(bus_stream())
import asyncio
import json
import ssl
import uuid
import threading
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware  # Added this
from sse_starlette.sse import EventSourceResponse
import paho.mqtt.client as mqtt

# -------------------------------
# Configuration
# -------------------------------
REFRESH_INTERVAL = 1  # seconds
bus_cache = {}  # vehicle_id -> list of recent positions
bus_cache_lock = threading.Lock()

# -------------------------------
# MQTT callbacks
# -------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT broker successfully")
        client.subscribe("/hfp/v2/journey/ongoing/#")
    else:
        print("Failed to connect, reason code:", reason_code)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if "VP" not in payload: return
        vp = payload["VP"]
        record = {
            "vehicle_id": vp.get("veh"),
            "line": vp.get("desi"),
            "direction": vp.get("dir"),
            "latitude": vp.get("lat"),
            "longitude": vp.get("long"),
            "timestamp": vp.get("tst"),
            "speed": vp.get("spd")
        }
        vehicle_id = record["vehicle_id"]
        if not vehicle_id: return
        with bus_cache_lock:
            bus_cache.setdefault(vehicle_id, []).insert(0, record)
            bus_cache[vehicle_id] = bus_cache[vehicle_id][:10]
    except Exception as e:
        print("Error processing MQTT message:", e)

# -------------------------------
# MQTT client setup
# -------------------------------
client = mqtt.Client(
    client_id=f"bus-tracker-{uuid.uuid4()}",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.hsl.fi", 8883, keepalive=60)
client.loop_start()

# -------------------------------
# SSE streaming
# -------------------------------
async def bus_stream():
    while True:
        with bus_cache_lock:
            latest_positions = [pos[0] for pos in bus_cache.values() if pos]
        yield f"data: {json.dumps(latest_positions)}\n\n"
        await asyncio.sleep(REFRESH_INTERVAL)

# -------------------------------
# FastAPI app & CORS FIX
# -------------------------------
app = FastAPI()

# THIS IS THE KEY PART FOR POWER BI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any origin (including Power BI)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/stream")
async def stream_buses():
    return EventSourceResponse(bus_stream())

@app.get("/ping")
async def ping():
    return {"message": "pong"}