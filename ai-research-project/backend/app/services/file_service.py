"""File parsing and data cleaning services."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd
import numpy as np

# ─── File Parsing ──────────────────────────────────────────────────────────────────


def parse_file(file_path: Path) -> Tuple[pd.DataFrame, str]:
    """Parse a file and return DataFrame + file type.

    Supported formats: CSV, Excel (.xlsx/.xls), JSON, SPSS (.sav), Stata (.dta)
    """
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
        file_type = "csv"
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, engine="openpyxl")
        file_type = "xlsx"
    elif suffix == ".json":
        df = pd.read_json(file_path)
        file_type = "json"
    elif suffix == ".sav":
        try:
            import pyreadstat
            df, meta = pyreadstat.read_sav(file_path)
            file_type = "sav"
        except ImportError:
            raise ImportError(
                "需要安装 pyreadstat 来读取 SPSS (.sav) 文件。"
                "请运行: pip install pyreadstat"
            )
    elif suffix == ".dta":
        try:
            import pyreadstat
            df, meta = pyreadstat.read_dta(file_path)
            file_type = "dta"
        except ImportError:
            raise ImportError(
                "需要安装 pyreadstat 来读取 Stata (.dta) 文件。"
                "请运行: pip install pyreadstat"
            )
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    return df, file_type


# ─── Data Preview ──────────────────────────────────────────────────────────────────


def get_preview(df: pd.DataFrame, n_rows: int = 5) -> Dict[str, Any]:
    """Extract preview data from a DataFrame."""
    columns = df.columns.tolist()
    preview_df = df.head(n_rows).fillna("")

    # Convert to JSON-serializable format
    preview_rows: List[Dict[str, Any]] = []
    for _, row in preview_df.iterrows():
        row_dict: Dict[str, Any] = {}
        for col in columns:
            val = row[col]
            if pd.isna(val):
                row_dict[col] = None
            elif hasattr(val, "item"):  # numpy types
                row_dict[col] = val.item()
            else:
                row_dict[col] = str(val) if not isinstance(val, (int, float, bool, str, type(None))) else val
        preview_rows.append(row_dict)

    return {
        "columns": columns,
        "preview_rows": preview_rows,
        "total_rows": len(df),
    }


# ─── Data Quality Report ───────────────────────────────────────────────────────────


def get_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a data quality report for the DataFrame."""
    total_rows = len(df)
    columns_info = []

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = round(missing_count / total_rows * 100, 2)
        unique_count = int(series.nunique())
        dtype = str(series.dtype)

        col_info = {
            "column": col,
            "dtype": dtype,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
            "duplicate_pct": round((total_rows - unique_count) / total_rows * 100, 2),
        }

        # Numeric columns: basic stats + outlier detection
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            col_info["min"] = float(desc["min"]) if not pd.isna(desc["min"]) else None
            col_info["max"] = float(desc["max"]) if not pd.isna(desc["max"]) else None
            col_info["mean"] = float(desc["mean"]) if not pd.isna(desc["mean"]) else None
            col_info["std"] = float(desc["std"]) if not pd.isna(desc["std"]) else None

            # IQR-based outlier detection
            q1 = float(desc["25%"])
            q3 = float(desc["75%"])
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outlier_count = int(((series < lower) | (series > upper)).sum())
                col_info["outlier_count"] = outlier_count
                col_info["outlier_pct"] = round(outlier_count / total_rows * 100, 2)
            else:
                col_info["outlier_count"] = 0
                col_info["outlier_pct"] = 0

        # Categorical columns: value distribution
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
            value_counts = series.value_counts().head(10).to_dict()
            col_info["top_values"] = {str(k): int(v) for k, v in value_counts.items()}

        columns_info.append(col_info)

    # Overall stats
    duplicate_rows = int(df.duplicated().sum())
    total_missing = int(df.isna().sum().sum())
    total_cells = total_rows * len(df.columns)

    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round(duplicate_rows / total_rows * 100, 2) if total_rows > 0 else 0,
        "total_missing": total_missing,
        "missing_pct": round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0,
        "columns": columns_info,
    }


# ─── Data Cleaning ─────────────────────────────────────────────────────────────────


