import time
import re
import pickle
from collections import Counter

# Clean function
def clean_log(line):
    line = re.sub(r'[^a-zA-Z ]', ' ', line)
    return line.lower().strip()

# Load trained model
with open("model.pkl", "rb") as f:
    kmeans = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Simulated real-time logs
log_stream = [
    "ERROR database connection timeout",
    "INFO user login successful",
    "WARN high memory usage detected",
    "ERROR api response failed",
    "INFO service started",
    "ERROR container crashed",
    "WARN disk space low",
    "ERROR unauthorized access",
    "INFO backup completed"
]

labels_list = []

print("\n Real-Time Log Processing Started...\n")

for new_log in log_stream:
    print("Incoming Log:", new_log)

    # Clean
    cleaned = clean_log(new_log)

    # Convert using trained vectorizer
    X = vectorizer.transform([cleaned])

    # Predict cluster
    label = kmeans.predict(X)[0]
    labels_list.append(label)

    # Count clusters so far
    cluster_counts = Counter(labels_list)
    print("Cluster Counts:", cluster_counts)

    # Anomaly detection
    THRESHOLD = 1
    if cluster_counts[label] <= THRESHOLD:
        print("ANOMALY →", new_log)

    print("-" * 50)

    time.sleep(2)