import boto3
import time
import random

# -------------------------------------------------
# AWS CLIENT
# -------------------------------------------------
client = boto3.client(
    "logs",
    region_name="us-east-1"
)

# -------------------------------------------------
# CLOUDWATCH CONFIG
# -------------------------------------------------
log_group = "chronolog-group"
log_stream = "chronolog-stream"

# -------------------------------------------------
# LOG DATASET
# -------------------------------------------------
logs = [

    # ---------------- NORMAL ----------------
    "INFO user login successful",
    "INFO service started",
    "INFO backup completed",
    "INFO cache refreshed",

    # ---------------- WARNING ----------------
    "WARN high memory usage",
    "WARN disk space low",
    "WARN cpu spike detected",

    # ---------------- ERROR ----------------
    "ERROR database timeout",
    "ERROR API failed",
    "ERROR payment gateway failed",

    # ---------------- CRITICAL ----------------
    "CRITICAL container crashed",
    "CRITICAL unauthorized access",
    "CRITICAL kubernetes node failure",
    "CRITICAL ransomware activity detected"
]

# -------------------------------------------------
# TOKEN
# -------------------------------------------------
sequence_token = None

print("\n🚀 ChronoLog AI Real-Time Pipeline Started...\n")

# -------------------------------------------------
# REAL-TIME LOOP
# -------------------------------------------------
while True:

    # -------------------------------------------------
    # RANDOM SYSTEM STATE
    # -------------------------------------------------
    mode = random.choice([
        "stable",
        "warning",
        "critical"
    ])

    # -------------------------------------------------
    # STABLE MODE
    # -------------------------------------------------
    if mode == "stable":

        selected_log = random.choice(logs[:4])

        print("🟢 SYSTEM STATE → STABLE")

    # -------------------------------------------------
    # WARNING MODE
    # -------------------------------------------------
    elif mode == "warning":

        selected_log = random.choice(logs[4:10])

        print("🟠 SYSTEM STATE → RISK DETECTED")

    # -------------------------------------------------
    # CRITICAL MODE
    # -------------------------------------------------
    else:

        selected_log = random.choice(logs[10:])

        print("🔴 SYSTEM STATE → FAILURE")

    # -------------------------------------------------
    # CREATE LOG EVENT
    # -------------------------------------------------
    log_event = {
        'timestamp': int(time.time() * 1000),
        'message': selected_log
    }

    # -------------------------------------------------
    # CLOUDWATCH PAYLOAD
    # -------------------------------------------------
    kwargs = {
        'logGroupName': log_group,
        'logStreamName': log_stream,
        'logEvents': [log_event]
    }

    if sequence_token:
        kwargs['sequenceToken'] = sequence_token

    # -------------------------------------------------
    # PUSH LOG TO CLOUDWATCH
    # -------------------------------------------------
    response = client.put_log_events(**kwargs)

    sequence_token = response['nextSequenceToken']

    print(f"📡 Sent Log → {selected_log}")

    print("-" * 60)

    # -------------------------------------------------
    # WAIT
    # -------------------------------------------------
    time.sleep(3)