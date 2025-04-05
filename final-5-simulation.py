import streamlit as st
import psutil
import wmi
import time
from groq import Groq
import json

# Initialize Groq API client
groq_client = Groq(api_key="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")

# Thresholds for detecting issues
TEMP_THRESHOLD = 85
DISK_USAGE_THRESHOLD = 90
CPU_USAGE_THRESHOLD = 90

def get_cpu_temperature():
    """Get CPU temperature using WMI on Windows."""
    try:
        w = wmi.WMI(namespace="root\\wmi")
        temp_info = w.MSAcpi_ThermalZoneTemperature()[0]
        temp_celsius = (temp_info.CurrentTemperature / 10.0) - 273.15
        return temp_celsius
    except Exception as e:
        st.warning("CPU temperature unavailable without admin privileges or unsupported hardware.")
        return None

def check_disk_health(simulate_failure=False):
    """Check disk health using SMART status via WMI and simulate specific issues if requested."""
    try:
        if simulate_failure:
            disk_status = {
                "Simulated Disk 1": {
                    "Status": "Pred Fail",
                    "PredictFailure": "Failure",
                    "SpecificIssues": [
                        "Impending disk failure detected (SMART prediction).",
                        "Excessive bad sectors detected."
                    ]
                },
                "Simulated Disk 2": {
                    "Status": "Error",
                    "PredictFailure": "Failure",
                    "SpecificIssues": [
                        "Disk read/write errors detected."
                    ]
                }
            }
            return disk_status

        w = wmi.WMI()
        disks = w.Win32_DiskDrive()
        disk_status = {}
        for disk in disks:
            status = disk.Status
            specific_issues = []
            predict_failure = "Failure" if status != "OK" else "No Failure"
            
            if status != "OK":
                if "Pred Fail" in status:
                    specific_issues.append("Impending disk failure detected (SMART prediction).")
                elif "Error" in status:
                    specific_issues.append("Disk read/write errors detected.")
                else:
                    specific_issues.append("Unspecified disk health degradation.")
            
            disk_status[disk.Caption] = {
                "Status": status,
                "PredictFailure": predict_failure,
                "SpecificIssues": specific_issues
            }
        return disk_status
    except Exception as e:
        st.error(f"Error checking disk health: {e}")
        return None

def get_system_metrics(simulate_failure=False):
    """Collect CPU, RAM, and Disk usage metrics."""
    metrics = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "cpu_temperature": get_cpu_temperature(),
        "disk_health": check_disk_health(simulate_failure=simulate_failure)
    }
    return metrics

def predict_failure(metrics):
    """Analyze metrics and predict potential failures, including specific disk issues."""
    predictions = []
    recommendations = []

    if metrics["cpu_temperature"] and metrics["cpu_temperature"] > TEMP_THRESHOLD:
        predictions.append(f"CPU overheating detected: {metrics['cpu_temperature']}°C")
        recommendations.append("Clean fans, improve ventilation, or replace thermal paste.")

    if metrics["cpu_usage"] > CPU_USAGE_THRESHOLD:
        predictions.append(f"High CPU usage: {metrics['cpu_usage']}%")
        recommendations.append("Check for resource-intensive processes and terminate unnecessary ones.")

    if metrics["ram_usage"] > 90:
        predictions.append(f"High RAM usage: {metrics['ram_usage']}%")
        recommendations.append("Close unused applications or upgrade RAM.")

    if metrics["disk_usage"] > DISK_USAGE_THRESHOLD:
        predictions.append(f"High disk usage: {metrics['disk_usage']}%")
        recommendations.append("Free up disk space or upgrade storage.")

    if metrics["disk_health"]:
        for disk, info in metrics["disk_health"].items():
            if info["PredictFailure"] == "Failure":
                predictions.append(f"Disk failure predicted for {disk}: {info['Status']}")
                for issue in info["SpecificIssues"]:
                    predictions.append(f"- Specific disk issue: {issue}")
                recommendations.append("Backup data immediately and replace the disk.")

    return predictions, recommendations

def send_to_llama(predictions, recommendations):
    """Send predictions and recommendations to Llama 3.3 via Groq API."""
    try:
        payload = {
            "predictions": predictions,
            "recommendations": recommendations,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "request": "Analyze these system health issues (including specific disk problems) and provide detailed solutions."
        }
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=[
                {"role": "system", "content": "You are an AI that analyzes system health predictions and provides detailed solutions."},
                {"role": "user", "content": json.dumps(payload)}
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error sending to Groq API: {e}")
        return None

def main():
    st.title("System Health Monitor")
    st.write("Monitor your system's CPU, RAM, Disk usage, and health in real-time.")

    # Button to refresh metrics
    if st.button("Check System Health"):
        with st.spinner("Collecting system metrics..."):
            # For demonstration, simulate disk failure (you can toggle this off)
            metrics = get_system_metrics(simulate_failure=True)

            # Display metrics using Streamlit's metric widget
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("CPU Usage", f"{metrics['cpu_usage']}%")
            with col2:
                st.metric("RAM Usage", f"{metrics['ram_usage']}%")
            with col3:
                st.metric("Disk Usage", f"{metrics['disk_usage']}%")
            with col4:
                temp = metrics['cpu_temperature'] if metrics['cpu_temperature'] is not None else "N/A"
                if isinstance(temp, (int, float)):
                    st.metric("CPU Temperature", f"{temp:.2f}°C")
                else:
                    st.metric("CPU Temperature", f"{temp}")

            # Display disk health
            st.subheader("Disk Health")
            if metrics["disk_health"]:
                st.json(metrics["disk_health"])
            else:
                st.write("Unable to retrieve disk health data.")

            # Predict failures and display results
            predictions, recommendations = predict_failure(metrics)
            if predictions:
                st.subheader("Potential Issues Detected")
                for pred in predictions:
                    st.warning(pred)
                
                st.subheader("Recommended Actions")
                for rec in recommendations:
                    st.info(rec)

                # Send to Groq API for detailed analysis
                with st.spinner("Analyzing with AI..."):
                    ai_response = send_to_llama(predictions, recommendations)
                    if ai_response:
                        st.subheader("AI Analysis and Solutions")
                        st.write(ai_response)
            else:
                st.success("No issues detected at this time.")

    # Auto-refresh option
    st.write("---")
    auto_refresh = st.checkbox("Auto-refresh every 10 seconds")
    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()