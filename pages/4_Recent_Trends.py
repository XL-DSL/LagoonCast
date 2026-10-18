import altair as alt
import pandas as pd
import streamlit as st

from utils.live_forecast import load_recent_estimates
from utils.styles import apply_styles
from utils.ui import (
    OFFICIAL_URL,
    SITE_NAME,
    render_footer,
)


apply_styles()


# ==========================================================
# CONSTANTS
# ==========================================================

ECOLI_CAUTION = 0.10
ECOLI_UNSAFE = 0.50

ENTERO_CAUTION = 0.40
ENTERO_UNSAFE = 0.85


SAFE_COLOR = "#2E7D32"
CAUTION_COLOR = "#B26A00"
UNSAFE_COLOR = "#C62828"
LINE_COLOR = "#0F6B78"


# ==========================================================
# PAGE HEADER
# ==========================================================

st.title(
    "Recent Trends"
)

st.caption(
    "Reconstructed LagoonCast model estimates for "
    f"{SITE_NAME}. These are historical model estimates "
    "generated from available environmental data, not "
    "forecasts that were necessarily saved on those dates."
)


# ==========================================================
# WINDOW
# ==========================================================

window = st.select_slider(
    "Trend window",
    options=[
        7,
        14,
        21,
        30,
    ],
    value=14,
    format_func=lambda value:
        f"{value} days",
)


# ==========================================================
# LOAD
# ==========================================================

try:

    with st.spinner(
        "Loading recent LagoonCast estimates..."
    ):

        trends = load_recent_estimates(
            days=window
        )

except Exception:

    st.error(
        "Recent LagoonCast trends are temporarily unavailable."
    )

    st.link_button(
        "View Official San Mateo County Beach Status",
        OFFICIAL_URL,
        width="stretch",
    )

    st.stop()


trends = trends.copy()

trends[
    "prediction_date"
] = pd.to_datetime(
    trends[
        "prediction_date"
    ],
    errors="coerce",
)

trends = (
    trends
    .dropna(
        subset=[
            "prediction_date"
        ]
    )
    .sort_values(
        "prediction_date"
    )
    .reset_index(
        drop=True
    )
)


if trends.empty:

    st.error(
        "No recent LagoonCast estimates are available."
    )

    st.stop()


# ==========================================================
# HELPERS
# ==========================================================

def change_text(
    series
):
    if len(series) < 2:
        return (
            "Change unavailable",
            "neutral",
        )

    current = float(
        series.iloc[-1]
    )

    previous = float(
        series.iloc[-2]
    )

    change = (
        current
        - previous
    ) * 100

    if abs(change) < 0.05:
        return (
            "Unchanged from previous day",
            "neutral",
        )

    if change > 0:
        return (
            f"Up {abs(change):.1f} percentage points",
            "up",
        )

    return (
        f"Down {abs(change):.1f} percentage points",
        "down",
    )


def trend_summary(
    title,
    value,
    risk,
    change,
):
    risk_color = {
        "Safe":
            SAFE_COLOR,

        "Caution":
            CAUTION_COLOR,

        "Unsafe":
            UNSAFE_COLOR,
    }.get(
        risk,
        "#667085",
    )

    st.html(
        f"""
<div style="
    background:#FFFFFF;
    border:1px solid #E4E7EC;
    border-radius:14px;
    padding:1rem 1.1rem;
    margin-bottom:0.8rem;
">

    <div style="
        color:#667085;
        font-size:0.76rem;
        font-weight:600;
    ">
        {title}
    </div>

    <div style="
        display:flex;
        align-items:baseline;
        gap:0.7rem;
        margin-top:0.25rem;
    ">

        <span style="
            color:#172033;
            font-size:1.7rem;
            font-weight:800;
        ">
            {value:.1%}
        </span>

        <span style="
            color:{risk_color};
            font-size:0.78rem;
            font-weight:750;
        ">
            {risk}
        </span>

    </div>

    <div style="
        color:#667085;
        font-size:0.72rem;
        margin-top:0.2rem;
    ">
        {change}
    </div>

</div>
"""
    )


