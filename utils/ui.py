import html
from datetime import date

import pandas as pd
import streamlit as st


# ==========================================================
# APP / SITE CONSTANTS
# ==========================================================

APP_NAME = "LagoonCast"

APP_TAGLINE = (
    "Recreational Water Quality Forecast"
)

SITE_NAME = (
    "Parkside Aquatic Park, San Mateo"
)

PACIFIC_TIMEZONE = (
    "America/Los_Angeles"
)


# San Mateo County Beach Data Map
OFFICIAL_URL = (
    "https://www.google.com/maps/d/viewer"
    "?femb=1"
    "&ll=37.41494222054769,-122.38601015000002"
    "&mid=1Y0U-5M0-ej_PnH8i1mJYFaXBlok-8fE"
    "&z=10"
)


# Keep the current repository URL until the repository
# itself is renamed.
GITHUB_URL = (
    "https://github.com/"
    "XL-DSL/LagoonCast"
)


# ==========================================================
# RISK HELPERS
# ==========================================================

def risk_class(risk):

    return {
        "Safe": "safe",
        "Caution": "caution",
        "Unsafe": "unsafe",
    }.get(
        str(risk).strip(),
        "safe",
    )


def risk_icon(risk):

    return {
        "Safe": "✓",
        "Caution": "!",
        "Unsafe": "×",
    }.get(
        str(risk).strip(),
        "•",
    )


def interpretation(risk):

    return {
        "Safe":
            (
                "The model currently predicts a low likelihood "
                "of elevated bacterial risk."
            ),

        "Caution":
            (
                "The model predicts moderate or uncertain risk. "
                "Check official San Mateo County beach information "
                "before entering the water."
            ),

        "Unsafe":
            (
                "The model predicts elevated bacterial risk. "
                "Avoid water contact and follow official "
                "San Mateo County guidance."
            ),

    }.get(
        str(risk).strip(),
        "Current model risk is unavailable.",
    )


# ==========================================================
# OVERALL RISK DRIVER
# ==========================================================

def risk_driver_text(
    e_coli_risk,
    enterococcus_risk,
):

    rank = {
        "Safe": 0,
        "Caution": 1,
        "Unsafe": 2,
    }


    e_coli_risk = str(
        e_coli_risk
    ).strip()


    enterococcus_risk = str(
        enterococcus_risk
    ).strip()


    e_rank = rank.get(
        e_coli_risk,
        0,
    )


    entero_rank = rank.get(
        enterococcus_risk,
        0,
    )


    if e_rank > entero_rank:

        return (
            "Overall risk is currently driven "
            "by the E. coli prediction."
        )


    if entero_rank > e_rank:

        return (
            "Overall risk is currently driven "
            "by the Enterococcus prediction."
        )


    if (
        e_coli_risk == "Safe"
        and enterococcus_risk == "Safe"
    ):

        return (
            "Both bacteria are currently "
            "classified as Safe."
        )


    return (
        "Both bacteria are currently classified "
        f"as {e_coli_risk}."
    )


# ==========================================================
# TIMESTAMP HELPERS
# ==========================================================

def _row_value(
    row,
    field,
):

    if row is None:
        return None


    try:

        value = row.get(
            field
        )

    except Exception:

        return None


    if value is None:
        return None


    try:

        if pd.isna(
            value
        ):

            return None

    except Exception:

        pass


    text = str(
        value
    ).strip()


    if (
        text == ""
        or text.lower()
        in {
            "none",
            "nan",
            "nat",
        }
    ):

        return None


    return value


def _to_pacific_timestamp(
    value,
):

    if value is None:
        return None


    timestamp = pd.to_datetime(
        value,
        errors="coerce",
    )


    if pd.isna(
        timestamp
    ):

        return None


    try:

        if timestamp.tzinfo is None:

            timestamp = (
                timestamp
                .tz_localize(
                    PACIFIC_TIMEZONE
                )
            )

        else:

            timestamp = (
                timestamp
                .tz_convert(
                    PACIFIC_TIMEZONE
                )
            )

    except Exception:

        return None


    return timestamp


def _format_timestamp(
    timestamp,
    include_time=True,
):

    if timestamp is None:

        return "Unavailable"


    date_text = timestamp.strftime(
        "%b %d, %Y"
    )


    if not include_time:

        return date_text


    time_text = (
        timestamp
        .strftime(
            "%I:%M %p"
        )
        .lstrip(
            "0"
        )
    )


    return (
        f"{date_text} · "
        f"{time_text} PT"
    )


def _looks_date_only(
    value,
):

    if value is None:

        return False


    text = str(
        value
    ).strip()


    return len(
        text
    ) <= 10


# ==========================================================
# FORECAST GENERATION TIME
# ==========================================================

def successful_generation_text(
    row=None,
    using_live=None,
):

    for field in [
        "model_run_timestamp",
        "generated_at",
        "forecast_generated_at",
    ]:

        raw_value = _row_value(
            row,
            field,
        )


        if raw_value is None:

            continue


        timestamp = _to_pacific_timestamp(
            raw_value
        )


        if timestamp is None:

            continue


        if _looks_date_only(
            raw_value
        ):

            return (
                _format_timestamp(
                    timestamp,
                    include_time=False,
                )
                + " · exact run time unavailable"
            )


        return _format_timestamp(
            timestamp,
            include_time=True,
        )


    raw_value = _row_value(
        row,
        "data_last_updated",
    )


    if raw_value is not None:

        timestamp = _to_pacific_timestamp(
            raw_value
        )


        if timestamp is not None:

            return (
                _format_timestamp(
                    timestamp,
                    include_time=False,
                )
                + " · exact run time unavailable"
            )


    return "Generation time unavailable"


