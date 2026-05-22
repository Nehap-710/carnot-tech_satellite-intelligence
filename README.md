# Satellite Intelligence Data Pipeline

## Overview

This project is a data engineering pipeline built for processing and analysing parcel-level agricultural satellite intelligence data.

The pipeline ingests raw parcel sensor readings and parcel metadata, performs data quality checks and cleaning, joins the datasets, and analyses vegetation growth trends using NDVI (Normalized Difference Vegetation Index).

The analysis compares average NDVI values in the 30 days before and after crop sowing dates to evaluate vegetation growth patterns across crop types.

---

# Project Structure

```text
satellite-intelligence-assignment/
├── data/
│   ├── parcel_readings.csv
│   └── parcel_metadata.csv
├── notebooks/
│   └── assignment_solution.ipynb
├── src/
│   └── pipeline.py
├── outputs/
│   └── cleaned_parcel_timeseries.csv
├── README.md
└── requirements.txt
```

---

# Dataset Description

## parcel_readings.csv

Contains parcel-level time-series sensor and satellite readings.

### Columns

* `parcel_id` → unique parcel identifier
* `date` → observation date
* `ndvi_value` → vegetation index value
* `temperature_c` → temperature in Celsius
* `rainfall_mm` → rainfall in millimeters
* `sensor_status` → sensor health status

---

## parcel_metadata.csv

Contains static parcel metadata.

### Columns

* `parcel_id` → unique parcel identifier
* `crop_type` → crop grown in the parcel
* `sowing_date` → crop sowing date

---

# Pipeline Steps

## 1. Ingestion

* Read raw CSV datasets using Pandas.

---

## 2. Data Cleaning

### Readings Cleaning

The following quality issues were identified and handled:

* Mixed date formats standardized using `pd.to_datetime()`
* Inconsistent `sensor_status` formatting normalized
* Missing sensor statuses filled as `"unknown"`
* Invalid NDVI values outside the valid range `[-1, 1]` replaced with `NaN`
* Duplicate rows identified and logged

### Metadata Cleaning

* `sowing_date` converted to datetime format
* Duplicate parcel identifiers checked

---

## 3. Join

The cleaned datasets were joined using:

```python
merge(on="parcel_id", how="inner")
```

This ensures only parcels present in both datasets are retained.

---

# NDVI Analysis

The analysis computes average NDVI values:

* 30 days before sowing
* 30 days after sowing

for each crop type.

Only rows where:

```python
sensor_status == "ok"
```

were included in the analysis.

---

# Analysis Logic

For each parcel:

```text
days_from_sowing = observation_date - sowing_date
```

Rows were grouped into two windows:

| Window        | Range          |
| ------------- | -------------- |
| Before sowing | -30 to -1 days |
| After sowing  | 1 to 30 days   |

The pipeline then calculates:

* Mean NDVI before sowing
* Mean NDVI after sowing
* Number of unique contributing parcels

---

# Key Findings

The analysis showed that all crop types exhibited higher NDVI values after sowing, indicating expected vegetation growth after crop establishment.

Example output:

| crop_type | mean_ndvi_before | mean_ndvi_after | n_parcels |
| --------- | ---------------- | --------------- | --------- |
| soybean   | 0.2312           | 0.3286          | 4         |
| sugarcane | 0.3327           | 0.3936          | 19        |
| wheat     | 0.2058           | 0.3263          | 2         |

Observations:

* Sugarcane had the largest parcel coverage and most stable signal
* Wheat showed the largest relative NDVI increase
* NDVI trends aligned with expected agricultural growth behaviour

---

# Outputs

The pipeline exports:

## cleaned_parcel_timeseries.csv

Cleaned and joined parcel-level dataset.

---

# How to Run

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Pipeline

```bash
python src/pipeline.py
```

---

# Requirements

* Python 3.10+
* pandas
* numpy

---

# Author

Neha Pattankar