def organism_chart(
    data,
    probability_column,
    caution_threshold,
    unsafe_threshold,
    title,
):
    chart_data = data[
        [
            "prediction_date",
            probability_column,
        ]
    ].copy()

    chart_data[
        probability_column
    ] = pd.to_numeric(
        chart_data[
            probability_column
        ],
        errors="coerce",
    )

    chart_data = chart_data.dropna()

    observed_max = float(
        chart_data[
            probability_column
        ].max()
    )

    # Focus the chart while still showing the nearest
    # decision boundary clearly.
    y_max = max(
        observed_max + 0.08,
        caution_threshold + 0.08,
        0.20,
    )

    # If observations approach the Unsafe threshold,
    # expand the scale to show it.
    if (
        observed_max
        >= unsafe_threshold * 0.70
    ):
        y_max = max(
            y_max,
            unsafe_threshold + 0.05,
        )

    y_max = min(
        y_max,
        1.0,
    )


    start_date = (
        chart_data[
            "prediction_date"
        ].min()
        - pd.Timedelta(
            hours=12
        )
    )

    end_date = (
        chart_data[
            "prediction_date"
        ].max()
        + pd.Timedelta(
            hours=12
        )
    )


    zones = []


    safe_top = min(
        caution_threshold,
        y_max,
    )

    if safe_top > 0:

        zones.append(
            {
                "start":
                    start_date,

                "end":
                    end_date,

                "y1":
                    0.0,

                "y2":
                    safe_top,

                "color":
                    SAFE_COLOR,
            }
        )


    if y_max > caution_threshold:

        caution_top = min(
            unsafe_threshold,
            y_max,
        )

        zones.append(
            {
                "start":
                    start_date,

                "end":
                    end_date,

                "y1":
                    caution_threshold,

                "y2":
                    caution_top,

                "color":
                    CAUTION_COLOR,
            }
        )


    if y_max > unsafe_threshold:

        zones.append(
            {
                "start":
                    start_date,

                "end":
                    end_date,

                "y1":
                    unsafe_threshold,

                "y2":
                    y_max,

                "color":
                    UNSAFE_COLOR,
            }
        )


    zone_data = pd.DataFrame(
        zones
    )


    base = alt.Chart(
        chart_data
    )


    if not zone_data.empty:

        background = (
            alt.Chart(
                zone_data
            )
            .mark_rect(
                opacity=0.10
            )
            .encode(
                x=alt.X(
                    "start:T",
                    title=None,
                ),

                x2="end:T",

                y=alt.Y(
                    "y1:Q",
                    scale=alt.Scale(
                        domain=[
                            0,
                            y_max,
                        ]
                    ),
                    axis=alt.Axis(
                        format=".0%",
                    ),
                ),

                y2="y2:Q",

                color=alt.Color(
                    "color:N",
                    scale=None,
                    legend=None,
                ),
            )
        )

    else:

        background = alt.Chart(
            pd.DataFrame(
                {
                    "x": [],
                    "y": [],
                }
            )
        ).mark_point()


    line = (
        base
        .mark_line(
            point=True,
            strokeWidth=3,
            color=LINE_COLOR,
        )
        .encode(
            x=alt.X(
                "prediction_date:T",
                title=None,
                axis=alt.Axis(
                    format="%b %d",
                    labelAngle=-35,
                ),
            ),

            y=alt.Y(
                f"{probability_column}:Q",
                title="Exceedance probability",
                scale=alt.Scale(
                    domain=[
                        0,
                        y_max,
                    ]
                ),
                axis=alt.Axis(
                    format=".0%",
                ),
            ),

            tooltip=[
                alt.Tooltip(
                    "prediction_date:T",
                    title="Date",
                    format="%b %d, %Y",
                ),

                alt.Tooltip(
                    f"{probability_column}:Q",
                    title="Probability",
                    format=".1%",
                ),
            ],
        )
    )


    rules = []


    if caution_threshold <= y_max:

        rules.append(
            {
                "threshold":
                    caution_threshold,

                "label":
                    "Caution threshold",
            }
        )


    if unsafe_threshold <= y_max:

        rules.append(
            {
                "threshold":
                    unsafe_threshold,

                "label":
                    "Unsafe threshold",
            }
        )


    if rules:

        rule_data = pd.DataFrame(
            rules
        )

        threshold_rules = (
            alt.Chart(
                rule_data
            )
            .mark_rule(
                strokeDash=[
                    5,
                    4,
                ],
                color="#667085",
            )
            .encode(
                y="threshold:Q",

                tooltip=[
                    "label:N",

                    alt.Tooltip(
                        "threshold:Q",
                        format=".0%",
                    ),
                ],
            )
        )

        chart = (
            background
            + line
            + threshold_rules
        )

    else:

        chart = (
            background
            + line
        )


    st.subheader(
        title
    )


    st.altair_chart(
        chart.properties(
            height=280
        ).interactive(),
        width="stretch",
    )


    if unsafe_threshold > y_max:

        st.caption(
            "The chart uses a focused vertical scale so "
            "small recent changes remain visible. "
            f"The Unsafe threshold ({unsafe_threshold:.0%}) "
            "is above the displayed range."
        )

    else:

        st.caption(
            "The vertical scale is focused on recent values "
            "and the relevant decision thresholds. "
            "All displayed percentages are absolute probabilities."
        )


# ==========================================================
# LATEST VALUES
# ==========================================================

latest = trends.iloc[-1]


ecoli_change, _ = change_text(
    trends[
        "e_coli_probability"
    ]
)

entero_change, _ = change_text(
    trends[
        "enterococcus_probability"
    ]
)


summary_left, summary_right = st.columns(
    2
)


with summary_left:

    trend_summary(
        "Latest E. coli estimate",
        float(
            latest[
                "e_coli_probability"
            ]
        ),
        str(
            latest[
                "e_coli_risk"
            ]
        ),
        ecoli_change,
    )


with summary_right:

    trend_summary(
        "Latest Enterococcus estimate",
        float(
            latest[
                "enterococcus_probability"
            ]
        ),
        str(
            latest[
                "enterococcus_risk"
            ]
        ),
        entero_change,
    )


# ==========================================================
# CHARTS
# ==========================================================

organism_chart(
    trends,
    "e_coli_probability",
    ECOLI_CAUTION,
    ECOLI_UNSAFE,
    "E. coli Trend",
)


organism_chart(
    trends,
    "enterococcus_probability",
    ENTERO_CAUTION,
    ENTERO_UNSAFE,
    "Enterococcus Trend",
)


# ==========================================================
# DAILY VALUES
# ==========================================================

with st.expander(
    "View daily values"
):

    display = trends[
        [
            "prediction_date",
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
        display[
            "prediction_date"
        ]
        .dt.strftime(
            "%a, %b %d"
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
        "E. coli",
        "E. coli Risk",
        "Enterococcus",
        "Enterococcus Risk",
        "Overall Risk",
    ]


    st.dataframe(
        display.iloc[::-1],
        hide_index=True,
        width="stretch",
    )


# ==========================================================
# SCIENTIFIC NOTE
# ==========================================================

st.info(
    "Previous-day values on this page are reconstructed "
    "LagoonCast model estimates. They are not laboratory "
    "measurements and should not be interpreted as official "
    "historical advisories."
)


render_footer()
