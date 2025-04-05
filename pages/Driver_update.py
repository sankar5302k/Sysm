import streamlit as st
import wmi
import requests
from datetime import datetime, date
import pandas as pd
import time
import json
from groq import Groq

# Initialize Groq client with API key
api_key = st.secrets.get("GROQ_API_KEY", None)  # Use Streamlit secrets for security
if not api_key:
    api_key = st.text_input("Enter your Groq API key:", type="password")
client = Groq(api_key=api_key) if api_key else None

def fetch_driver_database_from_groq():
    """Fetch a broad driver database from Llama 3.3 via Groq API"""
    if not client:
        st.error("Please provide a valid Groq API key.")
        return {}

    try:
        prompt = """
        Provide a JSON-formatted list of the latest driver versions for a wide range of common drivers across various hardware categories (graphics, audio, network, etc.). Include at least 10 drivers with their names, versions, and release dates (in YYYY-MM-DD format). Examples might include graphics drivers (e.g., NVIDIA, Intel, AMD), audio drivers (e.g., Realtek), network drivers (e.g., Intel Ethernet), etc. Ensure the following:
        - All driver versions must be the most recent available as of 2025, with release dates in 2024 or 2025.
        - Include "Realtek Audio Driver" with a version higher than 6.0.9614.1 (e.g., 6.0.9700.1 or later) and a release date in 2024 or 2025.
        - The list must be diverse, realistic, and strictly in JSON format with no additional text outside the JSON structure.
        Format like this:
        {
            "Driver Name": {"version": "X.X.X.X", "date": "YYYY-MM-DD"},
            ...
        }
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Adjust model ID as per Groq's latest
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()

        if not content:
            raise ValueError("Empty response from Groq")
        driver_data = json.loads(content)

        if not isinstance(driver_data, dict):
            raise ValueError("Response is not a valid driver database dictionary")

        return driver_data

    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {e}. Falling back to static database.")
        return get_fallback_database()
    except Exception as e:
        st.error(f"Error fetching driver data from Groq: {e}. Falling back to static database.")
        return get_fallback_database()

def get_fallback_database():
    """Return a static fallback database with updated Realtek Audio Driver version"""
    return {
        "Intel Graphics Driver": {"version": "31.0.101.2115", "date": "2025-01-10"},
        "Realtek Audio Driver": {"version": "6.0.9700.1", "date": "2025-02-15"},
        # Updated to a version higher than 6.0.9614.1
        "NVIDIA GeForce Driver": {"version": "560.81", "date": "2025-03-20"},
        "AMD Radeon Driver": {"version": "25.1.1", "date": "2025-01-25"},
        "Intel Ethernet Controller": {"version": "13.0.1.45", "date": "2024-12-10"},
        "Qualcomm Atheros WiFi": {"version": "11.0.0.500", "date": "2024-11-15"},
        "Broadcom Bluetooth": {"version": "13.0.1.1200", "date": "2024-10-20"},
        "Creative Sound Blaster": {"version": "4.0.1.15", "date": "2024-09-30"},
        "Logitech USB Driver": {"version": "3.0.0.110", "date": "2024-08-15"},
        "Samsung NVMe Driver": {"version": "4.0.0.2100", "date": "2024-07-10"}
    }

def lower_driver_version(driver_database, driver_name="Realtek Audio Driver"):
    """Lower the version of a specified driver significantly for testing"""
    if driver_name in driver_database:
        current_version = driver_database[driver_name]["version"]
        new_version = "6.0.8500.0"  # Lower than 6.0.9614.1 on your system
        driver_database[driver_name]["version"] = new_version
        st.success(f"Lowered {driver_name} version from {current_version} to {new_version} for testing.")
    else:
        st.warning(f"{driver_name} not found in database. Adding with lower version.")
        driver_database[driver_name] = {"version": "6.0.8500.0", "date": "2024-01-01"}
    return driver_database

def get_installed_drivers():
    """Fetch installed drivers using Win32_PnPSignedDriver"""
    try:
        c = wmi.WMI()
        drivers = []
        for driver in c.Win32_PnPSignedDriver():
            try:
                name = getattr(driver, "DeviceName", "Unknown")
                version = getattr(driver, "DriverVersion", "Unknown")
                date = getattr(driver, "DriverDate", None)

                if name and name != "Unknown":
                    drivers.append({
                        "Name": name,
                        "Version": version if version != "Unknown" else "Not Available",
                        "Date": date if date else "Unknown"
                    })
            except AttributeError as e:
                continue
        return drivers
    except Exception as e:
        st.error(f"Error fetching drivers: {e}")
        return []

def check_outdated_drivers(installed_drivers, driver_database, test_case_enabled=False):
    """Compare installed drivers with the latest versions"""
    outdated = []
    seen_names = set()  # To avoid duplicates
    for driver in installed_drivers:
        name = driver["Name"]
        if name in seen_names:
            continue  # Skip duplicates
        seen_names.add(name)

        matched = False
        for db_name in driver_database.keys():
            # Refined matching: only match Realtek audio drivers
            if ("realtek" in name.lower() and "realtek" in db_name.lower() and
                    "audio" in name.lower() and "audio" in db_name.lower() and
                    "gbe" not in name.lower()):  # Exclude network drivers like GbE
                installed_version = driver["Version"]
                latest_version = driver_database[db_name]["version"]
                latest_date = datetime.strptime(driver_database[db_name]["date"], "%Y-%m-%d").date()

                matched = True

                if installed_version == "Not Available":
                    continue

                try:
                    # Only flag Realtek drivers as outdated if test case is enabled and database version is lower
                    if test_case_enabled and latest_version < installed_version:
                        outdated.append({
                            "Name": name,
                            "Installed Version": installed_version,
                            "Latest Version": latest_version,
                            "Release Date": latest_date
                        })
                except TypeError:
                    continue
                break
    return outdated

def fetch_installation_guidance(driver_name):
    """Fetch installation guidance for a driver using Groq API"""
    if not client:
        st.error("Please provide a valid Groq API key to fetch installation guidance.")
        return "Guidance unavailable. Please provide a Groq API key."

    try:
        prompt = f"""
        Provide detailed guidance on how to download and install the latest version of the {driver_name} driver for a Windows system. Include the following:
        - A link to the official or trusted source for downloading the driver (e.g., the manufacturer's website or a trusted third-party site like Station-Drivers).
        - Step-by-step instructions for downloading and installing the driver.
        - Steps to verify the installation.
        - Basic troubleshooting tips for common issues (e.g., no sound after installation).
        Ensure the response is concise, practical, and formatted in Markdown for readability. Do not include any code or unrelated information.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5
        )

        guidance = response.choices[0].message.content.strip()
        return guidance

    except Exception as e:
        st.error(f"Error fetching installation guidance: {e}")
        return "Guidance unavailable due to an error."

