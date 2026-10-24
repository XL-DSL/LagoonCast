import pandas as pd
import streamlit as st

from utils.live_forecast import (
    get_data_freshness,
    get_model_metadata,
    load_live_latest,
)
from utils.styles import apply_styles
from utils.ui import (
    OFFICIAL_URL,
    SITE_NAME,
    render_footer,
)


st.set_page_config(
    page_title="LagoonCast | Model & Data",
    page_icon="assets/LagoonCast_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


def _date_text(value):

    dt = pd.to_datetime(
        value,
        errors="coerce",
    )

    return (
        dt.strftime(
            "%b %d, %Y"
        )
        if pd.notna(
            dt
        )
        else "Unavailable"
    )


def _timestamp_text(value):

    dt = pd.to_datetime(
        value,
        errors="coerce",
    )

    return (
        dt.strftime(
            "%b %d, %Y at %I:%M %p"
        )
        if pd.notna(
            dt
        )
        else "Unavailable"
    )


# ==========================================================
# LOAD MODEL ARTIFACTS DYNAMICALLY
# ==========================================================

try:

    (
        manifest,
        metrics,
    ) = get_model_metadata()

except Exception as exc:

    st.error(
        "Model metadata is currently unavailable. "
        "LagoonCast will not display hardcoded replacement metrics."
    )

    st.code(
        str(
            exc
        )
    )

    st.stop()


selected_rows = []

consistency_errors = []


for bacteria_name in [
    "E. coli",
    "Enterococcus",
]:

    cfg = manifest[
        "models"
    ].get(
        bacteria_name
    )

    if cfg is None:

        consistency_errors.append(
            f"Manifest is missing {bacteria_name}."
        )

        continue


    match = metrics[
        (
            metrics[
                "bacteria"
            ]
            == bacteria_name
        )
        &
        (
            metrics[
                "model"
            ]
            == cfg[
                "model"
            ]
        )
        &
        (
            metrics[
                "feature_set"
            ]
            == cfg[
                "feature_set"
            ]
        )
    ]


    if len(
        match
    ) != 1:

        consistency_errors.append(
            f"{bacteria_name}: expected exactly one metrics "
            f"row for {cfg['model']} / {cfg['feature_set']}, "
            f"found {len(match)}."
        )

        continue


    row = (
        match.iloc[
            0
        ]
        .copy()
    )


    manifest_feature_count = len(
        cfg[
            "features"
        ]
    )


    if (
        "n_features"
        in row
        and int(
            row[
                "n_features"
            ]
        )
        != manifest_feature_count
    ):

        consistency_errors.append(
            f"{bacteria_name}: manifest has "
            f"{manifest_feature_count} features "
            f"but metrics CSV reports "
            f"{int(row['n_features'])}."
        )


    selected_rows.append(
        (
            bacteria_name,
            cfg,
            row,
        )
    )


data_checks_passed = (
    len(
        consistency_errors
    )
    == 0
    and len(
        selected_rows
    )
    == 2
)


if consistency_errors:

    st.error(
        "Model artifact consistency check failed. "
        "The page shows the mismatch instead of hiding it."
    )

    for error in consistency_errors:

        st.write(
            "•",
            error,
        )


# ==========================================================
# DATA / FORECAST FRESHNESS
# ==========================================================

try:

    freshness = get_data_freshness(
        include_weather=False
    )

except Exception as exc:

    freshness = {
        "latest_lab_date":
            None,

        "e_coli_latest_lab_date":
            None,

        "enterococcus_latest_lab_date":
            None,

        "history_error":
            str(
                exc
            ),
    }


try:

    live = (
        load_live_latest()
    )

    latest_weather = live.get(
        "weather_input_end_date"
    )

    generated_at = live.get(
        "forecast_generated_at"
    )

    live_status = (
        "Available"
    )

except Exception as exc:

    live = None

    latest_weather = None

    generated_at = None

    live_status = (
        "Unavailable"
    )

    live_error = str(
        exc
    )


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "Model & Data"
)


