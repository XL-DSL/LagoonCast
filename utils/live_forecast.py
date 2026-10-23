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


ROOT = Path(__file__).resolve().parents[1]
PACIFIC = ZoneInfo("America/Los_Angeles")

SITE_ID = "aquatic_park_san_mateo"
SITE_NAME = "Parkside Aquatic Park, San Mateo"
COUNTY = "San Mateo"
SITE_LAT = 37.5602
SITE_LON = -122.2910

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

DISPLAY_THRESHOLDS = {
    "E. coli": {"safe_max": 0.10, "unsafe_min": 0.50},
    "Enterococcus": {"safe_max": 0.40, "unsafe_min": 0.85},
}

RISK_ORDER = {"Safe": 0, "Caution": 1, "Unsafe": 2}


class ForecastUnavailableError(RuntimeError):
    """Raised when LagoonCast cannot construct a valid live forecast."""


class FeatureConstructionError(ForecastUnavailableError):
    """Raised when one or more required model inputs cannot be constructed."""


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
    manifest = json.loads(path.read_text(encoding="utf-8"))

    if "models" not in manifest:
        raise ForecastUnavailableError(
            "model_manifest.json does not contain a 'models' section."
        )

    for bacteria_name in ("E. coli", "Enterococcus"):
        if bacteria_name not in manifest["models"]:
            raise ForecastUnavailableError(
                f"model_manifest.json is missing {bacteria_name}."
            )

        cfg = manifest["models"][bacteria_name]
        required = [
            "model",
            "features",
            "model_file",
            "locked_threshold",
            "bacteria_threshold_mpn_100ml",
        ]
        missing = [k for k in required if k not in cfg]
        if missing:
            raise ForecastUnavailableError(
                f"{bacteria_name} manifest entry is missing: {missing}"
            )

    return manifest


@lru_cache(maxsize=2)
def _load_model(bacteria_name: str):
    manifest = load_model_manifest()
    cfg = manifest["models"][bacteria_name]
    model_path = _find_file(cfg["model_file"])
    return joblib.load(model_path)


def _normalize_indicator(value: Any) -> str:
    s = str(value).strip().lower()
    if s in {"e. coli", "e coli", "ecoli", "e_coli"}:
        return "E. coli"
    if s in {"enterococcus", "enterococci"}:
        return "Enterococcus"
    return str(value).strip()


def _history_candidates() -> list[Path]:
    return [
        ROOT / "data" / "lagooncast_lab_history.csv",
        ROOT / "lagooncast_lab_history.csv",
        ROOT / "data" / "Aquacast15Years_Weekly.csv",
        ROOT / "Aquacast15Years_Weekly.csv",
        ROOT / "data" / "Aquacast15Years_enhanced_no_tides.csv",
        ROOT / "Aquacast15Years_enhanced_no_tides.csv",
        ROOT
        / "data"
        / "aquacast_combined_cleaned_fib_sorted_2004_2026_COMPLETE_WITH_2010_2019(1).csv",
        ROOT
        / "aquacast_combined_cleaned_fib_sorted_2004_2026_COMPLETE_WITH_2010_2019(1).csv",
        ROOT
        / "data"
        / "aquacast_combined_cleaned_fib_sorted_2004_2026_COMPLETE_WITH_2010_2019.csv",
        ROOT
        / "aquacast_combined_cleaned_fib_sorted_2004_2026_COMPLETE_WITH_2010_2019.csv",
    ]


