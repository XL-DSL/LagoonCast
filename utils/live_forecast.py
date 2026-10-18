import json
import math
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import streamlit as st


# ==========================================================
# SCIKIT-LEARN COMPATIBILITY
# ==========================================================

try:
    import sklearn._loss._loss as sklearn_loss_core

    sys.modules.setdefault(
        "_loss",
        sklearn_loss_core,
    )

except Exception:
    pass


# ==========================================================
# PATHS / SITE INFORMATION
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    ROOT
    / "data"
    / "Aquacast15Years_Weekly.csv"
)

MODEL_DIR = (
    ROOT
    / "models"
)

MANIFEST = (
    MODEL_DIR
    / "model_manifest.json"
)


SITE_ID = (
    "parkside_aquatic_park_san_mateo"
)

SITE_NAME = (
    "Parkside Aquatic Park, San Mateo"
)

SITE_LAT = 37.5602
SITE_LON = -122.2910

TIMEZONE = (
    "America/Los_Angeles"
)

APP_MODEL_VERSION = (
    "V2.1-LIVE"
)


# ==========================================================
# BACTERIA THRESHOLDS
# ==========================================================

BACTERIA_LIMITS = {
    "E. coli": 235.0,
    "Enterococcus": 130.0,
}


DISPLAY_THRESHOLDS = {
    "E. coli": {
        "caution": 0.10,
        "unsafe": 0.50,
    },

    "Enterococcus": {
        "caution": 0.40,
        "unsafe": 0.85,
    },
}


DATE_CANDIDATES = [
    "prediction_date",
    "sample_date",
    "date",
    "Date",
    "SampleDate",
    "sample_datetime",
]


ECOLI_VALUE_CANDIDATES = [
    "e_coli",
    "E_coli",
    "ecoli",
    "E. coli",
    "e_coli_result",
    "ecoli_result",
    "ecoli_value",
    "e_coli_value",
]


ENTERO_VALUE_CANDIDATES = [
    "enterococcus",
    "Enterococcus",
    "entero",
    "enterococcus_result",
    "entero_result",
    "enterococcus_value",
    "entero_value",
]


# ==========================================================
# RISK HELPERS
# ==========================================================

def risk_level(
    bacteria,
    probability,
):
    probability = float(
        probability
    )

    thresholds = (
        DISPLAY_THRESHOLDS[
            bacteria
        ]
    )

    if (
        probability
        < thresholds[
            "caution"
        ]
    ):
        return "Safe"

    if (
        probability
        < thresholds[
            "unsafe"
        ]
    ):
        return "Caution"

    return "Unsafe"


def overall_risk(
    e_coli_risk,
    enterococcus_risk,
):
    rank = {
        "Safe": 0,
        "Caution": 1,
        "Unsafe": 2,
    }

    return max(
        [
            e_coli_risk,
            enterococcus_risk,
        ],
        key=lambda value:
            rank[value],
    )


# ==========================================================
# COLUMN HELPERS
# ==========================================================

def _normalized(text):
    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(text).lower(),
    )


def _find_column(
    columns,
    candidates,
):
    columns = list(
        columns
    )

    for candidate in candidates:
        if candidate in columns:
            return candidate

    normalized_lookup = {
        _normalized(column):
            column
        for column in columns
    }

    for candidate in candidates:
        key = _normalized(
            candidate
        )

        if key in normalized_lookup:
            return (
                normalized_lookup[
                    key
                ]
            )

    return None


def _date_column(df):
    column = _find_column(
        df.columns,
        DATE_CANDIDATES,
    )

    if column is None:
        raise RuntimeError(
            "Could not find a date "
            "column in the AquaCast dataset."
        )

    return column


def _bacteria_value_column(
    df,
    bacteria,
):
    candidates = (
        ECOLI_VALUE_CANDIDATES
        if bacteria == "E. coli"
        else ENTERO_VALUE_CANDIDATES
    )

    return _find_column(
        df.columns,
        candidates,
    )


# ==========================================================
# LOAD DATASET
# ==========================================================

