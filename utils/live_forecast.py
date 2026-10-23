from __future__ import annotations

import json
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests


# ==========================================================
# SCIKIT-LEARN / JOBLIB COMPATIBILITY
# ==========================================================
#
# Some saved sklearn models reference the compiled _loss
# module directly when unpickled. Keep this compatibility
# alias before importing joblib.
# ==========================================================

try:
    import sklearn._loss._loss as sklearn_loss_core

    sys.modules.setdefault(
        "_loss",
        sklearn_loss_core,
    )

except Exception:
    pass


import joblib


# ==========================================================
# PROJECT CONFIGURATION
# ==========================================================

ROOT_DIR = Path(
    __file__
).resolve().parents[1]


SITE_ID = "aquatic_park_san_mateo"

SITE_NAME = (
    "Parkside Aquatic Park, San Mateo"
)

COUNTY = "San Mateo"

SITE_LAT = 37.5602

SITE_LON = -122.2910

PACIFIC_TIMEZONE = (
    "America/Los_Angeles"
)


# ==========================================================
# MODEL / APP THRESHOLDS
# ==========================================================
#
# These concentration thresholds are model target
# definitions.
#
# Public Safe / Caution / Unsafe probability bands are
# separate from the binary model's locked evaluation
# threshold.
# ==========================================================

BACTERIA_THRESHOLDS = {
    "E. coli": 235.0,
    "Enterococcus": 130.0,
}


APP_THRESHOLDS = {
    "E. coli": {
        "caution": 0.10,
        "unsafe": 0.50,
    },

    "Enterococcus": {
        "caution": 0.40,
        "unsafe": 0.85,
    },
}


RISK_ORDER = {
    "Safe": 0,
    "Caution": 1,
    "Unsafe": 2,
}


RISK_COLORS = {
    "Safe": "green",
    "Caution": "yellow",
    "Unsafe": "red",
}


# ==========================================================
# FILE DISCOVERY
# ==========================================================

def _first_existing_path(
    candidates,
):
    for candidate in candidates:

        path = ROOT_DIR / candidate

        if path.exists():

            return path

    return None


def _require_path(
    candidates,
    description,
):
    path = _first_existing_path(
        candidates
    )

    if path is None:

        checked = "\n".join(
            str(
                ROOT_DIR / candidate
            )
            for candidate
            in candidates
        )

        raise FileNotFoundError(
            f"Could not find {description}.\n"
            f"Checked:\n{checked}"
        )

    return path


# ==========================================================
# MODEL MANIFEST
# ==========================================================

@lru_cache(
    maxsize=1
)
def _load_manifest():
    path = _require_path(
        [
            "model_manifest.json",
            "models/model_manifest.json",
            "data/model_manifest.json",
            "artifacts/model_manifest.json",
        ],
        "model_manifest.json",
    )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as handle:

        manifest = json.load(
            handle
        )

    if (
        "models"
        not in manifest
    ):

        # Support older manifest structure if encountered.
        if (
            "E. coli" in manifest
            and "Enterococcus" in manifest
        ):

            manifest = {
                "pipeline_version":
                    "AquaCast_Model_Pipeline_Version_12",

                "models":
                    manifest,
            }

        else:

            raise ValueError(
                "model_manifest.json does not contain "
                "a valid models section."
            )

    return manifest


# ==========================================================
# MODEL FILE LOCATION
# ==========================================================

def _model_path(
    filename,
):
    candidates = [
        filename,
        f"models/{filename}",
        f"data/{filename}",
        f"artifacts/{filename}",
        (
            "AquaCast_Model_Pipeline_"
            f"Version_12_Outputs/{filename}"
        ),
    ]

    return _require_path(
        candidates,
        filename,
    )


# ==========================================================
# MODEL LOADING
# ==========================================================

@lru_cache(
    maxsize=4
)
def _load_model(
    bacteria,
):
    manifest = _load_manifest()

    model_info = (
        manifest[
            "models"
        ].get(
            bacteria
        )
    )

    if model_info is None:

        raise KeyError(
            f"No model configuration found for {bacteria}."
        )

    model_filename = (
        model_info.get(
            "model_file"
        )
    )

    if not model_filename:

        raise ValueError(
            f"No model_file listed for {bacteria}."
        )

    path = _model_path(
        model_filename
    )

    model = joblib.load(
        path
    )

    return model


# ==========================================================
# FEATURE LISTS
# ==========================================================

