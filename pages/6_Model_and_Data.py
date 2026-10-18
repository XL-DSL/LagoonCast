import re
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.live_forecast import load_live_latest
from utils.styles import apply_styles
from utils.ui import (
    GITHUB_URL,
    OFFICIAL_URL,
    render_footer,
    successful_generation_text,
)
from utils.validation import (
    validate_prediction_row,
)


apply_styles()


# ==========================================================
# PATH
# ==========================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_PATH = (
    ROOT
    / "data"
    / "Aquacast15Years_Weekly.csv"
)


# ==========================================================
# HELPERS
# ==========================================================

def normalize(
    value
):
    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(
            value
        ).lower(),
    )


def find_column(
    columns,
    candidates,
):
    lookup = {
        normalize(
            column
        ):
            column
        for column
        in columns
    }

    for candidate in candidates:

        key = normalize(
            candidate
        )

        if key in lookup:
            return lookup[
                key
            ]

    return None


@st.cache_data(
    show_spinner=False
)
def dataset_summary():

    result = {
        "latest_lab_date":
            None,

        "ecoli_n":
            None,

        "ecoli_cases":
            None,

        "entero_n":
            None,

        "entero_cases":
            None,
    }


    if not DATA_PATH.exists():
        return result


    try:

        df = pd.read_csv(
            DATA_PATH
        )

    except Exception:

        return result


    date_col = find_column(
        df.columns,
        [
            "prediction_date",
            "sample_date",
            "date",
            "Date",
            "SampleDate",
        ],
    )


    ecoli_col = find_column(
        df.columns,
        [
            "e_coli",
            "ecoli",
            "E. coli",
            "E_coli",
            "e_coli_result",
            "ecoli_result",
            "e_coli_value",
            "ecoli_value",
        ],
    )


    entero_col = find_column(
        df.columns,
        [
            "enterococcus",
            "Enterococcus",
            "entero",
            "enterococcus_result",
            "entero_result",
            "enterococcus_value",
            "entero_value",
        ],
    )


    if date_col is None:
        return result


    df[
        date_col
    ] = pd.to_datetime(
        df[
            date_col
        ],
        errors="coerce",
    )


    dated = df.dropna(
        subset=[
            date_col
        ]
    )


    if not dated.empty:

        result[
            "latest_lab_date"
        ] = (
            dated[
                date_col
            ]
            .max()
        )


    # Chronological held-out test period used by AquaCast.
    test = dated[
        (
            dated[
                date_col
            ]
            >= pd.Timestamp(
                "2024-01-01"
            )
        )
        &
        (
            dated[
                date_col
            ]
            <= pd.Timestamp(
                "2025-12-31"
            )
        )
    ].copy()


    if ecoli_col is not None:

        values = pd.to_numeric(
            test[
                ecoli_col
            ],
            errors="coerce",
        ).dropna()

        if not values.empty:

            result[
                "ecoli_n"
            ] = int(
                len(
                    values
                )
            )

            result[
                "ecoli_cases"
            ] = int(
                (
                    values
                    >= 235
                ).sum()
            )


    if entero_col is not None:

        values = pd.to_numeric(
            test[
                entero_col
            ],
            errors="coerce",
        ).dropna()

        if not values.empty:

            result[
                "entero_n"
            ] = int(
                len(
                    values
                )
            )

            result[
                "entero_cases"
            ] = int(
                (
                    values
                    >= 130
                ).sum()
            )


    return result


def display_number(
    value
):
    if value is None:
        return "Not available"

    return str(
        value
    )


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "Model & Data"
)

st.caption(
    "Technical details for reviewers, researchers, "
    "and users who want to understand how AquaCast works."
)


# ==========================================================
# CURRENT SYSTEM STATUS
# ==========================================================

st.subheader(
    "System Status"
)


try:

    latest = load_live_latest()

    validation = (
        validate_prediction_row(
            latest
        )
    )

    generated_text = (
        successful_generation_text(
            latest,
            using_live=True,
        )
    )

    model_version = str(
        latest[
            "model_version"
        ]
    )

    data_check = (
        "Passed"
        if validation[
            "valid"
        ]
        else "Attention needed"
    )

except Exception:

    latest = None

    generated_text = (
        "Live forecast unavailable"
    )

    model_version = (
        "Unavailable"
    )

    data_check = (
        "Unavailable"
    )


summary = dataset_summary()


latest_lab_date = (
    summary[
        "latest_lab_date"
    ]
)


latest_lab_text = (
    latest_lab_date.strftime(
        "%b %d, %Y"
    )
    if pd.notna(
        latest_lab_date
    )
    else "Not available"
)


status1, status2 = st.columns(
    2
)


with status1:

    st.metric(
        "Automated Data Checks",
        data_check,
    )


with status2:

    st.metric(
        "Weather Input",
        "Open-Meteo",
    )


status3, status4 = st.columns(
    2
)


with status3:

    st.metric(
        "Latest Laboratory Input",
        latest_lab_text,
    )


with status4:

    st.metric(
        "Forecast Generated",
        generated_text,
    )


st.caption(
    f"Deployed model version: {model_version}"
)


# ==========================================================
# WHAT THE MODEL PREDICTS
# ==========================================================

st.subheader(
    "What AquaCast predicts"
)


st.write(
    "AquaCast is a binary classification system. "
    "It estimates the probability that a bacterial "
    "measurement exceeds a concentration threshold; "
    "it does not predict the exact bacterial concentration."
)


