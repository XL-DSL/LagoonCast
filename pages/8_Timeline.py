
import pandas as pd
import streamlit as st

from utils.live_forecast import load_live_outlook, load_recent_estimates
from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_BUTTON_LABEL,
    ADVISORY_URL,
    OFFICIAL_PRIORITY_NOTICE,
    OFFICIAL_URL,
    REPORTS_BUTTON_LABEL,
    SAFE_EXPLANATION,
    SITE_NAME,
    render_footer,
    risk_class,
    risk_driver_text,
    risk_icon,
)

apply_styles()


# ==========================================================
# ORIGINAL TIMELINE STYLING — VALUES UNCHANGED
# ==========================================================

st.html("""
<style>
.timeline-page-intro {color: #667085; font-size: 0.95rem; line-height: 1.55; margin-bottom: 1.5rem;}
.timeline-section-header {display: flex; align-items: baseline; gap: 0.7rem; margin-top: 1.5rem; margin-bottom: 0.8rem;}
.timeline-section-header h2 {margin: 0 !important; color: #172033; font-size: 1.15rem; font-weight: 800;}
.timeline-section-header span {color: #98A2B3; font-size: 0.75rem;}
.timeline-tile {min-height: 145px; display: flex; flex-direction: column; gap: 0.35rem;}
.timeline-tile-day {color: #172033; font-size: 0.85rem; font-weight: 800;}
.timeline-tile-date {color: #98A2B3; font-size: 0.68rem; margin-top: -0.2rem;}
.timeline-tile-badge {display: inline-flex; width: fit-content; align-items: center; padding: 0.2rem 0.45rem; border-radius: 999px; color: #FFFFFF; font-size: 0.63rem; font-weight: 800; margin: 0.25rem 0;}
.timeline-tile-badge.safe {background: #2E7D32;}
.timeline-tile-badge.caution {background: #B26A00;}
.timeline-tile-badge.unsafe {background: #C62828;}
.timeline-tile-values {display: grid; gap: 0.2rem; margin-top: 0.15rem; color: #667085; font-size: 0.7rem;}
.timeline-tile-values strong {color: #172033; font-weight: 800;}
.timeline-horizon {color: #98A2B3; font-size: 0.62rem; margin-top: 0.15rem;}
.timeline-today {display: grid; grid-template-columns: minmax(180px, 0.8fr) repeat(2, minmax(150px, 1fr)); gap: 1rem; align-items: center; background: #FFFFFF; border: 2px solid #0F6B78; border-radius: 16px; padding: 1.35rem 1.5rem; margin-bottom: 0.8rem; box-shadow: 0 4px 16px rgba(15, 107, 120, 0.10);}
.timeline-today-label {color: #0F6B78; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em;}
.timeline-today-date {margin-top: 0.25rem; color: #172033; font-size: 1.15rem; font-weight: 800;}
.timeline-today-risk {margin-top: 0.45rem; font-size: 1.55rem; font-weight: 800;}
.timeline-today-risk.safe {color: #2E7D32;}
.timeline-today-risk.caution {color: #B26A00;}
.timeline-today-risk.unsafe {color: #C62828;}
.timeline-today-bacteria {background: #F8FAFC; border-radius: 12px; padding: 0.85rem 1rem;}
.timeline-today-bacteria-name {color: #667085; font-size: 0.75rem; font-weight: 600;}
.timeline-today-bacteria-value {margin-top: 0.2rem; color: #172033; font-size: 1.55rem; font-weight: 800;}
.timeline-today-bacteria-risk {margin-top: 0.1rem; font-size: 0.7rem; font-weight: 700;}
.timeline-today-bacteria-risk.safe {color: #2E7D32;}
.timeline-today-bacteria-risk.caution {color: #B26A00;}
.timeline-today-bacteria-risk.unsafe {color: #C62828;}
.popup-summary {background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: 1rem;}
.popup-period {color: #98A2B3; font-size: 0.68rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em;}
.popup-date {color: #172033; font-size: 1.15rem; font-weight: 800; margin-top: 0.2rem;}
.popup-overall {margin-top: 0.55rem; font-size: 1.35rem; font-weight: 800;}
.popup-overall.safe {color: #2E7D32;}
.popup-overall.caution {color: #B26A00;}
.popup-overall.unsafe {color: #C62828;}
.popup-driver {margin-top: 0.75rem; background: #F8FAFC; color: #475467; border-radius: 10px; padding: 0.7rem 0.8rem; font-size: 0.8rem; line-height: 1.45;}
.popup-bacteria-grid {display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; margin-bottom: 1rem;}
.popup-bacteria-card {background: #F8FAFC; border: 1px solid #EAECF0; border-radius: 12px; padding: 0.9rem 1rem;}
.popup-bacteria-name {color: #667085; font-size: 0.75rem; font-weight: 650;}
.popup-bacteria-value {color: #172033; font-size: 1.7rem; font-weight: 800; margin-top: 0.2rem;}
.popup-bacteria-risk {font-size: 0.72rem; font-weight: 750; margin-top: 0.1rem;}
.popup-bacteria-risk.safe {color: #2E7D32;}
.popup-bacteria-risk.caution {color: #B26A00;}
.popup-bacteria-risk.unsafe {color: #C62828;}
div[data-testid="stButton"] > button {width: 100% !important; min-height: 34px !important; background: #FFFFFF !important; color: #344054 !important; border: 1px solid #D0D5DD !important; border-radius: 8px !important; font-size: 0.7rem !important; font-weight: 700 !important; padding: 0.3rem 0.5rem !important; box-shadow: none !important;}
div[data-testid="stButton"] > button *, div[data-testid="stButton"] > button p, div[data-testid="stButton"] > button span {color: #344054 !important; opacity: 1 !important;}
div[data-testid="stButton"] > button:hover {background: #F0F7F8 !important; color: #0F6B78 !important; border-color: #0F6B78 !important;}
div[data-testid="stButton"] > button:hover *, div[data-testid="stButton"] > button:hover p, div[data-testid="stButton"] > button:hover span {color: #0F6B78 !important;}
.timeline-future-note {background: #FFF8CC; color: #5C4A00; border: 1px solid #F1E59A; border-radius: 12px; padding: 0.8rem 1rem; margin-top: 0.8rem; margin-bottom: 1rem; font-size: 0.8rem; line-height: 1.5;}
@media (max-width: 720px) {
    .timeline-today {grid-template-columns: 1fr; padding: 1.1rem;}
    .timeline-tile {min-height: auto;}
    .popup-bacteria-grid {grid-template-columns: 1fr;}
}
</style>
""")


