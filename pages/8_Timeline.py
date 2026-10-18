import pandas as pd
import streamlit as st

from utils.live_forecast import (
    load_live_outlook,
    load_recent_estimates,
)
from utils.styles import apply_styles
from utils.ui import (
    OFFICIAL_URL,
    SITE_NAME,
    render_footer,
    risk_class,
    risk_icon,
)


apply_styles()


# ==========================================================
# PAGE-SPECIFIC STYLING
# ==========================================================

st.html(
    """
<style>

/* ==========================================================
   TIMELINE PAGE
   ========================================================== */

.timeline-page-intro {
    color: #667085;
    font-size: 0.95rem;
    line-height: 1.55;
    margin-bottom: 1.5rem;
}


/* ----------------------------------------------------------
   SECTION HEADERS
   ---------------------------------------------------------- */

.timeline-section-header {
    display: flex;
    align-items: baseline;
    gap: 0.7rem;

    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
}

.timeline-section-header h2 {
    margin: 0 !important;
    color: #172033;
    font-size: 1.15rem;
    font-weight: 800;
}

.timeline-section-header span {
    color: #98A2B3;
    font-size: 0.75rem;
}


/* ----------------------------------------------------------
   DAY TILE
   ---------------------------------------------------------- */

.timeline-tile {
    min-height: 145px;

    display: flex;
    flex-direction: column;

    gap: 0.35rem;
}

.timeline-tile-day {
    color: #172033;

    font-size: 0.85rem;
    font-weight: 800;
}

.timeline-tile-date {
    color: #98A2B3;

    font-size: 0.68rem;

    margin-top: -0.2rem;
}

.timeline-tile-badge {
    display: inline-flex;

    width: fit-content;

    align-items: center;

    padding: 0.2rem 0.45rem;

    border-radius: 999px;

    color: #FFFFFF;

    font-size: 0.63rem;
    font-weight: 800;

    margin: 0.25rem 0;
}

.timeline-tile-badge.safe {
    background: #2E7D32;
}

.timeline-tile-badge.caution {
    background: #B26A00;
}

.timeline-tile-badge.unsafe {
    background: #C62828;
}

.timeline-tile-values {
    display: grid;

    gap: 0.2rem;

    margin-top: 0.15rem;

    color: #667085;

    font-size: 0.7rem;
}

.timeline-tile-values strong {
    color: #172033;

    font-weight: 800;
}

.timeline-horizon {
    color: #98A2B3;

    font-size: 0.62rem;

    margin-top: 0.15rem;
}


/* ----------------------------------------------------------
   TODAY
   ---------------------------------------------------------- */

.timeline-today {
    display: grid;

    grid-template-columns:
        minmax(180px, 0.8fr)
        repeat(2, minmax(150px, 1fr));

    gap: 1rem;

    align-items: center;

    background: #FFFFFF;

    border: 2px solid #0F6B78;

    border-radius: 16px;

    padding: 1.35rem 1.5rem;

    margin-bottom: 0.8rem;

    box-shadow:
        0 4px 16px rgba(15, 107, 120, 0.10);
}

.timeline-today-label {
    color: #0F6B78;

    font-size: 0.7rem;
    font-weight: 800;

    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.timeline-today-date {
    margin-top: 0.25rem;

    color: #172033;

    font-size: 1.15rem;
    font-weight: 800;
}

.timeline-today-risk {
    margin-top: 0.45rem;

    font-size: 1.55rem;
    font-weight: 800;
}

.timeline-today-risk.safe {
    color: #2E7D32;
}

.timeline-today-risk.caution {
    color: #B26A00;
}

.timeline-today-risk.unsafe {
    color: #C62828;
}

.timeline-today-bacteria {
    background: #F8FAFC;

    border-radius: 12px;

    padding: 0.85rem 1rem;
}

.timeline-today-bacteria-name {
    color: #667085;

    font-size: 0.75rem;
    font-weight: 600;
}

.timeline-today-bacteria-value {
    margin-top: 0.2rem;

    color: #172033;

    font-size: 1.55rem;
    font-weight: 800;
}

.timeline-today-bacteria-risk {
    margin-top: 0.1rem;

    font-size: 0.7rem;
    font-weight: 700;
}

.timeline-today-bacteria-risk.safe {
    color: #2E7D32;
}

.timeline-today-bacteria-risk.caution {
    color: #B26A00;
}

.timeline-today-bacteria-risk.unsafe {
    color: #C62828;
}


/* ----------------------------------------------------------
   POPUP DETAILS
   ---------------------------------------------------------- */

.popup-summary {
    background: #FFFFFF;

    border: 1px solid #E4E7EC;

    border-radius: 14px;

    padding: 1rem 1.1rem;

    margin-bottom: 1rem;
}

.popup-period {
    color: #98A2B3;

    font-size: 0.68rem;
    font-weight: 750;

    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.popup-date {
    color: #172033;

    font-size: 1.15rem;
    font-weight: 800;

    margin-top: 0.2rem;
}

.popup-overall {
    margin-top: 0.55rem;

    font-size: 1.35rem;
    font-weight: 800;
}

.popup-overall.safe {
    color: #2E7D32;
}

.popup-overall.caution {
    color: #B26A00;
}

.popup-overall.unsafe {
    color: #C62828;
}

.popup-driver {
    margin-top: 0.75rem;

    background: #F8FAFC;

    color: #475467;

    border-radius: 10px;

    padding: 0.7rem 0.8rem;

    font-size: 0.8rem;
    line-height: 1.45;
}

.popup-bacteria-grid {
    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 0.8rem;

    margin-bottom: 1rem;
}

.popup-bacteria-card {
    background: #F8FAFC;

    border: 1px solid #EAECF0;

    border-radius: 12px;

    padding: 0.9rem 1rem;
}

.popup-bacteria-name {
    color: #667085;

    font-size: 0.75rem;
    font-weight: 650;
}

.popup-bacteria-value {
    color: #172033;

    font-size: 1.7rem;
    font-weight: 800;

    margin-top: 0.2rem;
}

.popup-bacteria-risk {
    font-size: 0.72rem;
    font-weight: 750;

    margin-top: 0.1rem;
}

.popup-bacteria-risk.safe {
    color: #2E7D32;
}

.popup-bacteria-risk.caution {
    color: #B26A00;
}

.popup-bacteria-risk.unsafe {
    color: #C62828;
}


/* ----------------------------------------------------------
   VIEW BUTTONS
   ---------------------------------------------------------- */

div[data-testid="stButton"] > button {
    width: 100% !important;
    min-height: 34px !important;

    background: #FFFFFF !important;
    color: #344054 !important;

    border: 1px solid #D0D5DD !important;
    border-radius: 8px !important;

    font-size: 0.7rem !important;
    font-weight: 700 !important;

    padding: 0.3rem 0.5rem !important;

    box-shadow: none !important;
}

div[data-testid="stButton"] > button *,
div[data-testid="stButton"] > button p,
div[data-testid="stButton"] > button span {
    color: #344054 !important;
    opacity: 1 !important;
}

div[data-testid="stButton"] > button:hover {
    background: #F0F7F8 !important;
    color: #0F6B78 !important;
    border-color: #0F6B78 !important;
}

div[data-testid="stButton"] > button:hover *,
div[data-testid="stButton"] > button:hover p,
div[data-testid="stButton"] > button:hover span {
    color: #0F6B78 !important;
}


/* ----------------------------------------------------------
   FUTURE WARNING
   ---------------------------------------------------------- */

.timeline-future-note {
    background: #FFF8CC;

    color: #5C4A00;

    border: 1px solid #F1E59A;

    border-radius: 12px;

    padding: 0.8rem 1rem;

    margin-top: 0.8rem;
    margin-bottom: 1rem;

    font-size: 0.8rem;
    line-height: 1.5;
}


/* ----------------------------------------------------------
   MOBILE
   ---------------------------------------------------------- */

@media (max-width: 720px) {

    .timeline-today {
        grid-template-columns: 1fr;

        padding: 1.1rem;
    }

    .timeline-tile {
        min-height: auto;
    }

    .popup-bacteria-grid {
        grid-template-columns: 1fr;
    }

}

</style>
"""
)


