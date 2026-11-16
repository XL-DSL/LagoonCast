
import pandas as pd
import streamlit as st

from utils.live_forecast import load_live_latest
from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_URL,
    ADVISORY_BUTTON_LABEL,
    OFFICIAL_URL,
    REPORTS_BUTTON_LABEL,
    SITE_NAME,
    PREDICTION_EXPLANATION,
    SAFE_EXPLANATION,
    OFFICIAL_PRIORITY_NOTICE,
    freshness_chip,
    probability_meter,
    render_footer,
    risk_class,
    risk_driver_text,
    risk_icon,
)
from utils.validation import validate_prediction_row


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="LagoonCast | Risk Details",
    page_icon="assets/LagoonCast_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


# ==========================================================
# LOAD CURRENT PREDICTION
# Do not display an old saved prediction as current.
# ==========================================================

try:
    latest = load_live_latest()

except Exception:

    st.error(
        "Current predictions are temporarily unavailable. "
        "LagoonCast could not generate a valid live forecast. "
        "Please refer to official water-quality information."
    )

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
    )

    st.stop()


# ==========================================================
# VALIDATE CURRENT PREDICTION
# ==========================================================

validation = validate_prediction_row(
    latest
)

if not validation["valid"]:

    st.error(
        "The current prediction did not pass data "
        "validation and cannot be displayed reliably."
    )

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
    )

    st.stop()


if validation["stale"]:

    st.warning(
        "The latest prediction is outdated and is not "
        "being presented as a current risk assessment."
    )

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
    )

    st.stop()


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


ecoli_prob = float(
    latest["e_coli_probability"]
)

ecoli_risk = str(
    latest["e_coli_risk"]
).strip()


entero_prob = float(
    latest["enterococcus_probability"]
)

entero_risk = str(
    latest["enterococcus_risk"]
).strip()


prediction_text = (
    prediction_date.strftime(
        "%b %d, %Y"
    )
    if pd.notna(prediction_date)
    else "Date unavailable"
)


# ==========================================================
# VERIFY OVERALL CLASSIFICATION
# No recalculation or modification of model predictions.
# ==========================================================

risk_rank = {
    "Safe": 0,
    "Caution": 1,
    "Unsafe": 2,
}

if (
    overall_risk not in risk_rank
    or ecoli_risk not in risk_rank
    or entero_risk not in risk_rank
):

    st.error(
        "One or more risk classifications are invalid."
    )

    st.stop()


expected_overall = max(
    (ecoli_risk, entero_risk),
    key=lambda risk: risk_rank[risk],
)


if overall_risk != expected_overall:

    st.error(
        "The overall risk classification does not match "
        "the bacteria-specific results. Please refer to "
        "official water-quality information."
    )

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
    )

    st.stop()


driver_explanation = risk_driver_text(
    ecoli_risk,
    entero_risk,
)


# ==========================================================
# HEADER
# ==========================================================

st.html(
    f"""
<div class="bg-reading">

    <div class="bg-page-heading">

        <h1>
            Risk Details
        </h1>

        <p>
            Explore the two bacteria-specific predictions
            that determine LagoonCast's overall forecast
            for {SITE_NAME}.
        </p>

        <div class="bg-page-meta">
            Forecast for {prediction_text}
            &nbsp;·&nbsp;
            {freshness_chip(updated_date)}
        </div>

    </div>

</div>
"""
)


# ==========================================================
# HOW TO INTERPRET THE FORECAST
# ==========================================================

st.html(
    f"""
<div class="bg-reading">

    <div class="bg-how-read">

        <strong>
            How to read this page
        </strong>

        <p>
            {PREDICTION_EXPLANATION}
        </p>

        <p>
            Each percentage estimates the likelihood
            that one bacterial indicator exceeds its
            model-defined concentration threshold.
            These percentages do not represent the
            probability that swimming is safe.
        </p>

    </div>

</div>
"""
)


# ==========================================================
# OVERALL RISK AND RISK DRIVER
# ==========================================================

