
import pandas as pd
import streamlit as st

from utils.live_forecast import (
    get_data_freshness,
    get_model_metadata,
    load_live_latest,
)
from utils.styles import apply_styles
from utils.ui import (
    ADVISORY_BUTTON_LABEL,
    ADVISORY_URL,
    MODEL_METHODS_URL,
    METHODOLOGY_URL,
    OFFICIAL_PRIORITY_NOTICE,
    OFFICIAL_URL,
    PREDICTION_EXPLANATION,
    REPORTS_BUTTON_LABEL,
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
    dt = pd.to_datetime(value, errors="coerce")
    return dt.strftime("%b %d, %Y") if pd.notna(dt) else "Unavailable"


# ==========================================================
# DEPLOYED MODEL ARTIFACTS — NO HARDCODED METRICS
# ==========================================================

try:
    manifest, metrics = get_model_metadata()
except Exception as exc:
    st.error(
        "Model metadata is currently unavailable. "
        "LagoonCast will not display hardcoded replacement metrics."
    )
    with st.expander("Technical error"):
        st.code(str(exc))
    st.stop()

selected_rows = []
consistency_errors = []

for bacteria_name in ["E. coli", "Enterococcus"]:
    cfg = manifest["models"].get(bacteria_name)

    if cfg is None:
        consistency_errors.append(f"Manifest is missing {bacteria_name}.")
        continue

    match = metrics[
        (metrics["bacteria"] == bacteria_name)
        & (metrics["model"] == cfg["model"])
        & (metrics["feature_set"] == cfg["feature_set"])
    ]

    if len(match) != 1:
        consistency_errors.append(
            f"{bacteria_name}: expected exactly one metrics row for "
            f"{cfg['model']} / {cfg['feature_set']}, found {len(match)}."
        )
        continue

    row = match.iloc[0].copy()
    feature_count = len(cfg["features"])

    if "n_features" in row and pd.notna(row["n_features"]):
        if int(row["n_features"]) != feature_count:
            consistency_errors.append(
                f"{bacteria_name}: manifest has {feature_count} features "
                f"but metrics CSV reports {int(row['n_features'])}."
            )

    selected_rows.append((bacteria_name, cfg, row))

data_checks_passed = (
    not consistency_errors and len(selected_rows) == 2
)

if consistency_errors:
    st.error(
        "Model artifact consistency check failed. "
        "The mismatches are shown below rather than hidden."
    )
    for error in consistency_errors:
        st.write("•", error)


# ==========================================================
# DATA AND LIVE FORECAST FRESHNESS
# ==========================================================

try:
    freshness = get_data_freshness(include_weather=False)
except Exception as exc:
    freshness = {
        "latest_lab_date": None,
        "e_coli_latest_lab_date": None,
        "enterococcus_latest_lab_date": None,
        "history_error": str(exc),
    }

try:
    live = load_live_latest()
    generated_at = live.get("forecast_generated_at")
    live_status = "Available"
except Exception as exc:
    live = None
    generated_at = None
    live_status = "Unavailable"
    live_error = str(exc)


# ==========================================================
# HEADER AND STATUS
# ==========================================================

selected_algorithms = "; ".join(
    f"{bacteria_name}: {cfg['model']}"
    for bacteria_name, cfg, _ in selected_rows
)

st.title("Model & Data")
st.caption(
    f"At {SITE_NAME}, LagoonCast uses machine-learning models "
    "trained on historical bacteria measurements and weather data "
    "to estimate bacterial exceedance risk between laboratory tests. "
    f"Deployed algorithms: {selected_algorithms or 'Unavailable'}. "
    "The selected models and performance values below are loaded "
    "from the deployed model artifacts, not entered manually."
)

st.markdown(
    f"**Deployed model release:** "
    f"`{manifest.get('pipeline_version', 'Unavailable')}`"
    f" · [Selected model details]({MODEL_METHODS_URL})"
    f" · [Feature timing and methodology]({METHODOLOGY_URL})"
)

c1, c2 = st.columns(2)
with c1:
    st.metric(
        "Automated Data Checks",
        "Passed" if data_checks_passed else "Needs attention",
    )
with c2:
    st.metric("Forecast Generated", _date_text(generated_at))

st.caption(
    f"Live inference status: {live_status}. "
    f"Model pipeline: {manifest.get('pipeline_version', 'Unavailable')}."
)

if live is not None:
    st.info(
        "Weather inputs and laboratory measurements have different "
        "freshness. The current model uses weather through "
        f"{_date_text(live.get('weather_input_end_date'))}. "
        "The latest E. coli laboratory sample used is "
        f"{_date_text(live.get('e_coli_latest_lab_date'))}; "
        "the latest Enterococcus sample is "
        f"{_date_text(live.get('enterococcus_latest_lab_date'))}. "
        "A freshly generated forecast does not mean bacteria were "
        "measured that day."
    )
else:
    st.warning(
        "Live forecasting is unavailable. Model metadata and historical "
        "evaluation results below do not represent today's water conditions."
    )
    with st.expander("Why live freshness is unavailable"):
        st.code(live_error)


# ==========================================================
# SELECTED MODELS AND RETROSPECTIVE PERFORMANCE
# ==========================================================

st.subheader("Selected models and held-out performance")

performance_rows = []
for bacteria_name, cfg, row in selected_rows:
    test_n = int(row["tn"] + row["fp"] + row["fn"] + row["tp"])
    elevated_n = int(row["fn"] + row["tp"])

    performance_rows.append({
        "Bacterium": bacteria_name,
        "Selected model": cfg["model"],
        "Feature set": cfg["feature_set"],
        "Features": len(cfg["features"]),
        "Classification threshold": float(cfg["locked_threshold"]),
        "Test observations": test_n,
        "Elevated cases": elevated_n,
        "Accuracy": float(row["accuracy"]),
        "Precision": float(row["precision"]),
        "Recall": float(row["recall"]),
        "F1": float(row["f1"]),
        "False negatives": int(row["fn"]),
        "PR-AUC": (
            float(row["pr_auc"])
            if "pr_auc" in row and pd.notna(row["pr_auc"])
            else float("nan")
        ),
        "Brier score": (
            float(row["brier_score"])
            if "brier_score" in row and pd.notna(row["brier_score"])
            else float("nan")
        ),
    })

performance = pd.DataFrame(performance_rows)
if not performance.empty:
    formatted = performance.copy()

    for col in ["Accuracy", "Precision", "Recall", "F1", "PR-AUC"]:
        formatted[col] = formatted[col].map(
            lambda value: f"{value:.1%}" if pd.notna(value) else "—"
        )

    formatted["Brier score"] = formatted["Brier score"].map(
        lambda value: f"{value:.3f}" if pd.notna(value) else "—"
    )
    formatted["Classification threshold"] = formatted[
        "Classification threshold"
    ].map(lambda value: f"{value:.2f}")

    st.dataframe(formatted, use_container_width=True, hide_index=True)

st.caption(
    "These metrics describe retrospective performance on held-out "
    "chronological observations at the pilot site, not verified accuracy "
    "for today's forecast or seven-day predictions. Recall measures "
    "how often elevated events were correctly identified; precision "
    "measures how often predicted elevated events were truly elevated."
)

st.caption(
    "The classification threshold in the model table is the locked "
    "binary decision threshold from the deployed model artifacts. "
    "It is distinct from the three Safe/Caution/Unsafe display bands below."
)


# ==========================================================
# CONCENTRATION THRESHOLDS AND PUBLIC DISPLAY BANDS
# ==========================================================

st.subheader("Model-defined concentration thresholds")
threshold_rows = []

for bacteria_name, cfg, _ in selected_rows:
    threshold_rows.append({
        "Bacterium": bacteria_name,
        "Model-defined exceedance threshold": (
            f"{float(cfg['bacteria_threshold_mpn_100ml']):.0f} MPN/100 mL"
        ),
        "Use in LagoonCast": "Defines the binary training/evaluation label",
    })

if threshold_rows:
    st.dataframe(
        pd.DataFrame(threshold_rows),
        use_container_width=True,
        hide_index=True,
    )

st.warning(
    "The deployed LagoonCast models use research-defined bacterial "
    "concentration thresholds. These are not presented as current "
    "official closure criteria for Parkside Aquatic Park."
)

links_left, links_right = st.columns(2)
with links_left:
    st.link_button(ADVISORY_BUTTON_LABEL, ADVISORY_URL, width="stretch")
with links_right:
    st.link_button(REPORTS_BUTTON_LABEL, OFFICIAL_URL, width="stretch")

st.subheader("Probability display bands")
st.markdown(
    """
These are **display categories applied to model-estimated exceedance
probabilities**, not bacterial concentration standards or probabilities
that swimming is safe.

| Bacterium | Safe | Caution | Unsafe |
|---|---:|---:|---:|
| E. coli | <10% | 10% to <50% | ≥50% |
| Enterococcus | <40% | 40% to <85% | ≥85% |
"""
)
st.caption(
    "The overall risk follows the more severe bacteria-specific "
    "category, not whichever bacterium has the larger percentage. "
    "There is no single combined water-safety probability."
)


# ==========================================================
# INPUT CONSTRUCTION AND DATA SOURCES
# ==========================================================

st.subheader("How live features are constructed")
st.markdown(
    """
- `rain_1day` uses rainfall from the **day before** the target date.
- Multi-day rainfall and temperature windows exclude the target day,
  matching model training.
- Lagged rainfall uses prior days only.
- First-flush and antecedent-dry-period features follow the same
  training definitions.
- Laboratory-history features use only samples dated **strictly
  before** the target date.
- If a required feature cannot be constructed as a finite numeric
  value, the forecast is marked **unavailable** rather than silently
  replacing the missing input with zero.
"""
)

st.subheader("Data sources")
st.markdown(
    """
**Historical bacteria:** California Water Boards / SWAMP records
used in the project dataset.

**Historical training weather:** NOAA / NCEI daily weather records.

**Live and forecast weather:** Open-Meteo daily forecast data.

**Important:** Weather inputs and laboratory observations have
independent update schedules. LagoonCast is not a real-time
bacteria measurement system.
"""
)

with st.expander("View deployed model feature lists"):
    for bacteria_name, cfg, _ in selected_rows:
        st.markdown(f"**{bacteria_name}: {len(cfg['features'])} features**")
        st.code("\n".join(cfg["features"]))


# ==========================================================
# VALIDATION DESIGN AND SAFETY
# ==========================================================

st.subheader("Validation design")
st.markdown(
    """
Model performance is evaluated chronologically: earlier
observations are used for model development and later
observations are held out for final testing. This reduces
the risk of evaluating a model on future observations used
in training.

The results describe historical model evaluation at one
pilot site. They do not establish regulatory approval or
validate every future forecast date.
"""
)

st.caption(PREDICTION_EXPLANATION)
st.caption(OFFICIAL_PRIORITY_NOTICE)

render_footer(
    str(manifest.get("pipeline_version", "Unavailable"))
)
