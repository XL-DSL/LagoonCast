
import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.live_forecast import load_live_latest
from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_URL,
    ADVISORY_BUTTON_LABEL,
    OFFICIAL_URL,
    REPORTS_BUTTON_LABEL,
    OFFICIAL_PRIORITY_NOTICE,
    SAFE_EXPLANATION,
    SITE_NAME,
    render_footer,
)
from utils.validation import load_valid_latest


apply_styles()


# ==========================================================
# SITE
# ==========================================================

SITE_LAT = 37.5602
SITE_LON = -122.2910


# ==========================================================
# LOAD CURRENT FORECAST
# ==========================================================

live_prediction = True


try:

    latest = load_live_latest()

except Exception:

    live_prediction = False

    try:

        latest = load_valid_latest()

    except Exception:

        st.error(
            "The LagoonCast map is temporarily unavailable."
        )

        st.link_button(
            ADVISORY_BUTTON_LABEL,
            ADVISORY_URL,
            width="stretch",
        )

        st.stop()


overall = str(
    latest[
        "overall_risk"
    ]
).strip()


ecoli = float(
    latest[
        "e_coli_probability"
    ]
)


entero = float(
    latest[
        "enterococcus_probability"
    ]
)


prediction_date = pd.to_datetime(
    latest[
        "prediction_date"
    ],
    errors="coerce",
)


date_text = (
    prediction_date.strftime(
        "%b %d, %Y"
    )
    if pd.notna(
        prediction_date
    )
    else "Date unavailable"
)


# ==========================================================
# FORECAST SOURCE LABELS
# ==========================================================

if live_prediction:

    forecast_label = "Current LagoonCast forecast"

    source_text = (
        "Live weather-based LagoonCast forecast"
    )

    map_status_label = (
        "Current predicted risk"
    )

else:

    forecast_label = "Saved historical model estimate"

    source_text = (
        "Latest validated saved LagoonCast prediction "
        "(historical, not a current forecast)"
    )

    map_status_label = (
        "Historical predicted risk"
    )


# ==========================================================
# RISK COLOR
# ==========================================================

RISK_COLORS = {
    "Safe":
        [
            46,
            125,
            50,
            210,
        ],

    "Caution":
        [
            178,
            106,
            0,
            210,
        ],

    "Unsafe":
        [
            198,
            40,
            40,
            210,
        ],
}


marker_color = RISK_COLORS.get(
    overall,
    [
        102,
        112,
        133,
        210,
    ],
)


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "Map"
)

st.caption(
    f"LagoonCast's pilot forecast location at {SITE_NAME}. "
    "Map colors represent model-estimated bacterial risk, "
    "not official beach advisories or closures."
)


# ==========================================================
# HISTORICAL FORECAST WARNING
# ==========================================================

if not live_prediction:

    st.warning(
        "Live forecasting is currently unavailable. "
        f"The map is displaying a saved model estimate "
        f"dated {date_text}, not today's water-quality "
        "forecast. Check official county information "
        "for current conditions."
    )


# ==========================================================
# COMPACT SITE SUMMARY
# Original styling preserved.
# ==========================================================

risk_color = {
    "Safe":
        "#2E7D32",

    "Caution":
        "#B26A00",

    "Unsafe":
        "#C62828",
}.get(
    overall,
    "#667085",
)


