import streamlit as st

from utils.styles import apply_styles
from utils.ui import (
    OFFICIAL_URL,
    render_footer,
)


apply_styles()


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "Safety & Data Notes"
)

st.caption(
    "How to interpret LagoonCast and where its information comes from."
)


# ==========================================================
# OFFICIAL INFORMATION
# ==========================================================

st.html(
    """
<div style="
    background:#FFF8CC;
    color:#5C4A00;
    border:1px solid #F1E59A;
    border-radius:12px;
    padding:1rem 1.1rem;
    margin-bottom:1.4rem;
    line-height:1.55;
">

    <strong>
        Official information always takes priority.
    </strong>

    <br>

    LagoonCast is an experimental research prototype.
    It does not issue government advisories, postings,
    or closures.

</div>
"""
)


st.link_button(
    "View Official San Mateo County Beach Status",
    OFFICIAL_URL,
    width="stretch",
)


# ==========================================================
# WHAT THE APP DOES
# ==========================================================

st.subheader(
    "What the forecast means"
)


st.write(
    "LagoonCast estimates the probability that E. coli or "
    "Enterococcus concentrations exceed the model's "
    "elevated-risk concentration threshold. It does not "
    "predict an exact bacteria concentration."
)


st.write(
    "Safe, Caution, and Unsafe are LagoonCast model "
    "communication categories. They should not be interpreted "
    "as official government posting or closure categories."
)


# ==========================================================
# DATA SOURCES
# ==========================================================

st.subheader(
    "Data sources"
)


source1, source2 = st.columns(
    2
)


with source1:

    st.link_button(
        "California Water Boards / SWAMP",
        "https://www.waterboards.ca.gov/water_issues/programs/swamp/",
        width="stretch",
    )


with source2:

    st.link_button(
        "NOAA NCEI Daily Summaries",
        "https://www.ncei.noaa.gov/access/search/data-search/daily-summaries",
        width="stretch",
    )


source3, source4 = st.columns(
    2
)


with source3:

    st.link_button(
        "Open-Meteo Forecast Weather",
        "https://open-meteo.com/",
        width="stretch",
    )


with source4:

    st.link_button(
        "San Mateo County Beach Information",
        OFFICIAL_URL,
        width="stretch",
    )


# ==========================================================
# DATA NOTES
# ==========================================================

with st.expander(
    "Laboratory bacteria data"
):

    st.write(
        "Historical E. coli and Enterococcus observations "
        "are used to train and evaluate LagoonCast. "
        "Laboratory observations are not continuously available, "
        "so the live forecast is not a real-time bacteria sensor."
    )


with st.expander(
    "Weather data"
):

    st.write(
        "Historical weather information supports model "
        "development, while the live application uses "
        "forecast environmental conditions to estimate "
        "future bacterial risk."
    )


with st.expander(
    "Excluded data sources"
):

    st.write(
        "Tide variables and sanitary sewer overflow variables "
        "were evaluated during project development but are not "
        "included in the selected deployed model configuration."
    )


# ==========================================================
# PUBLIC SAFETY
# ==========================================================

st.subheader(
    "Before entering the water"
)


st.write(
    "Check current official beach information, follow posted "
    "signage, and use local public-health guidance. LagoonCast "
    "should be treated as supplemental research information only."
)


render_footer()
