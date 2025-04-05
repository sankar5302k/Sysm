import streamlit as st
import psutil
import logging
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import pandas as pd
import subprocess
import os
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(filename='systemlogs.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Set page config
st.set_page_config(
    page_title="SysMind AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: black;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .terminate-btn {
        background-color: #f44336 !important;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .streamlit-expanderHeader {
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Groq client
try:
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "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")
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logging.error(f"Error initializing Groq client: {str(e)}")
    client = None

class SystemMonitor:
    def __init__(self):
        self.history = []
        self.network_history = []
        self.max_history = 100  # Max data points to store

    def get_system_metrics(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            net = psutil.net_io_counters()
            sent_mb = net.bytes_sent / (1024 * 1024)
            recv_mb = net.bytes_recv / (1024 * 1024)

            metrics = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'datetime': datetime.now(),
                'cpu': cpu_usage,
                'ram': ram_usage,
                'disk': disk_usage,
                'sent_mb': sent_mb,
                'recv_mb': recv_mb
            }

            self.history.append(metrics)
            self.network_history.append({
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'datetime': datetime.now(),
                'sent_mb': sent_mb,
                'recv_mb': recv_mb
            })

            if len(self.history) > self.max_history:
                self.history.pop(0)
            if len(self.network_history) > self.max_history:
                self.network_history.pop(0)

            logging.info(f"Metrics: CPU={cpu_usage}%, RAM={ram_usage}%, Disk={disk_usage}%")
            return metrics
        except Exception as e:
            logging.error(f"Error getting metrics: {str(e)}")
            return None

    def get_running_processes(self):
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent'],
                        'user': proc.info['username']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return sorted(processes, key=lambda x: x['cpu'], reverse=True)
        except Exception as e:
            logging.error(f"Error getting processes: {str(e)}")
            return []

    def terminate_process(self, pid):
        try:
            process = psutil.Process(pid)
            process.terminate()
            logging.info(f"Successfully terminated process PID {pid}")
            return True, f"Process {pid} terminated successfully"
        except psutil.NoSuchProcess:
            logging.warning(f"Process PID {pid} not found")
            return False, f"Process {pid} not found"
        except psutil.AccessDenied:
            logging.error(f"Access denied when terminating process PID {pid}")
            return False, f"Access denied for process {pid} - try running as administrator"
        except Exception as e:
            logging.error(f"Error terminating process PID {pid}: {str(e)}")
            return False, f"Error terminating process {pid}: {str(e)}"

class Chatbot:
    def __init__(self):
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are a system optimization expert. Provide concise, actionable advice:
                - Analyze given system metrics and processes
                - Identify performance bottlenecks
                - Suggest specific optimizations
                - Flag suspicious/unnecessary processes with specific reasons            
                - Format response with clear sections
                - For processes to terminate, include: 'TERMINATE: ProcessName (PID: X) - Reason: [specific reason]'"""
            }
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_response(self, prompt):
        try:
            if not client:
                return "Groq API not available"
            self.conversation_history.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=self.conversation_history,
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )
            response_text = ""
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    response_text += chunk.choices[0].delta.content or ""
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
        except Exception as e:
            logging.error(f"Groq API error: {str(e)}")
            return f"Error: {str(e)}"

def main():
    st.title(" SysMind AI ")

    # Initialize session state
    if 'monitor' not in st.session_state:
        st.session_state.monitor = SystemMonitor()
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = Chatbot()
    if 'last_update' not in st.session_state:
        st.session_state.last_update = 0
    if 'ai_response' not in st.session_state:
        st.session_state.ai_response = None
    if 'flagged_processes' not in st.session_state:
        st.session_state.flagged_processes = []
    if 'metrics' not in st.session_state:
        st.session_state.metrics = None

    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        refresh_rate = st.slider("Refresh rate (seconds)", 1, 10, 2)
        process_limit = st.slider("Processes to show", 5, 50, 15)

        st.header("AI Analysis")
        enable_ai = st.checkbox("Enable AI", True)
        if enable_ai and st.button("Get Optimization Tips"):
            with st.spinner("Analyzing..."):
                metrics = st.session_state.monitor.get_system_metrics()
                processes = st.session_state.monitor.get_running_processes()[:20]
                prompt = f"""System Status:
                - CPU: {metrics['cpu']}%
                - RAM: {metrics['ram']}%
                - Disk: {metrics['disk']}%

                Top Processes:
                {chr(10).join([f"{p['name']} (PID:{p['pid']}, CPU:{p['cpu']}%, RAM:{p['memory']}%)" for p in processes])}

                Provide optimization recommendations and flag any unnecessary processes."""
                st.session_state.ai_response = st.session_state.chatbot.get_response(prompt)
                if st.session_state.ai_response:
                    import re
                    matches = re.findall(r'TERMINATE:\s*(.*?)\s*\(PID:\s*(\d+)\)\s*-\s*Reason:\s*(.*?)(?:\n|$)', st.session_state.ai_response)
                    st.session_state.flagged_processes = [{'name': m[0], 'pid': int(m[1]), 'reason': m[2]} for m in matches]
                else:
                    st.session_state.flagged_processes = []

    # Metrics refresh logic
    def update_metrics():
        st.session_state.metrics = st.session_state.monitor.get_system_metrics()
        st.session_state.last_update = time.time()

    # Initial metrics fetch
    if st.session_state.metrics is None:
        update_metrics()

    # Auto-refresh metrics only
    if time.time() - st.session_state.last_update >= refresh_rate:  # Use the refresh_rate from slider
        update_metrics()

    # Display metrics
    metrics = st.session_state.metrics
    if not metrics:
        st.error("Failed to get system metrics")
        return

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><p class='metric-label'>CPU Usage</p><p class='metric-value'>{metrics['cpu']}%</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><p class='metric-label'>RAM Usage</p><p class='metric-value'>{metrics['ram']}%</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><p class='metric-label'>Disk Usage</p><p class='metric-value'>{metrics['disk']}%</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><p class='metric-label'>Network</p><p class='metric-value'>↑{metrics['sent_mb']:.1f}MB ↓{metrics['recv_mb']:.1f}MB</p></div>", unsafe_allow_html=True)

    # Charts section
    st.header("📈 Performance Trends")
    tab1, tab2 = st.tabs(["CPU/RAM", "Network"])
    with tab1:
        if len(st.session_state.monitor.history) > 1:
            df = pd.DataFrame(st.session_state.monitor.history)
            fig = px.line(df, x='timestamp', y=['cpu', 'ram'], title="CPU and RAM Usage Over Time")
            st.plotly_chart(fig, use_container_width=True)
    with tab2:
        if len(st.session_state.monitor.network_history) > 1:
            df = pd.DataFrame(st.session_state.monitor.network_history)
            fig = px.line(df, x='timestamp', y=['sent_mb', 'recv_mb'], title="Network Usage Over Time")
            st.plotly_chart(fig, use_container_width=True)

    # Processes table with termination
    st.header("⚡ Running Processes")
    processes = st.session_state.monitor.get_running_processes()[:process_limit]
    if processes:
        process_container = st.container()
        with process_container:
            for proc in processes:
                cols = st.columns([1, 3, 1, 1, 2])
                with cols[0]:
                    st.text(proc['pid'])
                with cols[1]:
                    st.text(proc['name'])
                with cols[2]:
                    st.text(f"{proc['cpu']:.1f}%")
                with cols[3]:
                    st.text(f"{proc['memory']:.1f}%")
                with cols[4]:
                    if st.button("Terminate", key=f"kill_{proc['pid']}"):
                        success, msg = st.session_state.monitor.terminate_process(proc['pid'])
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                        time.sleep(0.5)
                        st.rerun()

    # AI Analysis section
    if enable_ai and st.session_state.ai_response:
        st.header("🧠 AI Recommendations")
        st.markdown(st.session_state.ai_response)
    if st.session_state.flagged_processes:
        st.subheader("🚩 Flagged Processes")
        flagged_container = st.container()
        with flagged_container:
            flagged_processes = st.session_state.flagged_processes.copy()
            for i, proc in enumerate(flagged_processes):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"{proc['name']} (PID: {proc['pid']})")
                with col2:
                    st.text(f"Reason: {proc['reason']}")
                with col3:
                    if st.button(f"Terminate {proc['name']}", key=f"kill_flagged_{proc['pid']}"):
                        success, msg = st.session_state.monitor.terminate_process(proc['pid'])
                        if success:
                            st.success(msg)
                            st.session_state.flagged_processes = [
                                p for p in st.session_state.flagged_processes
                                if p['pid'] != proc['pid']
                            ]
                        else:
                            st.error(msg)
                        time.sleep(0.5)
                        st.rerun()

    # Logs download
    st.header("📜 System Logs")
    try:
        with open('systemlogs.txt', 'r') as f:
            log_content = f.read()
        st.download_button(
            label="Download System Logs",
            data=log_content,
            file_name=f"systemlogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )
    except FileNotFoundError:
        st.warning("No logs found to download")

    placeholder = st.empty()
    while True:
        if time.time() - st.session_state.last_update >= refresh_rate:
            update_metrics()
            with placeholder.container():
                metrics = st.session_state.metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<div class='metric-card'><p class='metric-label'>CPU Usage</p><p class='metric-value'>{metrics['cpu']}%</p></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='metric-card'><p class='metric-label'>RAM Usage</p><p class='metric-value'>{metrics['ram']}%</p></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='metric-card'><p class='metric-label'>Disk Usage</p><p class='metric-value'>{metrics['disk']}%</p></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div class='metric-card'><p class='metric-label'>Network</p><p class='metric-value'>↑{metrics['sent_mb']:.1f}MB ↓{metrics['recv_mb']:.1f}MB</p></div>", unsafe_allow_html=True)
        time.sleep(0.1)

if __name__ == "__main__":
    main()