"""
Carnot Data Engineer Assignment - Satellite Intelligence
Author: Neha Pattankar
Pipeline: Ingest → Clean → Join → Analyse → Export
"""

import pandas as pd
import numpy as np

# 1. INGEST

def ingest(readings_path: str, metadata_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    readings = pd.read_csv(readings_path)
    metadata = pd.read_csv(metadata_path)
    print(f"[ingest] readings: {readings.shape}, metadata: {metadata.shape}")
    return readings, metadata


# 2. CLEAN READINGS

def clean_readings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    original_len = len(df)

    # ── Issue 1: Mixed date formats → parse to a single datetime ──────────
    # Three formats found: YYYY-MM-DD, DD/MM/YYYY, DD-Mon-YYYY
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, format="mixed")

    # ── Issue 2: sensor_status has inconsistent case + whitespace ─────────
    # Values seen: 'OK', 'ok', 'OK ', ' OK', 'Error', 'ERROR', 'error'
    # Normalise to lowercase, strip whitespace → 'ok' or 'error'
    df["sensor_status"] = df["sensor_status"].str.strip().str.lower()

    # ── Issue 3: sensor_status NaN (137 rows) → treat as 'unknown' ────────
    # We cannot call these 'ok'; flagging lets analysis exclude or include.
    df["sensor_status"] = df["sensor_status"].fillna("unknown")

    # ── Issue 4: NDVI values outside valid range [-1, 1] (104 rows, 3%) ───
    # These are sensor/transmission errors — cannot impute meaningfully
    # without neighbouring-day context (out of scope here). Flag and nullify.
    invalid_ndvi_mask = (df["ndvi_value"] < -1) | (df["ndvi_value"] > 1)
    df.loc[invalid_ndvi_mask, "ndvi_value"] = np.nan
    df["ndvi_flag"] = invalid_ndvi_mask.map({True: "out_of_range", False: "ok"})
    print(f"[clean_readings] NDVI out-of-range nullified: {invalid_ndvi_mask.sum()} rows")

    return df


# 3. CLEAN METADATA

def clean_metadata(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ── Issue 5: sowing_date stored as string → parse to datetime ─────────
    df["sowing_date"] = pd.to_datetime(df["sowing_date"])

    return df


# 4. JOIN

def join_datasets(readings: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    # Inner join: only keep rows where both sides match.
    joined = readings.merge(metadata, on="parcel_id", how="inner")
    print(f"[join] joined dataset: {joined.shape}")
    return joined


# 5. EXPORT

def export(df: pd.DataFrame, output_path: str) -> None:
    df.to_csv(output_path, index=False)
    print(f"[export] Written to {output_path} — {df.shape[0]} rows, {df.shape[1]} cols")


# 6. ANALYSIS – NDVI before vs after sowing

def analyse_ndvi_around_sowing(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each crop_type, compute mean NDVI in the 30 days before and after
    sowing_date. Excludes rows where sensor_status is not 'ok'.
    """
    # Use only clean sensor readings
    clean = df[df["sensor_status"] == "ok"].copy()

    # Days relative to sowing
    clean["days_from_sowing"] = (clean["date"] - clean["sowing_date"]).dt.days

    before = (
        clean[(clean["days_from_sowing"] >= -30) & (clean["days_from_sowing"] < 0)]
        .groupby("crop_type")
        .agg(
            mean_ndvi_before=("ndvi_value", "mean"),
            n_parcels_before=("parcel_id", "nunique"),
        )
    )

    after = (
        clean[(clean["days_from_sowing"] > 0) & (clean["days_from_sowing"] <= 30)]
        .groupby("crop_type")
        .agg(
            mean_ndvi_after=("ndvi_value", "mean"),
            n_parcels_after=("parcel_id", "nunique"),
        )
    )

    result = before.join(after, how="outer")

    # n_parcels = parcels that appear in at least one of the two windows
    result["n_parcels"] = result[["n_parcels_before", "n_parcels_after"]].max(axis=1).astype(int)
    result = result[["mean_ndvi_before", "mean_ndvi_after", "n_parcels"]].round(4)
    result = result.reset_index()

    return result


# MAIN

if __name__ == "__main__":
    # Paths
    READINGS_PATH  = "data/parcel_readings.csv"
    METADATA_PATH  = "data/parcel_metadata.csv"
    OUTPUT_PATH    = "output/cleaned_parcel_timeseries.csv"

    # Run pipeline
    readings, metadata = ingest(READINGS_PATH, METADATA_PATH)
    readings_clean     = clean_readings(readings)
    metadata_clean     = clean_metadata(metadata)
    joined             = join_datasets(readings_clean, metadata_clean)
    export(joined, OUTPUT_PATH)

    # Run analysis
    print("\n── NDVI Analysis: 30 days before vs after sowing ──")
    analysis = analyse_ndvi_around_sowing(joined)
    print(analysis.to_string(index=False))