# ==========================================================
# HELPERS
# ==========================================================

RISK_RANK = {
    "Safe": 0,
    "Caution": 1,
    "Unsafe": 2,
}


def risk_badge_html(
    risk
):
    css_class = risk_class(
        risk
    )

    return f"""
<span class="timeline-tile-badge {css_class}">
    {risk_icon(risk)} {risk}
</span>
"""


def risk_driver(
    ecoli_risk,
    entero_risk,
):
    ecoli_rank = RISK_RANK.get(
        ecoli_risk,
        0,
    )

    entero_rank = RISK_RANK.get(
        entero_risk,
        0,
    )


    if ecoli_rank > entero_rank:

        return (
            "Overall risk is driven by "
            "the E. coli prediction."
        )


    if entero_rank > ecoli_rank:

        return (
            "Overall risk is driven by "
            "the Enterococcus prediction."
        )


    if ecoli_rank == 0:

        return (
            "Both bacteria are classified as Safe."
        )


    return (
        "Both bacteria are classified "
        f"as {ecoli_risk}."
    )


# ==========================================================
# POPUP / MODAL
# ==========================================================

@st.dialog(
    "LagoonCast Day Details",
    width="large",
)
def show_day_details(
    row_dict,
    period,
    today,
):
    row = pd.Series(
        row_dict
    )


    selected_date = pd.to_datetime(
        row[
            "prediction_date"
        ]
    )


    overall = str(
        row[
            "overall_risk"
        ]
    ).strip()


    ecoli_risk = str(
        row[
            "e_coli_risk"
        ]
    ).strip()


    entero_risk = str(
        row[
            "enterococcus_risk"
        ]
    ).strip()


    ecoli_probability = float(
        row[
            "e_coli_probability"
        ]
    )


    entero_probability = float(
        row[
            "enterococcus_probability"
        ]
    )


    if period == "past":

        period_text = (
            "Reconstructed Recent Estimate"
        )


    elif period == "today":

        period_text = (
            "Current Forecast"
        )


    else:

        horizon = (
            selected_date.normalize()
            - pd.Timestamp(
                today
            ).normalize()
        ).days

        period_text = (
            f"Future Forecast · "
            f"{horizon} day"
            f"{'s' if horizon != 1 else ''} ahead"
        )


    st.html(
        f"""
<div class="popup-summary">

    <div class="popup-period">
        {period_text}
    </div>

    <div class="popup-date">
        {selected_date.strftime("%A, %B %d, %Y")}
    </div>

    <div class="popup-overall {risk_class(overall)}">
        {risk_icon(overall)}
        {overall}
    </div>

    <div class="popup-driver">
        {risk_driver(
            ecoli_risk,
            entero_risk
        )}
    </div>

</div>


<div class="popup-bacteria-grid">

    <div class="popup-bacteria-card">

        <div class="popup-bacteria-name">
            E. coli
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
            Enterococcus
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


    if period == "past":

        st.caption(
            "This value is a reconstructed LagoonCast model "
            "estimate, not a laboratory measurement or a "
            "forecast that was necessarily saved on that date."
        )


    elif period == "future":

        horizon = (
            selected_date.normalize()
            - pd.Timestamp(
                today
            ).normalize()
        ).days

        st.caption(
            f"This forecast is {horizon} "
            f"day{'s' if horizon != 1 else ''} ahead. "
            "Forecast uncertainty generally increases "
            "farther from today."
        )


    st.link_button(
        "View Official San Mateo County Beach Status",
        OFFICIAL_URL,
        width="stretch",
    )


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "15-Day LagoonCast Timeline"
)


st.html(
    f"""
<div class="timeline-page-intro">

    Seven reconstructed recent model estimates,
    today's current forecast, and seven future forecasts
    for <strong>{SITE_NAME}</strong>.

</div>
"""
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
        "View Official San Mateo County Beach Status",
        OFFICIAL_URL,
        width="stretch",
    )

    st.stop()


# ==========================================================
# CLEAN DATES
# ==========================================================

recent = recent.copy()
outlook = outlook.copy()


recent[
    "prediction_date"
] = pd.to_datetime(
    recent[
        "prediction_date"
    ],
    errors="coerce",
)


outlook[
    "prediction_date"
] = pd.to_datetime(
    outlook[
        "prediction_date"
    ],
    errors="coerce",
)


recent = recent.dropna(
    subset=[
        "prediction_date"
    ]
)


outlook = outlook.dropna(
    subset=[
        "prediction_date"
    ]
)


today = (
    pd.Timestamp.now(
        tz="America/Los_Angeles"
    )
    .tz_localize(
        None
    )
    .normalize()
)


# ==========================================================
# PREVIOUS 7 DAYS
# ==========================================================

past = (
    recent[
        recent[
            "prediction_date"
        ]
        .dt.normalize()
        < today
    ]
    .sort_values(
        "prediction_date"
    )
    .tail(
        7
    )
    .copy()
)


past[
    "period"
] = "past"


# ==========================================================
# TODAY
# ==========================================================

current = (
    outlook[
        outlook[
            "prediction_date"
        ]
        .dt.normalize()
        == today
    ]
    .head(
        1
    )
    .copy()
)


if current.empty:

    current = (
        recent[
            recent[
                "prediction_date"
            ]
            .dt.normalize()
            == today
        ]
        .tail(
            1
        )
        .copy()
    )


current[
    "period"
] = "today"


# ==========================================================
# NEXT 7 DAYS
# ==========================================================

future = (
    outlook[
        outlook[
            "prediction_date"
        ]
        .dt.normalize()
        > today
    ]
    .sort_values(
        "prediction_date"
    )
    .head(
        7
    )
    .copy()
)


future[
    "period"
] = "future"


# ==========================================================
# PREVIOUS 7 DAYS
# ==========================================================

st.html(
    """
<div class="timeline-section-header">

    <h2>
        Previous 7 Days
    </h2>

    <span>
        Reconstructed model estimates
    </span>

</div>
"""
)


past_columns = st.columns(
    max(
        len(
            past
        ),
        1,
    )
)


for column, (_, row) in zip(
    past_columns,
    past.iterrows(),
):

    with column:

        date_value = pd.to_datetime(
            row[
                "prediction_date"
            ]
        )


        overall = str(
            row[
                "overall_risk"
            ]
        ).strip()


        ecoli_probability = float(
            row[
                "e_coli_probability"
            ]
        )


        entero_probability = float(
            row[
                "enterococcus_probability"
            ]
        )


        with st.container(
            border=True
        ):

            st.html(
                f"""
<div class="timeline-tile">

    <div class="timeline-tile-day">
        {date_value.strftime("%a")}
    </div>

    <div class="timeline-tile-date">
        {date_value.strftime("%b %d")}
    </div>

    {risk_badge_html(overall)}

    <div class="timeline-tile-values">

        <div>
            E. coli
            <strong>
                {ecoli_probability:.0%}
            </strong>
        </div>

        <div>
            Enterococcus
            <strong>
                {entero_probability:.0%}
            </strong>
        </div>

    </div>

</div>
"""
            )


            if st.button(
                "View",
                key=(
                    "past_"
                    + date_value.strftime(
                        "%Y%m%d"
                    )
                ),
            ):

                show_day_details(
                    row.to_dict(),
                    "past",
                    today,
                )


# ==========================================================
# TODAY
# ==========================================================

st.html(
    """
<div class="timeline-section-header">

    <h2>
        Today
    </h2>

    <span>
        Current LagoonCast forecast
    </span>

</div>
"""
)


if not current.empty:

    today_row = (
        current.iloc[
            0
        ]
    )


    current_overall = str(
        today_row[
            "overall_risk"
        ]
    ).strip()


    current_ecoli_risk = str(
        today_row[
            "e_coli_risk"
        ]
    ).strip()


    current_entero_risk = str(
        today_row[
            "enterococcus_risk"
        ]
    ).strip()


    current_ecoli = float(
        today_row[
            "e_coli_probability"
        ]
    )


    current_entero = float(
        today_row[
            "enterococcus_probability"
        ]
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
            {today.strftime("%A, %b %d")}
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
        risk_driver(
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


# ==========================================================
# NEXT 7 DAYS
# ==========================================================

st.html(
    """
<div class="timeline-section-header">

    <h2>
        Next 7 Days
    </h2>

    <span>
        Forecast uncertainty increases with horizon
    </span>

</div>
"""
)


future_columns = st.columns(
    max(
        len(
            future
        ),
        1,
    )
)


for column, (_, row) in zip(
    future_columns,
    future.iterrows(),
):

    with column:

        date_value = pd.to_datetime(
            row[
                "prediction_date"
            ]
        )


        overall = str(
            row[
                "overall_risk"
            ]
        ).strip()


        ecoli_probability = float(
            row[
                "e_coli_probability"
            ]
        )


        entero_probability = float(
            row[
                "enterococcus_probability"
            ]
        )


        horizon = (
            date_value.normalize()
            - today
        ).days


        with st.container(
            border=True
        ):

            st.html(
                f"""
<div class="timeline-tile">

    <div class="timeline-tile-day">
        {date_value.strftime("%a")}
    </div>

    <div class="timeline-tile-date">
        {date_value.strftime("%b %d")}
    </div>

    {risk_badge_html(overall)}

    <div class="timeline-tile-values">

        <div>
            E. coli
            <strong>
                {ecoli_probability:.0%}
            </strong>
        </div>

        <div>
            Enterococcus
            <strong>
                {entero_probability:.0%}
            </strong>
        </div>

    </div>

    <div class="timeline-horizon">
        {horizon}
        day{"s" if horizon != 1 else ""}
        ahead
    </div>

</div>
"""
            )


            if st.button(
                "View",
                key=(
                    "future_"
                    + date_value.strftime(
                        "%Y%m%d"
                    )
                ),
            ):

                show_day_details(
                    row.to_dict(),
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
# FULL TABLE
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


    display[
        "prediction_date"
    ] = (
        pd.to_datetime(
            display[
                "prediction_date"
            ]
        )
        .dt.strftime(
            "%a, %b %d"
        )
    )


    display[
        "period"
    ] = (
        display[
            "period"
        ]
        .replace(
            {
                "past":
                    "Reconstructed estimate",

                "today":
                    "Today",

                "future":
                    "Future forecast",
            }
        )
    )


    display[
        "e_coli_probability"
    ] = (
        display[
            "e_coli_probability"
        ]
        .map(
            lambda value:
                f"{float(value):.1%}"
        )
    )


    display[
        "enterococcus_probability"
    ] = (
        display[
            "enterococcus_probability"
        ]
        .map(
            lambda value:
                f"{float(value):.1%}"
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
# FOOTER
# ==========================================================

model_version = None


if (
    not current.empty
    and "model_version"
    in current.columns
):

    model_version = str(
        current.iloc[
            0
        ][
            "model_version"
        ]
    )


render_footer(
    model_version
)
