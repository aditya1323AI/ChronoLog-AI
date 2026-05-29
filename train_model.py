import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Clean function
def clean_log(line):
    line = re.sub(r'[^a-zA-Z ]', ' ', line)
    return line.lower().strip()

logs = []

# Read dataset
with open("cloud_logs.txt", "r") as file:
    for line in file:
        if line.strip():
            logs.append(clean_log(line))

# Convert text to numbers
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(logs)

# Train clustering model
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(X)

# Save model
with open("model.pkl", "wb") as f:
    pickle.dump(kmeans, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model trained successfully!")
print("Total logs used:", len(logs))