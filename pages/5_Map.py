import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.live_forecast import load_live_latest
from utils.styles import apply_styles
from utils.ui import (
    OFFICIAL_URL,
    SITE_NAME,
    render_footer,
    risk_class,
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
            "The AquaCast map is temporarily unavailable."
        )

        st.link_button(
            "View Official San Mateo County Beach Status",
            OFFICIAL_URL,
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
    "Current AquaCast forecast location at "
    f"{SITE_NAME}."
)


# ==========================================================
# COMPACT SITE SUMMARY
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
            color:{risk_color};
            font-size:1rem;
            font-weight:800;
        ">
            {overall}
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
            E. coli
            <strong style="color:#172033;">
                {ecoli:.1%}
            </strong>
        </span>

        <span>
            Enterococcus
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
            "Current AquaCast forecast: {overall}<br/>"
            "E. coli: {ecoli}<br/>"
            "Enterococcus: {entero}<br/>"
            "Forecast date: {date}",

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

source_text = (
    "Live weather-based AquaCast forecast"
    if live_prediction
    else "Latest validated saved AquaCast forecast"
)


st.caption(
    f"Forecast source: {source_text}. "
    "Map marker color uses the same Safe / Caution / "
    "Unsafe classification shown throughout LagoonCast."
)


st.warning(
    "The map shows AquaCast's pilot forecast location. "
    "It does not indicate an official beach closure "
    "or advisory."
)


st.link_button(
    "View Official San Mateo County Beach Status",
    OFFICIAL_URL,
    width="stretch",
)


render_footer(
    str(
        latest[
            "model_version"
        ]
    )
)