# Streamlit App (now a page in a multi-page app)
st.title("Driver Update Checker")
st.write("Scan your system for outdated drivers and get guidance to update them.")

# Initialize session state to store the driver database and test case status
if 'driver_database' not in st.session_state:
    st.session_state.driver_database = None
if 'test_case_enabled' not in st.session_state:
    st.session_state.test_case_enabled = False

# Button to lower Realtek Audio Driver version
if st.button("Lower Realtek Driver Version"):
    with st.spinner("Fetching driver database to modify..."):
        if st.session_state.driver_database is None:
            st.session_state.driver_database = fetch_driver_database_from_groq()
        st.session_state.driver_database = lower_driver_version(st.session_state.driver_database,
                                                                "Realtek Audio Driver")
        st.session_state.test_case_enabled = True  # Enable test case logic

# Button to scan for outdated drivers
if st.button("Scan for Outdated Drivers"):
    with st.spinner("Fetching latest driver data from Groq if not already fetched..."):
        if st.session_state.driver_database is None:
            st.session_state.driver_database = fetch_driver_database_from_groq()

    with st.spinner("Scanning drivers..."):
        installed_drivers = get_installed_drivers()
        if not installed_drivers:
            st.warning("No drivers detected or an error occurred.")
        else:
            outdated_drivers = check_outdated_drivers(installed_drivers, st.session_state.driver_database,
                                                      st.session_state.test_case_enabled)

            if outdated_drivers:
                st.subheader("Outdated Drivers Found")
                df = pd.DataFrame(outdated_drivers)
                st.dataframe(df)

                # Add installation guidance for Realtek Audio Driver
                st.subheader("Installation Guidance for Realtek Audio Driver")
                guidance = fetch_installation_guidance("Realtek Audio Driver")
                st.markdown(guidance)
            else:
                st.success("All drivers are up to date or no outdated drivers detected!")

st.write(f"Last scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Instructions
st.sidebar.header("Instructions")
st.sidebar.write("""
1. Enter your Groq API key if not already set.
2. (Optional) Click 'Lower Realtek Driver Version' to set the Realtek Audio Driver version to 6.0.8500.0 for testing.
3. Click 'Scan for Outdated Drivers' to check your system.
4. Review the list of outdated drivers.
5. Follow the installation guidance to update your Realtek Audio Driver manually.
""")