threshold_table = pd.DataFrame(
    {
        "Organism":
            [
                "E. coli",
                "Enterococcus",
            ],

        "Concentration threshold":
            [
                "235 MPN/100 mL",
                "130 MPN/100 mL",
            ],

        "AquaCast Safe":
            [
                "<10%",
                "<40%",
            ],

        "AquaCast Caution":
            [
                "10% to <50%",
                "40% to <85%",
            ],

        "AquaCast Unsafe":
            [
                "≥50%",
                "≥85%",
            ],
    }
)


st.dataframe(
    threshold_table,
    hide_index=True,
    width="stretch",
)


st.info(
    "The bacterial concentration thresholds and the "
    "AquaCast probability display thresholds are different "
    "concepts. Concentration thresholds define the event "
    "the model is trying to predict. Probability thresholds "
    "determine how LagoonCast communicates model risk."
)


st.link_button(
    "Verify Official San Mateo County Beach Information",
    OFFICIAL_URL,
)


# ==========================================================
# INPUT FEATURES
# ==========================================================

st.subheader(
    "Selected environmental features"
)


st.write(
    "The deployed models use combinations of recent rainfall, "
    "antecedent dry conditions, temperature, seasonal information, "
    "and available historical bacteria information."
)


features = pd.DataFrame(
    {
        "Feature group":
            [
                "Rainfall",
                "Dry-period conditions",
                "Temperature",
                "Seasonality",
                "Historical laboratory information",
            ],

        "Examples":
            [
                "1-day rain, 3-day rain, lagged rainfall",
                "Antecedent dry days and first-flush index",
                "Recent average temperature",
                "Month / seasonal timing",
                "Latest available bacteria information",
            ],
    }
)


st.dataframe(
    features,
    hide_index=True,
    width="stretch",
)


# ==========================================================
# VALIDATION METHOD
# ==========================================================

st.subheader(
    "Validation method"
)


st.write(
    "AquaCast uses a chronological split rather than randomly "
    "mixing observations across time. Earlier observations were "
    "used for model development, while 2024–2025 observations "
    "were held out for final evaluation."
)


st.write(
    "Probability decision thresholds were selected using "
    "validation data only. The final held-out test period was "
    "not used to choose those thresholds."
)


# ==========================================================
# PERFORMANCE
# ==========================================================

st.subheader(
    "Held-out test performance"
)


performance = pd.DataFrame(
    {
        "Model":
            [
                "E. coli",
                "Enterococcus",
            ],

        "Selected method":
            [
                "Logistic Regression",
                "Logistic Regression",
            ],

        "Test observations":
            [
                display_number(
                    summary[
                        "ecoli_n"
                    ]
                ),

                display_number(
                    summary[
                        "entero_n"
                    ]
                ),
            ],

        "Elevated-risk cases":
            [
                display_number(
                    summary[
                        "ecoli_cases"
                    ]
                ),

                display_number(
                    summary[
                        "entero_cases"
                    ]
                ),
            ],

        "Recall":
            [
                "95.0%",
                "65.7%",
            ],

        "Precision":
            [
                "53.3%",
                "65.7%",
            ],

        "F1":
            [
                "68.3%",
                "65.7%",
            ],

        "PR-AUC":
            [
                "76.7%",
                "69.1%",
            ],
    }
)


st.dataframe(
    performance,
    hide_index=True,
    width="stretch",
)


st.caption(
    "If the deployed weekly dataset does not contain an "
    "identifiable raw concentration column, the test observation "
    "and elevated-case fields are intentionally shown as "
    "'Not available' rather than estimated."
)


# ==========================================================
# METRIC DEFINITIONS
# ==========================================================

with st.expander(
    "What do Recall, Precision, F1, and PR-AUC mean?"
):

    st.markdown(
        """
**Recall** describes how often actual elevated-risk events
were correctly identified.

**Precision** describes how often an elevated-risk prediction
was actually associated with an elevated-risk event.

**F1** balances recall and precision in one score.

**PR-AUC** summarizes performance across different probability
thresholds and is particularly useful when elevated-risk events
are less common than normal observations.
"""
    )


# ==========================================================
# FUTURE FORECASTING
# ==========================================================

st.subheader(
    "Live forecasting"
)


st.write(
    "The deployed application uses Open-Meteo environmental "
    "forecasts to extend AquaCast beyond the historical dataset. "
    "Future AquaCast uncertainty therefore includes both model "
    "uncertainty and uncertainty in the environmental forecast."
)


# ==========================================================
# DATA SOURCES
# ==========================================================

st.subheader(
    "Data provenance"
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
        "NOAA NCEI",
        "https://www.ncei.noaa.gov/",
        width="stretch",
    )


source3, source4 = st.columns(
    2
)


with source3:

    st.link_button(
        "Open-Meteo",
        "https://open-meteo.com/",
        width="stretch",
    )


with source4:

    st.link_button(
        "Project Repository / Methodology",
        GITHUB_URL,
        width="stretch",
    )


# ==========================================================
# EXCLUDED INPUTS
# ==========================================================

with st.expander(
    "Inputs evaluated but not used in the deployed model"
):

    st.write(
        "Tide variables and sanitary sewer overflow variables "
        "were evaluated during development but are not part "
        "of the selected deployed model configuration."
    )


# ==========================================================
# AI DISCLOSURE
# ==========================================================

with st.expander(
    "AI-assisted development disclosure"
):

    st.write(
        "AI tools were used as development assistance for "
        "tasks such as coding support, debugging, organization, "
        "and interface refinement. Model design decisions, "
        "data preparation, evaluation, interpretation, and "
        "project conclusions remain part of the research workflow "
        "and should be evaluated on the documented methodology "
        "and reproducible project artifacts."
    )


render_footer(
    model_version
)