@lru_cache(maxsize=1)
def load_lab_history() -> pd.DataFrame:
    path = next((p for p in _history_candidates() if p.exists()), None)
    if path is None:
        raise ForecastUnavailableError(
            "No laboratory-history file is available. Add "
            "data/lagooncast_lab_history.csv or the approved historical dataset."
        )

    df = pd.read_csv(path, low_memory=False)

    if "sample_date" not in df.columns and "sampledate" in df.columns:
        df["sample_date"] = df["sampledate"]
    if "indicator_clean" not in df.columns and "analyte" in df.columns:
        df["indicator_clean"] = df["analyte"]
    if "indicator_clean" not in df.columns and "indicator" in df.columns:
        df["indicator_clean"] = df["indicator"]
    if "result_value" not in df.columns and "result" in df.columns:
        df["result_value"] = df["result"]

    required = ["sample_date", "indicator_clean", "result_value"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ForecastUnavailableError(
            f"Laboratory-history file is missing required columns: {missing}"
        )

    out = df[required].copy()
    out["sample_date"] = pd.to_datetime(
        out["sample_date"], errors="coerce"
    ).dt.normalize()
    out["indicator_clean"] = out["indicator_clean"].map(_normalize_indicator)
    out["result_value"] = pd.to_numeric(out["result_value"], errors="coerce")

    out = (
        out[out["indicator_clean"].isin(["E. coli", "Enterococcus"])]
        .dropna(subset=required)
        .sort_values(["indicator_clean", "sample_date"])
        .reset_index(drop=True)
    )

    if out.empty:
        raise ForecastUnavailableError(
            "Laboratory-history file has no usable rows."
        )

    return out


def _fetch_open_meteo_weather(
    *,
    past_days: int = 30,
    forecast_days: int = 8,
    timeout: int = 20,
) -> tuple[pd.DataFrame, dict[str, Any]]:
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
        "past_days": int(past_days),
        "forecast_days": int(forecast_days),
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

    daily = payload.get("daily")
    if not daily:
        raise ForecastUnavailableError(
            "Open-Meteo response did not contain daily weather data."
        )

    required = [
        "time",
        "precipitation_sum",
        "temperature_2m_max",
        "temperature_2m_min",
    ]

    missing = [
        c
        for c in required
        if c not in daily
    ]

    if missing:
        raise ForecastUnavailableError(
            f"Open-Meteo response is missing fields: {missing}"
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

    weather["tavg_c"] = (
        weather["tmax_c"]
        + weather["tmin_c"]
    ) / 2.0

    weather = (
        weather
        .dropna(
            subset=[
                "date"
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
            "Open-Meteo returned no usable daily weather rows."
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


def _build_weather_features(
    weather_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reproduce Version 12 training timing exactly.

    For target date t:
    - rain_1day = precipitation on t-1
    - rain_1day_lag1 = precipitation on t-2
    - rain_1day_lag2 = precipitation on t-3
    - every rolling weather feature is shifted by one day
    """

    weather = weather_daily.copy()

    if not isinstance(
        weather.index,
        pd.DatetimeIndex,
    ):
        if "date" not in weather.columns:
            raise FeatureConstructionError(
                "Weather input must have a DatetimeIndex "
                "or a 'date' column."
            )

        weather["date"] = pd.to_datetime(
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

    for col in [
        "prcp_mm",
        "tavg_c",
    ]:
        if col not in weather.columns:
            raise FeatureConstructionError(
                f"Weather input is missing required column '{col}'."
            )

        weather[col] = pd.to_numeric(
            weather[col],
            errors="coerce",
        )

    pr = weather[
        "prcp_mm"
    ]

    temp = weather[
        "tavg_c"
    ]

    weather[
        "rain_1day"
    ] = pr.shift(
        1
    )

    weather[
        "rain_1day_lag1"
    ] = pr.shift(
        2
    )

    weather[
        "rain_1day_lag2"
    ] = pr.shift(
        3
    )

    for win in [
        3,
        7,
        14,
    ]:

        weather[
            f"rain_{win}day_sum"
        ] = (
            pr
            .rolling(
                win,
                min_periods=win,
            )
            .sum()
            .shift(
                1
            )
        )

        weather[
            f"rain_{win}day_avg"
        ] = (
            pr
            .rolling(
                win,
                min_periods=win,
            )
            .mean()
            .shift(
                1
            )
        )

        weather[
            f"rain_{win}day_max"
        ] = (
            pr
            .rolling(
                win,
                min_periods=win,
            )
            .max()
            .shift(
                1
            )
        )

        weather[
            f"rain_{win}day_rainy_days"
        ] = (
            (
                pr > 0
            )
            .astype(
                float
            )
            .rolling(
                win,
                min_periods=win,
            )
            .sum()
            .shift(
                1
            )
        )

        weather[
            f"rain_intensity_{win}day"
        ] = (
            weather[
                f"rain_{win}day_sum"
            ]
            /
            (
                weather[
                    f"rain_{win}day_rainy_days"
                ]
                + 1e-6
            )
        )

        min_periods = max(
            2,
            win // 2,
        )

        weather[
            f"temp_{win}day_avg"
        ] = (
            temp
            .rolling(
                win,
                min_periods=min_periods,
            )
            .mean()
            .shift(
                1
            )
        )

        weather[
            f"temp_{win}day_min"
        ] = (
            temp
            .rolling(
                win,
                min_periods=min_periods,
            )
            .min()
            .shift(
                1
            )
        )

        weather[
            f"temp_{win}day_max"
        ] = (
            temp
            .rolling(
                win,
                min_periods=min_periods,
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
        if d.month
        in [
            11,
            12,
            1,
            2,
            3,
        ]
        else 0
        for d
        in weather.index
    ]

    # Training semantics:
    # adp_days on target date t is the dry-day count before t.
    adp = []
    count = 0

    for value in pr.to_numpy():

        adp.append(
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
    ] = adp

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
) -> tuple[dict[str, float], dict[str, Any]]:
    """
    Use ONLY laboratory samples strictly before target_date.

    The strict '< target_date' rule prevents same-day laboratory leakage
    in both live forecasts and reconstructed historical estimates.
    """

    target_date = pd.Timestamp(
        target_date
    ).normalize()

    sub = history_df[
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

    sub = sub.sort_values(
        "sample_date"
    )

    if len(
        sub
    ) < 5:

        raise FeatureConstructionError(
            f"{bacteria_name}: fewer than five prior laboratory "
            f"samples are available before {target_date.date()}."
        )

    values = sub[
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

    latest = sub.iloc[
        -1
    ]

    latest_date = pd.Timestamp(
        latest[
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
                    sub
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
        f
        for f
        in required_features
        if f not in values
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

        details = []

        if missing:
            details.append(
                f"missing={missing}"
            )

        if invalid:
            details.append(
                f"invalid_or_nan={invalid}"
            )

        raise FeatureConstructionError(
            f"{bacteria_name} forecast unavailable for "
            f"{pd.Timestamp(target_date).date()}: "
            + "; ".join(
                details
            )
            + ". Required model inputs are never silently "
            "replaced with zero."
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

    cfg = manifest[
        "models"
    ][
        bacteria_name
    ]

    required_features = list(
        cfg[
            "features"
        ]
    )

    concentration_threshold = float(
        cfg[
            "bacteria_threshold_mpn_100ml"
        ]
    )

    if weather_df is None:

        weather_df, weather_meta = (
            _fetch_open_meteo_weather()
        )

    else:

        latest_weather_date = None

        if (
            isinstance(
                weather_df.index,
                pd.DatetimeIndex,
            )
            and len(
                weather_df
            )
        ):

            latest_weather_date = (
                weather_df
                .index
                .max()
                .date()
                .isoformat()
            )

        weather_meta = {
            "weather_retrieved_at":
                None,

            "latest_weather_date":
                latest_weather_date,

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
            f"No weather row is available for target date "
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
        lab_meta,
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

        **weather_meta,
        **lab_meta,

        "required_feature_count":
            len(
                required_features
            ),

        "feature_validation":
            "PASS",
    }

    return snapshot


def _risk_level(
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


def _overall_risk(
    ecoli_risk: str,
    entero_risk: str,
) -> str:

    return max(
        [
            ecoli_risk,
            entero_risk,
        ],
        key=lambda x:
            RISK_ORDER[
                x
            ],
    )


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

    manifest = (
        load_model_manifest()
    )

    cfg = manifest[
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
        cfg[
            "features"
        ]
    )

    X = pd.DataFrame(
        [
            [
                snapshot[
                    f
                ]
                for f
                in required_features
            ]
        ],
        columns=required_features,
    )

    model = _load_model(
        bacteria_name
    )

    if not hasattr(
        model,
        "predict_proba",
    ):
        raise ForecastUnavailableError(
            f"{bacteria_name} model does not support predict_proba()."
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
            f"{bacteria_name} model returned invalid probability: "
            f"{probability}"
        )

    return (
        probability,
        _risk_level(
            bacteria_name,
            probability,
        ),
        snapshot[
            "_metadata"
        ],
    )


def _predict_date(
    target_date: Any,
    *,
    weather_df: pd.DataFrame,
    weather_meta: dict[str, Any],
    history_df: pd.DataFrame,
    source_type: str,
    generated_at: datetime,
) -> dict[str, Any]:

    target = pd.Timestamp(
        target_date
    ).normalize()

    (
        ecoli_prob,
        ecoli_risk,
        ecoli_meta,
    ) = _predict_one(
        "E. coli",
        target,
        weather_df=weather_df,
        history_df=history_df,
    )

    (
        entero_prob,
        entero_risk,
        entero_meta,
    ) = _predict_one(
        "Enterococcus",
        target,
        weather_df=weather_df,
        history_df=history_df,
    )

    overall = _overall_risk(
        ecoli_risk,
        entero_risk,
    )

    manifest = (
        load_model_manifest()
    )

    latest_lab_dates = [
        pd.Timestamp(
            ecoli_meta[
                "latest_lab_date"
            ]
        ),
        pd.Timestamp(
            entero_meta[
                "latest_lab_date"
            ]
        ),
    ]

    latest_lab_date = (
        max(
            latest_lab_dates
        )
        .date()
        .isoformat()
    )

    return {
        "site_id":
            SITE_ID,

        "site_name":
            SITE_NAME,

        "county":
            COUNTY,

        "prediction_date":
            target
            .date()
            .isoformat(),

        "data_last_updated":
            generated_at.isoformat(
                timespec="seconds"
            ),

        "forecast_generated_at":
            generated_at.isoformat(
                timespec="seconds"
            ),

        "weather_retrieved_at":
            weather_meta.get(
                "weather_retrieved_at"
            ),

        "latest_weather_date":
            weather_meta.get(
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
            ecoli_meta[
                "latest_lab_date"
            ],

        "enterococcus_latest_lab_date":
            entero_meta[
                "latest_lab_date"
            ],

        "e_coli_lab_age_days":
            ecoli_meta[
                "lab_age_days"
            ],

        "enterococcus_lab_age_days":
            entero_meta[
                "lab_age_days"
            ],

        "e_coli_probability":
            ecoli_prob,

        "enterococcus_probability":
            entero_prob,

        "e_coli_risk":
            ecoli_risk,

        "enterococcus_risk":
            entero_risk,

        "overall_risk":
            overall,

        "risk_color":
            {
                "Safe":
                    "green",

                "Caution":
                    "yellow",

                "Unsafe":
                    "red",
            }[
                overall
            ],

        "safety_message":
            (
                "Experimental LagoonCast forecast only. "
                "Follow official water-quality advisories "
                "and closures."
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


def load_live_latest() -> dict[str, Any]:

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    (
        weather,
        weather_meta,
    ) = _fetch_open_meteo_weather(
        past_days=30,
        forecast_days=8,
    )

    history = (
        load_lab_history()
    )

    generated_at = datetime.now(
        PACIFIC
    )

    return _predict_date(
        today,
        weather_df=weather,
        weather_meta=weather_meta,
        history_df=history,
        source_type="live_forecast",
        generated_at=generated_at,
    )


def load_live_outlook(
    days: int = 7,
) -> pd.DataFrame:

    days = int(
        days
    )

    if (
        days < 0
        or days > 7
    ):
        raise ValueError(
            "Live outlook supports 0 through 7 future days."
        )

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    (
        weather,
        weather_meta,
    ) = _fetch_open_meteo_weather(
        past_days=30,
        forecast_days=max(
            8,
            days + 1,
        ),
    )

    history = (
        load_lab_history()
    )

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
            weather_meta=weather_meta,
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
                f"{horizon} "
                f"day{'s' if horizon != 1 else ''} ahead"
            )
        )

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
    Reconstruct previous dates using only information available
    before each date.

    These are reconstructed historical estimates, NOT saved forecasts.
    """

    days = int(
        days
    )

    if (
        days < 1
        or days > 14
    ):
        raise ValueError(
            "Recent reconstructed estimates support 1-14 days."
        )

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    (
        weather,
        weather_meta,
    ) = _fetch_open_meteo_weather(
        past_days=max(
            30,
            days + 16,
        ),
        forecast_days=8,
    )

    history = (
        load_lab_history()
    )

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
            weather_meta=weather_meta,
            history_df=history,
            source_type="reconstructed_historical_estimate",
            generated_at=generated_at,
        )

        row[
            "forecast_horizon_days"
        ] = -offset

        row[
            "timeline_label"
        ] = (
            "Reconstructed historical estimate"
        )

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

    history = (
        load_lab_history()
    )

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

        sub = history[
            history[
                "indicator_clean"
            ]
            == bacteria_name
        ]

        if sub.empty:

            result[
                f"{prefix}_latest_lab_date"
            ] = None

            continue

        latest = (
            pd.Timestamp(
                sub[
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
                weather_meta,
            ) = _fetch_open_meteo_weather(
                past_days=16,
                forecast_days=8,
            )

            result.update(
                weather_meta
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

    manifest = (
        load_model_manifest()
    )

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
