
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
    risk_icon,
)
from utils.validation import (
    load_valid_latest,
    validate_prediction_row,
)


st.set_page_config(
    page_title="LagoonCast | Model & Data",
    page_icon="assets/LagoonCast_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


SITE_LAT = 37.5602
SITE_LON = -122.2910


# ==========================================================
# LOAD CURRENT PREDICTION
# Try live forecast first.
# If live forecasting fails, do not present an old saved
# prediction as a current forecast.
# ==========================================================

live_prediction = True
live_error = None

try:
    latest = load_live_latest()

except Exception as exc:
    live_prediction = False
    live_error = exc

    historical_text = ""

    try:
        historical = load_valid_latest()

        historical_date = pd.to_datetime(
            historical.get(
                "prediction_date"
            ),
            errors="coerce",
        )

        if pd.notna(
            historical_date
        ):
            historical_text = (
                "<p>"
                "The latest saved LagoonCast prediction is historical "
                f"({historical_date.strftime('%b %d, %Y')}) "
                "and is not being displayed as the current forecast."
                "</p>"
            )

    except Exception:
        historical_text = ""

    st.html(
        f"""
<div class="bg-empty-state">

    <div class="bg-empty-icon">
        !
    </div>

    <h2>
        Current forecast unavailable
    </h2>

    <p>
        LagoonCast cannot retrieve a valid live forecast
        right now. Please check the official
        San Mateo County water-quality advisory.
    </p>

    {historical_text}

    <a
        class="bg-primary-button"
        href="{OFFICIAL_URL}"
        target="_blank"
    >
        Check Official Advisories
    </a>

</div>
"""
    )

    st.stop()


# ==========================================================
# VALIDATE PREDICTION BEFORE DISPLAYING IT
# ==========================================================

validation = validate_prediction_row(
    latest
)

if not validation["valid"]:
    st.error(
        "Prediction currently unavailable. "
        "The latest forecast did not pass "
        "data validation."
    )

    st.link_button(
        "Check Official Water-Quality Advisories",
        OFFICIAL_URL,
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


# ==========================================================
# DISPLAY-ONLY RISK DRIVER
#
# Original model probabilities and classifications remain
# unchanged. Identify which bacterium determines the overall
# category without creating a combined probability.
# ==========================================================

risk_rank = {
    "Safe": 0,
    "Caution": 1,
    "Unsafe": 2,
}

expected_overall_risk = max(
    (ecoli_risk, entero_risk),
    key=lambda label: risk_rank.get(label, -1),
)

if overall_risk != expected_overall_risk:
    risk_driver_name = "See individual bacteria"
    risk_driver_reason = (
        "The overall and bacteria-specific labels do not align. "
        "Please use the official water-quality information."
    )

elif overall_risk == "Safe":
    risk_driver_name = "No elevated driver identified"
    risk_driver_reason = (
        "Both bacteria are classified as Safe by LagoonCast. "
        "This does not guarantee safe water."
    )

else:
    risk_drivers = [
        name
        for name, category in (
            ("E. coli", ecoli_risk),
            ("Enterococcus", entero_risk),
        )
        if category == overall_risk
    ]

    risk_driver_name = " and ".join(risk_drivers)

    if len(risk_drivers) == 2:
        risk_driver_reason = (
            f"Both bacteria are classified as {overall_risk}, "
            "so both contribute to the overall category."
        )
    else:
        risk_driver_reason = (
            f"{risk_driver_name} has the more severe risk category "
            f"({overall_risk}) and determines the overall result."
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


generated_date = pd.to_datetime(
    latest.get(
        "forecast_generated_at",
        latest.get(
            "data_last_updated"
        ),
    ),
    errors="coerce",
)

generated_date_text = (
    generated_date.strftime(
        "%b %d, %Y"
    )
    if pd.notna(
        generated_date
    )
    else "Unavailable"
)


source_text = (
    "Live weather-based AquaCast forecast"
    if live_prediction
    else "Latest validated saved AquaCast forecast"
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

        <!-- RISK DRIVER INDICATOR -->

        <div style="
            margin: 0 0 1.25rem;
            padding: 0.8rem 1rem;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.24);
            border-radius: 12px;
            color: white;
        ">

            <div style="
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.07em;
                opacity: 0.85;
            ">
                RISK DRIVER
            </div>

            <div style="
                font-size: 1.08rem;
                font-weight: 700;
                margin-top: 0.3rem;
            ">
                {risk_driver_name}
            </div>

            <div style="
                font-size: 0.87rem;
                line-height: 1.45;
                margin-top: 0.25rem;
                opacity: 0.92;
            ">
                {risk_driver_reason}
            </div>

        </div>

        <a
            class="bg-primary-button hero-button"
            href="{OFFICIAL_URL}"
            target="_blank"
        >
            Check Official Water-Quality Advisories
        </a>

    </section>

</div>
"""
)


# ==========================================================
# LAST GENERATED DATE
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

    <div class="bg-inline-notice">
        Last successfully generated:
        <strong>{generated_date_text}</strong>
    </div>

</div>
"""
)


# ==========================================================
# FALLBACK NOTICE
# Only appears when the live forecast failed.
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
# OVERALL RISK EXPLANATION
# ==========================================================

st.html(
    """
<div class="bg-home-shell">

    <div class="bg-section-title-row">

        <div>

            <h2 class="bg-section-title">
                Water Quality Risk
            </h2>

            <p class="bg-section-subtitle">
                LagoonCast predicts E. coli and Enterococcus
                separately. The overall Safe, Caution, or Unsafe
                category follows the more severe of the two
                bacteria-specific categories. It is not a combined
                probability of water safety.
            </p>

        </div>

    </div>

</div>
"""
)



# ==========================================================
# WATER QUALITY RISK CARDS
# Both bacterial predictions remain fully visible.
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

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
                Predicted exceedance probability, not the
                probability that swimming is safe
            </div>

            {ecoli_meter}

            <div class="bg-risk-threshold">
                Model-defined concentration threshold:
                <strong>235 MPN/100 mL</strong>
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
                Predicted exceedance probability, not the
                probability that swimming is safe
            </div>

            {entero_meter}

            <div class="bg-risk-threshold">
                Model-defined concentration threshold:
                <strong>130 MPN/100 mL</strong>
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
            "Current LagoonCast forecast: {overall}<br/>"
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
# SAFETY NOTICE
# ==========================================================

st.html(
    """
<div class="bg-home-shell">

    <div class="bg-support-note">

        <strong>
            Important:
        </strong>

        BeachGuard is an experimental decision-support
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
