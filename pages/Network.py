import streamlit as st
import netML as n
import time
import subprocess
import psutil
from groq import Groq
import plotly.graph_objects as go
import pandas as pd

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; font-family: 'Arial', sans-serif; }
    .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; padding: 10px 20px; font-size: 16px; }
    .stButton>button:hover { background-color: #45a049; }
    .stSpinner { color: #4CAF50; }
    h1, h2, h3 { color: #333; }
    .sidebar .sidebar-content { background-color: #ffffff; border-radius: 10px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# Initialize Groq API
client = Groq(api_key="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")

# Grok API call
def get_grok_suggestion(issue):
    try:
        prompt = f"Provide a technical suggestion to resolve a network issue: {issue}"
        response = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error fetching suggestion: {e}. Default: Restart router."

# Solutions dictionary
solutions = {
    "Normal": "No issues detected.",
    "Minor Unstable": "Minor fluctuations. Check Wi-Fi or reboot router.",
    "Severe Unstable": "Severe instability. Run diagnostic or contact ISP.",
    "High Latency": "High delay. Reduce network load.",
    "Router Down": "Router offline. Restart router.",
    "ISP Failure": "ISP disruption. Contact support.",
    "DNS Failure": "DNS failed. Flush DNS or use 8.8.8.8.",
    "Bandwidth Saturation": "Bandwidth maxed. Limit apps.",
    "Intermittent Connectivity": "Frequent drops. Check cables.",
    "Firewall Blocking": "Firewall blocking. Check rules.",
    "Server Unreachable": "Server down. Verify status or check network path.",
    "Hardware Fault": "Hardware issue. Inspect equipment."
}

def automate_solution(issue):
    if issue == "Normal":
        st.write("No action needed.")
    elif issue == "Minor Unstable":
        if st.button("Simulate Router Reboot"):
            with st.spinner("Rebooting..."): time.sleep(2); st.success("Rebooted (simulated).")
    elif issue == "Severe Unstable":
        if st.button("Run Ping Test"):
            with st.spinner("Pinging..."):
                result = subprocess.run("ping 8.8.8.8 -n 10", shell=True, capture_output=True, text=True)
                if result.returncode == 0: st.success("Ping completed!"); st.write(result.stdout)
                else: st.error("Ping failed: " + result.stderr)
    elif issue == "High Latency":
        if st.button("Analyze Network Load"):
            with st.spinner("Analyzing..."):
                net_io_start = psutil.net_io_counters(); time.sleep(5); net_io_end = psutil.net_io_counters()
                total_mbps = ((net_io_end.bytes_sent + net_io_end.bytes_recv -
                               net_io_start.bytes_sent - net_io_start.bytes_recv) * 8) / (5 * 1024 * 1024)
                st.success(f"Usage: {total_mbps:.2f} Mbps")
                if total_mbps > 50: st.warning("High load. Close apps.")
    elif issue == "Router Down":
        if st.button("Simulate Router Restart"):
            with st.spinner("Restarting..."): time.sleep(2); st.success("Restarted (simulated).")
    elif issue == "ISP Failure":
        if st.button("Contact ISP"): st.write("Check ISP status or call support.")
    elif issue == "DNS Failure":
        if st.button("Flush DNS"):
            with st.spinner("Flushing..."):
                result = subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, text=True)
                if result.returncode == 0: st.success("Flushed!"); st.write(result.stdout)
                else: st.error("Failed: " + result.stderr)
    elif issue == "Bandwidth Saturation":
        if st.button("List Network Processes"):
            with st.spinner("Fetching..."):
                processes = [f"PID: {proc.pid}, Name: {proc.name()}" for proc in
                             psutil.process_iter(['pid', 'name', 'connections']) if proc.info['connections']]
                if processes: st.success("Top 5:"); st.write(processes[:5])
                else: st.write("No significant processes.")
    elif issue == "Intermittent Connectivity":
        if st.button("Test Stability"):
            with st.spinner("Testing..."):
                result = subprocess.run("ping 8.8.8.8 -n 10", shell=True, capture_output=True, text=True)
                if result.returncode == 0: st.success("Completed!"); st.write(result.stdout)
                else: st.error("Failed: " + result.stderr)
    elif issue == "Firewall Blocking":
        if st.button("Check Firewall"):
            with st.spinner("Checking..."):
                result = subprocess.run("netsh advfirewall show allprofiles", shell=True, capture_output=True, text=True)
                if result.returncode == 0: st.success("Status:"); st.write(result.stdout)
                else: st.error("Failed: " + result.stderr)
    elif issue == "Server Unreachable":
        if st.button("Run Traceroute"):
            with st.spinner("Tracing route to 8.8.8.8..."):
                result = subprocess.run("tracert 8.8.8.8", shell=True, capture_output=True, text=True)
                if result.returncode == 0: st.success("Traceroute completed!"); st.write(result.stdout)
                else: st.error("Traceroute failed: " + result.stderr)
    elif issue == "Hardware Fault":
        if st.button("Check Adapter"):
            with st.spinner("Checking..."):
                adapters = psutil.net_if_stats()
                any_adapter_up = any(stats.isup for stats in adapters.values())
                st.success("Status")
                for name, stats in adapters.items():
                    st.write(f"{name}: Up={stats.isup}, Speed={stats.speed} Mbps")
                if not any_adapter_up:
                    st.warning("Turn on your internet! No active network adapters detected.")

# Plotly graphs for individual metrics
def plot_latency(logs):
    df = pd.DataFrame(logs)
    timestamps = [i * 4 for i in range(len(logs))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=df['latency'], mode='lines+markers', name='Latency', line=dict(color='#00cc96')))
    fig.update_layout(title="Latency Over Time", xaxis_title="Time (s)", yaxis_title="Latency (ms)", template="plotly_white")
    return fig

def plot_packet_loss(logs):
    df = pd.DataFrame(logs)
    timestamps = [i * 4 for i in range(len(logs))]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=timestamps, y=df['packet_loss'], name='Packet Loss', marker_color='#ff6361'))
    fig.update_layout(title="Packet Loss Over Time", xaxis_title="Time (s)", yaxis_title="Packet Loss (%)", template="plotly_white")
    return fig