# ==========================================================
# HELPERS
# ==========================================================

def risk_badge_html(risk):
    css = risk_class(risk)
    return (
        f'<span class="timeline-tile-badge {css}">'
        f'{risk_icon(risk)} {risk}'
        '</span>'
    )


# ==========================================================
# DAY DETAILS POPUP
# ==========================================================

@st.dialog("LagoonCast Day Details", width="large")
def show_day_details(row_dict, period, today):

    row = pd.Series(row_dict)

    selected_date = pd.to_datetime(
        row["prediction_date"]
    )

    overall = str(row["overall_risk"]).strip()
    ecoli_risk = str(row["e_coli_risk"]).strip()
    entero_risk = str(row["enterococcus_risk"]).strip()

    ecoli_probability = float(
        row["e_coli_probability"]
    )

    entero_probability = float(
        row["enterococcus_probability"]
    )

    if period == "past":
        period_text = "Reconstructed Recent Estimate"

    elif period == "today":
        period_text = "Current Forecast"

    else:
        horizon = (
            selected_date.normalize()
            - pd.Timestamp(today).normalize()
        ).days

        period_text = (
            f"Future Forecast · {horizon} day"
            f"{'s' if horizon != 1 else ''} ahead"
        )

    st.html(
        f"""
<div class="popup-summary">

    <div class="popup-period">
        {period_text}
    </div>

    <div class="popup-date">
        {selected_date.strftime('%A, %B %d, %Y')}
    </div>

    <div class="popup-overall {risk_class(overall)}">
        {risk_icon(overall)} {overall}
    </div>

    <div class="popup-driver">
        {risk_driver_text(ecoli_risk, entero_risk)}
    </div>

</div>

<div class="popup-bacteria-grid">

    <div class="popup-bacteria-card">

        <div class="popup-bacteria-name">
            E. coli exceedance probability
        </div>

        <div class="popup-bacteria-value">
            {ecoli_probability:.1%}
        </div>

        <div class="popup-bacteria-risk {risk_class(ecoli_risk)}">
            {ecoli_risk}
        </div>

    </div>

    <div class="popup-bacteria-card">

        <div class="popup-bacteria-name">
            Enterococcus exceedance probability
        </div>

        <div class="popup-bacteria-value">
            {entero_probability:.1%}
        </div>

        <div class="popup-bacteria-risk {risk_class(entero_risk)}">
            {entero_risk}
        </div>

    </div>

</div>
"""
    )

    st.caption(
        "Percentages are model-estimated probabilities of exceeding "
        "bacteria-specific thresholds, not the chance that swimming is safe."
    )

    if period == "past":
        st.caption(
            "This is a reconstructed LagoonCast model estimate, not a "
            "laboratory measurement or necessarily a forecast saved on that date."
        )

    elif period == "future":
        horizon = (
            selected_date.normalize()
            - pd.Timestamp(today).normalize()
        ).days

        st.caption(
            f"This forecast is {horizon} day{'s' if horizon != 1 else ''} "
            "ahead. Forecast uncertainty generally increases farther from today."
        )

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
        width="stretch",
    )


