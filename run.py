import subprocess
import sys
import os

def run_streamlit():
    # Get the absolute path to Home.py relative to the executable
    script_path = os.path.join(os.path.dirname(__file__), "Home.py")
    # Run Streamlit with the app and ensure browser opens
    subprocess.run([
        sys.executable,
        "-m", "streamlit", "run", script_path,
        "--server.port=8501",
        "--server.headless=true"
    ])

if __name__ == "__main__":
    run_streamlit()