import streamlit as st

from utils.styles import apply_styles
from utils.ui import (
    GITHUB_URL,
    OFFICIAL_URL,
    SITE_NAME,
    render_footer,
)


apply_styles()


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "About LagoonCast"
)

st.caption(
    "A plain-language overview of what LagoonCast "
    "does and why it was created."
)


# ==========================================================
# WHY THIS MATTERS
# ==========================================================

st.subheader(
    "Why this matters"
)


st.write(
    "Recreational-water bacteria measurements depend on "
    "laboratory sampling, so information about changing "
    "conditions may not always be available immediately. "
    "LagoonCast explores whether environmental information "
    "such as recent rainfall and temperature can provide "
    "an additional early indication of elevated bacterial risk."
)


# ==========================================================
# WORKFLOW
# ==========================================================

st.subheader(
    "How LagoonCast works"
)


step1, step2, step3 = st.columns(
    3
)


with step1:

    st.html(
        """
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-radius:14px;
    padding:1.1rem;
    min-height:175px;
">

    <div style="
        color:#0F6B78;
        font-weight:800;
        font-size:0.75rem;
    ">
        1 · ENVIRONMENTAL DATA
    </div>

    <h3 style="
        color:#172033;
        margin-top:0.5rem;
    ">
        Observe conditions
    </h3>

    <p style="
        color:#667085;
        font-size:0.82rem;
        line-height:1.5;
    ">
        LagoonCast uses recent and forecast environmental
        information such as rainfall and temperature.
    </p>

</div>
"""
    )


with step2:

    st.html(
        """
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-radius:14px;
    padding:1.1rem;
    min-height:175px;
">

    <div style="
        color:#0F6B78;
        font-weight:800;
        font-size:0.75rem;
    ">
        2 · LagoonCast MODEL
    </div>

    <h3 style="
        color:#172033;
        margin-top:0.5rem;
    ">
        Estimate probability
    </h3>

    <p style="
        color:#667085;
        font-size:0.82rem;
        line-height:1.5;
    ">
        Separate machine-learning models estimate
        the probability of elevated E. coli and
        Enterococcus concentrations.
    </p>

</div>
"""
    )


with step3:

    st.html(
        """
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-radius:14px;
    padding:1.1rem;
    min-height:175px;
">

    <div style="
        color:#0F6B78;
        font-weight:800;
        font-size:0.75rem;
    ">
        3 · RISK FORECAST
    </div>

    <h3 style="
        color:#172033;
        margin-top:0.5rem;
    ">
        Communicate risk
    </h3>

    <p style="
        color:#667085;
        font-size:0.82rem;
        line-height:1.5;
    ">
        LagoonCast translates the probabilities
        into Safe, Caution, and Unsafe model
        classifications for easier interpretation.
    </p>

</div>
"""
    )


# ==========================================================
# TERMS
# ==========================================================

st.subheader(
    "Quick definitions"
)


with st.expander(
    "Fecal indicator bacteria"
):

    st.write(
        "Bacteria such as E. coli and Enterococcus are used "
        "as indicators of possible fecal contamination. "
        "They are monitored because elevated concentrations "
        "can indicate increased health risk in recreational water."
    )


with st.expander(
    "Exceedance probability"
):

    st.write(
        "The probability that the model assigns to bacterial "
        "concentrations exceeding the concentration threshold "
        "used by LagoonCast. A probability is not the same thing "
        "as a measured bacteria concentration."
    )


with st.expander(
    "Chronological validation"
):

    st.write(
        "The model was trained on earlier observations and "
        "evaluated on later observations. This better reflects "
        "the real forecasting task than randomly mixing older "
        "and newer dates."
    )


# ==========================================================
# PILOT SCOPE
# ==========================================================

st.subheader(
    "Current pilot"
)


st.write(
    f"LagoonCast is currently demonstrated at {SITE_NAME}. "
    "The project is intended as a research prototype and "
    "a framework that could be evaluated at additional "
    "recreational-water sites in the future."
)


# ==========================================================
# LINKS
# ==========================================================

col1, col2 = st.columns(
    2
)


with col1:

    st.link_button(
        "View Project on GitHub",
        GITHUB_URL,
        width="stretch",
    )


with col2:

    st.link_button(
        "Official San Mateo County Beach Status",
        OFFICIAL_URL,
        width="stretch",
    )


render_footer()
