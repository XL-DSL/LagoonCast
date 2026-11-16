
import streamlit as st

from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_URL,
    ADVISORY_BUTTON_LABEL,
    OFFICIAL_URL,
    REPORTS_BUTTON_LABEL,
    PREDICTION_EXPLANATION,
    SAFE_EXPLANATION,
    OFFICIAL_PRIORITY_NOTICE,
    MODEL_LIMITATION_NOTICE,
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
    "How to interpret LagoonCast predictions, understand "
    "their limitations, and find official water-quality information."
)


# ==========================================================
# OFFICIAL INFORMATION
# ==========================================================

st.html(
    f"""
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
        Official water-quality information always takes priority.
    </strong>

    <p style="margin:0.6rem 0 0;">
        {OFFICIAL_PRIORITY_NOTICE}
    </p>

    <p style="margin:0.6rem 0 0;">
        LagoonCast provides independent model predictions.
        It does not issue government advisories,
        warnings, or closures.
    </p>

</div>
"""
)


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
# WHAT THE APP DOES
# ==========================================================

st.subheader(
    "What the forecast means"
)


st.write(
    PREDICTION_EXPLANATION
)


st.write(
    "LagoonCast estimates the probability that E. coli or "
    "Enterococcus concentrations exceed their respective "
    "model-defined concentration thresholds. These probabilities "
    "are not direct measurements or predictions of exact "
    "bacterial concentrations."
)


st.write(
    "The two bacteria are evaluated separately. LagoonCast "
    "uses the more severe bacteria-specific classification "
    "to determine the overall risk category. It does not "
    "calculate a single combined probability of water safety."
)


# ==========================================================
# RISK CLASSIFICATIONS
# ==========================================================

st.subheader(
    "Understanding Safe, Caution, and Unsafe"
)


st.write(
    "LagoonCast organizes its predictions into three categories "
    "to help communicate bacterial risk. These are model-generated "
    "categories, not official government advisories or closures."
)


st.markdown(
    """
**Safe — Lower predicted risk**

The model estimates lower bacterial risk based on the available
environmental information. This does not guarantee safe conditions.

**Caution — Possible elevated risk**

The model identifies conditions that may indicate elevated
bacterial risk. Check official water-quality information
before entering the water.

**Unsafe — Elevated predicted risk**

The model indicates elevated bacterial risk. Avoid water
contact and follow official public-health guidance.
"""
)


st.info(
    SAFE_EXPLANATION
)


# ==========================================================
# PREDICTION UNCERTAINTY
# ==========================================================

st.subheader(
    "What if the prediction is incorrect?"
)


st.write(
    MODEL_LIMITATION_NOTICE
)


st.write(
    "Like other statistical models, LagoonCast can make "
    "incorrect predictions. Two important types of errors are:"
)


st.markdown(
    """
- **False negative:** LagoonCast predicts lower bacterial risk,
  but laboratory testing would show elevated bacteria levels.
  This is especially important because users might incorrectly
  assume that the water is safe.

- **False positive:** LagoonCast predicts elevated bacterial risk,
  but laboratory testing would not show an exceedance.
  This may result in a more cautious assessment than necessary.
"""
)


st.write(
    "Bacterial concentrations can change between laboratory "
    "sampling events, particularly following rainfall, runoff, "
    "or other environmental disturbances. LagoonCast cannot "
    "detect every such change and cannot guarantee that its "
    "predictions reflect actual water conditions."
)


# ==========================================================
# CONFLICTS WITH OFFICIAL ADVISORIES
# ==========================================================

st.subheader(
    "What if LagoonCast disagrees with an official advisory?"
)


st.write(
    "Official advisories and closures always take priority, "
    "regardless of LagoonCast's prediction."
)


st.write(
    'For example, if LagoonCast displays "Safe" while '
    "San Mateo County has issued a closure or warning, "
    "follow the county's instructions. LagoonCast's "
    "prediction does not override official water-quality "
    "information."
)


# ==========================================================
# DATA SOURCES
# ==========================================================

st.subheader(
    "Data sources"
)


st.write(
    "LagoonCast uses historical bacterial observations "
    "and environmental information to develop and "
    "generate its predictions."
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
        REPORTS_BUTTON_LABEL,
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
        "are used to train and evaluate LagoonCast's models. "
        "These measurements come from laboratory testing "
        "rather than continuous monitoring."
    )

    st.write(
        "The latest laboratory measurement may not represent "
        "current conditions. LagoonCast uses environmental "
        "information to estimate risk between routine "
        "sampling events, but it does not directly "
        "measure bacteria in real time."
    )


with st.expander(
    "Weather data"
):

    st.write(
        "Historical weather information supports model "
        "development, while the live application uses "
        "recent and forecast environmental conditions "
        "to estimate bacterial risk."
    )

    st.write(
        "Weather forecasts and environmental measurements "
        "may contain uncertainty. These uncertainties "
        "can affect the reliability of model predictions."
    )


with st.expander(
    "Excluded data sources"
):

    st.write(
        "Tide variables and sanitary sewer overflow variables "
        "were evaluated during project development but are not "
        "included in the selected deployed model configuration."
    )

    st.write(
        "As a result, LagoonCast may not fully account for "
        "every environmental factor influencing bacterial "
        "concentrations at the pilot site."
    )


# ==========================================================
# PUBLIC SAFETY
# ==========================================================

st.subheader(
    "Before entering the water"
)


st.write(
    "LagoonCast is intended to provide additional information "
    "about possible bacterial risk, particularly between "
    "routine monitoring events. It is not a substitute "
    "for official water-quality testing or public-health "
    "guidance."
)


st.markdown(
    """
Before entering the water:

1. Check the latest official county advisories and reports.
2. Follow posted warning signs and closure notices.
3. Remember that a low-risk prediction does not guarantee
   that bacteria levels are safe.
"""
)


st.link_button(
    ADVISORY_BUTTON_LABEL,
    ADVISORY_URL,
    width="stretch",
)


# ==========================================================
# FOOTER
# ==========================================================

render_footer()
