import pandas as pd
import streamlit as st

from utils.live_forecast import load_live_latest
from utils.styles import apply_styles, load_latest
from utils.ui import (
    OFFICIAL_URL,
    SITE_NAME,
    freshness_chip,
    probability_meter,
    render_footer,
    risk_class,
    risk_icon,
)


st.set_page_config(
    page_title="LagoonCast | Model & Data",
    page_icon="assets/LagoonCast_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


try:
    latest = load_live_latest()

except Exception:

    try:
        latest = load_latest()

    except Exception:

        st.error(
            "Prediction data is currently unavailable."
        )

        st.stop()


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


st.html(
    f"""
<div class="bg-reading">

    <div class="bg-page-heading">

        <h1>
            Risk Details
        </h1>

        <p>
            See the two bacteria-specific predictions
            that determine the overall LagoonCast forecast
            for {SITE_NAME}.
        </p>

        <div class="bg-page-meta">
            Forecast for {prediction_text}
            &nbsp;·&nbsp;
            {freshness_chip(updated_date)}
        </div>

    </div>


    <div class="bg-how-read">

        <strong>
            How to read this page
        </strong>

        <p>
            Each card shows the model-estimated probability
            that one bacterial indicator exceeds its
            elevated-risk concentration threshold.
            The overall LagoonCast status uses the more
            serious of the two individual risk levels.
        </p>

    </div>

</div>
"""
)


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


tech_left, tech_right = st.columns(
    2
)


with tech_left:

    with st.expander(
        "E. coli technical details"
    ):

        st.markdown(
            """
**Concentration threshold:** 235 MPN/100 mL

**Display thresholds**

- Safe: <10%
- Caution: 10% to <50%
- Unsafe: ≥50%

E. coli is a fecal-indicator bacterium.
Elevated levels can indicate increased
contamination risk in recreational water.
"""
        )


with tech_right:

    with st.expander(
        "Enterococcus technical details"
    ):

        st.markdown(
            """
**Concentration threshold:** 130 MPN/100 mL

**Display thresholds**

- Safe: <40%
- Caution: 40% to <85%
- Unsafe: ≥85%

Enterococcus is commonly used as a
fecal-indicator bacterium in marine and
estuarine recreational waters.
"""
        )


st.html(
    """
<div class="bg-reading">

    <div class="bg-small-explainer">

        <strong>
            Why are the probability thresholds different?
        </strong>

        <p>
            E. coli and Enterococcus use different
            model probability boundaries because the two
            models have different performance characteristics.
            These probability boundaries are model-display
            thresholds and are separate from the underlying
            bacterial concentration standards.
        </p>

    </div>

</div>
"""
)


st.link_button(
    "Check Official Water-Quality Advisories",
    OFFICIAL_URL,
)


render_footer(
    model_ver
)