st.html(
    f"""
<div class="bg-reading">

    <div class="bg-small-explainer">

        <strong>
            Overall predicted risk: {overall_risk}
        </strong>

        <p>
            {driver_explanation}
        </p>

        <p>
            LagoonCast evaluates E. coli and Enterococcus
            separately. The overall risk is determined
            by whichever bacterium has the more severe
            Safe, Caution, or Unsafe classification.
            If both have the same classification,
            both contribute equally to the overall category.
        </p>

        <p>
            LagoonCast does not calculate a single
            combined probability of water safety.
        </p>

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
# BACTERIA-SPECIFIC RISK CARDS
# ==========================================================

st.html(
    f"""
<div class="bg-reading">

    <div class="bg-risk-detail-grid">

        <article class="bg-risk-detail-card {risk_class(ecoli_risk)}">

            <div class="bg-risk-card-top">

                <div class="bg-organism-icon">
                    EC
                </div>

                <div>

                    <h2>
                        E. coli
                    </h2>

                    <div class="bg-risk-pill {risk_class(ecoli_risk)}">
                        {risk_icon(ecoli_risk)}
                        {ecoli_risk}
                    </div>

                </div>

            </div>

            <div class="bg-detail-probability">
                {ecoli_prob:.0%}
            </div>

            <div class="bg-risk-value-label">
                Predicted exceedance probability
            </div>

            {ecoli_meter}

        </article>


        <article class="bg-risk-detail-card {risk_class(entero_risk)}">

            <div class="bg-risk-card-top">

                <div class="bg-organism-icon">
                    EN
                </div>

                <div>

                    <h2>
                        Enterococcus
                    </h2>

                    <div class="bg-risk-pill {risk_class(entero_risk)}">
                        {risk_icon(entero_risk)}
                        {entero_risk}
                    </div>

                </div>

            </div>

            <div class="bg-detail-probability">
                {entero_prob:.0%}
            </div>

            <div class="bg-risk-value-label">
                Predicted exceedance probability
            </div>

            {entero_meter}

        </article>

    </div>

</div>
"""
)


# ==========================================================
# TECHNICAL DETAILS
# ==========================================================

tech_left, tech_right = st.columns(
    2
)


with tech_left:

    with st.expander(
        "E. coli technical details"
    ):

        st.markdown(
            """
**Model-defined concentration threshold:** 235 MPN/100 mL

**Probability display thresholds**

- Safe: Below 10%
- Caution: 10% to below 50%
- Unsafe: 50% or higher

E. coli is a fecal-indicator bacterium.
Elevated levels can indicate increased
contamination risk in recreational water.

These concentration and probability thresholds
describe LagoonCast's deployed model. They
should not be interpreted as current official
closure criteria.
"""
        )


with tech_right:

    with st.expander(
        "Enterococcus technical details"
    ):

        st.markdown(
            """
**Model-defined concentration threshold:** 130 MPN/100 mL

**Probability display thresholds**

- Safe: Below 40%
- Caution: 40% to below 85%
- Unsafe: 85% or higher

Enterococcus is commonly used as a
fecal-indicator bacterium in marine and
estuarine recreational waters.

These concentration and probability thresholds
describe LagoonCast's deployed model. They
should not be interpreted as current official
closure criteria.
"""
        )


# ==========================================================
# EXPLANATION OF DIFFERENT THRESHOLDS
# ==========================================================

st.html(
    """
<div class="bg-reading">

    <div class="bg-small-explainer">

        <strong>
            Why are the probability thresholds different?
        </strong>

        <p>
            E. coli and Enterococcus use different
            probability boundaries because the two
            models have different performance
            characteristics.
        </p>

        <p>
            These boundaries determine which risk
            category LagoonCast displays. They are
            separate from the bacterial concentration
            thresholds used to define exceedances.
        </p>

        <p>
            A higher probability does not necessarily
            produce a more severe classification
            than a lower probability for the other
            bacterium, because the two models use
            different display boundaries.
        </p>

    </div>

</div>
"""
)


# ==========================================================
# SAFETY AND UNCERTAINTY
# ==========================================================

st.subheader(
    "Important safety information"
)


st.info(
    SAFE_EXPLANATION
)


st.write(
    "Even when LagoonCast predicts lower bacterial risk, "
    "actual concentrations may be elevated. The models "
    "can produce incorrect predictions and do not "
    "directly measure bacteria in the water."
)


st.write(
    OFFICIAL_PRIORITY_NOTICE
)


# ==========================================================
# OFFICIAL INFORMATION LINKS
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
    model_ver
)
