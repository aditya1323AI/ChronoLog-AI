# ChronoLog-AI

## NLP Based AI-Powered Cloud-Native Log Monitoring and Anomaly Detection System

ChronoLog is a real-time cloud monitoring and anomaly detection system developed using AWS, Machine Learning, and Streamlit. The system continuously monitors logs from AWS CloudWatch, processes them using TF-IDF vectorization and K-Means clustering, and detects unusual patterns automatically.
The project aims to simplify cloud log monitoring by providing real-time analytics, anomaly alerts, and interactive visualizations through a lightweight dashboard.

# Features

- Real-time AWS CloudWatch log monitoring
- AI-based anomaly detection using Machine Learning
- TF-IDF feature extraction for log processing
- K-Means clustering for anomaly identification
- Interactive Streamlit dashboard
- Live log streaming and monitoring
- Real-time anomaly alerts
- Graphical analysis and visual insights
- Lightweight and scalable cloud-native architecture

---

# System Architecture

![Architecture](screenshots/architecture.png)

---

# Dashboard Preview

## Main Dashboard

![Dashboard](screenshots/dashboard.jpeg)

---

## Anomaly Detection

![Anomaly](screenshots/anomaly.jpeg)

---

# Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core Programming |
| AWS CloudWatch | Cloud Log Monitoring |
| Streamlit | Dashboard Development |
| Scikit-learn | Machine Learning |
| TF-IDF | Feature Extraction |
| K-Means | Clustering Algorithm |
| Pandas | Data Processing |
| Boto3 | AWS SDK Integration |

---

# Machine Learning Workflow

1. Logs are fetched from AWS CloudWatch.
2. Log data is cleaned and preprocessed.
3. TF-IDF converts logs into numerical vectors.
4. K-Means clustering groups similar logs.
5. Rare clusters are identified as anomalies.
6. Results are displayed on the Streamlit dashboard.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/aditya1323AI/ChronoLog-AI.git
```

## Move into Project Folder

```bash
cd ChronoLog-AI
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Streamlit Application

```bash
streamlit run app.py
```

---

# Project Structure

```text
ChronoLog-AI/
│
├── app.py
├── model.pkl
├── vectorizer.pkl
├── requirements.txt
├── README.md
│
├── screenshots/
│   ├── dashboard.png
│   ├── anomaly.png
│   ├── architecture.png
│
├── dataset/
│
└── docs/
    └── project_report.pdf
```

---

# Future Scope

- Lambda integration
- CloudTrail security monitoring
- Predictive anomaly analysis
- Docker container deployment
- Multi-cloud monitoring support

---

# Applications

- Cloud Infrastructure Monitoring
- Server Log Analysis
- Security Threat Detection
- Real-Time System Monitoring
- DevOps and Observability Platforms

---

# Authors

- Aditya Malpure
- Sayali Nandapurkar

---

# License

This project is developed for educational and research purposes.
