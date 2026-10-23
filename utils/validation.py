from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACIFIC = ZoneInfo("America/Los_Angeles")

VALID_RISKS = {"Safe", "Caution", "Unsafe"}
RISK_ORDER = {"Safe": 0, "Caution": 1, "Unsafe": 2}

REQUIRED_PREDICTION_FIELDS = [
    "prediction_date",
    "data_last_updated",
    "e_coli_probability",
    "enterococcus_probability",
    "e_coli_risk",
    "enterococcus_risk",
    "overall_risk",
    "model_version",
]


def _prediction_file_candidates() -> list[Path]:
    return [
        ROOT / "app_predictions.csv",
        ROOT / "data" / "app_predictions.csv",
    ]


def _find_prediction_file() -> Path:
    for path in _prediction_file_candidates():
        if path.exists():
            return path

    raise FileNotFoundError(
        "app_predictions.csv was not found."
    )


def validate_prediction_row(
    row: dict[str, Any] | pd.Series,
    *,
    stale_after_days: int = 1,
) -> dict[str, Any]:

    data = dict(
        row
    )

    errors: list[
        str
    ] = []

    missing = [
        field
        for field
        in REQUIRED_PREDICTION_FIELDS
        if (
            field not in data
            or pd.isna(
                data[
                    field
                ]
            )
        )
    ]

    if missing:
        errors.append(
            f"Missing required fields: {missing}"
        )

    for field in [
        "e_coli_probability",
        "enterococcus_probability",
    ]:

        if field not in data:
            continue

        try:
            value = float(
                data[
                    field
                ]
            )

        except (
            TypeError,
            ValueError,
        ):
            errors.append(
                f"{field} is not numeric."
            )
            continue

        if (
            not np.isfinite(
                value
            )
            or not 0 <= value <= 1
        ):
            errors.append(
                f"{field} must be between 0 and 1."
            )

    for field in [
        "e_coli_risk",
        "enterococcus_risk",
        "overall_risk",
    ]:

        if (
            field in data
            and str(
                data[
                    field
                ]
            ).strip()
            not in VALID_RISKS
        ):

            errors.append(
                f"{field} must be one of "
                f"{sorted(VALID_RISKS)}."
            )

    if all(
        field in data
        for field in [
            "e_coli_risk",
            "enterococcus_risk",
            "overall_risk",
        ]
    ):

        e_coli = str(
            data[
                "e_coli_risk"
            ]
        ).strip()

        entero = str(
            data[
                "enterococcus_risk"
            ]
        ).strip()

        overall = str(
            data[
                "overall_risk"
            ]
        ).strip()

        if (
            e_coli in VALID_RISKS
            and entero in VALID_RISKS
            and overall in VALID_RISKS
        ):

            expected = max(
                [
                    e_coli,
                    entero,
                ],
                key=lambda risk:
                    RISK_ORDER[
                        risk
                    ],
            )

            if overall != expected:

                errors.append(
                    f"overall_risk is {overall}, "
                    f"but should be {expected}."
                )

    prediction_date = pd.to_datetime(
        data.get(
            "prediction_date"
        ),
        errors="coerce",
    )

    updated = pd.to_datetime(
        data.get(
            "data_last_updated"
        ),
        errors="coerce",
    )

    if pd.isna(
        prediction_date
    ):
        errors.append(
            "prediction_date is invalid."
        )

    if pd.isna(
        updated
    ):
        errors.append(
            "data_last_updated is invalid."
        )

    today = pd.Timestamp(
        datetime.now(
            PACIFIC
        ).date()
    )

    stale = False
    age_days = None

    if pd.notna(
        prediction_date
    ):

        prediction_date = pd.Timestamp(
            prediction_date
        ).normalize()

        age_days = int(
            (
                today
                - prediction_date
            ).days
        )

        if (
            prediction_date
            >
            today
            +
            pd.Timedelta(
                days=7
            )
        ):

            errors.append(
                "prediction_date is beyond the "
                "approved 7-day forecast horizon."
            )

        stale = (
            age_days
            >
            int(
                stale_after_days
            )
        )

    return {
        "valid":
            len(
                errors
            )
            == 0,

        "stale":
            bool(
                stale
            ),

        "age_days":
            age_days,

        "errors":
            errors,
    }


def load_valid_latest() -> dict[str, Any]:
    """
    Return the newest structurally valid saved row.

    Historical/technical pages may use this.
    The Current Forecast page must not present
    a stale saved row as a current forecast.
    """

    path = (
        _find_prediction_file()
    )

    df = pd.read_csv(
        path,
        low_memory=False,
    )

    if df.empty:
        raise ValueError(
            "app_predictions.csv is empty."
        )

    if (
        "prediction_date"
        not in df.columns
    ):
        raise ValueError(
            "app_predictions.csv has no "
            "prediction_date column."
        )

    df[
        "prediction_date"
    ] = pd.to_datetime(
        df[
            "prediction_date"
        ],
        errors="coerce",
    )

    df = (
        df
        .dropna(
            subset=[
                "prediction_date"
            ]
        )
        .sort_values(
            "prediction_date"
        )
    )

    for (
        _,
        row,
    ) in df.iloc[
        ::-1
    ].iterrows():

        result = (
            validate_prediction_row(
                row
            )
        )

        if result[
            "valid"
        ]:

            return row.to_dict()

    raise ValueError(
        "No valid saved prediction row was found."
    )


def load_saved_backup_metadata() -> dict[str, Any] | None:
    """
    Return metadata only about the latest saved prediction.

    Risk/probability values are intentionally omitted so a
    stale historical output cannot be rendered as today's
    current forecast.
    """

    try:
        row = load_valid_latest()

    except Exception:
        return None

    validation = (
        validate_prediction_row(
            row
        )
    )

    return {
        "prediction_date":
            row.get(
                "prediction_date"
            ),

        "data_last_updated":
            row.get(
                "data_last_updated"
            ),

        "model_version":
            row.get(
                "model_version"
            ),

        "stale":
            validation[
                "stale"
            ],

        "age_days":
            validation[
                "age_days"
            ],
    }
