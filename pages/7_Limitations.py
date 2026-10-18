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
    "Limitations"
)

st.caption(
    "Important boundaries on how AquaCast should be interpreted."
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
        AquaCast is a research prototype and does
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
        AquaCast estimates risk from environmental
        information. It does not continuously measure
        bacteria in the water.
    </div>

</div>
"""
    )


# ==========================================================
# DETAILS
# ==========================================================

st.subheader(
    "More detail"
)


with st.expander(
    "Model limitations"
):

    st.write(
        "AquaCast learns statistical relationships from historical "
        "observations. Those relationships may change over time, "
        "and conditions outside the historical range may produce "
        "less reliable predictions."
    )

    st.write(
        "E. coli and Enterococcus are modeled separately and "
        "their predictive performance is not identical."
    )


with st.expander(
    "Data limitations"
):

    st.write(
        "The amount and timing of available laboratory sampling "
        "limit what the model can learn. Missing observations and "
        "unequal numbers of elevated-risk events can also affect "
        "performance."
    )

    st.write(
        "Enterococcus has fewer elevated-risk examples in the "
        "available data, which makes that prediction task "
        "particularly difficult."
    )


with st.expander(
    "Weather uncertainty"
):

    st.write(
        "Future AquaCast predictions depend partly on forecast "
        "environmental conditions. Rainfall and temperature "
        "forecasts can change, so AquaCast uncertainty generally "
        "increases farther into the future."
    )


with st.expander(
    "Laboratory-data limitations"
):

    st.write(
        "The live system does not receive a new bacteria sample "
        "every day. Some model features therefore rely on the "
        "latest available historical laboratory information "
        "rather than a same-day measurement."
    )


with st.expander(
    "Potential false negatives"
):

    st.write(
        "No prediction model identifies every elevated-risk event. "
        "A false negative occurs when actual bacterial risk is "
        "elevated but the model does not identify it as such. "
        "This is one reason official laboratory testing and "
        "public-health guidance remain essential."
    )


# ==========================================================
# SAFETY
# ==========================================================

st.html(
    """
<div style="
    background:#FFF8CC;
    color:#5C4A00;
    border:1px solid #F1E59A;
    border-radius:12px;
    padding:1rem 1.1rem;
    margin-top:1.3rem;
    margin-bottom:1rem;
    line-height:1.5;
">

    <strong>
        Official information takes priority.
    </strong>

    LagoonCast should never replace beach signage,
    laboratory results, public-health advisories,
    or official closures.

</div>
"""
)


st.link_button(
    "View Official San Mateo County Beach Status",
    OFFICIAL_URL,
    width="stretch",
)


render_footer()