def plot_bandwidth(logs):
    df = pd.DataFrame(logs)
    timestamps = [i * 4 for i in range(len(logs))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=df['bandwidth_usage'], mode='lines+markers', name='Bandwidth', line=dict(color='#bcbd22')))
    fig.update_layout(title="Bandwidth Usage Over Time", xaxis_title="Time (s)", yaxis_title="Bandwidth Usage (%)", template="plotly_white")
    return fig

def plot_signal_strength(logs):
    df = pd.DataFrame(logs)
    timestamps = [i * 4 for i in range(len(logs))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=df['signal_strength'], mode='lines+markers', name='Signal Strength', line=dict(color='#6a5acd')))
    fig.update_layout(title="Signal Strength Over Time", xaxis_title="Time (s)", yaxis_title="Signal Strength (dBm)", template="plotly_white")
    return fig

# Streamlit app
def main():
    st.title("Network Diagnostic Dashboard")
    st.markdown("Real-time network diagnostics with interactive insights.")

    # Sidebar for metric analysis buttons
    with st.sidebar:
        st.header("Network Metric Analysis")
        if "logs" in st.session_state:
            if st.button("Show Latency Graph"):
                st.session_state["show_graph"] = "latency"
            if st.button("Show Packet Loss Graph"):
                st.session_state["show_graph"] = "packet_loss"
            if st.button("Show Bandwidth Graph"):
                st.session_state["show_graph"] = "bandwidth"
            if st.button("Show Signal Strength Graph"):
                st.session_state["show_graph"] = "signal_strength"
        else:
            st.write("Run a diagnosis to enable metric graphs.")
        st.info("Diagnosis takes 20 seconds.")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("Start Network Diagnosis"):
            with st.spinner("Diagnosing network (20 seconds)..."):
                logs = n.collect_network_logs_for_20_seconds()
                result = n.get_predicted_network_issue()
                st.session_state["diagnosis"] = result
                st.session_state["logs"] = logs
                st.session_state["show_graph"] = None  # Reset graph display

        st.subheader("Diagnosis Result")
        if "diagnosis" in st.session_state:
            st.markdown(f"**Predicted Issue:** <span style='color:#4CAF50'>{st.session_state['diagnosis']}</span>", unsafe_allow_html=True)
        else:
            st.write("Run a diagnosis to see results.")

        st.subheader("Network Metrics")
        if "logs" in st.session_state:
            if "show_graph" in st.session_state and st.session_state["show_graph"]:
                if st.session_state["show_graph"] == "latency":
                    st.plotly_chart(plot_latency(st.session_state["logs"]), use_container_width=True)
                elif st.session_state["show_graph"] == "packet_loss":
                    st.plotly_chart(plot_packet_loss(st.session_state["logs"]), use_container_width=True)
                elif st.session_state["show_graph"] == "bandwidth":
                    st.plotly_chart(plot_bandwidth(st.session_state["logs"]), use_container_width=True)
                elif st.session_state["show_graph"] == "signal_strength":
                    st.plotly_chart(plot_signal_strength(st.session_state["logs"]), use_container_width=True)
            else:
                st.write("Select a metric graph from the sidebar.")
        else:
            st.write("No metrics available. Run a diagnosis first.")

    with col2:
        st.subheader("Suggested Solution")
        st.write(solutions.get(st.session_state.get("diagnosis", "N/A"), "Run a diagnosis first."))

        st.subheader("Automated Actions")
        automate_solution(st.session_state.get("diagnosis", "N/A"))

        st.subheader("AI Suggestion")
        if "diagnosis" in st.session_state:
            with st.spinner("Fetching AI suggestion..."):
                st.write(get_grok_suggestion(st.session_state["diagnosis"]))

    if "diagnosis" in st.session_state:
        st.markdown(f"**Last Diagnosis:** {st.session_state['diagnosis']}", unsafe_allow_html=True)

if __name__ == "__main__":
    main()