# ==========================================================
# HEADER
# ==========================================================

st.title("15-Day LagoonCast Timeline")

st.html(
    f"""
<div class="timeline-page-intro">

    Seven reconstructed recent model estimates,
    today's current forecast, and seven future forecasts
    for <strong>{SITE_NAME}</strong>.

</div>
"""
)

st.caption(
    "All percentages are model-estimated probabilities of exceeding "
    "bacteria-specific concentration thresholds. They are not "
    "direct measurements or the probability that swimming is safe."
)


# ==========================================================
# LOAD DATA
# ==========================================================

try:

    with st.spinner(
        "Building LagoonCast timeline..."
    ):

        recent = load_recent_estimates(
            days=8
        )

        outlook = load_live_outlook(
            days=8
        )

except Exception:

    st.error(
        "The LagoonCast timeline is temporarily unavailable."
    )

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
        width="stretch",
    )

    st.stop()


# ==========================================================
# PREPARE DATA
# ==========================================================

recent = recent.copy()
outlook = outlook.copy()

recent["prediction_date"] = pd.to_datetime(
    recent["prediction_date"],
    errors="coerce",
)

outlook["prediction_date"] = pd.to_datetime(
    outlook["prediction_date"],
    errors="coerce",
)

recent = recent.dropna(
    subset=["prediction_date"]
)

outlook = outlook.dropna(
    subset=["prediction_date"]
)

today = (
    pd.Timestamp.now(
        tz="America/Los_Angeles"
    )
    .tz_localize(None)
    .normalize()
)


# ==========================================================
# PREVIOUS 7 DAYS
# ==========================================================

past = (
    recent[
        recent["prediction_date"].dt.normalize() < today
    ]
    .sort_values("prediction_date")
    .tail(7)
    .copy()
)

past["period"] = "past"


# ==========================================================
# TODAY
# ==========================================================

