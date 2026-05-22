# Satellite Intelligence Data Pipeline

## Overview

This project is a data engineering pipeline built for processing and analysing parcel-level agricultural satellite intelligence data.

The pipeline ingests raw parcel sensor readings and parcel metadata, performs data quality checks and cleaning, joins the datasets, and analyses vegetation growth trends using NDVI (Normalized Difference Vegetation Index).

The analysis compares average NDVI values in the 30 days before and after crop sowing dates to evaluate vegetation growth patterns across crop types.

---

# Project Structure

```text
satellite-intelligence/
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

## Data Quality Audit

| Issue | Count | Action Taken |
|-------|-------|--------------|
| Mixed date formats (3 formats: DD/MM/YYYY, YYYY-MM-DD, DD-Mon-YYYY) | across 3447 rows | Standardized using pd.to_datetime() with dayfirst=True |
| Invalid NDVI values (outside -1 to 1) | 104 rows | Replaced with NaN |
| Missing sensor_status | 137 rows | Filled as "unknown" |
| Inconsistent sensor_status casing/spacing (ok, OK, OK , Error, ERROR etc.) | 8 variants | Stripped and normalized to lowercase |
| Duplicate parcel+date combinations | 8 rows | Logged and retained — multiple readings per day valid in sensor data |
| Exact duplicates | 0 | No action needed |

---

# Production Readiness Reflection

## What three things would you change?

1. **Switch from Pandas to PySpark/Databricks** — Pandas loads everything into memory. At 100x scale (~350K rows), this would cause memory issues. PySpark handles distributed processing and can scale horizontally.

2. **Replace CSV with Delta Lake format** — CSVs have no schema enforcement, no ACID transactions, and no versioning. Delta Lake gives you all three plus time travel for debugging bad runs.

3. **Parameterize the pipeline with a config file** — Currently paths are hardcoded. For daily runs, input paths, date ranges, and thresholds should come from a config so you can change them without touching code.

## What would you monitor in production?

- Row count after each stage — to catch silent data drops mid-pipeline
- Null rate on `ndvi_value` column — a sudden spike means sensor issues upstream
- `sensor_status` distribution daily — if "error" % increases, something is wrong with the source
- Pipeline run duration — sudden slowdowns indicate data volume anomalies

## What is the most likely thing to silently break?

Date parsing. If the upstream sensor system changes its date format slightly, `pd.to_datetime()` will silently produce `NaT` values instead of throwing an error. This would corrupt the entire NDVI window calculation — before/after sowing comparisons would return NaN with no warning.

---

# AI Usage

Claude (Anthropic) was used during this assignment for code review, debugging pipeline logic, and README structuring. All analytical decisions, data quality observations, and interpretations are my own.



# Author

Neha Pattankar
