from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
import requests


# ============================================================
# LagoonCast live forecasting
#
# This file intentionally preserves the public functions used
# by the existing pages:
#   - load_live_latest()
#   - load_live_outlook(days=7)
#   - load_recent_estimates(days=7)
#   - build_feature_snapshot(...)
#
# Priority-1 fixes are limited to:
#   1) training-consistent weather timing
#   2) explicit required-feature validation
#   3) prior-only lab history for reconstructed dates
#   4) separate input-freshness metadata
#
# It does NOT redesign pages or impose a 14-day history limit.
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
PACIFIC = ZoneInfo("America/Los_Angeles")

SITE_ID = "aquatic_park_san_mateo"
SITE_NAME = "Parkside Aquatic Park, San Mateo"
COUNTY = "San Mateo"
SITE_LAT = 37.5602
SITE_LON = -122.2910

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

DISPLAY_THRESHOLDS = {
    "E. coli": {
        "safe_max": 0.10,
        "unsafe_min": 0.50,
    },
    "Enterococcus": {
        "safe_max": 0.40,
        "unsafe_min": 0.85,
    },
}

RISK_ORDER = {
    "Safe": 0,
    "Caution": 1,
    "Unsafe": 2,
}


class ForecastUnavailableError(RuntimeError):
    """Raised when a valid forecast cannot be constructed."""


class FeatureConstructionError(ForecastUnavailableError):
    """Raised when required model inputs cannot be constructed."""


def _find_file(filename: str) -> Path:
    candidates = [
        ROOT / filename,
        ROOT / "data" / filename,
        ROOT / "models" / filename,
        ROOT / "artifacts" / filename,
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"Required LagoonCast file not found: {filename}. "
        f"Checked: {[str(p) for p in candidates]}"
    )


@lru_cache(maxsize=1)
def load_model_manifest() -> dict[str, Any]:
    path = _find_file("model_manifest.json")
    manifest = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if "models" not in manifest:
        raise ForecastUnavailableError(
            "model_manifest.json has no 'models' section."
        )

    for bacteria_name in [
        "E. coli",
        "Enterococcus",
    ]:
        if bacteria_name not in manifest["models"]:
            raise ForecastUnavailableError(
                f"model_manifest.json is missing {bacteria_name}."
            )

        config = manifest["models"][bacteria_name]

        required = [
            "model",
            "features",
            "model_file",
            "locked_threshold",
            "bacteria_threshold_mpn_100ml",
        ]

        missing = [
            key
            for key in required
            if key not in config
        ]

        if missing:
            raise ForecastUnavailableError(
                f"{bacteria_name} manifest entry is missing: {missing}"
            )

    return manifest


@lru_cache(maxsize=2)
def _load_model(
    bacteria_name: str,
):
    manifest = load_model_manifest()
    config = manifest["models"][bacteria_name]

    model_path = _find_file(
        config["model_file"]
    )

    return joblib.load(
        model_path
    )


def _normalize_indicator(
    value: Any,
) -> str:
    text = str(
        value
    ).strip().lower()

    if text in {
        "e. coli",
        "e coli",
        "ecoli",
        "e_coli",
    }:
        return "E. coli"

    if text in {
        "enterococcus",
        "enterococci",
    }:
        return "Enterococcus"

    return str(
        value
    ).strip()


def _history_candidates() -> list[Path]:
    return [
        ROOT / "data" / "lagooncast_lab_history.csv",
        ROOT / "lagooncast_lab_history.csv",
        ROOT / "data" / "Aquacast15Years_Weekly.csv",
        ROOT / "Aquacast15Years_Weekly.csv",
        ROOT / "data" / "Aquacast15Years_enhanced_no_tides.csv",
        ROOT / "Aquacast15Years_enhanced_no_tides.csv",
    ]


