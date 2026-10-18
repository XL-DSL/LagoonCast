import streamlit as st

from utils.ui import APP_NAME


# ==========================================================
# APP CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title=f"{APP_NAME} | Water Quality Forecast",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# PAGE DEFINITIONS
# ==========================================================

current_forecast = st.Page(
    "pages/0_Current_Forecast.py",
    title="Current Forecast",
    default=True,
)


timeline = st.Page(
    "pages/8_Timeline.py",
    title="Timeline",
)


recent_trends = st.Page(
    "pages/4_Recent_Trends.py",
    title="Recent Trends",
)


map_page = st.Page(
    "pages/5_Map.py",
    title="Map",
)


risk_details = st.Page(
    "pages/1_Risk_Details.py",
    title="Risk Details",
)


about = st.Page(
    "pages/2_About.py",
    title=f"About {APP_NAME}",
)


safety = st.Page(
    "pages/3_Disclaimer.py",
    title="Safety & Data Notes",
)


model_data = st.Page(
    "pages/6_Model_and_Data.py",
    title="Model & Data",
)


limitations = st.Page(
    "pages/7_Limitations.py",
    title="Limitations",
)


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

navigation = st.navigation(
    {
        f"🌊 {APP_NAME}": [
            current_forecast,
            timeline,
            recent_trends,
            map_page,
            risk_details,
        ],

        "About & Safety": [
            about,
            safety,
        ],

        "Technical": [
            model_data,
            limitations,
        ],
    },
    position="sidebar",
    expanded=True,
)


# ==========================================================
# RUN SELECTED PAGE
# ==========================================================

navigation.run()
