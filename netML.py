import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import psutil
import socket
import time
import os
from ping3 import ping
import platform
import subprocess
import joblib

MODEL_PATH = "pages/network_model.pkl"

def load_or_train_model():
    if os.path.exists(MODEL_PATH):
        print("Loading pre-trained model...")
        model = joblib.load(MODEL_PATH)

        X_cols = joblib.load("pages/X_columns.pkl")
    else:
        print("Training model with 200,000-entry dataset...")
        file_path = "network_dataset_200000.xlsx"
        df = pd.read_excel(file_path)
        df["latency"] = df["latency"].astype("Float64").fillna(999)
        df["jitter"] = df["jitter"].astype("Float64").fillna(999)
        df["dns_resolution_time"] = df["dns_resolution_time"].astype("Float64").fillna(999)
        df["error"] = df["error"].fillna("none")
        df_encoded = pd.get_dummies(df, columns=["error"], prefix="err")
        X = df_encoded.drop("label", axis=1)
        y = df["label"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=500,max_depth=20, random_state=40)
        model.fit(X_train, y_train)

        joblib.dump(model, MODEL_PATH)
        joblib.dump(X.columns, "pages/X_columns.pkl")
        print("Model training completed and saved.")

        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        print(f"Train Accuracy: {accuracy_score(y_train, train_pred):.2f}")
        print(f"Test Accuracy: {accuracy_score(y_test, test_pred):.2f}")
        print(f"Feature Importance: {dict(zip(X.columns, model.feature_importances_))}")
        print("\nClassification Report (Test Set):\n", classification_report(y_test, test_pred))

        X_cols = X.columns

    return model, X_cols


model, X_columns = load_or_train_model()



def measure_network_metrics(target="8.8.8.8", count=5, timeout=1):
    latencies = []
    packets_sent = 0
    packets_received = 0
    drops = 0

    for _ in range(count):
        try:
            delay = ping(target, timeout=timeout)
            packets_sent += 1
            if delay is not None and delay is not False:
                delay_ms = delay * 1000
                latencies.append(delay_ms)
                packets_received += 1
            else:
                drops += 1
            time.sleep(0.1)
        except Exception:
            packets_sent += 1
            drops += 1

    latency = np.mean(latencies) if latencies else 999
    jitter = np.std(latencies) if len(latencies) > 1 else 999
    packet_loss = ((packets_sent - packets_received) / packets_sent) * 100 if packets_sent > 0 else 100
    connection_drops = drops

    return latency, jitter, packet_loss, connection_drops

def measure_dns_resolution_time(target="google.com"):
    try:
        start_time = time.time()
        socket.getaddrinfo(target, 80, proto=socket.IPPROTO_TCP)
        return (time.time() - start_time) * 1000
    except Exception:
        return 999

def measure_bandwidth_usage(interval=1):
    try:
        net_io_start = psutil.net_io_counters()
        time.sleep(interval)
        net_io_end = psutil.net_io_counters()
        total_bytes = (net_io_end.bytes_sent + net_io_end.bytes_recv -
                       net_io_start.bytes_sent - net_io_start.bytes_recv) * 8 / interval
        max_speed = 100 * 1024 * 1024  # 100 Mbps
        return min(total_bytes / max_speed * 100, 100)
    except Exception:
        return 50


def measure_signal_strength():
    if platform.system() != "Windows":
        return -999
    try:
        result = subprocess.check_output("netsh wlan show interfaces", shell=True, stderr=subprocess.STDOUT).decode()
        for line in result.split("\n"):
            if "Signal" in line:
                signal_percent = int(line.split(":")[1].strip().replace("%", ""))
                return -100 + (signal_percent * 0.7)
        return -999
    except Exception:
        return -999

def detect_network_error(latency, packet_loss, dns_time):
    try:
        socket.gethostbyname("google.com")
        if packet_loss == 100:
            return "unreachable"
        elif latency > 200 or dns_time > 200:
            return "timeout"
        return "none"
    except socket.gaierror:
        return "refused"
    except socket.timeout:
        return "timeout"
    except Exception:
        return "timeout"


