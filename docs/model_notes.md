# Model Notes

## Purpose

LagoonCast estimates the probability that bacteria levels may exceed recreational water-quality thresholds at a pilot recreational water site.

The project currently produces model outputs for:

* E. coli
* Enterococcus

## Backend workflow

The main backend notebook is:
notebooks/AquaCast\_Model\_Pipeline\_Version\_10.ipynb
The notebook uses:
data/Aquacast15Years\_Weekly.csv

It trains and evaluates bacteria exceedance models, then exports a simplified prediction file for the Streamlit app.

## Streamlit V1 workflow

For V1, the app does not retrain models when a user opens it. Instead, it reads:
data/app\_predictions.csv

This keeps the web app simple, fast, and easier to debug.

## App prediction columns

`data/app\_predictions.csv` includes:

* `site\_name`
* `latitude`
* `longitude`
* `prediction\_date`
* `data\_last\_updated`
* `e\_coli\_probability`
* `enterococcus\_probability`
* `e\_coli\_risk`
* `enterococcus\_risk`
* `overall\_risk`
* `risk\_color`
* `safety\_message`

## Risk labels

The app displays risk levels as:

* Safe
* Caution
* Unsafe

The overall risk is based on the bacteria-specific model outputs.

## Included model files

The repository includes model metadata and feature lists in `models/`:

* `model\_manifest.json`
* `e\_coli\_model\_info.json`
* `enterococcus\_model\_info.json`
* `e\_coli\_features.txt`
* `enterococcus\_features.txt`

The trained `.joblib` model files are not included in this public V1 repository because the app uses the precomputed prediction CSV. If future versions load models directly, model files should be added only if they are small, non-sensitive, and clearly documented.

## Disclaimer

This model is experimental and intended for student research and app-development purposes only. It is not an official public-health advisory system. Users should always follow official beach closure and advisory notices.

