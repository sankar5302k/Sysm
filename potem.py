import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Define parameters
n_entries = 200000  # 2 lakh entries
labels = [
    "Normal", "Minor Unstable", "Severe Unstable", "High Latency",
    "Router Down", "ISP Failure", "DNS Failure", "Bandwidth Saturation",
    "Intermittent Connectivity", "Firewall Blocking", "Server Unreachable", "Hardware Fault"
]
n_per_label = n_entries // len(labels)  # ~16666 per label

# Initialize DataFrame with explicit dtypes
df = pd.DataFrame({
    "latency": pd.Series(dtype="float64"),
    "packet_loss": pd.Series(dtype="int64"),
    "connected": pd.Series(dtype="int64"),
    "jitter": pd.Series(dtype="float64"),
    "error": pd.Series(dtype="object"),
    "bandwidth_usage": pd.Series(dtype="float64"),
    "signal_strength": pd.Series(dtype="float64"),
    "dns_resolution_time": pd.Series(dtype="float64"),
    "connection_drops": pd.Series(dtype="int64"),
    "label": pd.Series(dtype="object")
})


# Helper function to add missing values (10% chance)
def add_missing(values):
    mask = np.random.random(len(values)) < 0.1
    values[mask] = np.nan
    return values


# Generate data for each label
for label in labels:
    n = n_per_label
    if label == "Normal":
        latency = add_missing(np.random.uniform(0, 50, n).astype("float64"))
        packet_loss = np.random.randint(0, 11, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(0, 10, n).astype("float64"))
        error = np.full(n, "none", dtype="object")
        bandwidth_usage = np.random.uniform(0, 50, n)
        signal_strength = np.random.uniform(-70, -30, n)
        dns_resolution_time = add_missing(np.random.uniform(0, 50, n).astype("float64"))
        connection_drops = np.zeros(n, dtype="int64")

    elif label == "Minor Unstable":
        latency = add_missing(np.random.uniform(50, 200, n).astype("float64"))
        packet_loss = np.random.randint(10, 41, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(10, 30, n).astype("float64"))
        error = np.random.choice(["none", "timeout"], n, p=[0.7, 0.3])
        bandwidth_usage = np.random.uniform(20, 70, n)
        signal_strength = np.random.uniform(-80, -50, n)
        dns_resolution_time = add_missing(np.random.uniform(50, 200, n).astype("float64"))
        connection_drops = np.random.randint(0, 3, n)

    elif label == "Severe Unstable":
        latency = add_missing(np.random.uniform(200, 500, n).astype("float64"))
        packet_loss = np.random.randint(40, 81, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(30, 50, n).astype("float64"))
        error = np.random.choice(["timeout", "unreachable"], n, p=[0.6, 0.4])
        bandwidth_usage = np.random.uniform(30, 80, n)
        signal_strength = np.random.uniform(-90, -60, n)
        dns_resolution_time = add_missing(np.random.uniform(200, 500, n).astype("float64"))
        connection_drops = np.random.randint(2, 6, n)

    elif label == "High Latency":
        latency = add_missing(np.random.uniform(200, 1000, n).astype("float64"))
        packet_loss = np.random.randint(0, 21, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(10, 30, n).astype("float64"))
        error = np.random.choice(["none", "timeout"], n, p=[0.8, 0.2])
        bandwidth_usage = np.random.uniform(10, 60, n)
        signal_strength = np.random.uniform(-70, -40, n)
        dns_resolution_time = add_missing(np.random.uniform(50, 300, n).astype("float64"))
        connection_drops = np.random.randint(0, 2, n)

    elif label == "Router Down":
        latency = add_missing(np.full(n, 999, dtype="float64"))
        packet_loss = np.random.randint(80, 101, n)
        connected = np.random.choice([0, 1], n, p=[0.3, 0.7])
        jitter = add_missing(np.full(n, 999, dtype="float64"))
        error = np.full(n, "unreachable", dtype="object")
        bandwidth_usage = np.random.uniform(0, 20, n)
        signal_strength = np.full(n, -999, dtype="float64")
        dns_resolution_time = add_missing(np.full(n, 999, dtype="float64"))
        connection_drops = np.random.randint(5, 11, n)

    elif label == "ISP Failure":
        latency = add_missing(np.full(n, 999, dtype="float64"))
        packet_loss = np.random.randint(80, 101, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.full(n, 999, dtype="float64"))
        error = np.random.choice(["unreachable", "timeout"], n, p=[0.6, 0.4])
        bandwidth_usage = np.random.uniform(0, 30, n)
        signal_strength = np.random.uniform(-80, -50, n)
        dns_resolution_time = add_missing(np.full(n, 999, dtype="float64"))
        connection_drops = np.random.randint(3, 9, n)

    elif label == "DNS Failure":
        latency = add_missing(np.random.uniform(500, 1000, n).astype("float64"))
        packet_loss = np.random.randint(50, 101, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(50, 1000, n).astype("float64"))
        error = np.full(n, "refused", dtype="object")
        bandwidth_usage = np.random.uniform(20, 70, n)
        signal_strength = np.random.uniform(-80, -50, n)
        dns_resolution_time = add_missing(np.full(n, 999, dtype="float64"))
        connection_drops = np.random.randint(0, 4, n)

    elif label == "Bandwidth Saturation":
        latency = add_missing(np.random.uniform(100, 500, n).astype("float64"))
        packet_loss = np.random.randint(0, 16, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(20, 100, n).astype("float64"))
        error = np.full(n, "none", dtype="object")
        bandwidth_usage = np.random.uniform(80, 100, n)
        signal_strength = np.random.uniform(-70, -40, n)
        dns_resolution_time = add_missing(np.random.uniform(50, 200, n).astype("float64"))
        connection_drops = np.random.randint(0, 2, n)

    elif label == "Intermittent Connectivity":
        latency = add_missing(np.random.uniform(50, 999, n).astype("float64"))
        packet_loss = np.random.randint(20, 81, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(50, 500, n).astype("float64"))
        error = np.full(n, "timeout", dtype="object")
        bandwidth_usage = np.random.uniform(20, 80, n)
        signal_strength = np.random.uniform(-90, -60, n)
        dns_resolution_time = add_missing(np.random.uniform(200, 999, n).astype("float64"))
        connection_drops = np.random.randint(5, 11, n)

    elif label == "Firewall Blocking":
        latency = add_missing(np.random.uniform(200, 999, n).astype("float64"))
        packet_loss = np.random.randint(0, 31, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.random.uniform(10, 50, n).astype("float64"))
        error = np.random.choice(["refused", "unreachable"], n, p=[0.5, 0.5])
        bandwidth_usage = np.random.uniform(10, 60, n)
        signal_strength = np.random.uniform(-70, -40, n)
        dns_resolution_time = add_missing(np.random.uniform(500, 999, n).astype("float64"))
        connection_drops = np.random.randint(0, 3, n)

    elif label == "Server Unreachable":
        latency = add_missing(np.full(n, 999, dtype="float64"))
        packet_loss = np.random.randint(80, 101, n)
        connected = np.ones(n, dtype="int64")
        jitter = add_missing(np.full(n, 999, dtype="float64"))
        error = np.full(n, "unreachable", dtype="object")
        bandwidth_usage = np.random.uniform(0, 30, n)
        signal_strength = np.random.uniform(-80, -50, n)
        dns_resolution_time = add_missing(np.full(n, 999, dtype="float64"))
        connection_drops = np.random.randint(3, 8, n)

    elif label == "Hardware Fault":
        latency = add_missing(np.full(n, 999, dtype="float64"))
        packet_loss = np.random.randint(50, 101, n)
        connected = np.random.choice([0, 1], n, p=[0.5, 0.5])
        jitter = add_missing(np.full(n, 999, dtype="float64"))
        error = np.random.choice(["timeout", "unreachable"], n, p=[0.5, 0.5])
        bandwidth_usage = np.random.uniform(0, 50, n)
        signal_strength = np.full(n, -999, dtype="float64")
        dns_resolution_time = add_missing(np.full(n, 999, dtype="float64"))
        connection_drops = np.random.randint(5, 11, n)

    # Combine into a temporary DataFrame
    temp_df = pd.DataFrame({
        "latency": latency,
        "packet_loss": packet_loss,
        "connected": connected,
        "jitter": jitter,
        "error": error,
        "bandwidth_usage": bandwidth_usage,
        "signal_strength": signal_strength,
        "dns_resolution_time": dns_resolution_time,
        "connection_drops": connection_drops,
        "label": np.full(n, label, dtype="object")
    })

    # Append to main DataFrame
    df = pd.concat([df, temp_df], ignore_index=True)

# Shuffle the dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save to Excel (Note: Excel has a 1,048,576-row limit, so we'll split into two files if needed)
if len(df) <= 1048576:
    df.to_excel("network_datasetss_200000.xlsx", index=False)
    print("Dataset with 200,000 entries saved as 'network_dataset_200000.xlsx'.")
else:
    # Split into two parts if exceeding Excel limit (not needed here, but included for generality)
    df_part1 = df.iloc[:100000]
    df_part2 = df.iloc[100000:]
    df_part1.to_excel("network_dataset_200000_part1.xlsx", index=False)
    df_part2.to_excel("network_dataset_200000_part2.xlsx", index=False)
    print("Dataset split and saved as 'network_dataset_200000_part1.xlsx' and 'network_dataset_200000_part2.xlsx'.")

# Preview the first few rows
print("\nDataset Preview:")
print(df.head())

# Summary statistics
print("\nLabel Distribution:")
print(df["label"].value_counts())
print("\nError Distribution:")
print(df["error"].value_counts())