def get_single_network_log():
    network_log = {
        "latency": 999,
        "packet_loss": 100,
        "connected": 0,
        "jitter": 999,
        "error": "timeout",
        "bandwidth_usage": 50,
        "signal_strength": -999,
        "dns_resolution_time": 999,
        "connection_drops": 5
    }

    try:
        interfaces = psutil.net_if_stats()
        connected = 1 if any(stats.isup for stats in interfaces.values()) else 0
        network_log["connected"] = connected

        if not connected:
            network_log["error"] = "unreachable"
            network_log["bandwidth_usage"] = 0
            network_log["signal_strength"] = -999
            network_log["connection_drops"] = 5
            return network_log

        latency, jitter, packet_loss, connection_drops = measure_network_metrics()
        dns_time = measure_dns_resolution_time()
        bandwidth_usage = measure_bandwidth_usage()
        signal_strength = measure_signal_strength()

        network_log["latency"] = latency
        network_log["jitter"] = jitter
        network_log["packet_loss"] = packet_loss
        network_log["dns_resolution_time"] = dns_time
        network_log["bandwidth_usage"] = bandwidth_usage
        network_log["signal_strength"] = signal_strength
        network_log["connection_drops"] = connection_drops
        network_log["error"] = detect_network_error(latency, packet_loss, dns_time)

    except Exception as e:
        print(f"Error collecting network log: {e}")

    return network_log


def collect_network_logs_for_20_seconds(log_file="network_logs.txt"):
    logs = []
    duration = 20
    interval = 4
    start_time = time.time()

    print("Collecting network logs for 20 seconds...")
    with open(log_file, "a") as f:
        while time.time() - start_time < duration:
            log = get_single_network_log()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - {log}\n")
            logs.append(log)
            time.sleep(interval)

    return logs


def analyze_cumulative_logs(logs):
    if not logs:
        return {
            "latency": 999,
            "packet_loss": 100,
            "connected": 0,
            "jitter": 999,
            "error": "timeout",
            "bandwidth_usage": 50,
            "signal_strength": -999,
            "dns_resolution_time": 999,
            "connection_drops": 5
        }

    summary_log = {
        "latency": np.mean([log["latency"] for log in logs]),
        "packet_loss": max([log["packet_loss"] for log in logs]),
        "connected": min([log["connected"] for log in logs]),
        "jitter": np.mean([log["jitter"] for log in logs]),
        "error": "refused" if "refused" in [log["error"] for log in logs] else
        "unreachable" if "unreachable" in [log["error"] for log in logs] else
        "timeout" if "timeout" in [log["error"] for log in logs] else "none",
        "bandwidth_usage": np.mean([log["bandwidth_usage"] for log in logs]),
        "signal_strength": np.mean([log["signal_strength"] for log in logs]),
        "dns_resolution_time": np.mean([log["dns_resolution_time"] for log in logs]),
        "connection_drops": max([log["connection_drops"] for log in logs])
    }
    return summary_log


def get_predicted_network_issue(log_file="network_logs.txt"):
    if os.path.exists(log_file):
        os.remove(log_file)

    logs = collect_network_logs_for_20_seconds(log_file)
    summary_log = analyze_cumulative_logs(logs)

    log_df = pd.DataFrame([summary_log])
    log_df["latency"] = log_df["latency"].astype("Float64").fillna(999)
    log_df["jitter"] = log_df["jitter"].astype("Float64").fillna(999)
    log_df["dns_resolution_time"] = log_df["dns_resolution_time"].astype("Float64").fillna(999)
    log_df["error"] = log_df["error"].fillna("none")
    log_encoded = pd.get_dummies(log_df, columns=["error"], prefix="err")
    log_encoded = log_encoded.reindex(columns=X_columns, fill_value=0)

    prediction = model.predict(log_encoded)[0]
    return prediction


if __name__ == "__main__":
    prediction = get_predicted_network_issue()
    print(f"Predicted Network Issue: {prediction}")