import pandas as pd
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
    page_title="BeachGuard | AquaCast Water Quality Forecast",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


SITE_LAT = 37.5602
SITE_LON = -122.2910


# ==========================================================
# LOAD CURRENT PREDICTION
# Try live forecast first.
# If live forecasting fails, use the latest validated saved
# prediction instead.
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
        San Mateo County water-quality advisory.
    </p>

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
                Predicted exceedance probability
            </div>

            {entero_meter}

            <div class="bg-risk-threshold">
                Concentration threshold:
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

map_left, map_center, map_right = st.columns(
    [1, 10, 1]
)

with map_center:

    with st.container(
        border=True
    ):

        map_data = pd.DataFrame(
            {
                "lat": [
                    SITE_LAT
                ],
                "lon": [
                    SITE_LON
                ],
            }
        )

        st.map(
            map_data,
            zoom=14,
        )

        map_col1, map_col2 = st.columns(
            [3, 1]
        )

        with map_col1:

            st.caption(
                f"📍 {SITE_NAME} · "
                "Live LagoonCast model forecast"
            )

        with map_col2:

            st.link_button(
                "Open larger map",
                (
                    "https://www.google.com/maps/search/"
                    "?api=1&query="
                    f"{SITE_LAT},{SITE_LON}"
                ),
                use_container_width=True,
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