# ==========================================================
# LATEST INPUT DATE
# ==========================================================

def latest_input_text(
    row=None,
):

    for field in [
        "input_data_end_date",
        "source_record_date",
        "data_last_updated",
    ]:

        raw_value = _row_value(
            row,
            field,
        )


        if raw_value is None:

            continue


        timestamp = pd.to_datetime(
            raw_value,
            errors="coerce",
        )


        if pd.isna(
            timestamp
        ):

            continue


        return timestamp.strftime(
            "%b %d, %Y"
        )


    return "Input date unavailable"


# ==========================================================
# FRESHNESS CHIP
# ==========================================================

def freshness_chip(
    updated_date,
):

    updated = pd.to_datetime(
        updated_date,
        errors="coerce",
    )


    if pd.isna(
        updated
    ):

        return (
            '<span class="bg-fresh-chip stale">'
            'Input date unavailable'
            '</span>'
        )


    try:

        if updated.tzinfo is not None:

            updated = (
                updated
                .tz_convert(
                    PACIFIC_TIMEZONE
                )
                .tz_localize(
                    None
                )
            )

    except Exception:

        pass


    today = (
        pd.Timestamp.now(
            tz=PACIFIC_TIMEZONE
        )
        .tz_localize(
            None
        )
        .normalize()
    )


    days_old = (
        today
        - updated.normalize()
    ).days


    if days_old <= 0:

        text = (
            "Latest input: today"
        )

        css_class = (
            "current"
        )


    elif days_old == 1:

        text = (
            "Latest input: yesterday"
        )

        css_class = (
            "current"
        )


    elif days_old <= 7:

        text = (
            f"Latest input: {days_old} days ago"
        )

        css_class = (
            "warn"
        )


    else:

        text = (
            "Older input · "
            + updated.strftime(
                "%b %d, %Y"
            )
        )

        css_class = (
            "stale"
        )


    return (
        f'<span class="bg-fresh-chip {css_class}">'
        f'{text}'
        f'</span>'
    )


# ==========================================================
# SEGMENTED PROBABILITY METER
# ==========================================================

def probability_meter(
    probability,
    caution_threshold,
    unsafe_threshold,
    risk,
):

    probability = max(
        0.0,
        min(
            float(
                probability
            ),
            1.0,
        ),
    )


    value = (
        probability
        * 100
    )


    caution = (
        float(
            caution_threshold
        )
        * 100
    )


    unsafe = (
        float(
            unsafe_threshold
        )
        * 100
    )


    safe_width = max(
        caution,
        0,
    )


    caution_width = max(
        unsafe - caution,
        0,
    )


    unsafe_width = max(
        100 - unsafe,
        0,
    )


    marker_position = min(
        max(
            value,
            1.5,
        ),
        98.5,
    )


    css_class = risk_class(
        risk
    )


    return f"""
<div class="bg-prob-meter {css_class}">

    <div class="bg-prob-track">

        <div
            class="bg-prob-zone safe"
            style="width:{safe_width:.2f}%;">
        </div>

        <div
            class="bg-prob-zone caution"
            style="width:{caution_width:.2f}%;">
        </div>

        <div
            class="bg-prob-zone unsafe"
            style="width:{unsafe_width:.2f}%;">
        </div>

        <div
            class="bg-prob-marker"
            style="left:{marker_position:.2f}%;">

            <div class="bg-prob-marker-dot">
            </div>

        </div>

    </div>


    <div class="bg-prob-zone-labels">

        <div>

            <strong>
                Safe
            </strong>

            <span>
                &lt; {caution:.0f}%
            </span>

        </div>


        <div>

            <strong>
                Caution
            </strong>

            <span>
                {caution:.0f}%–&lt;{unsafe:.0f}%
            </span>

        </div>


        <div>

            <strong>
                Unsafe
            </strong>

            <span>
                ≥ {unsafe:.0f}%
            </span>

        </div>

    </div>

</div>
"""


# ==========================================================
# FOOTER
# ==========================================================

def render_footer(
    model_version=None,
):

    version_html = ""


    if model_version:

        version_html = (
            " &nbsp;·&nbsp; "
            + "<span>"
            + html.escape(
                str(
                    model_version
                )
            )
            + "</span>"
        )


    st.html(
        f"""
<div class="bg-site-footer">

    <div>

        {APP_NAME}
        &nbsp;·&nbsp;
        Experimental research prototype
        {version_html}

    </div>


    <div class="bg-site-footer-links">

        <a
            href="{OFFICIAL_URL}"
            target="_blank"
            rel="noopener noreferrer"
        >
            Official San Mateo County Beach Status
        </a>

        <span>
            ·
        </span>

        <a
            href="{GITHUB_URL}"
            target="_blank"
            rel="noopener noreferrer"
        >
            GitHub
        </a>

        <span>
            ·
        </span>

        <span>
            LagoonCast methodology
        </span>

    </div>

</div>
"""
    )
