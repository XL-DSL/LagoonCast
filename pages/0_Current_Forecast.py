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
    load_saved_backup_metadata,
    validate_prediction_row,
)


st.set_page_config(
    page_title="LagoonCast | Water Quality Forecast",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()

SITE_LAT = 37.5602
SITE_LON = -122.2910


def _format_date(value):

    dt = pd.to_datetime(
        value,
        errors="coerce",
    )

    return (
        dt.strftime(
            "%b %d, %Y"
        )
        if pd.notna(
            dt
        )
        else "Unavailable"
    )


# ==========================================================
# LOAD CURRENT LIVE FORECAST
# ==========================================================

try:

    latest = (
        load_live_latest()
    )

except Exception as exc:

    backup = (
        load_saved_backup_metadata()
    )

    backup_text = ""

    if backup is not None:

        backup_text = (
            "<p class='bg-section-subtitle'>"
            "The latest saved model output is historical "
            f"({_format_date(backup.get('prediction_date'))}) "
            "and is not being displayed as a current forecast."
            "</p>"
        )

    st.html(
        f"""
<div class="bg-empty-state">

    <div class="bg-empty-icon">!</div>

    <h2>
        Current forecast unavailable
    </h2>

    <p>
        LagoonCast could not construct a valid live forecast.
        No historical prediction is being presented as current.
        Please use the official San Mateo County water-quality
        information before entering the water.
    </p>

    {backup_text}

    <a
        class="bg-primary-button"
        href="{OFFICIAL_URL}"
        target="_blank"
    >
        Check Official Water-Quality Advisories
    </a>

</div>
"""
    )

    with st.expander(
        "Technical details"
    ):

        st.code(
            str(
                exc
            )
        )

    render_footer(
        "Unavailable"
    )

    st.stop()


# ==========================================================
# VALIDATE LIVE OUTPUT BEFORE DISPLAY
# ==========================================================

validation = (
    validate_prediction_row(
        latest,
        stale_after_days=0,
    )
)


if (
    not validation[
        "valid"
    ]
    or validation[
        "stale"
    ]
):

    st.html(
        f"""
<div class="bg-empty-state">

    <div class="bg-empty-icon">!</div>

    <h2>
        Current forecast unavailable
    </h2>

    <p>
        LagoonCast generated an output that did not pass the
        current-forecast checks, so it is not being shown as
        a current Safe/Caution/Unsafe result.
    </p>

    <a
        class="bg-primary-button"
        href="{OFFICIAL_URL}"
        target="_blank"
    >
        Check Official Water-Quality Advisories
    </a>

</div>
"""
    )

    with st.expander(
        "Technical details"
    ):

        st.write(
            validation[
                "errors"
            ]
        )

        st.write(
            "Forecast age (days):",
            validation[
                "age_days"
            ],
        )

    render_footer(
        str(
            latest.get(
                "model_version",
                "Unavailable",
            )
        )
    )

    st.stop()


# ==========================================================
# PREPARE DISPLAY VALUES
# ==========================================================

prediction_date = pd.to_datetime(
    latest[
        "prediction_date"
    ],
    errors="coerce",
)

updated_date = pd.to_datetime(
    latest[
        "data_last_updated"
    ],
    errors="coerce",
)

model_ver = str(
    latest[
        "model_version"
    ]
).upper()


overall_risk = str(
    latest[
        "overall_risk"
    ]
).strip()

overall_class = risk_class(
    overall_risk
)

overall_icon = risk_icon(
    overall_risk
)


ecoli_risk = str(
    latest[
        "e_coli_risk"
    ]
).strip()

ecoli_prob = float(
    latest[
        "e_coli_probability"
    ]
)

ecoli_class = risk_class(
    ecoli_risk
)


entero_risk = str(
    latest[
        "enterococcus_risk"
    ]
).strip()

entero_prob = float(
    latest[
        "enterococcus_probability"
    ]
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


forecast_generated_text = (
    _format_date(
        latest.get(
            "forecast_generated_at"
        )
    )
)


weather_input_text = (
    _format_date(
        latest.get(
            "weather_input_end_date"
        )
    )
)


ecoli_lab_text = (
    _format_date(
        latest.get(
            "e_coli_latest_lab_date"
        )
    )
)


entero_lab_text = (
    _format_date(
        latest.get(
            "enterococcus_latest_lab_date"
        )
    )
)


# ==========================================================
# HERO
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
# INPUT FRESHNESS
# ==========================================================

st.html(
    f"""
<div class="bg-home-shell">

    <div class="bg-inline-notice">

        <strong>
            Last successfully generated:
        </strong>

        {forecast_generated_text}

        &nbsp;·&nbsp;

        <strong>
            Weather input through:
        </strong>

        {weather_input_text}

        <br>

        <strong>
            Latest actual E. coli lab sample used:
        </strong>

        {ecoli_lab_text}

        &nbsp;·&nbsp;

        <strong>
            Latest actual Enterococcus lab sample used:
        </strong>

        {entero_lab_text}

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
                Predicted probability that bacterial levels exceed
                LagoonCast's model-defined concentration threshold.
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

                Model-defined exceedance threshold:

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

                Model-defined exceedance threshold:

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
# PILOT SITE + MAP
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

                Current LagoonCast forecast:
                {overall_risk}

            </p>

        </div>

    </div>

</div>
"""
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

        map_data = pd.DataFrame(
            {
                "lat":
                    [
                        SITE_LAT
                    ],

                "lon":
                    [
                        SITE_LON
                    ],
            }
        )

        st.map(
            map_data,
            zoom=14,
        )


        map_col1, map_col2 = st.columns(
            [
                3,
                1,
            ]
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
# SAFETY NOTE
# ==========================================================

st.html(
    """
<div class="bg-home-shell">

    <div class="bg-support-note">

        <strong>
            Important:
        </strong>

        LagoonCast is an experimental decision-support forecast.
        It does not directly measure bacteria and does not replace
        official laboratory results, advisories, or closures.

        The 235 and 130 MPN/100 mL values shown above are the
        model-defined concentration thresholds used to create
        LagoonCast's training labels. They are not presented here
        as current official closure limits for Parkside Aquatic Park.

    </div>

</div>
"""
)


render_footer(
    model_ver
)