st.caption(
    f"Technical details for LagoonCast's pilot at {SITE_NAME}. "
    "Values on this page are loaded from the deployed model "
    "artifacts rather than typed into the page."
)


# ==========================================================
# STATUS CARDS
# ==========================================================

c1, c2 = st.columns(
    2
)


with c1:

    st.metric(
        "Automated Data Checks",
        (
            "Passed"
            if data_checks_passed
            else "Needs attention"
        ),
    )


with c2:

    st.metric(
        "Forecast Generated",
        _date_text(
            generated_at
        ),
    )


st.caption(
    f"Live inference status: {live_status}. "
    f"Model pipeline: "
    f"{manifest.get('pipeline_version', 'Unavailable')}."
)


if live is not None:

    st.info(
        "Weather and laboratory inputs have different freshness. "
        f"The current model uses weather through "
        f"{_date_text(live.get('weather_input_end_date'))}. "
        f"The latest actual E. coli laboratory sample used is "
        f"{_date_text(live.get('e_coli_latest_lab_date'))}; "
        f"the latest Enterococcus sample is "
        f"{_date_text(live.get('enterococcus_latest_lab_date'))}."
    )


elif "live_error" in locals():

    with st.expander(
        "Why live freshness is unavailable"
    ):

        st.code(
            live_error
        )


# ==========================================================
# SELECTED MODELS + PERFORMANCE
# ==========================================================

st.subheader(
    "Selected models and held-out performance"
)


display_rows = []


for (
    bacteria_name,
    cfg,
    row,
) in selected_rows:

    test_n = int(
        row[
            "tn"
        ]
        +
        row[
            "fp"
        ]
        +
        row[
            "fn"
        ]
        +
        row[
            "tp"
        ]
    )

    elevated_n = int(
        row[
            "fn"
        ]
        +
        row[
            "tp"
        ]
    )


    display_rows.append(
        {
            "Bacterium":
                bacteria_name,

            "Selected model":
                cfg[
                    "model"
                ],

            "Feature set":
                cfg[
                    "feature_set"
                ],

            "Features":
                len(
                    cfg[
                        "features"
                    ]
                ),

            "Classification threshold":
                float(
                    cfg[
                        "locked_threshold"
                    ]
                ),

            "Test observations":
                test_n,

            "Elevated cases":
                elevated_n,

            "Accuracy":
                float(
                    row[
                        "accuracy"
                    ]
                ),

            "Precision":
                float(
                    row[
                        "precision"
                    ]
                ),

            "Recall":
                float(
                    row[
                        "recall"
                    ]
                ),

            "F1":
                float(
                    row[
                        "f1"
                    ]
                ),

            "False negatives":
                int(
                    row[
                        "fn"
                    ]
                ),

            "PR-AUC":
                (
                    float(
                        row[
                            "pr_auc"
                        ]
                    )
                    if "pr_auc"
                    in row
                    else float(
                        "nan"
                    )
                ),

            "Brier score":
                (
                    float(
                        row[
                            "brier_score"
                        ]
                    )
                    if "brier_score"
                    in row
                    else float(
                        "nan"
                    )
                ),
        }
    )


performance = pd.DataFrame(
    display_rows
)


if not performance.empty:

    formatted = (
        performance.copy()
    )


    for col in [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "PR-AUC",
    ]:

        formatted[
            col
        ] = formatted[
            col
        ].map(
            lambda x:
                (
                    f"{x:.1%}"
                    if pd.notna(
                        x
                    )
                    else "—"
                )
        )


    formatted[
        "Brier score"
    ] = formatted[
        "Brier score"
    ].map(
        lambda x:
            (
                f"{x:.3f}"
                if pd.notna(
                    x
                )
                else "—"
            )
    )


    formatted[
        "Classification threshold"
    ] = formatted[
        "Classification threshold"
    ].map(
        lambda x:
            f"{x:.2f}"
    )


    st.dataframe(
        formatted,
        use_container_width=True,
        hide_index=True,
    )