def clean_data(
    df: pd.DataFrame,
    drop_duplicates: bool = False,
    fill_numeric: Optional[str] = None,  # "mean", "median", "mode", or None
    fill_categorical: Optional[str] = None,  # "mode", "missing_category", or None
    remove_outliers: bool = False,
    outlier_columns: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean a DataFrame and return the cleaned version + a summary of changes.

    Args:
        df: Input DataFrame
        drop_duplicates: Remove duplicate rows
        fill_numeric: Strategy for filling missing numeric values
        fill_categorical: Strategy for filling missing categorical values
        remove_outliers: Remove rows with outliers
        outlier_columns: Specific columns to check for outliers

    Returns:
        Tuple of (cleaned DataFrame, cleaning summary dict)
    """
    df_clean = df.copy()
    rows_before = len(df_clean)
    summary: Dict[str, Any] = {"rows_before": rows_before, "actions": []}

    # 1. Drop duplicates
    if drop_duplicates:
        dupes_before = int(df_clean.duplicated().sum())
        if dupes_before > 0:
            df_clean = df_clean.drop_duplicates()
            summary["actions"].append({
                "action": "drop_duplicates",
                "rows_removed": dupes_before,
                "message": f"删除 {dupes_before} 行重复数据",
            })

    # 2. Fill missing numeric values
    if fill_numeric:
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            missing = int(df_clean[col].isna().sum())
            if missing == 0:
                continue
            if fill_numeric == "mean":
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
            elif fill_numeric == "median":
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            elif fill_numeric == "mode":
                df_clean[col] = df_clean[col].fillna(df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else 0)
            summary["actions"].append({
                "action": "fill_numeric",
                "column": col,
                "strategy": fill_numeric,
                "filled_count": missing,
                "message": f"用{fill_numeric}填充列 '{col}' 的 {missing} 个缺失值",
            })

    # 3. Fill missing categorical values
    if fill_categorical:
        cat_cols = df_clean.select_dtypes(include=["object", "category"]).columns
        for col in cat_cols:
            missing = int(df_clean[col].isna().sum())
            if missing == 0:
                continue
            if fill_categorical == "mode":
                if not df_clean[col].mode().empty:
                    fill_val = df_clean[col].mode().iloc[0]
                    df_clean[col] = df_clean[col].fillna(fill_val)
            elif fill_categorical == "missing_category":
                df_clean[col] = df_clean[col].fillna("缺失")
            summary["actions"].append({
                "action": "fill_categorical",
                "column": col,
                "strategy": fill_categorical,
                "filled_count": missing,
                "message": f"用'{fill_categorical}'策略填充列 '{col}' 的 {missing} 个缺失值",
            })

    # 4. Remove outliers (IQR method)
    if remove_outliers:
        outlier_columns = outlier_columns or df_clean.select_dtypes(include=[np.number]).columns.tolist()
        outlier_mask = pd.Series(False, index=df_clean.index)
        for col in outlier_columns:
            if col not in df_clean.columns:
                continue
            if not pd.api.types.is_numeric_dtype(df_clean[col]):
                continue
            q1 = df_clean[col].quantile(0.25)
            q3 = df_clean[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outlier_mask |= (df_clean[col] < lower) | (df_clean[col] > upper)
        outlier_count = int(outlier_mask.sum())
        if outlier_count > 0:
            df_clean = df_clean[~outlier_mask]
            summary["actions"].append({
                "action": "remove_outliers",
                "rows_removed": outlier_count,
                "message": f"通过IQR方法删除 {outlier_count} 行含有异常值的数据",
            })

    summary["rows_after"] = len(df_clean)
    summary["total_removed"] = rows_before - len(df_clean)

    return df_clean, summary


# ─── Auto Statistics ───────────────────────────────────────────────────────────────


def compute_auto_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute automatic descriptive statistics for all columns."""
    stats = {}

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        stats[col] = {
            "type": "numeric",
            "count": int(len(series)),
            "mean": round(float(series.mean()), 3),
            "std": round(float(series.std()), 3),
            "min": round(float(series.min()), 3),
            "q25": round(float(series.quantile(0.25)), 3),
            "median": round(float(series.median()), 3),
            "q75": round(float(series.quantile(0.75)), 3),
            "max": round(float(series.max()), 3),
            "skewness": round(float(series.skew()), 3),
            "kurtosis": round(float(series.kurtosis()), 3),
        }

    for col in cat_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        value_counts = series.value_counts()
        stats[col] = {
            "type": "categorical",
            "count": int(len(series)),
            "unique": int(series.nunique()),
            "mode": str(value_counts.index[0]) if len(value_counts) > 0 else None,
            "top_values": [
                {"value": str(k), "count": int(v), "pct": round(v / len(series) * 100, 2)}
                for k, v in value_counts.head(10).items()
            ],
        }

    return stats