@st.cache_data(
    show_spinner=False
)
def _load_dataset():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: "
            f"{DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    date_col = _date_column(
        df
    )

    df[
        date_col
    ] = pd.to_datetime(
        df[
            date_col
        ],
        errors="coerce",
    )

    df = (
        df
        .dropna(
            subset=[
                date_col
            ]
        )
        .sort_values(
            date_col
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ==========================================================
# MODEL MANIFEST
# ==========================================================

@st.cache_data(
    show_spinner=False
)
def _load_manifest():
    if not MANIFEST.exists():
        return {}

    try:
        with MANIFEST.open(
            "r",
            encoding="utf-8",
        ) as handle:

            return json.load(
                handle
            )

    except Exception:
        return {}


def _manifest_bacteria_entry(
    manifest,
    bacteria,
):
    if not isinstance(
        manifest,
        dict,
    ):
        return {}

    target_keys = {
        _normalized(
            bacteria
        ),

        _normalized(
            "ecoli"
            if bacteria
            == "E. coli"
            else "enterococcus"
        ),
    }

    containers = [
        manifest
    ]

    for key in [
        "models",
        "artifacts",
        "bacteria",
        "model_artifacts",
    ]:
        value = manifest.get(
            key
        )

        if isinstance(
            value,
            dict,
        ):
            containers.append(
                value
            )

    for container in containers:
        for key, value in (
            container.items()
        ):

            if (
                _normalized(key)
                in target_keys
            ):

                if isinstance(
                    value,
                    dict,
                ):
                    return value

                if isinstance(
                    value,
                    str,
                ):
                    return {
                        "model_file":
                            value
                    }

    return {}


def _extract_feature_list(
    entry
):
    if not isinstance(
        entry,
        dict,
    ):
        return []

    for key in [
        "features",
        "feature_names",
        "model_features",
        "selected_features",
        "input_features",
    ]:
        value = entry.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return [
                str(item)
                for item
                in value
            ]

    return []


def _extract_model_file(
    entry
):
    if not isinstance(
        entry,
        dict,
    ):
        return None

    for key in [
        "model_file",
        "model_path",
        "artifact",
        "filename",
        "file",
        "path",
    ]:
        value = entry.get(
            key
        )

        if (
            isinstance(
                value,
                str,
            )
            and value.strip()
        ):
            return value.strip()

    return None


def _search_model_file(
    bacteria
):
    if not MODEL_DIR.exists():
        return None

    target_tokens = (
        [
            "ecoli",
            "e_coli",
            "e-coli",
        ]
        if bacteria == "E. coli"
        else [
            "enterococcus",
            "entero",
        ]
    )

    candidates = []

    for path in (
        MODEL_DIR.rglob("*")
    ):
        if not path.is_file():
            continue

        if (
            path.suffix.lower()
            not in {
                ".joblib",
                ".pkl",
                ".pickle",
            }
        ):
            continue

        name = (
            path.name.lower()
        )

        if any(
            token in name
            for token
            in target_tokens
        ):
            candidates.append(
                path
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda path: (
            "model"
            not in path.name.lower(),
            len(
                path.name
            ),
        )
    )

    return candidates[0]


@st.cache_resource(
    show_spinner=False
)
def _load_model_and_features(
    bacteria
):
    manifest = (
        _load_manifest()
    )

    entry = (
        _manifest_bacteria_entry(
            manifest,
            bacteria,
        )
    )

    model_file = (
        _extract_model_file(
            entry
        )
    )

    model_path = None

    if model_file:
        candidate = Path(
            model_file
        )

        if not candidate.is_absolute():
            direct = (
                ROOT
                / candidate
            )

            inside_models = (
                MODEL_DIR
                / candidate
            )

            if direct.exists():
                candidate = direct

            elif (
                inside_models.exists()
            ):
                candidate = (
                    inside_models
                )

        if candidate.exists():
            model_path = candidate

    if model_path is None:
        model_path = (
            _search_model_file(
                bacteria
            )
        )

    if model_path is None:
        raise FileNotFoundError(
            "Could not locate the saved "
            f"{bacteria} model."
        )

    model = joblib.load(
        model_path
    )

    features = (
        _extract_feature_list(
            entry
        )
    )

    if (
        not features
        and hasattr(
            model,
            "feature_names_in_",
        )
    ):
        features = [
            str(value)
            for value
            in model.feature_names_in_
        ]

    if not features:
        raise RuntimeError(
            "Could not determine the "
            "feature order for the "
            f"{bacteria} model."
        )

    return (
        model,
        features,
    )


def _model_version():
    manifest = (
        _load_manifest()
    )

    if isinstance(
        manifest,
        dict,
    ):

        for key in [
            "model_version",
            "version",
            "app_version",
        ]:
            value = manifest.get(
                key
            )

            if value not in [
                None,
                "",
            ]:
                return str(
                    value
                )

    return APP_MODEL_VERSION


# ==========================================================
# OPEN-METEO WEATHER
# ==========================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _fetch_weather():
    params = {
        "latitude":
            SITE_LAT,

        "longitude":
            SITE_LON,

        "daily":
            (
                "precipitation_sum,"
                "temperature_2m_mean"
            ),

        "timezone":
            TIMEZONE,

        # Gives enough history
        # for Recent Trends.
        "past_days":
            45,

        # TODAY + NEXT 7 DAYS
        "forecast_days":
            8,
    }

    url = (
        "https://api.open-meteo.com/"
        "v1/forecast?"
        + urllib.parse.urlencode(
            params
        )
    )

    request = (
        urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "LagoonCast-AquaCast/2.1"
            },
        )
    )

    with urllib.request.urlopen(
        request,
        timeout=15,
    ) as response:

        payload = json.loads(
            response
            .read()
            .decode(
                "utf-8"
            )
        )

    daily = payload.get(
        "daily",
        {},
    )

    dates = daily.get(
        "time",
        [],
    )

    precipitation = daily.get(
        "precipitation_sum",
        [],
    )

    temperature = daily.get(
        "temperature_2m_mean",
        [],
    )

    if not dates:
        raise RuntimeError(
            "Open-Meteo returned no "
            "daily weather data."
        )

    weather = pd.DataFrame(
        {
            "date":
                pd.to_datetime(
                    dates,
                    errors="coerce",
                ),

            "precipitation_sum":
                pd.to_numeric(
                    precipitation,
                    errors="coerce",
                ),

            "temperature_2m_mean":
                pd.to_numeric(
                    temperature,
                    errors="coerce",
                ),
        }
    )

    weather = (
        weather
        .dropna(
            subset=[
                "date"
            ]
        )
        .sort_values(
            "date"
        )
        .set_index(
            "date"
        )
    )

    weather[
        "precipitation_sum"
    ] = (
        weather[
            "precipitation_sum"
        ]
        .fillna(
            0.0
        )
        .clip(
            lower=0.0
        )
    )

    weather[
        "temperature_2m_mean"
    ] = (
        weather[
            "temperature_2m_mean"
        ]
        .interpolate(
            limit_direction="both"
        )
    )

    return weather