current = (
    outlook[
        outlook["prediction_date"].dt.normalize() == today
    ]
    .head(1)
    .copy()
)

# Do not silently substitute a reconstructed estimate
# for today's current live forecast.
current["period"] = "today"


# ==========================================================
# NEXT 7 DAYS
# ==========================================================

future = (
    outlook[
        outlook["prediction_date"].dt.normalize() > today
    ]
    .sort_values("prediction_date")
    .head(7)
    .copy()
)

future["period"] = "future"


# ==========================================================
# SHARED DAY TILE
# Existing visual classes and presentation are unchanged.
# ==========================================================

def show_tile(row, period, today):

    date_value = pd.to_datetime(
        row["prediction_date"]
    )

    overall = str(
        row["overall_risk"]
    ).strip()

    ecoli_probability = float(
        row["e_coli_probability"]
    )

    entero_probability = float(
        row["enterococcus_probability"]
    )

    horizon_html = ""

    if period == "future":

        horizon = (
            date_value.normalize() - today
        ).days

        horizon_html = (
            '<div class="timeline-horizon">'
            f"{horizon} day{'s' if horizon != 1 else ''} ahead"
            "</div>"
        )

    with st.container(border=True):

        st.html(
            f"""
<div class="timeline-tile">

    <div class="timeline-tile-day">
        {date_value.strftime('%a')}
    </div>

    <div class="timeline-tile-date">
        {date_value.strftime('%b %d')}
    </div>

    {risk_badge_html(overall)}

    <div class="timeline-tile-values">

        <div>
            E. coli
            <strong>{ecoli_probability:.0%}</strong>
        </div>

        <div>
            Enterococcus
            <strong>{entero_probability:.0%}</strong>
        </div>

    </div>

    {horizon_html}

</div>
"""
        )

        if st.button(
            "View",
            key=(
                f"{period}_"
                f"{date_value.strftime('%Y%m%d')}"
            ),
        ):

            show_day_details(
                row.to_dict(),
                period,
                today,
            )


# ==========================================================
# DISPLAY PREVIOUS 7 DAYS
# ==========================================================

st.html(
    """
<div class="timeline-section-header">

    <h2>Previous 7 Days</h2>

    <span>
        Reconstructed model estimates
    </span>

</div>
"""
)

past_columns = st.columns(
    max(len(past), 1)
)

for column, (_, row) in zip(
    past_columns,
    past.iterrows(),
):

    with column:
        show_tile(
            row,
            "past",
            today,
        )


# ==========================================================
# DISPLAY TODAY
# ==========================================================

st.html(
    """
<div class="timeline-section-header">

    <h2>Today</h2>

    <span>
        Current LagoonCast forecast
    </span>

</div>
"""
)

if not current.empty:

    today_row = current.iloc[0]

    current_overall = str(
        today_row["overall_risk"]
    ).strip()

    current_ecoli_risk = str(
        today_row["e_coli_risk"]
    ).strip()

    current_entero_risk = str(
        today_row["enterococcus_risk"]
    ).strip()

    current_ecoli = float(
        today_row["e_coli_probability"]
    )

    current_entero = float(
        today_row["enterococcus_probability"]
    )

    current_class = risk_class(
        current_overall
    )

    st.html(
        f"""
<div class="timeline-today">

    <div>

        <div class="timeline-today-label">
            Current Forecast
        </div>

        <div class="timeline-today-date">
            {today.strftime('%A, %b %d')}
        </div>

        <div class="timeline-today-risk {current_class}">
            {risk_icon(current_overall)}
            {current_overall}
        </div>

    </div>


    <div class="timeline-today-bacteria">

        <div class="timeline-today-bacteria-name">
            E. coli
        </div>

        <div class="timeline-today-bacteria-value">
            {current_ecoli:.0%}
        </div>

        <div class="timeline-today-bacteria-risk {risk_class(current_ecoli_risk)}">
            {current_ecoli_risk}
        </div>

    </div>


    <div class="timeline-today-bacteria">

        <div class="timeline-today-bacteria-name">
            Enterococcus
        </div>

        <div class="timeline-today-bacteria-value">
            {current_entero:.0%}
        </div>

        <div class="timeline-today-bacteria-risk {risk_class(current_entero_risk)}">
            {current_entero_risk}
        </div>

    </div>

</div>
"""
    )

    st.caption(
        risk_driver_text(
            current_ecoli_risk,
            current_entero_risk,
        )
    )

    if st.button(
        "View today's full details",
        key="today_details",
    ):

        show_day_details(
            today_row.to_dict(),
            "today",
            today,
        )