@lru_cache(
    maxsize=4
)
def _load_features(
    bacteria,
):
    manifest = _load_manifest()

    model_info = (
        manifest[
            "models"
        ].get(
            bacteria
        )
    )

    if model_info is None:

        raise KeyError(
            f"No model configuration found for {bacteria}."
        )

    features = model_info.get(
        "features"
    )

    if features:

        return [
            str(
                feature
            ).strip()
            for feature
            in features
            if str(
                feature
            ).strip()
        ]

    feature_filename = (
        model_info.get(
            "feature_file"
        )
        or model_info.get(
            "features_file"
        )
    )

    if not feature_filename:

        raise ValueError(
            f"No feature list found for {bacteria}."
        )

    feature_path = _model_path(
        feature_filename
    )

    with open(
        feature_path,
        "r",
        encoding="utf-8",
    ) as handle:

        features = [
            line.strip()
            for line
            in handle.readlines()
            if line.strip()
        ]

    if not features:

        raise ValueError(
            f"Feature list for {bacteria} is empty."
        )

    return features


# ==========================================================
# HISTORICAL LAB DATA
# ==========================================================

@lru_cache(
    maxsize=1
)
def _load_historical_dataset():
    path = _require_path(
        [
            "data/Aquacast15Years_Weekly.csv",
            "Aquacast15Years_Weekly.csv",
            "data/Aquacast15Years.csv",
            "Aquacast15Years.csv",
        ],
        "historical LagoonCast dataset",
    )

    data = pd.read_csv(
        path,
        low_memory=False,
    )

    return data


# ==========================================================
# COLUMN HELPERS
# ==========================================================

def _normalize_name(
    value,
):
    return (
        str(
            value
        )
        .strip()
        .lower()
        .replace(
            " ",
            "",
        )
        .replace(
            "_",
            "",
        )
        .replace(
            ".",
            "",
        )
        .replace(
            "-",
            "",
        )
    )


def _find_column(
    frame,
    candidates,
):
    lookup = {
        _normalize_name(
            column
        ): column
        for column
        in frame.columns
    }

    for candidate in candidates:

        normalized = (
            _normalize_name(
                candidate
            )
        )

        if normalized in lookup:

            return lookup[
                normalized
            ]

    return None


# ==========================================================
# OPEN-METEO LIVE WEATHER
# ==========================================================