# ==========================================================
# WEATHER FEATURE ENGINEERING
# ==========================================================

def _antecedent_dry_days(
    rain_series
):
    values = []
    dry_days = 0

    for rain in (
        rain_series
        .fillna(
            0.0
        )
    ):

        if float(rain) > 0.0:
            values.append(
                float(
                    dry_days
                )
            )

            dry_days = 0

        else:
            dry_days += 1

            values.append(
                float(
                    dry_days
                )
            )

    return pd.Series(
        values,
        index=rain_series.index,
        dtype=float,
    )


def _engineer_weather_features(
    weather
):
    df = weather.copy()

    rain = (
        df[
            "precipitation_sum"
        ]
        .astype(
            float
        )
    )

    temp = (
        df[
            "temperature_2m_mean"
        ]
        .astype(
            float
        )
    )

    df[
        "rain_1day"
    ] = rain

    df[
        "rain_3day_sum"
    ] = rain.rolling(
        3,
        min_periods=1,
    ).sum()

    df[
        "rain_7day_sum"
    ] = rain.rolling(
        7,
        min_periods=1,
    ).sum()

    df[
        "rain_14day_sum"
    ] = rain.rolling(
        14,
        min_periods=1,
    ).sum()

    df[
        "rain_1day_lag1"
    ] = (
        rain.shift(
            1
        )
        .fillna(
            0.0
        )
    )

    df[
        "rain_1day_lag2"
    ] = (
        rain.shift(
            2
        )
        .fillna(
            0.0
        )
    )

    df[
        "rain_lag1"
    ] = df[
        "rain_1day_lag1"
    ]

    df[
        "rain_lag2"
    ] = df[
        "rain_1day_lag2"
    ]

    df[
        "rain_ratio_1to3"
    ] = np.where(
        df[
            "rain_3day_sum"
        ] > 0,

        df[
            "rain_1day"
        ]
        / df[
            "rain_3day_sum"
        ],

        0.0,
    )

    df[
        "rain_3day_max"
    ] = rain.rolling(
        3,
        min_periods=1,
    ).max()

    df[
        "rain_7day_max"
    ] = rain.rolling(
        7,
        min_periods=1,
    ).max()

    df[
        "rain_days_3day"
    ] = (
        rain.gt(
            0
        )
        .astype(
            int
        )
        .rolling(
            3,
            min_periods=1,
        )
        .sum()
    )

    df[
        "rain_days_7day"
    ] = (
        rain.gt(
            0
        )
        .astype(
            int
        )
        .rolling(
            7,
            min_periods=1,
        )
        .sum()
    )

    df[
        "adp_days"
    ] = (
        _antecedent_dry_days(
            rain
        )
    )

    df[
        "first_flush_index"
    ] = (
        df[
            "rain_1day"
        ]
        * df[
            "adp_days"
        ]
    )

    df[
        "temp_1day"
    ] = temp

    df[
        "temp_3day_avg"
    ] = temp.rolling(
        3,
        min_periods=1,
    ).mean()

    df[
        "temp_7day_avg"
    ] = temp.rolling(
        7,
        min_periods=1,
    ).mean()

    df[
        "temp_14day_avg"
    ] = temp.rolling(
        14,
        min_periods=1,
    ).mean()

    df[
        "month"
    ] = (
        df.index.month
        .astype(
            float
        )
    )

    df[
        "day_of_year"
    ] = (
        df.index.dayofyear
        .astype(
            float
        )
    )

    df[
        "dayofyear"
    ] = df[
        "day_of_year"
    ]

    df[
        "month_sin"
    ] = np.sin(
        2
        * np.pi
        * df.index.month
        / 12.0
    )

    df[
        "month_cos"
    ] = np.cos(
        2
        * np.pi
        * df.index.month
        / 12.0
    )

    df[
        "dayofyear_sin"
    ] = np.sin(
        2
        * np.pi
        * df.index.dayofyear
        / 365.25
    )

    df[
        "dayofyear_cos"
    ] = np.cos(
        2
        * np.pi
        * df.index.dayofyear
        / 365.25
    )

    df[
        "wet_season"
    ] = (
        df.index.month
        .isin(
            [
                11,
                12,
                1,
                2,
                3,
            ]
        )
    ).astype(
        float
    )

    df[
        "rain_temp_interaction"
    ] = (
        df[
            "rain_1day"
        ]
        * df[
            "temp_3day_avg"
        ]
    )

    df[
        "rain3_temp_interaction"
    ] = (
        df[
            "rain_3day_sum"
        ]
        * df[
            "temp_3day_avg"
        ]
    )

    return df


