import streamlit as st
from streamlit.components.v1 import html

pentagon_css = """
<style>
.pentagon-container {
    position: relative;
    width: 300px;
    height: 300px;
    margin: 50px auto;
}
.pentagon {
    position: absolute;
    width: 100%;
    height: 100%;
    background: #2A2A2A;  /* Darker base for contrast */
    clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
}
.pen-button {
    position: absolute;
    width: 110px;
    height: 45px;
    color: white;
    text-align: center;
    line-height: 45px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    border: none;
    border-radius: 8px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);  /* 3D shadow */
    transition: transform 0.2s, box-shadow 0.2s;
}
.pen-button:hover {
    transform: translateY(-3px);  /* Lift effect on hover */
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);  /* Enhanced shadow */
}
.btn1 { top: -50px; left: 95px; background: #FF4D4D; }  /* Top - Bright Red */
.btn2 { top: 80px; right: -60px; background: #00E6E6; }  /* Top-right - Cyan */
.btn3 { bottom: 20px; right: -20px; background: #4D79FF; }  /* Bottom-right - Electric Blue */
.btn4 { bottom: 20px; left: -20px; background: #FFCC00; color: black; }  /* Bottom-left - Bright Yellow */
.btn5 { top: 80px; left: -60px; background: #FF66CC; }  /* Top-left - Hot Pink */
</style>
"""

pentagon_html = """
<div class="pentagon-container">
    <div class="pentagon"></div>
    <button class="pen-button btn1">
        <a href="/Network" onclick="window.location.href='/Network'; return false;" 
        style="text-decoration:none; color:white;">Network</a>
    </button>
    <button class="pen-button btn2">
        <a href="/System_monitor_app" onclick="window.location.href='/System_monitor_app'; return false;" 
        style="text-decoration:none; color:white; font-size:12px;">System Analysis</a>
    </button>
    <button class="pen-button btn3">
        <a href="/Disk_check" onclick="window.location.href='/Disk_check'; return false;"
        style="text-decoration:none; color:white;">Disk Check</a>
    </button>
    <button class="pen-button btn4">
        <a href="/Driver_update" onclick="window.location.href='/Driver_update'; return false;" 
        style="text-decoration:none; color:white;">Driver Update</a>
    </button>
    <button class="pen-button btn5">
        <a href="/" onclick="window.location.href='/'; return false;" 
        style="text-decoration:none; color:black;">Home</a>
    </button>
</div>
"""
st.set_page_config(page_title="Sysmind AI ", layout="wide")
st.markdown(pentagon_css, unsafe_allow_html=True)
st.title("Sysmind AI")
st.markdown(pentagon_html, unsafe_allow_html=True)
st.write("Click a button to launch the respective application.")