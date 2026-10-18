import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.live_forecast import load_live_latest
from utils.styles import apply_styles
from utils.ui import (
    OFFICIAL_URL,
    SITE_NAME,
    freshness_chip,
    interpretation,
    probability_meter,
    render_footer,
    risk_class,
    risk_driver_text,
    risk_icon,
    successful_generation_text,
)
from utils.validation import (
    load_valid_latest,
    validate_prediction_row,
)


apply_styles()


# ==========================================================
# SITE
# ==========================================================

SITE_LAT = 37.5602
SITE_LON = -122.2910


# ==========================================================
# LOAD CURRENT PREDICTION
# ==========================================================

live_prediction = True
live_error = None


try:

    latest = load_live_latest()


except Exception as exc:

    live_prediction = False
    live_error = exc

    try:

        latest = load_valid_latest()

    except Exception:

        st.html(
            f"""
<div class="bg-empty-state">

    <div class="bg-empty-icon">
        !
    </div>

    <h2>
        Forecast temporarily unavailable
    </h2>

    <p>
        AquaCast cannot retrieve a valid forecast
        right now. Please check the official
        San Mateo County water-quality information.
    </p>

    <a
        class="bg-primary-button"
        href="{OFFICIAL_URL}"
        target="_blank"
    >
        View Official San Mateo County Beach Status
    </a>

</div>
"""
        )

        st.stop()


# ==========================================================
# VALIDATE PREDICTION
# ==========================================================

validation = validate_prediction_row(
    latest
)


if not validation["valid"]:

    st.error(
        "Prediction currently unavailable. "
        "The latest forecast did not pass "
        "automated data checks."
    )

    st.link_button(
        "View Official San Mateo County Beach Status",
        OFFICIAL_URL,
        width="stretch",
    )

    st.stop()


if validation["stale"]:

    st.warning(
        "This prediction is more than 7 days old "
        "and may no longer represent current conditions."
    )


# ==========================================================
# PREPARE DISPLAY VALUES
# ==========================================================

prediction_date = pd.to_datetime(
    latest["prediction_date"],
    errors="coerce",
)


updated_date = pd.to_datetime(
    latest["data_last_updated"],
    errors="coerce",
)


model_ver = str(
    latest["model_version"]
).upper()


overall_risk = str(
    latest["overall_risk"]
).strip()


overall_class = risk_class(
    overall_risk
)


overall_icon = risk_icon(
    overall_risk
)


ecoli_risk = str(
    latest["e_coli_risk"]
).strip()


ecoli_prob = float(
    latest["e_coli_probability"]
)


ecoli_class = risk_class(
    ecoli_risk
)


entero_risk = str(
    latest["enterococcus_risk"]
).strip()


entero_prob = float(
    latest["enterococcus_probability"]
)


entero_class = risk_class(
    entero_risk
)


prediction_text = (
    prediction_date.strftime(
        "%b %d, %Y"
    )
    if pd.notna(
        prediction_date
    )
    else "Date unavailable"
)


freshness = freshness_chip(
    updated_date
)


source_text = (
    "Live weather-based AquaCast forecast"
    if live_prediction
    else "Latest validated saved AquaCast forecast"
)


driver_text = risk_driver_text(
    ecoli_risk,
    entero_risk,
)


generated_text = successful_generation_text(
    latest,
    using_live=live_prediction,
)


# ==========================================================
# HERO / CURRENT FORECAST
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

    <section class="bg-home-hero {overall_class}">

        <div class="bg-home-eyebrow">
            {SITE_NAME}
        </div>


        <div class="bg-home-meta">

            <span>
                Forecast for {prediction_text}
            </span>

            {freshness}

        </div>


        <div class="bg-home-status">

            <div class="bg-home-status-icon">
                {overall_icon}
            </div>


            <div>

                <div class="bg-home-status-label">
                    {overall_risk}
                </div>

                <p class="bg-home-status-message">
                    {interpretation(overall_risk)}
                </p>

            </div>

        </div>


        <a
            class="bg-primary-button hero-button"
            href="{OFFICIAL_URL}"
            target="_blank"
        >
            View Official San Mateo County Beach Status
        </a>

    </section>

</div>
"""
)


# ==========================================================
# FORECAST CONTEXT
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

    <div class="bg-forecast-context">

        <div class="bg-risk-driver">
            {driver_text}
        </div>

        <div class="bg-generated-time">
            Last successfully generated:
            <strong>
                {generated_text}
            </strong>
        </div>

    </div>

</div>
"""
)