# ==========================================================
# HISTORICAL FEATURE HELPERS
# ==========================================================

def _latest_dataset_row(
    dataset,
    target_date,
):
    date_col = (
        _date_column(
            dataset
        )
    )

    target_date = (
        pd.Timestamp(
            target_date
        )
        .normalize()
    )

    prior = dataset[
        dataset[
            date_col
        ]
        .dt.normalize()
        <= target_date
    ]

    if prior.empty:
        prior = dataset

    if prior.empty:
        return pd.Series(
            dtype=float
        )

    return (
        prior.iloc[-1]
    )


def _latest_lab_value(
    dataset,
    bacteria,
    target_date,
):
    date_col = (
        _date_column(
            dataset
        )
    )

    value_col = (
        _bacteria_value_column(
            dataset,
            bacteria,
        )
    )

    if value_col is None:
        return np.nan

    subset = (
        dataset[
            dataset[
                date_col
            ]
            .dt.normalize()
            <= pd.Timestamp(
                target_date
            ).normalize()
        ][
            [
                date_col,
                value_col,
            ]
        ]
        .copy()
    )

    subset[
        value_col
    ] = pd.to_numeric(
        subset[
            value_col
        ],
        errors="coerce",
    )

    subset = subset.dropna(
        subset=[
            value_col
        ]
    )

    if subset.empty:
        return np.nan

    return float(
        subset.iloc[-1][
            value_col
        ]
    )


