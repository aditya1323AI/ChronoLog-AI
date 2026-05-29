import boto3
import time
import random

client = boto3.client("logs", region_name="us-east-1")

log_group = "chronolog-group"
log_stream = "chronolog-stream"

logs = [
    "ERROR database timeout",
    "INFO user login successful",
    "WARN high memory usage",
    "ERROR API failed",
    "INFO service started"
]

sequence_token = None

while True:
    log_event = {
        'timestamp': int(time.time() * 1000),
        'message': random.choice(logs)
    }

    kwargs = {
        'logGroupName': log_group,
        'logStreamName': log_stream,
        'logEvents': [log_event]
    }

    if sequence_token:
        kwargs['sequenceToken'] = sequence_token

    response = client.put_log_events(**kwargs)
    sequence_token = response['nextSequenceToken']

    print("Sent log:", log_event['message'])
    time.sleep(2)