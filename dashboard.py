import streamlit as st
import boto3
import re
import pickle
import pandas as pd
from collections import Counter
from streamlit_autorefresh import st_autorefresh

# CONFIG
LOG_GROUP = "chronolog-group"
LOG_STREAM = "chronolog-stream"
REGION = "us-east-1"

# AWS CLIENT
client = boto3.client("logs", region_name=REGION)

# LOAD MODEL
@st.cache_resource
def load_models():
    with open("model.pkl", "rb") as f:
        kmeans = pickle.load(f)

    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    return kmeans, vectorizer

kmeans, vectorizer = load_models()

# CLEAN FUNCTION
def clean_log(line):
    line = re.sub(r"[^a-zA-Z ]", " ", line)
    return line.lower().strip()

# SESSION STATE
if "labels_list" not in st.session_state:
    st.session_state.labels_list = []

if "logs" not in st.session_state:
    st.session_state.logs = []

if "anomaly_logs" not in st.session_state:
    st.session_state.anomaly_logs = []

if "log_types" not in st.session_state:
    st.session_state.log_types = []

if "next_token" not in st.session_state:
    st.session_state.next_token = None

if "seen_event_ids" not in st.session_state:
    st.session_state.seen_event_ids = set()

if "anomaly_count_history" not in st.session_state:
    st.session_state.anomaly_count_history = []

if "total_log_count" not in st.session_state:
    st.session_state.total_log_count = 0

# 🔥 NEW (delta tracking)
if "prev_total" not in st.session_state:
    st.session_state.prev_total = 0

# UI
st.title("☁️ ChronoLog AI Cloud Monitoring")
st.subheader("Real-Time Streaming Logs + Anomaly Detection")


# FETCH LOGS
def fetch_logs():
    try:
        kwargs = {
            "logGroupName": LOG_GROUP,
            "logStreamName": LOG_STREAM,
            "startFromHead": False
        }

        if st.session_state.next_token:
            kwargs["nextToken"] = st.session_state.next_token

        response = client.get_log_events(**kwargs)
        st.session_state.next_token = response.get("nextForwardToken")

        return response["events"]

    except Exception as e:
        st.error(f"AWS Error: {e}")
        return []

# -------------------------
# PROCESS LOGS
def process_logs(events):
    THRESHOLD = 5

    for event in events:
        event_id = f"{event['timestamp']}_{event['message']}"

        if event_id in st.session_state.seen_event_ids:
            continue

        st.session_state.seen_event_ids.add(event_id)

        raw_log = event["message"]
        timestamp = event["timestamp"]

        # ML
        cleaned = clean_log(raw_log)
        X = vectorizer.transform([cleaned])
        label = kmeans.predict(X)[0]

        st.session_state.labels_list.append(label)
        cluster_counts = Counter(st.session_state.labels_list)

        # TYPE
        log_type = "INFO"
        if "error" in raw_log.lower():
            log_type = "ERROR"
        elif "warn" in raw_log.lower():
            log_type = "WARN"

        st.session_state.log_types.append(log_type)

        # ANOMALY
        if cluster_counts[label] <= THRESHOLD:
            reason = f"Cluster {label} is rare ({cluster_counts[label]})"
            log_text = f"{timestamp} | ⚠️ {raw_log} | {reason}"

            st.session_state.anomaly_logs.append({
                "log": raw_log,
                "label": label,
                "count": cluster_counts[label]
            })
        else:
            log_text = f"{timestamp} | {raw_log}"

        st.session_state.logs.append(log_text)

        # ✅ running counter
        st.session_state.total_log_count += 1

    # memory control
    if len(st.session_state.logs) > 5000:
        st.session_state.logs = st.session_state.logs[-3000:]

    st.session_state.anomaly_logs = st.session_state.anomaly_logs[-20:]
    st.session_state.log_types = st.session_state.log_types[-200:]

    # 📈 trend
    st.session_state.anomaly_count_history.append(len(st.session_state.anomaly_logs))
    st.session_state.anomaly_count_history = st.session_state.anomaly_count_history[-100:]

# -------------------------
# RUN
# -------------------------
events = fetch_logs()
process_logs(events)

# -------------------------
# METRICS (🔥 DELTA FIX)
# -------------------------
delta = st.session_state.total_log_count - st.session_state.prev_total

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Logs", st.session_state.total_log_count, delta=delta)

with col2:
    st.metric("Anomalies", len(st.session_state.anomaly_logs))

# update prev
st.session_state.prev_total = st.session_state.total_log_count

# -------------------------
# GRAPH
# -------------------------
st.subheader("📊 Log Analytics")

if st.session_state.log_types:
    df = pd.DataFrame(st.session_state.log_types, columns=["type"])
    st.bar_chart(df["type"].value_counts())

# -------------------------
# 📈 TREND
# -------------------------
st.subheader("📈 Anomaly Trend Over Time")

if st.session_state.anomaly_count_history:
    trend_df = pd.DataFrame(
        st.session_state.anomaly_count_history,
        columns=["Anomalies"]
    )
    st.line_chart(trend_df)

# -------------------------
# LIVE LOGS
# -------------------------
st.subheader("📡 Live Log Stream")

log_text = "\n".join(st.session_state.logs[-30:])
st.code(log_text)

# -------------------------
# ANOMALIES
# -------------------------
st.subheader("🚨 Detected Anomalies")

for item in st.session_state.anomaly_logs[-10:]:
    st.warning(
        f"{item['log']} \n👉 Cluster: {item['label']} | Occurrence: {item['count']}"
    )

# -------------------------
# AUTO REFRESH
# -------------------------
st_autorefresh(interval=2000, key="refresh")