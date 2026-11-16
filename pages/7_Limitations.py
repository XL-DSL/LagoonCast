
import streamlit as st

from utils.styles import apply_styles
from utils.ui import render_footer


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
        Experimental, not official
    </div>

    <div style="
        color:#667085;
        font-size:0.78rem;
        line-height:1.5;
        margin-top:0.45rem;
    ">
        LagoonCast is a research prototype and does
        not issue government advisories or closures.
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
    "Potential false negatives"
):

    st.write(
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
    "For practical water-safety guidance, official "
    "advisories, and explanations of how to interpret "
    "Safe, Caution, and Unsafe, see Safety & Data Notes."
)


# ==========================================================
# FOOTER
# ==========================================================

render_footer()
