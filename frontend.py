import streamlit as st
import pydeck as pdk
import pandas as pd
import backend
import os

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide", page_title="Flood-Sentry | Delhi")

st.markdown("""
<style>
.stApp { background-color: #0e1117; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🌊 Flood-Sentry: Delhi Command Node")
st.caption("Proactive GIS-based flood hotspot identification & verification")

# --------------------------------------------------
# SIDEBAR — CONTROLS
# --------------------------------------------------
st.sidebar.header("Controls")

st.sidebar.subheader("🌧️ Rainfall Source")
mode = st.sidebar.radio(
    "Select rainfall input",
    ["Manual (Simulation)", "Live Weather API"]
)

rain = 0.0
rain_source = "SIMULATION"

if mode == "Live Weather API":
    env_key = os.getenv("OPENWEATHER_API_KEY", "")
    api_key = st.sidebar.text_input(
        "OpenWeatherMap API Key",
        type="password",
        value=env_key
    )

    if api_key:
        rain, rain_source = backend.get_live_rainfall(api_key)
        if rain is None:
            st.sidebar.warning("Weather API failed — using fallback")
            rain = st.sidebar.slider("Fallback Rainfall (mm/hr)", 0, 150, 20)
            rain_source = "FALLBACK"
        else:
            st.sidebar.success(f"Live Rainfall: {rain} mm/hr")
    else:
        rain = st.sidebar.slider("Simulated Rainfall (mm/hr)", 0, 150, 20)
else:
    rain = st.sidebar.slider("Simulated Rainfall (mm/hr)", 0, 150, 20)

sms_text = st.sidebar.text_input("2G SMS Input (HELP / SOS)")

camera_choice = st.sidebar.selectbox(
    "Camera Feed",
    ["Normal Road", "Flooded Road", "Heavy Flood"]
)

IMAGE_PATHS = {
    "Normal Road": "assets/normal.jpg",
    "Flooded Road": "assets/flood.jpg",
    "Heavy Flood": "assets/warning.jpg"
}

image_path = IMAGE_PATHS[camera_choice]

# --------------------------------------------------
# DISPLAY CURRENT RAINFALL
# --------------------------------------------------
st.markdown(
    f"**🌧️ Current Rainfall:** `{rain} mm/hr` _(Source: {rain_source})_"
)

# --------------------------------------------------
# HOTSPOT DATA
# --------------------------------------------------
data = pd.DataFrame({
    "location": [
        "Minto Bridge",
        "Zakhira Underpass",
        "Pul Prahladpur",
        "Lajpat Nagar",
        "Connaught Place"
    ],
    "lat": [28.6327, 28.6678, 28.5042, 28.5677, 28.6304],
    "lon": [77.2210, 77.1539, 77.2913, 77.2433, 77.2177],
    "elevation": [208, 210, 211, 218, 215]
})

data["risk"] = data["elevation"].apply(lambda e: backend.compute_risk(e, rain))

def risk_color(r):
    if r > 140:
        return [200, 0, 0, 200]
    elif r > 90:
        return [255, 165, 0, 200]
    else:
        return [0, 200, 0, 150]

data["color"] = data["risk"].apply(risk_color)

# --------------------------------------------------
# VERIFICATION
# --------------------------------------------------
vision = backend.analyze_image(image_path)
sms_active = backend.sms_trigger(sms_text)

# --------------------------------------------------
# SYSTEM STATE (FIXED PRIORITY LOGIC)
# --------------------------------------------------
if sms_active:
    system_state = "CRITICAL"
elif vision["status"] == "CRITICAL":
    system_state = "CRITICAL"
elif vision["status"] == "WARNING":
    system_state = "WARNING"
elif rain > 80:
    system_state = "PREDICTED"
else:
    system_state = "SAFE"

st.subheader("🚦 System Status")

if system_state == "CRITICAL":
    st.error("🔴 VERIFIED FLOOD — DEPLOY PUMPS IMMEDIATELY")
elif system_state == "WARNING":
    st.warning("🟠 FLOOD DETECTED — PREPARE RESOURCES")
elif system_state == "PREDICTED":
    st.warning("🟡 HIGH RISK — FLOOD LIKELY SOON")
else:
    st.success("🟢 NO FLOOD DETECTED — NORMAL CONDITIONS")

# --------------------------------------------------
# 3D MAP
# --------------------------------------------------
st.subheader("🗺️ 3D Flood Risk Map")

layers = [
    pdk.Layer(
        "ColumnLayer",
        data=data,
        get_position=["lon", "lat"],
        get_elevation="risk",
        elevation_scale=40,
        radius=180,
        get_fill_color="color",
        pickable=True
    )
]

st.pydeck_chart(
    pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=28.62,
            longitude=77.21,
            zoom=12,
            pitch=55,
            bearing=15,
        ),
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={"html": "<b>{location}</b><br>Risk: {risk:.0f}"}
    )
)

# --------------------------------------------------
# VERIFICATION PANEL
# --------------------------------------------------
st.subheader("📹 Verification Panel")

st.image(image_path, caption=f"Camera Status: {vision['status']}")

c1, c2 = st.columns(2)
c1.metric("Estimated Water Depth (ft)", vision["depth"])
c2.metric("Occlusion", f"{int(vision['occlusion']*100)}%")




