
import streamlit as st

from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_BUTTON_LABEL,
    ADVISORY_URL,
    GITHUB_URL,
    OFFICIAL_URL,
    PREDICTION_EXPLANATION,
    REPORTS_BUTTON_LABEL,
    SAFE_EXPLANATION,
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
    "does, how it works, and why it was created."
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
    "Bacterial concentrations can change between routine "
    "sampling events, particularly following rainfall "
    "and runoff."
)


st.write(
    "LagoonCast explores whether environmental information, "
    "such as recent rainfall and temperature, can provide "
    "an additional early indication of elevated bacterial "
    "risk between laboratory measurements."
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
        information, including rainfall and temperature,
        as inputs for its predictions.
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
        2 · MACHINE LEARNING
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
        Models developed using historical bacterial
        observations estimate the probability of
        elevated E. coli and Enterococcus concentrations.
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
        LagoonCast translates the predictions into
        Safe, Caution, and Unsafe categories.
        The more severe bacteria-specific category
        determines the overall result.
    </p>

</div>
"""
    )


st.caption(
    PREDICTION_EXPLANATION
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
        "The model-estimated probability that bacterial "
        "concentrations exceed a concentration threshold "
        "defined in LagoonCast."
    )

    st.write(
        "This is not a measured bacteria concentration "
        "or the probability that swimming is safe."
    )


with st.expander(
    "Safe, Caution, and Unsafe"
):

    st.write(
        "These are LagoonCast's model-generated risk "
        "categories, not official government advisories "
        "or closure classifications."
    )

    st.markdown(
        """
- **Safe:** Lower predicted bacterial risk.
- **Caution:** Possible elevated bacterial risk.
- **Unsafe:** Elevated predicted bacterial risk.
"""
    )

    st.write(
        "LagoonCast classifies E. coli and Enterococcus "
        "separately. The overall category follows whichever "
        "bacterium has the more severe classification."
    )

    st.write(
        "Because the two models use different probability "
        "boundaries, the higher percentage does not "
        "necessarily determine the overall risk."
    )


with st.expander(
    "Chronological validation"
):

    st.write(
        "The model was trained on earlier observations "
        "and evaluated on later observations. This better "
        "reflects the real forecasting task than randomly "
        "mixing older and newer dates."
    )

    st.write(
        "Historical evaluation results help assess model "
        "performance but do not guarantee the accuracy "
        "of future predictions."
    )


# ==========================================================
# PILOT SCOPE
# ==========================================================

st.subheader(
    "Current pilot"
)


st.write(
    f"LagoonCast is currently demonstrated at {SITE_NAME}. "
    "The project is intended as an experimental research "
    "prototype and a framework that could be evaluated "
    "at additional recreational-water sites in the future."
)


st.write(
    "The current models were developed for this pilot "
    "location and should not automatically be assumed "
    "to perform equally well at other sites."
)


# ==========================================================
# IMPORTANT SAFETY NOTE
# ==========================================================

st.caption(
    SAFE_EXPLANATION
)


st.caption(
    "LagoonCast does not conduct laboratory testing "
    "or issue official advisories. For guidance before "
    "entering the water, see Safety & Data Notes "
    "and the latest county advisories."
)


# ==========================================================
# PROJECT AND OFFICIAL LINKS
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
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
        width="stretch",
    )


st.markdown(
    f"[{REPORTS_BUTTON_LABEL}]({OFFICIAL_URL})"
    " — Water-quality reports, separate from current "
    "county advisories."
)


# ==========================================================
# FOOTER
# ==========================================================

render_footer()