def _history_feature_values(
    dataset,
    target_date,
):
    ecoli = (
        _latest_lab_value(
            dataset,
            "E. coli",
            target_date,
        )
    )

    entero = (
        _latest_lab_value(
            dataset,
            "Enterococcus",
            target_date,
        )
    )

    ecoli_exceed = (
        float(
            ecoli
            >= BACTERIA_LIMITS[
                "E. coli"
            ]
        )
        if pd.notna(
            ecoli
        )
        else 0.0
    )

    entero_exceed = (
        float(
            entero
            >= BACTERIA_LIMITS[
                "Enterococcus"
            ]
        )
        if pd.notna(
            entero
        )
        else 0.0
    )

    return {
        "previous_e_coli":
            ecoli,

        "previous_ecoli":
            ecoli,

        "prev_e_coli":
            ecoli,

        "prev_ecoli":
            ecoli,

        "lag_e_coli":
            ecoli,

        "lag_ecoli":
            ecoli,

        "e_coli_previous":
            ecoli,

        "ecoli_previous":
            ecoli,

        "previous_enterococcus":
            entero,

        "previous_entero":
            entero,

        "prev_enterococcus":
            entero,

        "prev_entero":
            entero,

        "lag_enterococcus":
            entero,

        "lag_entero":
            entero,

        "enterococcus_previous":
            entero,

        "entero_previous":
            entero,

        "previous_e_coli_exceedance":
            ecoli_exceed,

        "previous_ecoli_exceedance":
            ecoli_exceed,

        "prev_e_coli_exceedance":
            ecoli_exceed,

        "prev_ecoli_exceedance":
            ecoli_exceed,

        "previous_enterococcus_exceedance":
            entero_exceed,

        "previous_entero_exceedance":
            entero_exceed,

        "prev_enterococcus_exceedance":
            entero_exceed,

        "prev_entero_exceedance":
            entero_exceed,
    }