else:

    st.warning(
        "Today's live model forecast is unavailable. "
        "A reconstructed estimate is not being presented as current."
    )


# ==========================================================
# DISPLAY NEXT 7 DAYS
# ==========================================================

st.html(
    """
<div class="timeline-section-header">

    <h2>Next 7 Days</h2>

    <span>
        Forecast uncertainty increases with horizon
    </span>

</div>
"""
)

future_columns = st.columns(
    max(len(future), 1)
)

for column, (_, row) in zip(
    future_columns,
    future.iterrows(),
):

    with column:
        show_tile(
            row,
            "future",
            today,
        )


# ==========================================================
# FUTURE UNCERTAINTY
# ==========================================================

st.html(
    """
<div class="timeline-future-note">

    <strong>
        Future forecast:
    </strong>

    uncertainty increases farther from today because
    future rainfall, temperature, and other environmental
    conditions are themselves forecasted.

</div>
"""
)


# ==========================================================
# ALL DAILY VALUES
# ==========================================================

timeline = pd.concat(
    [
        past,
        current,
        future,
    ],
    ignore_index=True,
    sort=False,
)

with st.expander(
    "View all 15 daily values"
):

    display = timeline[
        [
            "prediction_date",
            "period",
            "e_coli_probability",
            "e_coli_risk",
            "enterococcus_probability",
            "enterococcus_risk",
            "overall_risk",
        ]
    ].copy()

    display["prediction_date"] = (
        pd.to_datetime(
            display["prediction_date"]
        )
        .dt.strftime("%a, %b %d")
    )

    display["period"] = (
        display["period"]
        .replace(
            {
                "past": "Reconstructed estimate",
                "today": "Today",
                "future": "Future forecast",
            }
        )
    )

    display["e_coli_probability"] = (
        display["e_coli_probability"]
        .map(
            lambda value: f"{float(value):.1%}"
        )
    )

    display["enterococcus_probability"] = (
        display["enterococcus_probability"]
        .map(
            lambda value: f"{float(value):.1%}"
        )
    )

    display.columns = [
        "Date",
        "Period",
        "E. coli Probability",
        "E. coli Risk",
        "Enterococcus Probability",
        "Enterococcus Risk",
        "Overall Risk",
    ]

    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
    )


# ==========================================================
# SAFETY AND OFFICIAL RESOURCES
# ==========================================================

st.caption(
    "Past values are reconstructed model estimates, not laboratory "
    "measurements or official historical advisories. Future forecasts "
    "depend partly on uncertain forecast weather inputs."
)

st.caption(
    SAFE_EXPLANATION
)

st.caption(
    OFFICIAL_PRIORITY_NOTICE
)

link_left, link_right = st.columns(2)

with link_left:

    st.link_button(
        ADVISORY_BUTTON_LABEL,
        ADVISORY_URL,
        width="stretch",
    )

with link_right:

    st.link_button(
        REPORTS_BUTTON_LABEL,
        OFFICIAL_URL,
        width="stretch",
    )


# ==========================================================
# FOOTER
# ==========================================================

model_version = None

if (
    not current.empty
    and "model_version" in current.columns
):

    model_version = str(
        current.iloc[0]["model_version"]
    )

render_footer(
    model_version
)