@lru_cache(maxsize=1)
def load_lab_history() -> pd.DataFrame:
    path = next(
        (
            candidate
            for candidate in _history_candidates()
            if candidate.exists()
        ),
        None,
    )

    if path is None:
        raise ForecastUnavailableError(
            "No laboratory-history file is available."
        )

    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    if (
        "sample_date" not in frame.columns
        and "sampledate" in frame.columns
    ):
        frame["sample_date"] = frame["sampledate"]

    if (
        "indicator_clean" not in frame.columns
        and "analyte" in frame.columns
    ):
        frame["indicator_clean"] = frame["analyte"]

    if (
        "indicator_clean" not in frame.columns
        and "indicator" in frame.columns
    ):
        frame["indicator_clean"] = frame["indicator"]

    if (
        "result_value" not in frame.columns
        and "result" in frame.columns
    ):
        frame["result_value"] = frame["result"]

    required = [
        "sample_date",
        "indicator_clean",
        "result_value",
    ]

    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing:
        raise ForecastUnavailableError(
            "Laboratory-history file is missing "
            f"required columns: {missing}"
        )

    history = frame[
        required
    ].copy()

    history[
        "sample_date"
    ] = pd.to_datetime(
        history["sample_date"],
        errors="coerce",
    ).dt.normalize()

    history[
        "indicator_clean"
    ] = history[
        "indicator_clean"
    ].map(
        _normalize_indicator
    )

    history[
        "result_value"
    ] = pd.to_numeric(
        history["result_value"],
        errors="coerce",
    )

    history = (
        history[
            history["indicator_clean"].isin(
                [
                    "E. coli",
                    "Enterococcus",
                ]
            )
        ]
        .dropna(
            subset=required
        )
        .sort_values(
            [
                "indicator_clean",
                "sample_date",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    if history.empty:
        raise ForecastUnavailableError(
            "Laboratory-history file has no usable rows."
        )

    return history


def _fetch_open_meteo_weather(
    *,
    past_days: int = 30,
    forecast_days: int = 8,
    timeout: int = 20,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    params = {
        "latitude": SITE_LAT,
        "longitude": SITE_LON,
        "daily": ",".join(
            [
                "precipitation_sum",
                "temperature_2m_max",
                "temperature_2m_min",
            ]
        ),
        "timezone": "America/Los_Angeles",
        "past_days": int(
            past_days
        ),
        "forecast_days": int(
            forecast_days
        ),
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()

    except Exception as exc:
        raise ForecastUnavailableError(
            f"Open-Meteo weather request failed: {exc}"
        ) from exc

    daily = payload.get(
        "daily"
    )

    if not daily:
        raise ForecastUnavailableError(
            "Open-Meteo returned no daily weather data."
        )

    required = [
        "time",
        "precipitation_sum",
        "temperature_2m_max",
        "temperature_2m_min",
    ]

    missing = [
        field
        for field in required
        if field not in daily
    ]

    if missing:
        raise ForecastUnavailableError(
            f"Open-Meteo is missing fields: {missing}"
        )

    weather = pd.DataFrame(
        {
            "date": pd.to_datetime(
                daily["time"],
                errors="coerce",
            ),
            "prcp_mm": pd.to_numeric(
                daily["precipitation_sum"],
                errors="coerce",
            ),
            "tmax_c": pd.to_numeric(
                daily["temperature_2m_max"],
                errors="coerce",
            ),
            "tmin_c": pd.to_numeric(
                daily["temperature_2m_min"],
                errors="coerce",
            ),
        }
    )

    weather[
        "tavg_c"
    ] = (
        weather["tmax_c"]
        + weather["tmin_c"]
    ) / 2.0

    weather = (
        weather
        .dropna(
            subset=[
                "date",
            ]
        )
        .drop_duplicates(
            "date"
        )
        .sort_values(
            "date"
        )
        .set_index(
            "date"
        )
    )

    weather.index = pd.DatetimeIndex(
        weather.index
    ).normalize()

    if weather.empty:
        raise ForecastUnavailableError(
            "Open-Meteo returned no usable weather rows."
        )

    retrieved_at = datetime.now(
        PACIFIC
    )

    metadata = {
        "weather_retrieved_at":
            retrieved_at.isoformat(
                timespec="seconds"
            ),
        "latest_weather_date":
            weather.index.max()
            .date()
            .isoformat(),
        "weather_source":
            "Open-Meteo",
    }

    return (
        weather[
            [
                "prcp_mm",
                "tavg_c",
            ]
        ],
        metadata,
    )


# Backward-compatible private alias used by some earlier code.
_fetch_weather = _fetch_open_meteo_weather


def _build_weather_features(
    weather_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match the Version 12 training definitions.

    For a target date t:
      rain_1day      = rainfall on t-1
      rain_1day_lag1 = rainfall on t-2
      rain_1day_lag2 = rainfall on t-3

    All rolling rainfall and temperature windows are shifted by
    one day, so target-day conditions are excluded.
    """

    weather = weather_daily.copy()

    if not isinstance(
        weather.index,
        pd.DatetimeIndex,
    ):
        if "date" not in weather.columns:
            raise FeatureConstructionError(
                "Weather data needs a DatetimeIndex "
                "or a 'date' column."
            )

        weather[
            "date"
        ] = pd.to_datetime(
            weather["date"],
            errors="coerce",
        )

        weather = weather.set_index(
            "date"
        )

    weather.index = pd.DatetimeIndex(
        weather.index
    ).normalize()

    weather = weather.sort_index()

    for column in [
        "prcp_mm",
        "tavg_c",
    ]:
        if column not in weather.columns:
            raise FeatureConstructionError(
                f"Weather data is missing '{column}'."
            )

        weather[
            column
        ] = pd.to_numeric(
            weather[column],
            errors="coerce",
        )

    precipitation = weather[
        "prcp_mm"
    ]

    temperature = weather[
        "tavg_c"
    ]

    weather[
        "rain_1day"
    ] = precipitation.shift(
        1
    )

    weather[
        "rain_1day_lag1"
    ] = precipitation.shift(
        2
    )

    weather[
        "rain_1day_lag2"
    ] = precipitation.shift(
        3
    )

    for window in [
        3,
        7,
        14,
    ]:
        weather[
            f"rain_{window}day_sum"
        ] = (
            precipitation
            .rolling(
                window,
                min_periods=window,
            )
            .sum()
            .shift(
                1
            )
        )

        weather[
            f"rain_{window}day_avg"
        ] = (
            precipitation
            .rolling(
                window,
                min_periods=window,
            )
            .mean()
            .shift(
                1
            )
        )

        weather[
            f"rain_{window}day_max"
        ] = (
            precipitation
            .rolling(
                window,
                min_periods=window,
            )
            .max()
            .shift(
                1
            )
        )

        weather[
            f"rain_{window}day_rainy_days"
        ] = (
            (
                precipitation
                > 0
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

        weather[
            f"rain_intensity_{window}day"
        ] = (
            weather[
                f"rain_{window}day_sum"
            ]
            /
            (
                weather[
                    f"rain_{window}day_rainy_days"
                ]
                + 1e-6
            )
        )

        minimum_periods = max(
            2,
            window // 2,
        )

        weather[
            f"temp_{window}day_avg"
        ] = (
            temperature
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .mean()
            .shift(
                1
            )
        )

        weather[
            f"temp_{window}day_min"
        ] = (
            temperature
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .min()
            .shift(
                1
            )
        )

        weather[
            f"temp_{window}day_max"
        ] = (
            temperature
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .max()
            .shift(
                1
            )
        )

    weather[
        "season_wet"
    ] = [
        1
        if day.month in [
            11,
            12,
            1,
            2,
            3,
        ]
        else 0
        for day in weather.index
    ]

    # Training definition: number of consecutive dry days ending
    # immediately BEFORE the target date.
    antecedent_dry_days = []
    count = 0

    for value in precipitation.to_numpy():
        antecedent_dry_days.append(
            count
        )

        if pd.isna(
            value
        ):
            count = 0

        elif value > 0:
            count = 0

        else:
            count += 1

    weather[
        "adp_days"
    ] = antecedent_dry_days

    weather[
        "rain_ratio_1to3"
    ] = (
        weather[
            "rain_1day"
        ]
        /
        (
            weather[
                "rain_3day_sum"
            ]
            + 1e-6
        )
    )

    weather[
        "first_flush_index"
    ] = (
        weather[
            "rain_1day"
        ]
        *
        weather[
            "adp_days"
        ]
    )

    weather[
        "wet_season_rain_1day"
    ] = (
        weather[
            "season_wet"
        ]
        *
        weather[
            "rain_1day"
        ]
    )

    weather[
        "wet_season_rain_3day_sum"
    ] = (
        weather[
            "season_wet"
        ]
        *
        weather[
            "rain_3day_sum"
        ]
    )

    weather[
        "wet_season_rain_7day_sum"
    ] = (
        weather[
            "season_wet"
        ]
        *
        weather[
            "rain_7day_sum"
        ]
    )

    weather[
        "rain_temp_interaction_1day"
    ] = (
        weather[
            "rain_1day"
        ]
        *
        weather[
            "temp_3day_avg"
        ]
    )

    weather[
        "rain_temp_interaction_3day"
    ] = (
        weather[
            "rain_3day_sum"
        ]
        *
        weather[
            "temp_3day_avg"
        ]
    )

    return weather


def _build_lab_history_features(
    history_df: pd.DataFrame,
    *,
    bacteria_name: str,
    target_date: pd.Timestamp,
    concentration_threshold: float,
) -> tuple[
    dict[str, float],
    dict[str, Any],
]:
    """
    Use only samples STRICTLY before the target date.

    This fixes same-day leakage in reconstructed estimates.
    Lab age is reported as metadata, but is no longer used as an
    E. coli predictor in the live-safe deployed model.
    """

    target_date = pd.Timestamp(
        target_date
    ).normalize()

    subset = history_df[
        (
            history_df[
                "indicator_clean"
            ]
            == bacteria_name
        )
        &
        (
            history_df[
                "sample_date"
            ]
            < target_date
        )
    ].copy()

    subset = subset.sort_values(
        "sample_date"
    )

    if len(
        subset
    ) < 5:
        raise FeatureConstructionError(
            f"{bacteria_name}: fewer than five prior "
            f"laboratory samples are available before "
            f"{target_date.date()}."
        )

    values = subset[
        "result_value"
    ].astype(
        float
    )

    exceedance = (
        values
        >= concentration_threshold
    ).astype(
        float
    )

    ratio = (
        values
        /
        float(
            concentration_threshold
        )
    )

    latest_date = pd.Timestamp(
        subset.iloc[
            -1
        ][
            "sample_date"
        ]
    ).normalize()

    features = {
        "prev_result_value":
            float(
                values.iloc[
                    -1
                ]
            ),

        "prev_exceedance":
            float(
                exceedance.iloc[
                    -1
                ]
            ),

        "prev_result_to_threshold_ratio":
            float(
                ratio.iloc[
                    -1
                ]
            ),

        "prev3_result_mean":
            float(
                values.iloc[
                    -3:
                ].mean()
            ),

        "prev5_result_mean":
            float(
                values.iloc[
                    -5:
                ].mean()
            ),

        "prev3_exceedance_rate":
            float(
                exceedance.iloc[
                    -3:
                ].mean()
            ),

        "prev5_exceedance_rate":
            float(
                exceedance.iloc[
                    -5:
                ].mean()
            ),

        "prev3_result_to_threshold_ratio_mean":
            float(
                ratio.iloc[
                    -3:
                ].mean()
            ),

        "prev5_result_to_threshold_ratio_mean":
            float(
                ratio.iloc[
                    -5:
                ].mean()
            ),

        # Kept for metadata / diagnostics only.
        "days_since_prev_sample":
            float(
                (
                    target_date
                    - latest_date
                ).days
            ),
    }

    metadata = {
        "latest_lab_date":
            latest_date
            .date()
            .isoformat(),

        "lab_age_days":
            int(
                (
                    target_date
                    - latest_date
                ).days
            ),

        "prior_lab_samples_available":
            int(
                len(
                    subset
                )
            ),
    }

    return (
        features,
        metadata,
    )


def _validate_feature_values(
    values: dict[str, Any],
    required_features: list[str],
    *,
    bacteria_name: str,
    target_date: pd.Timestamp,
) -> None:
    missing = [
        feature
        for feature in required_features
        if feature not in values
    ]

    invalid = []

    for feature in required_features:
        if feature not in values:
            continue

        try:
            number = float(
                values[
                    feature
                ]
            )

        except (
            TypeError,
            ValueError,
        ):
            invalid.append(
                feature
            )
            continue

        if not np.isfinite(
            number
        ):
            invalid.append(
                feature
            )

    if missing or invalid:
        detail = []

        if missing:
            detail.append(
                f"missing={missing}"
            )

        if invalid:
            detail.append(
                f"invalid_or_nan={invalid}"
            )

        raise FeatureConstructionError(
            f"{bacteria_name} forecast unavailable for "
            f"{pd.Timestamp(target_date).date()}: "
            + "; ".join(
                detail
            )
        )


def build_feature_snapshot(
    target_date: Any,
    bacteria_name: str,
    *,
    weather_df: pd.DataFrame | None = None,
    history_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    target_date = pd.Timestamp(
        target_date
    ).normalize()

    manifest = load_model_manifest()

    if bacteria_name not in manifest[
        "models"
    ]:
        raise FeatureConstructionError(
            f"Unknown model target: {bacteria_name}"
        )

    config = manifest[
        "models"
    ][
        bacteria_name
    ]

    required_features = list(
        config[
            "features"
        ]
    )

    concentration_threshold = float(
        config[
            "bacteria_threshold_mpn_100ml"
        ]
    )

    if weather_df is None:
        (
            weather_df,
            weather_metadata,
        ) = _fetch_open_meteo_weather()

    else:
        weather_metadata = {
            "weather_retrieved_at":
                None,

            "latest_weather_date":
                (
                    pd.DatetimeIndex(
                        weather_df.index
                    )
                    .max()
                    .date()
                    .isoformat()
                    if (
                        isinstance(
                            weather_df.index,
                            pd.DatetimeIndex,
                        )
                        and len(
                            weather_df
                        ) > 0
                    )
                    else None
                ),

            "weather_source":
                "supplied_weather_frame",
        }

    if history_df is None:
        history_df = (
            load_lab_history()
        )

    engineered_weather = (
        _build_weather_features(
            weather_df
        )
    )

    if (
        target_date
        not in engineered_weather.index
    ):
        raise FeatureConstructionError(
            "No weather row is available for "
            f"{target_date.date()}."
        )

    weather_values = (
        engineered_weather
        .loc[
            target_date
        ]
        .to_dict()
    )

    (
        lab_values,
        lab_metadata,
    ) = _build_lab_history_features(
        history_df,
        bacteria_name=bacteria_name,
        target_date=target_date,
        concentration_threshold=concentration_threshold,
    )

    values = {}

    values.update(
        weather_values
    )

    values.update(
        lab_values
    )

    _validate_feature_values(
        values,
        required_features,
        bacteria_name=bacteria_name,
        target_date=target_date,
    )

    snapshot = {
        feature:
            float(
                values[
                    feature
                ]
            )
        for feature
        in required_features
    }

    snapshot[
        "_metadata"
    ] = {
        "bacteria":
            bacteria_name,

        "target_date":
            target_date
            .date()
            .isoformat(),

        "weather_input_end_date":
            (
                target_date
                -
                pd.Timedelta(
                    days=1
                )
            )
            .date()
            .isoformat(),

        **weather_metadata,
        **lab_metadata,

        "required_feature_count":
            len(
                required_features
            ),

        "feature_validation":
            "PASS",
    }

    return snapshot


def risk_level(
    bacteria_name: str,
    probability: float,
) -> str:
    thresholds = DISPLAY_THRESHOLDS[
        bacteria_name
    ]

    if (
        probability
        <
        thresholds[
            "safe_max"
        ]
    ):
        return "Safe"

    if (
        probability
        <
        thresholds[
            "unsafe_min"
        ]
    ):
        return "Caution"

    return "Unsafe"


def overall_risk(
    e_coli_risk: str,
    enterococcus_risk: str,
) -> str:
    return max(
        [
            e_coli_risk,
            enterococcus_risk,
        ],
        key=lambda label:
            RISK_ORDER[
                label
            ],
    )


# Private aliases kept for compatibility with code written against
# the immediately previous implementation.
_risk_level = risk_level
_overall_risk = overall_risk


def _predict_one(
    bacteria_name: str,
    target_date: pd.Timestamp,
    *,
    weather_df: pd.DataFrame,
    history_df: pd.DataFrame,
) -> tuple[
    float,
    str,
    dict[str, Any],
]:
    manifest = load_model_manifest()

    config = manifest[
        "models"
    ][
        bacteria_name
    ]

    snapshot = build_feature_snapshot(
        target_date,
        bacteria_name,
        weather_df=weather_df,
        history_df=history_df,
    )

    required_features = list(
        config[
            "features"
        ]
    )

    X = pd.DataFrame(
        [
            [
                snapshot[
                    feature
                ]
                for feature
                in required_features
            ]
        ],
        columns=required_features,
    )

    model = _load_model(
        bacteria_name
    )

    probability = float(
        model.predict_proba(
            X
        )[
            :,
            1,
        ][
            0
        ]
    )

    if (
        not np.isfinite(
            probability
        )
        or probability < 0
        or probability > 1
    ):
        raise ForecastUnavailableError(
            f"{bacteria_name} returned an invalid probability."
        )

    return (
        probability,
        risk_level(
            bacteria_name,
            probability,
        ),
        snapshot[
            "_metadata"
        ],
    )


def _compatibility_fields(
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Add harmless aliases so older page code can consume the same row
    without requiring a Timeline / Recent Trends rewrite.
    """

    row[
        "date"
    ] = row[
        "prediction_date"
    ]

    row[
        "e_coli_prob"
    ] = row[
        "e_coli_probability"
    ]

    row[
        "enterococcus_prob"
    ] = row[
        "enterococcus_probability"
    ]

    row[
        "risk"
    ] = row[
        "overall_risk"
    ]

    row[
        "source"
    ] = row[
        "source_type"
    ]

    return row


def _predict_date(
    target_date: Any,
    *,
    weather_df: pd.DataFrame,
    weather_metadata: dict[str, Any],
    history_df: pd.DataFrame,
    source_type: str,
    generated_at: datetime,
) -> dict[str, Any]:
    target = pd.Timestamp(
        target_date
    ).normalize()

    (
        e_coli_probability,
        e_coli_risk,
        e_coli_metadata,
    ) = _predict_one(
        "E. coli",
        target,
        weather_df=weather_df,
        history_df=history_df,
    )

    (
        enterococcus_probability,
        enterococcus_risk,
        enterococcus_metadata,
    ) = _predict_one(
        "Enterococcus",
        target,
        weather_df=weather_df,
        history_df=history_df,
    )

    combined_risk = overall_risk(
        e_coli_risk,
        enterococcus_risk,
    )

    manifest = load_model_manifest()

    latest_lab_date = max(
        [
            pd.Timestamp(
                e_coli_metadata[
                    "latest_lab_date"
                ]
            ),
            pd.Timestamp(
                enterococcus_metadata[
                    "latest_lab_date"
                ]
            ),
        ]
    ).date().isoformat()

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
            target
            .date()
            .isoformat(),

        "data_last_updated":
            generated_at
            .date()
            .isoformat(),

        "forecast_generated_at":
            generated_at.isoformat(
                timespec="seconds"
            ),

        "weather_retrieved_at":
            weather_metadata.get(
                "weather_retrieved_at"
            ),

        "latest_weather_date":
            weather_metadata.get(
                "latest_weather_date"
            ),

        "weather_input_end_date":
            (
                target
                -
                pd.Timedelta(
                    days=1
                )
            )
            .date()
            .isoformat(),

        "latest_lab_date":
            latest_lab_date,

        "e_coli_latest_lab_date":
            e_coli_metadata[
                "latest_lab_date"
            ],

        "enterococcus_latest_lab_date":
            enterococcus_metadata[
                "latest_lab_date"
            ],

        "e_coli_lab_age_days":
            e_coli_metadata[
                "lab_age_days"
            ],

        "enterococcus_lab_age_days":
            enterococcus_metadata[
                "lab_age_days"
            ],

        "e_coli_probability":
            e_coli_probability,

        "enterococcus_probability":
            enterococcus_probability,

        "e_coli_risk":
            e_coli_risk,

        "enterococcus_risk":
            enterococcus_risk,

        "overall_risk":
            combined_risk,

        "risk_color":
            {
                "Safe":
                    "green",
                "Caution":
                    "yellow",
                "Unsafe":
                    "red",
            }[
                combined_risk
            ],

        "safety_message":
            (
                "Experimental forecast only. "
                "Follow official water-quality advisories "
                "and closure notices."
            ),

        "model_version":
            manifest.get(
                "pipeline_version",
                "AquaCast_Model_Pipeline_Version_12",
            ),

        "source_type":
            source_type,

        "feature_validation":
            "PASS",
    }

    return _compatibility_fields(
        row
    )


def load_live_latest() -> dict[str, Any]:
    """
    Current LagoonCast forecast.
    """

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    (
        weather,
        weather_metadata,
    ) = _fetch_open_meteo_weather(
        past_days=30,
        forecast_days=8,
    )

    history = load_lab_history()

    generated_at = datetime.now(
        PACIFIC
    )

    return _predict_date(
        today,
        weather_df=weather,
        weather_metadata=weather_metadata,
        history_df=history,
        source_type="live_forecast",
        generated_at=generated_at,
    )


def load_live_outlook(
    days: int = 7,
) -> pd.DataFrame:
    """
    Today plus `days` future dates.

    The existing Timeline uses days=7, producing 8 rows here:
    Today + next 7 days.
    """

    days = int(
        days
    )

    if days < 0:
        raise ValueError(
            "days must be zero or greater."
        )

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    (
        weather,
        weather_metadata,
    ) = _fetch_open_meteo_weather(
        past_days=30,
        forecast_days=max(
            8,
            days + 1,
        ),
    )

    history = load_lab_history()

    generated_at = datetime.now(
        PACIFIC
    )

    rows = []

    for horizon in range(
        days + 1
    ):
        target = (
            today
            +
            pd.Timedelta(
                days=horizon
            )
        )

        row = _predict_date(
            target,
            weather_df=weather,
            weather_metadata=weather_metadata,
            history_df=history,
            source_type=(
                "live_forecast"
                if horizon == 0
                else "future_forecast"
            ),
            generated_at=generated_at,
        )

        row[
            "forecast_horizon_days"
        ] = horizon

        row[
            "timeline_label"
        ] = (
            "Today"
            if horizon == 0
            else (
                f"{horizon} day"
                f"{'' if horizon == 1 else 's'} ahead"
            )
        )

        row[
            "is_today"
        ] = (
            horizon == 0
        )

        row[
            "is_future"
        ] = (
            horizon > 0
        )

        row[
            "is_reconstructed"
        ] = False

        rows.append(
            row
        )

    return pd.DataFrame(
        rows
    )


def load_recent_estimates(
    days: int = 7,
) -> pd.DataFrame:
    """
    Reconstructed estimates for the previous `days` dates.

    There is deliberately NO arbitrary 14-day cap here.
    A 30-day Recent Trends view is supported.

    Each estimate uses laboratory observations strictly before
    its target date.
    """

    days = int(
        days
    )

    if days < 1:
        raise ValueError(
            "days must be at least 1."
        )

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    (
        weather,
        weather_metadata,
    ) = _fetch_open_meteo_weather(
        past_days=max(
            30,
            days + 16,
        ),
        forecast_days=8,
    )

    history = load_lab_history()

    generated_at = datetime.now(
        PACIFIC
    )

    rows = []

    for offset in range(
        days,
        0,
        -1,
    ):
        target = (
            today
            -
            pd.Timedelta(
                days=offset
            )
        )

        row = _predict_date(
            target,
            weather_df=weather,
            weather_metadata=weather_metadata,
            history_df=history,
            source_type="reconstructed_historical_estimate",
            generated_at=generated_at,
        )

        row[
            "forecast_horizon_days"
        ] = -offset

        row[
            "timeline_label"
        ] = "Recent Estimate"

        row[
            "is_today"
        ] = False

        row[
            "is_future"
        ] = False

        row[
            "is_reconstructed"
        ] = True

        rows.append(
            row
        )

    return pd.DataFrame(
        rows
    )


def get_data_freshness(
    *,
    include_weather: bool = False,
) -> dict[str, Any]:
    history = load_lab_history()

    result: dict[
        str,
        Any,
    ] = {}

    latest_dates = []

    for (
        bacteria_name,
        prefix,
    ) in [
        (
            "E. coli",
            "e_coli",
        ),
        (
            "Enterococcus",
            "enterococcus",
        ),
    ]:
        subset = history[
            history[
                "indicator_clean"
            ]
            == bacteria_name
        ]

        if subset.empty:
            result[
                f"{prefix}_latest_lab_date"
            ] = None

            continue

        latest = (
            pd.Timestamp(
                subset[
                    "sample_date"
                ].max()
            )
            .date()
            .isoformat()
        )

        result[
            f"{prefix}_latest_lab_date"
        ] = latest

        latest_dates.append(
            pd.Timestamp(
                latest
            )
        )

    result[
        "latest_lab_date"
    ] = (
        max(
            latest_dates
        )
        .date()
        .isoformat()
        if latest_dates
        else None
    )

    if include_weather:
        try:
            (
                _,
                weather_metadata,
            ) = _fetch_open_meteo_weather(
                past_days=16,
                forecast_days=8,
            )

            result.update(
                weather_metadata
            )

            result[
                "weather_status"
            ] = "available"

        except Exception as exc:
            result[
                "weather_status"
            ] = "unavailable"

            result[
                "weather_error"
            ] = str(
                exc
            )

    return result


def get_model_metadata() -> tuple[
    dict[str, Any],
    pd.DataFrame,
]:
    manifest = load_model_manifest()

    metrics_path = _find_file(
        "current_best_model_metrics.csv"
    )

    metrics = pd.read_csv(
        metrics_path
    )

    return (
        manifest,
        metrics,
    )
