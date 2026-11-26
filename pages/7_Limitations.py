import streamlit as st

from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_BUTTON_LABEL,
    ADVISORY_URL,
    render_footer,
)


apply_styles()


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "Limitations"
)

st.caption(
    "Technical limitations of LagoonCast's models, "
    "data, and forecasting approach."
)


# ==========================================================
# THREE MAIN LIMITATIONS
# ==========================================================

card1, card2, card3 = st.columns(
    3
)


with card1:

    st.html(
        """
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-top:4px solid #B26A00;
    border-radius:14px;
    padding:1rem;
    min-height:150px;
">

    <div style="
        color:#172033;
        font-size:0.95rem;
        font-weight:800;
    ">
        Not an official advisory
    </div>

    <div style="
        color:#667085;
        font-size:0.78rem;
        line-height:1.5;
        margin-top:0.45rem;
    ">
        LagoonCast provides model-based water-quality
        estimates, not official laboratory results,
        beach advisories, or closures.
    </div>

</div>
"""
    )


with card2:

    st.html(
        """
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-top:4px solid #0F6B78;
    border-radius:14px;
    padding:1rem;
    min-height:150px;
">

    <div style="
        color:#172033;
        font-size:0.95rem;
        font-weight:800;
    ">
        One pilot site
    </div>

    <div style="
        color:#667085;
        font-size:0.78rem;
        line-height:1.5;
        margin-top:0.45rem;
    ">
        The current model was developed for Parkside
        Aquatic Park and should not automatically be
        assumed to perform the same way elsewhere.
    </div>

</div>
"""
    )


with card3:

    st.html(
        """
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-top:4px solid #667085;
    border-radius:14px;
    padding:1rem;
    min-height:150px;
">

    <div style="
        color:#172033;
        font-size:0.95rem;
        font-weight:800;
    ">
        Not a real-time sensor
    </div>

    <div style="
        color:#667085;
        font-size:0.78rem;
        line-height:1.5;
        margin-top:0.45rem;
    ">
        LagoonCast estimates risk from environmental
        information. It does not continuously measure
        bacteria in the water.
    </div>

</div>
"""
    )


# ==========================================================
# TECHNICAL DETAILS
# ==========================================================

st.subheader(
    "More detail"
)


with st.expander(
    "Model limitations"
):

    st.write(
        "LagoonCast learns statistical relationships "
        "between environmental conditions and historical "
        "bacterial observations. These relationships may "
        "change over time, especially under conditions "
        "that differ from those in the training data."
    )

    st.write(
        "E. coli and Enterococcus are modeled separately "
        "and have different predictive performance. "
        "A model's performance during historical evaluation "
        "does not guarantee the same accuracy for future predictions."
    )


with st.expander(
    "Data and sampling limitations"
):

    st.write(
        "Laboratory bacteria measurements are generally "
        "collected weekly rather than continuously. "
        "Short-term contamination events may therefore "
        "occur between sampling dates without being "
        "captured in the historical record."
    )

    st.write(
        "Missing observations and unequal numbers of "
        "elevated-risk events can affect model training "
        "and evaluation. Enterococcus has fewer "
        "elevated-risk examples in the available data, "
        "making its prediction task particularly challenging."
    )

    st.write(
        "Some model features rely on the latest available "
        "historical laboratory information rather than "
        "same-day measurements."
    )


with st.expander(
    "Weather and forecast uncertainty"
):

    st.write(
        "LagoonCast uses environmental conditions, "
        "including rainfall and temperature, to estimate "
        "bacterial risk. Future predictions also depend "
        "on weather forecasts, which can change."
    )

    st.write(
        "Forecast uncertainty generally increases "
        "farther into the future. Unexpected runoff "
        "or environmental changes may not be fully "
        "represented by the available inputs."
    )


with st.expander(
    "Prediction errors and model improvements"
):

    st.write(
        "LagoonCast can make incorrect predictions. "
        "A false negative occurs when bacterial "
        "concentrations exceed the model-defined threshold "
        "but LagoonCast fails to identify the elevated risk."
    )

    st.write(
        "These errors are particularly important "
        "because a lower-risk prediction does not "
        "guarantee that actual bacterial levels are low. "
        "The model cannot identify every contamination event."
    )

    st.write(
        "False positives can also occur, when LagoonCast "
        "predicts elevated risk but laboratory results "
        "do not exceed the model-defined threshold. "
        "These predictions may lead to unnecessary caution."
    )

    st.write(
        "Predictions can be compared with subsequent "
        "laboratory measurements to assess performance. "
        "Repeated misclassifications, especially false "
        "negatives, would warrant reviewing the model's "
        "input data, decision thresholds, and performance "
        "before considering updates or retraining."
    )

    st.write(
        "Any model changes would need to be evaluated "
        "using appropriate historical testing before "
        "being adopted. Until then, official laboratory "
        "results and public-health advisories should "
        "always take priority over LagoonCast estimates."
    )


with st.expander(
    "Possible future improvements"
):

    st.write(
        "Future development could investigate additional "
        "environmental predictors, more frequent "
        "monitoring data, and updated model training "
        "as new laboratory observations become available."
    )

    st.write(
        "Additional testing across different seasons "
        "and monitoring locations would also help "
        "assess how reliably LagoonCast performs "
        "outside its original development setting."
    )


# ==========================================================
# FINAL NOTE
# ==========================================================

st.caption(
    "LagoonCast is intended to provide additional "
    "water-quality information, not to determine whether "
    "swimming is safe. Even a Safe prediction cannot "
    "guarantee safe conditions. Always double-check "
    "official advisories before entering the water."
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