# ==========================================================
# FALLBACK NOTICE
# ==========================================================

if not live_prediction:

    st.html(
        """
<div class="bg-home-shell">

    <div class="bg-inline-notice">
        Live weather input is temporarily unavailable.
        Showing the latest validated saved
        AquaCast prediction.
    </div>

</div>
"""
    )


# ==========================================================
# BACTERIA PROBABILITY METERS
# ==========================================================

ecoli_meter = probability_meter(
    ecoli_prob,
    0.10,
    0.50,
    ecoli_risk,
)


entero_meter = probability_meter(
    entero_prob,
    0.40,
    0.85,
    entero_risk,
)


# ==========================================================
# WATER QUALITY RISK CARDS
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

    <div class="bg-section-title-row">

        <div>

            <h2 class="bg-section-title">
                Water Quality Risk
            </h2>

            <p class="bg-section-subtitle">
                Predicted probability that bacterial
                levels exceed the model's
                elevated-risk concentration threshold.
            </p>

        </div>

    </div>


    <div class="bg-risk-grid">

        <article class="bg-risk-card {ecoli_class}">

            <div class="bg-risk-card-top">

                <div class="bg-organism-icon">
                    EC
                </div>


                <div>

                    <div class="bg-risk-card-name">
                        E. coli
                    </div>

                    <div class="bg-risk-pill {ecoli_class}">
                        {risk_icon(ecoli_risk)}
                        {ecoli_risk}
                    </div>

                </div>

            </div>


            <div class="bg-risk-value">
                {ecoli_prob:.0%}
            </div>


            <div class="bg-risk-value-label">
                Predicted exceedance probability
            </div>


            {ecoli_meter}


            <div class="bg-risk-threshold">
                Concentration threshold:
                <strong>
                    235 MPN/100 mL
                </strong>
            </div>

        </article>


        <article class="bg-risk-card {entero_class}">

            <div class="bg-risk-card-top">

                <div class="bg-organism-icon">
                    EN
                </div>


                <div>

                    <div class="bg-risk-card-name">
                        Enterococcus
                    </div>

                    <div class="bg-risk-pill {entero_class}">
                        {risk_icon(entero_risk)}
                        {entero_risk}
                    </div>

                </div>

            </div>


            <div class="bg-risk-value">
                {entero_prob:.0%}
            </div>


            <div class="bg-risk-value-label">
                Predicted exceedance probability
            </div>


            {entero_meter}


            <div class="bg-risk-threshold">
                Concentration threshold:
                <strong>
                    130 MPN/100 mL
                </strong>
            </div>

        </article>

    </div>

</div>
"""
)


# ==========================================================
# PILOT SITE
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

    <div class="bg-section-title-row">

        <div>

            <h2 class="bg-section-title">
                Pilot Site
            </h2>

            <p class="bg-section-subtitle">
                {SITE_NAME}
                &nbsp;·&nbsp;
                Current forecast: {overall_risk}
            </p>

        </div>

    </div>

</div>
"""
)


# ==========================================================
# MAP
# Same interactive map style as standalone Map page.
# ==========================================================

RISK_COLORS = {
    "Safe": [
        46,
        125,
        50,
        210,
    ],

    "Caution": [
        178,
        106,
        0,
        210,
    ],

    "Unsafe": [
        198,
        40,
        40,
        210,
    ],
}


marker_color = RISK_COLORS.get(
    overall_risk,
    [
        102,
        112,
        133,
        210,
    ],
)


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
                overall_risk,

            "ecoli":
                f"{ecoli_prob:.1%}",

            "entero":
                f"{entero_prob:.1%}",

            "date":
                prediction_text,
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


map_left, map_center, map_right = st.columns(
    [
        1,
        10,
        1,
    ]
)


with map_center:

    with st.container(
        border=True
    ):

        st.pydeck_chart(
            deck,
            width="stretch",
            height=430,
        )


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


        st.caption(
            f"📍 {SITE_NAME} · "
            f"{source_text}. "
            "Hover over the marker for forecast details."
        )


# ==========================================================
# SAFETY NOTICE
# ==========================================================

st.html(
    """
<div class="bg-home-shell">

    <div class="bg-support-note">

        <strong>
            Important:
        </strong>

        LagoonCast is an experimental decision-support
        forecast. It does not directly measure bacteria
        and does not replace official laboratory results,
        advisories, or closures.

    </div>

</div>
"""
)


# ==========================================================
# FOOTER
# ==========================================================

render_footer(
    model_ver
)