st.caption(
    "Recall describes how often elevated laboratory events "
    "in the held-out chronological test period were correctly "
    "identified. Precision describes how often an elevated "
    "prediction corresponded to an elevated event."
)


# ==========================================================
# MODEL-DEFINED CONCENTRATION THRESHOLDS
# ==========================================================

st.subheader(
    "Model-defined concentration thresholds"
)


threshold_rows = []


for (
    bacteria_name,
    cfg,
    _,
) in selected_rows:

    threshold_rows.append(
        {
            "Bacterium":
                bacteria_name,

            "Model-defined exceedance threshold":
                (
                    f"{float(cfg['bacteria_threshold_mpn_100ml']):.0f} "
                    "MPN/100 mL"
                ),

            "Use in LagoonCast":
                (
                    "Creates the binary training/evaluation label"
                ),
        }
    )


st.dataframe(
    pd.DataFrame(
        threshold_rows
    ),
    use_container_width=True,
    hide_index=True,
)


st.warning(
    "LagoonCast uses 235 MPN/100 mL for E. coli and "
    "130 MPN/100 mL for Enterococcus as model-defined "
    "exceedance thresholds in this research pipeline. "
    "The app does not present these values as current official "
    "closure limits for Parkside Aquatic Park. Official "
    "advisories and closures always take priority."
)


st.link_button(
    "Check Official Water-Quality Advisories",
    OFFICIAL_URL,
)


# ==========================================================
# DISPLAY BANDS
# ==========================================================

st.subheader(
    "Probability display bands"
)


st.markdown(
    """
These are **display thresholds applied to model probabilities**,
not bacterial concentration standards.

| Bacterium | Safe | Caution | Unsafe |
|---|---:|---:|---:|
| E. coli | < 10% | 10% to < 50% | ≥ 50% |
| Enterococcus | < 40% | 40% to < 85% | ≥ 85% |
"""
)


# ==========================================================
# FEATURE TIMING / LEAKAGE PROTECTION
# ==========================================================

st.subheader(
    "How live features are constructed"
)


st.markdown(
    """
- `rain_1day` uses rainfall from the **day before** the target date.
- Multi-day rainfall and temperature windows are shifted so the
  **target day is excluded**, matching model training.
- Lagged rainfall uses prior days only.
- First-flush and antecedent-dry-period features follow the same
  training definitions.
- Laboratory-history features use only samples dated **strictly
  before** the target date.
- If any required model feature cannot be constructed as a finite
  numeric value, LagoonCast marks the forecast **unavailable**
  rather than replacing the missing value with zero.
"""
)


# ==========================================================
# DATA SOURCES
# ==========================================================

st.subheader(
    "Data sources"
)


st.markdown(
    """
**Historical bacteria:** California Water Boards / SWAMP records
used in the project dataset.

**Historical training weather:** NOAA / NCEI daily weather records.

**Live and forecast weather:** Open-Meteo daily forecast data.

**Important:** a freshly generated forecast does not mean the
latest laboratory measurement was collected on the same day.
LagoonCast reports laboratory freshness separately.
"""
)


# ==========================================================
# DEPLOYED FEATURES
# ==========================================================

with st.expander(
    "View deployed model feature lists"
):

    for (
        bacteria_name,
        cfg,
        _,
    ) in selected_rows:

        st.markdown(
            f"**{bacteria_name}: "
            f"{len(cfg['features'])} features**"
        )

        st.code(
            "\n".join(
                cfg[
                    "features"
                ]
            )
        )


# ==========================================================
# VALIDATION DESIGN
# ==========================================================

st.subheader(
    "Validation design"
)


st.markdown(
    """
Model performance is evaluated chronologically: earlier
observations are used for model development and later
observations are held out for final testing. This avoids
randomly mixing future observations into the training set.

The final test metrics shown above are descriptive performance
results for this pilot site. They do not make LagoonCast an
official monitoring or regulatory system.
"""
)


render_footer(
    str(
        manifest.get(
            "pipeline_version",
            "Unavailable",
        )
    )
)
