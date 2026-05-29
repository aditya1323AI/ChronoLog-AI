import streamlit as st
import boto3
import json
import re
import pickle
import pandas as pd
import time
from datetime import datetime
from collections import Counter
from streamlit_autorefresh import st_autorefresh

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="ChronoLog AI",
    page_icon="☁️",
    layout="wide"
)

# -------------------------------------------------
# AWS CONSOLE STYLE CSS
# -------------------------------------------------
st.markdown("""
<style>

.main {
    background-color: #16191f;
    color: #ffffff;
}

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

.stMetric {
    background-color: #1f232a;
    border: 1px solid #30363d;
    padding: 12px;
    border-radius: 8px;
}

.aws-log-box {
    background-color: #1f232a;
    border: 1px solid #30363d;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 8px;
    font-family: monospace;
    font-size: 14px;
    box-shadow: 0 0 5px rgba(0,0,0,0.3);
}

.critical {
    border-left: 4px solid #ff4b4b;
    box-shadow: 0 0 10px rgba(255,75,75,0.2);
}

.warning {
    border-left: 4px solid #ff9900;
}

.info {
    border-left: 4px solid #4da6ff;
}

.title-style {
    font-size: 34px;
    font-weight: 600;
    color: #ffffff;
}

.small-text {
    color: #9ba7b4;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
LOG_GROUP = "chronolog-group"
LOG_STREAM = "chronolog-stream"
REGION = "us-east-1"

TOPIC_ARN = "arn:aws:sns:us-east-1:007608901852:Chronolog"

BUCKET_NAME = "chronolog-ai-reports"

# -------------------------------------------------
# AWS CLIENTS
# -------------------------------------------------
client = boto3.client("logs", region_name=REGION)

sns_client = boto3.client("sns", region_name=REGION)

s3_client = boto3.client("s3", region_name=REGION)

# -------------------------------------------------
# LOAD MODEL
# -------------------------------------------------
@st.cache_resource
def load_models():

    with open("model.pkl", "rb") as f:
        kmeans = pickle.load(f)

    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    return kmeans, vectorizer

kmeans, vectorizer = load_models()

# -------------------------------------------------
# CLEAN FUNCTION
# -------------------------------------------------
def clean_log(line):
    line = re.sub(r"[^a-zA-Z ]", " ", line)
    return line.lower().strip()

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
def init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

init_state("labels_list", [])
init_state("logs", [])
init_state("anomaly_logs", [])
init_state("log_types", [])
init_state("next_token", None)
init_state("seen_event_ids", set())
init_state("anomaly_count_history", [])
init_state("total_log_count", 0)
init_state("prev_total", 0)
init_state("last_alert_time", 0)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("⚙️ ChronoLog Controls")

threshold = st.sidebar.slider(
    "Anomaly Threshold",
    min_value=1,
    max_value=10,
    value=5
)

window_size = st.sidebar.slider(
    "Detection Window",
    min_value=10,
    max_value=100,
    value=20
)

search_term = st.sidebar.text_input("Search Logs")

# RESET BUTTON
if st.sidebar.button("Reset Dashboard"):

    st.session_state.logs = []
    st.session_state.anomaly_logs = []
    st.session_state.labels_list = []
    st.session_state.log_types = []
    st.session_state.total_log_count = 0
    st.session_state.prev_total = 0
    st.session_state.anomaly_count_history = []
    st.session_state.seen_event_ids = set()

    st.rerun()

st.sidebar.markdown("---")

st.sidebar.success("Monitoring Active")

st.sidebar.info(
    "Adaptive anomaly detection using machine learning and rolling log analysis."
)

# -------------------------------------------------
# HEADER
# -------------------------------------------------
col1, col2 = st.columns([5, 1])

with col1:

    st.markdown(
        '<p class="title-style">☁️ ChronoLog AI Dashboard</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="small-text">AWS Cloud Monitoring | AI Anomaly Detection | SNS Alerting</p>',
        unsafe_allow_html=True
    )

with col2:

    current_clock = datetime.now().strftime("%H:%M:%S")

    st.markdown(f"### {current_clock}")

# -------------------------------------------------
# FETCH LOGS
# -------------------------------------------------
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

        st.session_state.next_token = response.get(
            "nextForwardToken"
        )

        return response["events"]

    except Exception as e:

        st.error(f"AWS Error: {e}")

        return []

# -------------------------------------------------
# SNS ALERT
# -------------------------------------------------
def send_sns_alert(message, severity):

    try:

        sns_client.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"ChronoLog AI Alert - {severity}",
            Message=json.dumps({
                "Severity": severity,
                "Alert": message,
                "System": "ChronoLog AI",
                "Status": "Critical Event Detected"
            }, indent=2)
        )

    except Exception as e:

        st.error(f"SNS Error: {e}")

# -------------------------------------------------
# S3 REPORT UPLOAD
# -------------------------------------------------
def upload_report_to_s3():

    if not st.session_state.anomaly_logs:

        st.warning("No anomaly logs available")

        return

    report_content = ""

    for item in st.session_state.anomaly_logs:

        report_content += (
            f"{item['message']} | "
            f"Severity: {item['severity']} | "
            f"Cluster: {item['cluster']}\n"
        )

    filename = f"incident_report_{int(time.time())}.txt"

    try:

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=report_content
        )

        st.success(f"Report uploaded to S3 → {filename}")

    except Exception as e:

        st.error(f"S3 Upload Error: {e}")

# -------------------------------------------------
# PROCESS LOGS
# -------------------------------------------------
def process_logs(events):

    for event in events:

        event_id = f"{event['timestamp']}_{event['message']}"

        if event_id in st.session_state.seen_event_ids:
            continue

        st.session_state.seen_event_ids.add(event_id)

        raw_log = event["message"]

        timestamp = event["timestamp"]

        # -------------------------------------------------
        # ML PROCESSING
        # -------------------------------------------------
        cleaned = clean_log(raw_log)

        X = vectorizer.transform([cleaned])

        label = kmeans.predict(X)[0]

        st.session_state.labels_list.append(label)

        # -------------------------------------------------
        # ROLLING WINDOW DETECTION
        # -------------------------------------------------
        recent_labels = st.session_state.labels_list[-window_size:]

        cluster_counts = Counter(recent_labels)

        # -------------------------------------------------
        # SEVERITY
        # -------------------------------------------------
        severity = "INFO"

        if (
            "critical" in raw_log.lower()
            or "unauthorized" in raw_log.lower()
            or "crashed" in raw_log.lower()
            or "failure" in raw_log.lower()
        ):
            severity = "CRITICAL"

        elif (
            "error" in raw_log.lower()
            or "warn" in raw_log.lower()
        ):
            severity = "WARNING"

        st.session_state.log_types.append(severity)

        # -------------------------------------------------
        # ANOMALY DETECTION
        # -------------------------------------------------
        is_anomaly = cluster_counts[label] <= threshold

        log_data = {
            "timestamp": timestamp,
            "message": raw_log,
            "severity": severity,
            "cluster": label,
            "count": cluster_counts[label],
            "anomaly": is_anomaly
        }

        st.session_state.logs.append(log_data)

        if is_anomaly:
            st.session_state.anomaly_logs.append(log_data)

        # -------------------------------------------------
        # SNS ALERTS
        # -------------------------------------------------
        current_time = time.time()

        if severity == "CRITICAL":

            if current_time - st.session_state.last_alert_time > 10:

                send_sns_alert(raw_log, severity)

                st.session_state.last_alert_time = current_time

        st.session_state.total_log_count += 1

    # -------------------------------------------------
    # MEMORY CONTROL
    # -------------------------------------------------
    st.session_state.logs = st.session_state.logs[-3000:]
    st.session_state.anomaly_logs = st.session_state.anomaly_logs[-20:]
    st.session_state.log_types = st.session_state.log_types[-300:]

    # -------------------------------------------------
    # TREND
    # -------------------------------------------------
    st.session_state.anomaly_count_history.append(
        len(st.session_state.anomaly_logs)
    )

    st.session_state.anomaly_count_history = (
        st.session_state.anomaly_count_history[-100:]
    )

# -------------------------------------------------
# RUN
# -------------------------------------------------
events = fetch_logs()

process_logs(events)

# -------------------------------------------------
# DYNAMIC HEALTH
# -------------------------------------------------
recent_logs = st.session_state.logs[-50:]

critical_count = sum(
    1 for log in recent_logs
    if log["severity"] == "CRITICAL"
)

if critical_count >= 8:
    system_health = "System Failure"

elif critical_count >= 4:
    system_health = "Risk Detected"

else:
    system_health = "Stable"

# -------------------------------------------------
# METRICS
# -------------------------------------------------
delta = (
    st.session_state.total_log_count
    - st.session_state.prev_total
)

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Total Logs",
        st.session_state.total_log_count,
        delta=delta
    )

with metric2:
    st.metric(
        "Anomalies",
        len(st.session_state.anomaly_logs)
    )

with metric3:
    st.metric(
        "Critical Logs",
        critical_count
    )

with metric4:
    st.metric(
        "System Health",
        system_health
    )

st.session_state.prev_total = (
    st.session_state.total_log_count
)

# -------------------------------------------------
# HEALTH STATUS
# -------------------------------------------------
if system_health == "Stable":
    st.success("🟢 All AWS Services Operational")

elif system_health == "Risk Detected":
    st.warning("🟠 High Resource Usage Detected")

else:
    st.error("🔴 Critical Infrastructure Failure")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
chart1, chart2 = st.columns(2)

with chart1:

    st.subheader("Severity Distribution")

    if st.session_state.log_types:

        df = pd.DataFrame(
            st.session_state.log_types,
            columns=["Severity"]
        )

        st.bar_chart(df["Severity"].value_counts())

with chart2:

    st.subheader("Anomaly Trend")

    if st.session_state.anomaly_count_history:

        trend_df = pd.DataFrame(
            st.session_state.anomaly_count_history,
            columns=["Anomalies"]
        )

        st.area_chart(trend_df)

# -------------------------------------------------
# SIDE-BY-SIDE PANELS
# -------------------------------------------------
left_logs, right_anomaly = st.columns(2)

# -------------------------------------------------
# LIVE LOGS
# -------------------------------------------------
with left_logs:

    st.subheader("Live Cloud Logs")

    filtered_logs = st.session_state.logs

    if search_term:

        filtered_logs = [
            log for log in filtered_logs
            if search_term.lower()
            in log["message"].lower()
        ]

    for log in reversed(filtered_logs[-15:]):

        log_time = datetime.fromtimestamp(
            log['timestamp'] / 1000
        ).strftime("%H:%M:%S")

        text = (
            f"{log_time} | "
            f"{log['severity']} | "
            f"Cluster {log['cluster']} | "
            f"{log['message']}"
        )

        css_class = "info"

        if log["severity"] == "CRITICAL":
            css_class = "critical"

        elif log["severity"] == "WARNING":
            css_class = "warning"

        st.markdown(
            f'''
            <div class="aws-log-box {css_class}">
            {text}
            </div>
            ''',
            unsafe_allow_html=True
        )

# -------------------------------------------------
# ANOMALY PANEL
# -------------------------------------------------
with right_anomaly:

    st.subheader("Detected Anomalies")

    if not st.session_state.anomaly_logs:
        st.success("No anomalies detected")

    for item in reversed(st.session_state.anomaly_logs[-10:]):

        st.markdown(
            f'''
            <div class="aws-log-box critical">
            {item['message']}<br><br>
            Cluster: {item['cluster']}<br>
            Occurrence: {item['count']}<br>
            Severity: {item['severity']}
            </div>
            ''',
            unsafe_allow_html=True
        )

# -------------------------------------------------
# S3 BUTTON
# -------------------------------------------------
if st.button("Upload Incident Report to S3"):

    upload_report_to_s3()

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("---")

st.caption(
    "ChronoLog AI • Intelligent Cloud Observability Platform"
)

# -------------------------------------------------
# AUTO REFRESH
# -------------------------------------------------
st_autorefresh(interval=5000, key="refresh")
