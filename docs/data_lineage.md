# Data Lineage

## Project

LagoonCast uses public water-quality and environmental data to produce experimental bacteria-risk predictions for a pilot recreational water site.

## Main backend dataset

The cleaned backend dataset stored in this repository is:
data/Aquacast15Years\_Weekly.csv

This file is the working dataset used by the model pipeline notebook. It contains weekly bacteria records and engineered environmental features, including rainfall, temperature, prior-sample, and derived weather features.

## App-ready prediction output

The Streamlit app does not read the full backend dataset directly. It reads:
data/app\_predictions.csv

This file is a simplified prediction table exported from the model pipeline. It contains the site name, location, prediction date, bacteria-specific probabilities, risk labels, overall risk, color label, and safety message.

## Public water-quality data sources

California Open Data Portal surface-water fecal indicator bacteria dataset:

* https://data.ca.gov/dataset/surface-water-fecal-indicator-bacteria-results
* https://data.ca.gov/dataset/surface-water-fecal-indicator-bacteria-results/resource/15a63495-8d9f-4a49-b43a-3092ef3106b9
* https://data.ca.gov/dataset/surface-water-fecal-indicator-bacteria-results/resource/04d98c22-5523-4cc1-86e7-3a6abf40bb60
* https://data.ca.gov/dataset/surface-water-fecal-indicator-bacteria-results/resource/1d333989-559a-433f-bb43d21da2b9

These sources provide the fecal indicator bacteria records used for model development and evaluation.

## Public weather data sources

NOAA/NCEI daily weather data documentation and access points:

* https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily
* https://www.ncei.noaa.gov/cdo-web/
* https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation

NOAA/NCEI daily-summaries CSV access URLs used for the compiled weather data:

* https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries\&stations=USC00047339\&startDate=2004-09-01\&endDate=2026-05-31\&format=csv\&units=metric
* https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries\&stations=US1CASM0006\&startDate=2008-11-10\&endDate=2026-05-31\&format=csv\&units=metric

## Processing summary

The model pipeline notebook:

1. Loads the cleaned weekly bacteria and environmental dataset.
2. Filters and prepares E. coli and Enterococcus exceedance targets.
3. Uses rainfall, temperature, seasonal, and prior-sample features.
4. Trains classification models for bacteria exceedance prediction.
5. Evaluates binary Safe/Unsafe model metrics.
6. Exports app-ready prediction output to `data/app\_predictions.csv`.

## Public repository note

This repository is public. It should not contain private credentials, API keys, passwords, private contact information, or non-public data. The app-ready CSV is designed to keep the first public version simple and reproducible.

