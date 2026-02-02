
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