def _safe_numeric(
    value,
    default=0.0,
):
    numeric = pd.to_numeric(
        pd.Series(
            [
                value
            ]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(
        numeric
    ):
        return float(
            default
        )

    return float(
        numeric
    )


def _build_feature_row(
    features,
    target_date,
    weather,
    dataset,
):
    target_date = (
        pd.Timestamp(
            target_date
        )
        .normalize()
    )

    if (
        target_date
        not in weather.index
    ):
        raise RuntimeError(
            "Weather data are unavailable "
            f"for {target_date.date()}."
        )

    weather_row = (
        weather.loc[
            target_date
        ]
    )

    if isinstance(
        weather_row,
        pd.DataFrame,
    ):
        weather_row = (
            weather_row.iloc[-1]
        )

    dataset_row = (
        _latest_dataset_row(
            dataset,
            target_date,
        )
    )

    history = (
        _history_feature_values(
            dataset,
            target_date,
        )
    )

    weather_lookup = {
        _normalized(key):
            value
        for key, value
        in weather_row.items()
    }

    dataset_lookup = {
        _normalized(key):
            value
        for key, value
        in dataset_row.items()
    }

    history_lookup = {
        _normalized(key):
            value
        for key, value
        in history.items()
    }

    row = {}

    for feature in features:
        key = _normalized(
            feature
        )

        if key in weather_lookup:
            value = (
                weather_lookup[
                    key
                ]
            )

        elif key in history_lookup:
            value = (
                history_lookup[
                    key
                ]
            )

        elif key in dataset_lookup:
            value = (
                dataset_lookup[
                    key
                ]
            )

        elif key in {
            "month",
            "monthnum",
        }:
            value = (
                target_date.month
            )

        elif key in {
            "dayofyear",
            "doy",
        }:
            value = (
                target_date.dayofyear
            )

        elif key == "year":
            value = (
                target_date.year
            )

        elif key in {
            "weekofyear",
            "week",
        }:
            value = (
                target_date
                .isocalendar()
                .week
            )

        else:
            value = 0.0

        row[
            feature
        ] = _safe_numeric(
            value,
            default=0.0,
        )

    return pd.DataFrame(
        [
            row
        ],
        columns=features,
    )


# ==========================================================
# MODEL PREDICTION
# ==========================================================

def _positive_probability(
    model,
    X,
):
    if hasattr(
        model,
        "predict_proba",
    ):
        probabilities = np.asarray(
            model.predict_proba(
                X
            )
        )

        if (
            probabilities.ndim
            == 1
        ):
            return float(
                probabilities[
                    0
                ]
            )

        if (
            probabilities.shape[
                1
            ]
            == 1
        ):
            return float(
                probabilities[
                    0,
                    0,
                ]
            )

        positive_index = 1

        classes = getattr(
            model,
            "classes_",
            None,
        )

        if classes is not None:
            classes = list(
                classes
            )

            for candidate in [
                1,
                True,
                "1",
                "Unsafe",
                "Exceedance",
                "exceedance",
            ]:

                if candidate in classes:
                    positive_index = (
                        classes.index(
                            candidate
                        )
                    )

                    break

        return float(
            probabilities[
                0,
                positive_index,
            ]
        )

    if hasattr(
        model,
        "decision_function",
    ):
        score = np.asarray(
            model.decision_function(
                X
            )
        ).reshape(
            -1
        )[0]

        return float(
            1.0
            / (
                1.0
                + math.exp(
                    -float(
                        score
                    )
                )
            )
        )

    prediction = np.asarray(
        model.predict(
            X
        )
    ).reshape(
        -1
    )[0]

    return float(
        np.clip(
            float(
                prediction
            ),
            0.0,
            1.0,
        )
    )


def _predict_bacteria(
    bacteria,
    model,
    features,
    target_date,
    weather,
    dataset,
):
    X = (
        _build_feature_row(
            features,
            target_date,
            weather,
            dataset,
        )
    )

    probability = (
        _positive_probability(
            model,
            X,
        )
    )

    probability = float(
        np.clip(
            probability,
            0.0,
            1.0,
        )
    )

    latest_lab = (
        _latest_lab_value(
            dataset,
            bacteria,
            target_date,
        )
    )

    estimated_history = True

    return (
        probability,
        estimated_history,
        latest_lab,
    )


# ==========================================================
# LIVE OUTLOOK
# ==========================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def load_live_outlook(
    days=3
):
    # Allows:
    # today + next 7 days
    days = max(
        1,
        min(
            int(
                days
            ),
            8,
        ),
    )

    dataset = (
        _load_dataset()
    )

    weather = (
        _engineer_weather_features(
            _fetch_weather()
        )
    )

    (
        ecoli_model,
        ecoli_features,
    ) = (
        _load_model_and_features(
            "E. coli"
        )
    )

    (
        entero_model,
        entero_features,
    ) = (
        _load_model_and_features(
            "Enterococcus"
        )
    )

    today = (
        pd.Timestamp.now(
            tz=TIMEZONE
        )
        .tz_localize(
            None
        )
        .normalize()
    )

    model_version = (
        _model_version()
    )

    rows = []

    for offset in range(
        days
    ):
        target_date = (
            today
            + pd.Timedelta(
                days=offset
            )
        )

        if (
            target_date
            not in weather.index
        ):
            continue

        (
            ecoli_probability,
            _,
            _,
        ) = _predict_bacteria(
            "E. coli",
            ecoli_model,
            ecoli_features,
            target_date,
            weather,
            dataset,
        )

        (
            entero_probability,
            _,
            _,
        ) = _predict_bacteria(
            "Enterococcus",
            entero_model,
            entero_features,
            target_date,
            weather,
            dataset,
        )

        ecoli_risk = (
            risk_level(
                "E. coli",
                ecoli_probability,
            )
        )

        entero_risk = (
            risk_level(
                "Enterococcus",
                entero_probability,
            )
        )

        rows.append(
            {
                "site_id":
                    SITE_ID,

                "site_name":
                    SITE_NAME,

                "latitude":
                    SITE_LAT,

                "longitude":
                    SITE_LON,

                "prediction_date":
                    target_date,

                "data_last_updated":
                    today,

                "e_coli_probability":
                    float(
                        ecoli_probability
                    ),

                "enterococcus_probability":
                    float(
                        entero_probability
                    ),

                "e_coli_risk":
                    ecoli_risk,

                "enterococcus_risk":
                    entero_risk,

                "overall_risk":
                    overall_risk(
                        ecoli_risk,
                        entero_risk,
                    ),

                "model_version":
                    model_version,

                "forecast_source":
                    "Open-Meteo",
            }
        )

    if not rows:
        raise RuntimeError(
            "Live weather forecast returned "
            "no usable forecast dates."
        )

    return (
        pd.DataFrame(
            rows
        )
        .sort_values(
            "prediction_date"
        )
        .reset_index(
            drop=True
        )
    )


# ==========================================================
# TODAY'S LIVE FORECAST
# ==========================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def load_live_latest():
    outlook = (
        load_live_outlook(
            days=1
        )
    )

    if outlook.empty:
        raise RuntimeError(
            "No live AquaCast "
            "prediction is available."
        )

    return (
        outlook
        .iloc[0]
        .copy()
    )


# ==========================================================
# RECENT MODEL ESTIMATES
# ==========================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def load_recent_estimates(
    days=30
):
    days = max(
        7,
        min(
            int(
                days
            ),
            30,
        ),
    )

    dataset = (
        _load_dataset()
    )

    weather = (
        _engineer_weather_features(
            _fetch_weather()
        )
    )

    (
        ecoli_model,
        ecoli_features,
    ) = (
        _load_model_and_features(
            "E. coli"
        )
    )

    (
        entero_model,
        entero_features,
    ) = (
        _load_model_and_features(
            "Enterococcus"
        )
    )

    today = (
        pd.Timestamp.now(
            tz=TIMEZONE
        )
        .tz_localize(
            None
        )
        .normalize()
    )

    start_date = (
        today
        - pd.Timedelta(
            days=days - 1
        )
    )

    rows = []

    for target_date in (
        pd.date_range(
            start_date,
            today,
            freq="D",
        )
    ):

        if (
            target_date
            not in weather.index
        ):
            continue

        try:
            (
                ecoli_probability,
                _,
                _,
            ) = _predict_bacteria(
                "E. coli",
                ecoli_model,
                ecoli_features,
                target_date,
                weather,
                dataset,
            )

            (
                entero_probability,
                _,
                _,
            ) = _predict_bacteria(
                "Enterococcus",
                entero_model,
                entero_features,
                target_date,
                weather,
                dataset,
            )

        except Exception:
            continue

        ecoli_risk = (
            risk_level(
                "E. coli",
                ecoli_probability,
            )
        )

        entero_risk = (
            risk_level(
                "Enterococcus",
                entero_probability,
            )
        )

        rows.append(
            {
                "prediction_date":
                    target_date,

                "e_coli_probability":
                    float(
                        ecoli_probability
                    ),

                "enterococcus_probability":
                    float(
                        entero_probability
                    ),

                "e_coli_risk":
                    ecoli_risk,

                "enterococcus_risk":
                    entero_risk,

                "overall_risk":
                    overall_risk(
                        ecoli_risk,
                        entero_risk,
                    ),
            }
        )

    if not rows:
        raise RuntimeError(
            "No recent trend estimates "
            "could be generated."
        )

    return (
        pd.DataFrame(
            rows
        )
        .sort_values(
            "prediction_date"
        )
        .reset_index(
            drop=True
        )
    )