st.html(
    f"""
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-radius:14px;
    padding:1rem 1.1rem;
    margin-bottom:1rem;
">

    <div style="
        display:flex;
        justify-content:space-between;
        gap:1rem;
        flex-wrap:wrap;
    ">

        <div>

            <div style="
                color:#172033;
                font-size:1rem;
                font-weight:800;
            ">
                Parkside Aquatic Park
            </div>

            <div style="
                color:#667085;
                font-size:0.76rem;
                margin-top:0.15rem;
            ">
                San Mateo, California · {date_text}
            </div>

        </div>


        <div style="
            text-align:right;
        ">

            <div style="
                color:#667085;
                font-size:0.72rem;
                font-weight:600;
                margin-bottom:0.15rem;
            ">
                {map_status_label}
            </div>

            <div style="
                color:{risk_color};
                font-size:1rem;
                font-weight:800;
            ">
                {overall}
            </div>

        </div>

    </div>


    <div style="
        display:flex;
        flex-wrap:wrap;
        gap:1.2rem;
        margin-top:0.8rem;
        color:#475467;
        font-size:0.78rem;
    ">

        <span>
            E. coli predicted exceedance
            <strong style="color:#172033;">
                {ecoli:.1%}
            </strong>
        </span>

        <span>
            Enterococcus predicted exceedance
            <strong style="color:#172033;">
                {entero:.1%}
            </strong>
        </span>

    </div>

</div>
"""
)


# ==========================================================
# MAP
# Original map design, zoom, marker size, and colors.
# ==========================================================

map_data = pd.DataFrame(
    [
        {
            "lat":
                SITE_LAT,

            "lon":
                SITE_LON,

            "site":
                "Parkside Aquatic Park",

            "overall":
                overall,

            "ecoli":
                f"{ecoli:.1%}",

            "entero":
                f"{entero:.1%}",

            "date":
                date_text,

            "source":
                forecast_label,
        }
    ]
)


layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_data,
    get_position=[
        "lon",
        "lat",
    ],
    get_fill_color=marker_color,
    get_line_color=[
        255,
        255,
        255,
        255,
    ],
    line_width_min_pixels=2,
    stroked=True,
    filled=True,
    radius_min_pixels=8,
    radius_max_pixels=12,
    pickable=True,
)


view_state = pdk.ViewState(
    latitude=SITE_LAT,
    longitude=SITE_LON,
    zoom=14.4,
    pitch=0,
)


deck = pdk.Deck(
    layers=[
        layer
    ],

    initial_view_state=view_state,

    tooltip={
        "html":
            "<b>{site}</b><br/>"
            "{source}<br/>"
            "Predicted risk: {overall}<br/>"
            "E. coli exceedance probability: {ecoli}<br/>"
            "Enterococcus exceedance probability: {entero}<br/>"
            "Prediction date: {date}",

        "style":
            {
                "backgroundColor":
                    "#172033",

                "color":
                    "white",
            },
    },
)


st.pydeck_chart(
    deck,
    width="stretch",
)


# ==========================================================
# MAP ACTIONS
# Original button layout preserved.
# ==========================================================

button1, button2 = st.columns(
    2
)


with button1:

    st.link_button(
        "Directions",
        (
            "https://www.google.com/maps/dir/"
            "?api=1&destination="
            f"{SITE_LAT},{SITE_LON}"
        ),
        width="stretch",
    )


with button2:

    st.link_button(
        "Open in Google Maps",
        (
            "https://www.google.com/maps/search/"
            "?api=1&query="
            f"{SITE_LAT},{SITE_LON}"
        ),
        width="stretch",
    )


# ==========================================================
# SOURCE
# ==========================================================

st.caption(
    f"Forecast source: {source_text}. "
    "Map marker color follows LagoonCast's Safe / Caution / "
    "Unsafe classification, not official beach status."
)


# ==========================================================
# SAFETY NOTES
# ==========================================================

st.warning(
    "This map shows LagoonCast's model-estimated risk "
    "at its pilot location. It does not indicate an "
    "official beach closure or advisory."
)


st.caption(
    SAFE_EXPLANATION
)


st.caption(
    OFFICIAL_PRIORITY_NOTICE
)


# ==========================================================
# OFFICIAL WATER-QUALITY INFORMATION
# ==========================================================

official_col1, official_col2 = st.columns(
    2
)


with official_col1:

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
        width="stretch",
    )


with official_col2:

    st.link_button(
        REPORTS_BUTTON_LABEL,
        OFFICIAL_URL,
        width="stretch",
    )


# ==========================================================
# FOOTER
# ==========================================================

render_footer(
    str(
        latest[
            "model_version"
        ]
    )
)