def _fetch_open_meteo_weather(
    past_days=60,
    forecast_days=8,
):
    """
    Download daily weather around Parkside Aquatic Park.

    We request enough historical weather to construct all
    14-day Version 12 rolling features and enough forecast
    weather for the seven-day outlook.

    Values requested:
      - daily precipitation
      - daily max temperature
      - daily min temperature

    Daily mean temperature is reconstructed as:
        (max + min) / 2
    """

    url = (
        "https://api.open-meteo.com/"
        "v1/forecast"
    )

    params = {
        "latitude":
            SITE_LAT,

        "longitude":
            SITE_LON,

        "daily":
            (
                "precipitation_sum,"
                "temperature_2m_max,"
                "temperature_2m_min"
            ),

        "timezone":
            PACIFIC_TIMEZONE,

        "past_days":
            int(
                past_days
            ),

        "forecast_days":
            int(
                forecast_days
            ),
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if (
        "daily"
        not in payload
    ):

        raise ValueError(
            "Open-Meteo did not return daily weather data."
        )

    daily = payload[
        "daily"
    ]

    required = [
        "time",
        "precipitation_sum",
        "temperature_2m_max",
        "temperature_2m_min",
    ]

    missing = [
        field
        for field
        in required
        if field not in daily
    ]

    if missing:

        raise ValueError(
            "Open-Meteo response is missing: "
            + ", ".join(
                missing
            )
        )

    frame = pd.DataFrame(
        {
            "date":
                pd.to_datetime(
                    daily[
                        "time"
                    ],
                    errors="coerce",
                ),

            "precipitation_sum":
                pd.to_numeric(
                    daily[
                        "precipitation_sum"
                    ],
                    errors="coerce",
                ),

            "temperature_2m_max":
                pd.to_numeric(
                    daily[
                        "temperature_2m_max"
                    ],
                    errors="coerce",
                ),

            "temperature_2m_min":
                pd.to_numeric(
                    daily[
                        "temperature_2m_min"
                    ],
                    errors="coerce",
                ),
        }
    )

    frame[
        "temperature_2m_mean"
    ] = (
        frame[
            "temperature_2m_max"
        ]
        +
        frame[
            "temperature_2m_min"
        ]
    ) / 2.0

    frame = (
        frame
        .dropna(
            subset=[
                "date"
            ]
        )
        .sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )

    if frame.empty:

        raise ValueError(
            "Open-Meteo returned no usable weather rows."
        )

    return frame


# ==========================================================
# TRAINING-ALIGNED WEATHER FEATURES
# ==========================================================

def _prepare_training_aligned_weather(
    weather,
):
    """
    Reproduce the Version 12 weather-feature definitions.

    For target date t:

      rain_1day      = rainfall on t-1
      rain_1day_lag1 = rainfall on t-2
      rain_1day_lag2 = rainfall on t-3

    Rolling rainfall and temperature windows are also
    shifted one day so target-day weather is excluded.

    This is deliberately different from calculating a
    rolling window directly through target date t.
    """

    if weather is None:

        raise ValueError(
            "Weather data are unavailable."
        )

    daily = weather.copy()

    if isinstance(
        daily.index,
        pd.DatetimeIndex,
    ):

        daily = (
            daily
            .reset_index()
        )

    date_col = _find_column(
        daily,
        [
            "date",
            "prediction_date",
            "sample_date",
            "time",
        ],
    )

    if date_col is None:

        raise ValueError(
            "Weather data do not contain a usable "
            "date column."
        )

    daily[
        "_weather_date"
    ] = (
        pd.to_datetime(
            daily[
                date_col
            ],
            errors="coerce",
        )
        .dt.normalize()
    )

    daily = (
        daily
        .dropna(
            subset=[
                "_weather_date"
            ]
        )
        .sort_values(
            "_weather_date"
        )
        .drop_duplicates(
            "_weather_date",
            keep="last",
        )
    )

    rain_col = _find_column(
        daily,
        [
            "precipitation_sum",
            "precipitation",
            "prcp_mm",
            "rain_mm",
            "rain",
            "prcp",
        ],
    )

    if rain_col is None:

        raise ValueError(
            "Weather data do not contain daily "
            "precipitation."
        )

    temp_col = _find_column(
        daily,
        [
            "temperature_2m_mean",
            "temperature_mean",
            "tavg_c",
            "temp_c",
            "temperature",
            "tavg",
        ],
    )

    if temp_col is not None:

        daily[
            "_temp_c"
        ] = pd.to_numeric(
            daily[
                temp_col
            ],
            errors="coerce",
        )

    else:

        tmax_col = _find_column(
            daily,
            [
                "temperature_2m_max",
                "tmax_c",
                "tmax",
            ],
        )

        tmin_col = _find_column(
            daily,
            [
                "temperature_2m_min",
                "tmin_c",
                "tmin",
            ],
        )

        if (
            tmax_col is None
            or tmin_col is None
        ):

            raise ValueError(
                "Weather data do not contain enough "
                "temperature information."
            )

        daily[
            "_temp_c"
        ] = (
            pd.to_numeric(
                daily[
                    tmax_col
                ],
                errors="coerce",
            )
            +
            pd.to_numeric(
                daily[
                    tmin_col
                ],
                errors="coerce",
            )
        ) / 2.0

    daily[
        "_prcp_mm"
    ] = pd.to_numeric(
        daily[
            rain_col
        ],
        errors="coerce",
    )

    daily = (
        daily[
            [
                "_weather_date",
                "_prcp_mm",
                "_temp_c",
            ]
        ]
        .set_index(
            "_weather_date"
        )
        .sort_index()
    )

    if daily.empty:

        raise ValueError(
            "Weather data contain no usable daily records."
        )

    full_index = pd.date_range(
        daily.index.min(),
        daily.index.max(),
        freq="D",
    )

    daily = daily.reindex(
        full_index
    )

    daily.index.name = (
        "prediction_date"
    )

    pr = daily[
        "_prcp_mm"
    ]

    temp = daily[
        "_temp_c"
    ]

    # ======================================================
    # EXACT VERSION 12 RAINFALL TIMING
    # ======================================================

    daily[
        "rain_1day"
    ] = pr.shift(
        1
    )

    daily[
        "rain_1day_lag1"
    ] = pr.shift(
        2
    )

    daily[
        "rain_1day_lag2"
    ] = pr.shift(
        3
    )

    # ======================================================
    # EXACT VERSION 12 ROLLING WINDOWS
    # ======================================================

    for window in [
        3,
        7,
        14,
    ]:

        daily[
            f"rain_{window}day_sum"
        ] = (
            pr
            .rolling(
                window,
                min_periods=window,
            )
            .sum()
            .shift(
                1
            )
        )

        daily[
            f"rain_{window}day_avg"
        ] = (
            pr
            .rolling(
                window,
                min_periods=window,
            )
            .mean()
            .shift(
                1
            )
        )

        daily[
            f"rain_{window}day_max"
        ] = (
            pr
            .rolling(
                window,
                min_periods=window,
            )
            .max()
            .shift(
                1
            )
        )

        daily[
            f"rain_{window}day_rainy_days"
        ] = (
            (
                pr > 0
            )
            .astype(
                float
            )
            .rolling(
                window,
                min_periods=window,
            )
            .sum()
            .shift(
                1
            )
        )

        daily[
            f"rain_intensity_{window}day"
        ] = (
            daily[
                f"rain_{window}day_sum"
            ]
            /
            (
                daily[
                    f"rain_{window}day_rainy_days"
                ]
                + 1e-6
            )
        )

        minimum_periods = max(
            2,
            window // 2,
        )

        daily[
            f"temp_{window}day_avg"
        ] = (
            temp
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .mean()
            .shift(
                1
            )
        )

        daily[
            f"temp_{window}day_min"
        ] = (
            temp
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .min()
            .shift(
                1
            )
        )

        daily[
            f"temp_{window}day_max"
        ] = (
            temp
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .max()
            .shift(
                1
            )
        )

    # ======================================================
    # WET-SEASON INDICATOR
    # ======================================================

    daily[
        "season_wet"
    ] = [
        1
        if date_value.month
        in [
            11,
            12,
            1,
            2,
            3,
        ]
        else 0
        for date_value
        in daily.index
    ]

    # ======================================================
    # ANTECEDENT DRY PERIOD
    #
    # This reproduces the Version 12 loop.
    # ======================================================

    adp_values = []

    dry_count = 0

    for precipitation in pr.values:

        adp_values.append(
            dry_count
        )

        if pd.isna(
            precipitation
        ):

            dry_count = 0

        elif precipitation > 0:

            dry_count = 0

        else:

            dry_count += 1

    daily[
        "adp_days"
    ] = adp_values

    # ======================================================
    # DERIVED WEATHER FEATURES
    # ======================================================

    daily[
        "rain_ratio_1to3"
    ] = (
        daily[
            "rain_1day"
        ]
        /
        (
            daily[
                "rain_3day_sum"
            ]
            + 1e-6
        )
    )

    daily[
        "first_flush_index"
    ] = (
        daily[
            "rain_1day"
        ]
        *
        daily[
            "adp_days"
        ]
    )

    daily[
        "wet_season_rain_1day"
    ] = (
        daily[
            "season_wet"
        ]
        *
        daily[
            "rain_1day"
        ]
    )

    daily[
        "wet_season_rain_3day_sum"
    ] = (
        daily[
            "season_wet"
        ]
        *
        daily[
            "rain_3day_sum"
        ]
    )

    daily[
        "wet_season_rain_7day_sum"
    ] = (
        daily[
            "season_wet"
        ]
        *
        daily[
            "rain_7day_sum"
        ]
    )

    daily[
        "rain_temp_interaction_1day"
    ] = (
        daily[
            "rain_1day"
        ]
        *
        daily[
            "temp_3day_avg"
        ]
    )

    daily[
        "rain_temp_interaction_3day"
    ] = (
        daily[
            "rain_3day_sum"
        ]
        *
        daily[
            "temp_3day_avg"
        ]
    )

    return daily


# ==========================================================
# LABORATORY HISTORY
# ==========================================================

def _prepare_lab_history(
    dataset,
    bacteria,
    target_date,
):
    """
    Return actual laboratory measurements available strictly
    BEFORE target_date.

    Same-day measurements are intentionally excluded so a
    reconstructed estimate cannot use information that would
    not have been available before that prediction date.
    """

    if dataset is None:

        return pd.DataFrame()

    data = dataset.copy()

    date_col = _find_column(
        data,
        [
            "sample_date",
            "sampledate",
            "prediction_date",
            "date",
        ],
    )

    bacteria_col = _find_column(
        data,
        [
            "indicator_clean",
            "analyte",
            "bacteria",
            "organism",
        ],
    )

    result_col = _find_column(
        data,
        [
            "result_value",
            "result",
            "value",
        ],
    )

    if (
        date_col is None
        or bacteria_col is None
        or result_col is None
    ):

        raise ValueError(
            "Historical dataset does not contain the "
            "required laboratory columns."
        )

    data[
        "_sample_date"
    ] = (
        pd.to_datetime(
            data[
                date_col
            ],
            errors="coerce",
        )
        .dt.normalize()
    )

    data[
        "_result"
    ] = pd.to_numeric(
        data[
            result_col
        ],
        errors="coerce",
    )

    normalized_bacteria = (
        data[
            bacteria_col
        ]
        .astype(
            str
        )
        .str.strip()
        .str.lower()
    )

    if bacteria == "E. coli":

        bacteria_mask = (
            normalized_bacteria.isin(
                [
                    "e. coli",
                    "e coli",
                    "ecoli",
                    "e_coli",
                ]
            )
        )

    elif bacteria == "Enterococcus":

        bacteria_mask = (
            normalized_bacteria.isin(
                [
                    "enterococcus",
                    "enterococci",
                ]
            )
        )

    else:

        raise ValueError(
            f"Unsupported bacteria: {bacteria}"
        )

    target = pd.Timestamp(
        target_date
    ).normalize()

    history = data[
        bacteria_mask
        &
        (
            data[
                "_sample_date"
            ]
            < target
        )
    ].copy()

    history = (
        history
        .dropna(
            subset=[
                "_sample_date",
                "_result",
            ]
        )
        .sort_values(
            [
                "_sample_date",
                "_result",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return history


# ==========================================================
# LAB HISTORY FEATURES
# ==========================================================

def _history_feature_values(
    dataset,
    bacteria,
    target_date,
):
    history = _prepare_lab_history(
        dataset,
        bacteria,
        target_date,
    )

    threshold = BACTERIA_THRESHOLDS[
        bacteria
    ]

    result = {
        "prev_result_value":
            np.nan,

        "prev_exceedance":
            np.nan,

        "prev_result_to_threshold_ratio":
            np.nan,

        "prev3_result_mean":
            np.nan,

        "prev5_result_mean":
            np.nan,

        "prev3_exceedance_rate":
            np.nan,

        "prev5_exceedance_rate":
            np.nan,

        "prev3_result_to_threshold_ratio_mean":
            np.nan,

        "prev5_result_to_threshold_ratio_mean":
            np.nan,

        "days_since_prev_sample":
            np.nan,
    }

    if history.empty:

        return result

    values = (
        history[
            "_result"
        ]
        .astype(
            float
        )
    )

    exceedance = (
        values
        >= threshold
    ).astype(
        float
    )

    ratios = (
        values
        / threshold
    )

    result[
        "prev_result_value"
    ] = float(
        values.iloc[
            -1
        ]
    )

    result[
        "prev_exceedance"
    ] = float(
        exceedance.iloc[
            -1
        ]
    )

    result[
        "prev_result_to_threshold_ratio"
    ] = float(
        ratios.iloc[
            -1
        ]
    )

    latest_date = history[
        "_sample_date"
    ].iloc[
        -1
    ]

    result[
        "days_since_prev_sample"
    ] = float(
        (
            pd.Timestamp(
                target_date
            ).normalize()
            - latest_date
        ).days
    )

    if len(
        history
    ) >= 3:

        result[
            "prev3_result_mean"
        ] = float(
            values.tail(
                3
            ).mean()
        )

        result[
            "prev3_exceedance_rate"
        ] = float(
            exceedance.tail(
                3
            ).mean()
        )

        result[
            "prev3_result_to_threshold_ratio_mean"
        ] = float(
            ratios.tail(
                3
            ).mean()
        )

    if len(
        history
    ) >= 5:

        result[
            "prev5_result_mean"
        ] = float(
            values.tail(
                5
            ).mean()
        )

        result[
            "prev5_exceedance_rate"
        ] = float(
            exceedance.tail(
                5
            ).mean()
        )

        result[
            "prev5_result_to_threshold_ratio_mean"
        ] = float(
            ratios.tail(
                5
            ).mean()
        )

    return result


def _latest_lab_value(
    dataset,
    bacteria,
    target_date,
):
    history = _prepare_lab_history(
        dataset,
        bacteria,
        target_date,
    )

    if history.empty:

        return np.nan

    return float(
        history[
            "_result"
        ].iloc[
            -1
        ]
    )


def _latest_lab_date(
    dataset,
    bacteria,
    target_date,
):
    history = _prepare_lab_history(
        dataset,
        bacteria,
        target_date,
    )

    if history.empty:

        return pd.NaT

    return history[
        "_sample_date"
    ].iloc[
        -1
    ]


# ==========================================================
# BUILD MODEL INPUT ROW
# ==========================================================

def _build_feature_row(
    features,
    target_date,
    weather,
    dataset,
    bacteria,
):
    """
    Construct one model input row.

    Critical Version 12 rule:
    all weather inputs stop at t-1.
    """

    target = pd.Timestamp(
        target_date
    ).normalize()

    training_weather = (
        _prepare_training_aligned_weather(
            weather
        )
    )

    if target not in training_weather.index:

        raise ValueError(
            "Weather data do not cover prediction date "
            f"{target.date()}."
        )

    weather_row = (
        training_weather.loc[
            target
        ]
    )

    history_values = (
        _history_feature_values(
            dataset,
            bacteria,
            target,
        )
    )

    values = {}

    missing_features = []

    for feature in features:

        if feature in weather_row.index:

            value = weather_row[
                feature
            ]

        elif feature in history_values:

            value = history_values[
                feature
            ]

        else:

            value = np.nan

        numeric_value = pd.to_numeric(
            pd.Series(
                [
                    value
                ]
            ),
            errors="coerce",
        ).iloc[
            0
        ]

        if (
            pd.isna(
                numeric_value
            )
            or not np.isfinite(
                float(
                    numeric_value
                )
            )
        ):

            missing_features.append(
                feature
            )

        else:

            values[
                feature
            ] = float(
                numeric_value
            )

    # ======================================================
    # DO NOT SILENTLY SUBSTITUTE ZERO
    # ======================================================

    if missing_features:

        raise ValueError(
            "Cannot generate a training-consistent "
            f"{bacteria} forecast for "
            f"{target.date()}. Missing or invalid "
            "required features: "
            + ", ".join(
                missing_features
            )
        )

    return pd.DataFrame(
        [
            values
        ],
        columns=features,
    )


# ==========================================================
# MODEL PROBABILITY
# ==========================================================

def _positive_probability(
    model,
    X,
):
    if hasattr(
        model,
        "predict_proba",
    ):

        probabilities = (
            model.predict_proba(
                X
            )
        )

        if probabilities.ndim != 2:

            raise ValueError(
                "Model predict_proba returned "
                "an unexpected shape."
            )

        classes = getattr(
            model,
            "classes_",
            None,
        )

        if classes is not None:

            classes = list(
                classes
            )

            if 1 in classes:

                positive_index = (
                    classes.index(
                        1
                    )
                )

                return float(
                    probabilities[
                        0,
                        positive_index,
                    ]
                )

        if (
            probabilities.shape[
                1
            ]
            >= 2
        ):

            return float(
                probabilities[
                    0,
                    1,
                ]
            )

        return float(
            probabilities[
                0,
                0,
            ]
        )

    if hasattr(
        model,
        "decision_function",
    ):

        decision = np.asarray(
            model.decision_function(
                X
            )
        ).reshape(
            -1
        )[0]

        return float(
            1.0
            /
            (
                1.0
                + np.exp(
                    -decision
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
        prediction
    )


# ==========================================================
# PREDICT ONE BACTERIUM
# ==========================================================

def _predict_bacteria(
    bacteria,
    model,
    features,
    target_date,
    weather,
    dataset,
):
    X = _build_feature_row(
        features=features,
        target_date=target_date,
        weather=weather,
        dataset=dataset,
        bacteria=bacteria,
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

    latest_lab = _latest_lab_value(
        dataset,
        bacteria,
        target_date,
    )

    latest_lab_date = (
        _latest_lab_date(
            dataset,
            bacteria,
            target_date,
        )
    )

    return (
        probability,
        latest_lab,
        latest_lab_date,
    )


# ==========================================================
# APP RISK CLASSIFICATION
# ==========================================================

def _risk_level(
    bacteria,
    probability,
):
    thresholds = APP_THRESHOLDS[
        bacteria
    ]

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


def _overall_risk(
    e_coli_risk,
    enterococcus_risk,
):
    return max(
        [
            e_coli_risk,
            enterococcus_risk,
        ],
        key=lambda value:
            RISK_ORDER.get(
                value,
                -1,
            ),
    )


def _safety_message(
    risk,
):
    if risk == "Unsafe":

        return (
            "The model predicts elevated bacterial risk. "
            "Avoid water contact and follow official "
            "San Mateo County guidance."
        )

    if risk == "Caution":

        return (
            "The model predicts moderate or uncertain "
            "bacterial risk. Check official San Mateo "
            "County information before entering the water."
        )

    return (
        "The model currently predicts a low likelihood "
        "of elevated bacterial risk. Always check official "
        "San Mateo County information before entering "
        "the water."
    )


# ==========================================================
# MODEL VERSION
# ==========================================================

def _model_version():
    manifest = _load_manifest()

    return str(
        manifest.get(
            "pipeline_version",
            "v12",
        )
    )


# ==========================================================
# CURRENT PACIFIC TIME
# ==========================================================

def _pacific_now():
    return datetime.now(
        ZoneInfo(
            PACIFIC_TIMEZONE
        )
    )


def _pacific_today():
    return pd.Timestamp(
        _pacific_now().date()
    )


# ==========================================================
# CREATE ONE OUTPUT ROW
# ==========================================================

def _generate_prediction_row(
    target_date,
    weather,
    dataset,
):
    target = pd.Timestamp(
        target_date
    ).normalize()

    e_coli_model = _load_model(
        "E. coli"
    )

    enterococcus_model = _load_model(
        "Enterococcus"
    )

    e_coli_features = _load_features(
        "E. coli"
    )

    enterococcus_features = _load_features(
        "Enterococcus"
    )

    (
        e_coli_probability,
        e_coli_latest_lab,
        e_coli_latest_lab_date,
    ) = _predict_bacteria(
        bacteria="E. coli",
        model=e_coli_model,
        features=e_coli_features,
        target_date=target,
        weather=weather,
        dataset=dataset,
    )

    (
        enterococcus_probability,
        enterococcus_latest_lab,
        enterococcus_latest_lab_date,
    ) = _predict_bacteria(
        bacteria="Enterococcus",
        model=enterococcus_model,
        features=enterococcus_features,
        target_date=target,
        weather=weather,
        dataset=dataset,
    )

    e_coli_risk = _risk_level(
        "E. coli",
        e_coli_probability,
    )

    enterococcus_risk = _risk_level(
        "Enterococcus",
        enterococcus_probability,
    )

    overall_risk = _overall_risk(
        e_coli_risk,
        enterococcus_risk,
    )

    generation_time = (
        _pacific_now()
    )

    # Weather predictors for target t end at t-1.
    latest_weather_input_date = (
        target
        - pd.Timedelta(
            days=1
        )
    )

    lab_dates = [
        value
        for value
        in [
            e_coli_latest_lab_date,
            enterococcus_latest_lab_date,
        ]
        if pd.notna(
            value
        )
    ]

    latest_lab_date = (
        max(
            lab_dates
        )
        if lab_dates
        else pd.NaT
    )

    row = {
        "site_id":
            SITE_ID,

        "site_name":
            SITE_NAME,

        "county":
            COUNTY,

        "latitude":
            SITE_LAT,

        "longitude":
            SITE_LON,

        "prediction_date":
            target,

        "data_last_updated":
            generation_time.isoformat(),

        "e_coli_probability":
            e_coli_probability,

        "enterococcus_probability":
            enterococcus_probability,

        "e_coli_risk":
            e_coli_risk,

        "enterococcus_risk":
            enterococcus_risk,

        "overall_risk":
            overall_risk,

        "risk_color":
            RISK_COLORS[
                overall_risk
            ],

        "safety_message":
            _safety_message(
                overall_risk
            ),

        "model_version":
            _model_version(),

        "source_dataset":
            (
                "California Water Boards/SWAMP "
                "laboratory observations + "
                "Open-Meteo weather"
            ),

        # Latest actual lab observation available before
        # target date.
        "source_record_date":
            (
                latest_lab_date
                if pd.notna(
                    latest_lab_date
                )
                else pd.NaT
            ),

        # Latest environmental date used in the weather
        # feature windows.
        "input_data_end_date":
            latest_weather_input_date,

        # This is when LIVE inference happened.
        "model_run_timestamp":
            generation_time.isoformat(),

        "data_quality_status":
            "Valid",

        "notes":
            (
                "Live weather-based experimental forecast. "
                "Weather features follow Version 12 "
                "training-date definitions."
            ),

        # Extra transparency fields. Existing pages can
        # ignore them safely.
        "latest_lab_sample_date":
            (
                latest_lab_date
                if pd.notna(
                    latest_lab_date
                )
                else pd.NaT
            ),

        "e_coli_latest_lab_date":
            (
                e_coli_latest_lab_date
                if pd.notna(
                    e_coli_latest_lab_date
                )
                else pd.NaT
            ),

        "enterococcus_latest_lab_date":
            (
                enterococcus_latest_lab_date
                if pd.notna(
                    enterococcus_latest_lab_date
                )
                else pd.NaT
            ),

        "e_coli_latest_lab_value":
            e_coli_latest_lab,

        "enterococcus_latest_lab_value":
            enterococcus_latest_lab,
    }

    return row


# ==========================================================
# LIVE OUTLOOK
# ==========================================================

def load_live_outlook(
    days=8,
):
    """
    Generate today's forecast plus future forecast dates.

    days=8 gives:
        today
        + next 7 days

    Prediction date t always uses weather through t-1.
    Therefore target-day weather is excluded exactly as in
    Version 12 training.
    """

    days = int(
        days
    )

    if days < 1:

        raise ValueError(
            "days must be at least 1."
        )

    # Need weather through the day before the furthest
    # prediction date.
    forecast_days = max(
        days,
        8,
    )

    weather = _fetch_open_meteo_weather(
        past_days=60,
        forecast_days=forecast_days,
    )

    dataset = _load_historical_dataset()

    today = _pacific_today()

    rows = []

    for offset in range(
        days
    ):

        target = (
            today
            + pd.Timedelta(
                days=offset
            )
        )

        rows.append(
            _generate_prediction_row(
                target_date=target,
                weather=weather,
                dataset=dataset,
            )
        )

    result = pd.DataFrame(
        rows
    )

    result[
        "prediction_date"
    ] = pd.to_datetime(
        result[
            "prediction_date"
        ],
        errors="coerce",
    )

    return (
        result
        .sort_values(
            "prediction_date"
        )
        .reset_index(
            drop=True
        )
    )


# ==========================================================
# CURRENT LIVE FORECAST
# ==========================================================

def load_live_latest():
    """
    Generate the current day's live LagoonCast forecast.
    """

    outlook = load_live_outlook(
        days=1
    )

    if outlook.empty:

        raise ValueError(
            "Live forecast returned no rows."
        )

    return outlook.iloc[
        0
    ].copy()


# ==========================================================
# RECENT RECONSTRUCTED ESTIMATES
# ==========================================================

def load_recent_estimates(
    days=14,
):
    """
    Reconstruct model estimates for recent PRIOR dates.

    These are NOT saved forecasts.

    Each historical target date:
      - uses weather only through t-1
      - uses laboratory observations strictly before t

    The returned series ends yesterday so the current day is
    reserved for the genuine live forecast.
    """

    days = int(
        days
    )

    if days < 1:

        raise ValueError(
            "days must be at least 1."
        )

    # Need up to 14 prior days for the earliest requested
    # estimate, plus a safety margin.
    required_past_days = max(
        60,
        days + 20,
    )

    weather = _fetch_open_meteo_weather(
        past_days=required_past_days,
        forecast_days=8,
    )

    dataset = _load_historical_dataset()

    today = _pacific_today()

    start_date = (
        today
        - pd.Timedelta(
            days=days
        )
    )

    end_date = (
        today
        - pd.Timedelta(
            days=1
        )
    )

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D",
    )

    rows = []

    for target in dates:

        row = _generate_prediction_row(
            target_date=target,
            weather=weather,
            dataset=dataset,
        )

        row[
            "estimate_type"
        ] = (
            "Reconstructed model estimate"
        )

        row[
            "is_reconstructed"
        ] = True

        row[
            "notes"
        ] = (
            "Reconstructed historical model estimate. "
            "Not a saved historical forecast and not a "
            "laboratory measurement."
        )

        rows.append(
            row
        )

    result = pd.DataFrame(
        rows
    )

    if result.empty:

        return result

    result[
        "prediction_date"
    ] = pd.to_datetime(
        result[
            "prediction_date"
        ],
        errors="coerce",
    )

    return (
        result
        .sort_values(
            "prediction_date"
        )
        .reset_index(
            drop=True
        )
    )


# ==========================================================
# OPTIONAL DEBUG / QA HELPER
# ==========================================================

def build_feature_snapshot(
    bacteria,
    target_date=None,
):
    """
    QA helper for checking the exact feature row that will
    be sent into one deployed model.

    This is useful for unit tests and for verifying that:
      rain_1day      = t-1
      rain_1day_lag1 = t-2
      rain_1day_lag2 = t-3

    It is not used by the public interface.
    """

    if target_date is None:

        target_date = _pacific_today()

    weather = _fetch_open_meteo_weather(
        past_days=60,
        forecast_days=8,
    )

    dataset = _load_historical_dataset()

    features = _load_features(
        bacteria
    )

    return _build_feature_row(
        features=features,
        target_date=target_date,
        weather=weather,
        dataset=dataset,
        bacteria=bacteria,
    )
