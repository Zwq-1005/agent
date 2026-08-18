import uuid
import json
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.config import UPLOAD_DIR
from app.models.file import UploadedFile as UploadedFileModel
from app.models.session import AnalysisSession
from app.services.file_service import (
    parse_file,
    get_preview,
    get_data_quality_report,
    clean_data,
    compute_auto_stats,
)

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

# File size limits
BASIC_MAX_SIZE = 1 * 1024 * 1024     # 1 MB
VIP_MAX_SIZE = 20 * 1024 * 1024      # 20 MB


class FieldDefinitionItem(BaseModel):
    original_name: str
    display_name: str
    field_type: str  # numeric, categorical, ordinal, datetime, text, id
    unit: Optional[str] = ""
    description: Optional[str] = ""
    levels: Optional[str] = ""


class SaveFieldsRequest(BaseModel):
    fields: List[FieldDefinitionItem]


class CleanDataRequest(BaseModel):
    file_id: int
    drop_duplicates: bool = False
    fill_numeric: Optional[str] = None  # "mean", "median", "mode"
    fill_categorical: Optional[str] = None  # "mode", "missing_category"
    remove_outliers: bool = False
    outlier_columns: Optional[List[str]] = None


def get_file_size_limit(vip_tier: Optional[str] = None) -> int:
    """Determine file size limit based on VIP tier."""
    if vip_tier == "vip":
        return VIP_MAX_SIZE
    return BASIC_MAX_SIZE


# ─── Upload ────────────────────────────────────────────────────────────────────────

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[int] = Form(default=None),
    x_vip_tier: Optional[str] = Header(default=None),
    db: Session = Depends(get_session),
):
    """Upload a data file, parse it, and return preview data."""
    # Validate file extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".csv", ".xlsx", ".xls", ".json", ".sav", ".dta"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {suffix}。支持 CSV, Excel, JSON, SPSS (.sav), Stata (.dta)",
        )

    # Read file content and check size
    content = await file.read()
    file_size = len(content)
    size_limit = get_file_size_limit(x_vip_tier)

    if file_size > size_limit:
        limit_mb = size_limit / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件大小 ({file_size / (1024 * 1024):.1f}MB) 超过限制 ({limit_mb:.0f}MB)。"
                   f"基础版限制 1MB，VIP 限制 20MB。",
        )

    # Save file to disk with unique name
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name
    file_path.write_bytes(content)

    # Parse file
    try:
        df, file_type = parse_file(file_path)
    except ImportError as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    # Get or create session
    if session_id:
        session = db.get(AnalysisSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = AnalysisSession(title=f"医学统计 - {file.filename}")
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save file metadata to DB
    columns = df.columns.tolist()
    db_file = UploadedFileModel(
        session_id=session.id,
        filename=file.filename or "unknown",
        file_path=str(file_path),
        file_type=file_type,
        columns=columns,
        row_count=len(df),
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Build preview
    preview = get_preview(df, n_rows=5)

    return {
        "file_id": db_file.id,
        "session_id": session.id,
        "filename": file.filename,
        "columns": preview["columns"],
        "preview_rows": preview["preview_rows"],
        "total_rows": preview["total_rows"],
    }


# ─── Preview ───────────────────────────────────────────────────────────────────────

@router.get("/preview/{file_id}")
async def get_file_preview(file_id: int, db: Session = Depends(get_session)):
    """Get preview data for a previously uploaded file."""
    db_file = db.get(UploadedFileModel, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    try:
        df, _ = parse_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")

    preview = get_preview(df, n_rows=5)

    return {
        "file_id": db_file.id,
        "filename": db_file.filename,
        "columns": preview["columns"],
        "preview_rows": preview["preview_rows"],
        "total_rows": preview["total_rows"],
        "fields": db_file.field_definitions,
    }


# ─── Field Definitions ─────────────────────────────────────────────────────────────

@router.put("/{file_id}/fields")
async def save_field_definitions(
    file_id: int,
    req: SaveFieldsRequest,
    db: Session = Depends(get_session),
):
    """Save field definitions for an uploaded file."""
    db_file = db.get(UploadedFileModel, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    db_file.field_definitions = [f.model_dump() for f in req.fields]
    db.add(db_file)
    db.commit()

    return {"success": True, "field_count": len(req.fields)}


@router.get("/{file_id}/fields")
async def get_field_definitions(
    file_id: int,
    db: Session = Depends(get_session),
):
    """Get field definitions for an uploaded file."""
    db_file = db.get(UploadedFileModel, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    return db_file.field_definitions or []


# ─── Data Quality ──────────────────────────────────────────────────────────────────

@router.get("/{file_id}/quality")
async def get_quality_report(file_id: int, db: Session = Depends(get_session)):
    """Generate a data quality report for an uploaded file."""
    db_file = db.get(UploadedFileModel, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    try:
        df, _ = parse_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")

    return get_data_quality_report(df)


# ─── Data Cleaning ─────────────────────────────────────────────────────────────────

@router.post("/clean")
async def clean_uploaded_data(
    req: CleanDataRequest,
    db: Session = Depends(get_session),
):
    """Clean an uploaded data file and return the result."""
    db_file = db.get(UploadedFileModel, req.file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    try:
        df, file_type = parse_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")

    # Clean data
    cleaned_df, summary = clean_data(
        df,
        drop_duplicates=req.drop_duplicates,
        fill_numeric=req.fill_numeric,
        fill_categorical=req.fill_categorical,
        remove_outliers=req.remove_outliers,
        outlier_columns=req.outlier_columns,
    )

    # Save cleaned version as a new file
    clean_name = f"{uuid.uuid4().hex}_cleaned_{db_file.filename}"
    clean_path = UPLOAD_DIR / clean_name

    if file_type in ("csv",):
        cleaned_df.to_csv(clean_path, index=False)
    elif file_type in ("xlsx", "sav", "dta"):
        cleaned_df.to_csv(clean_path.with_suffix(".csv"), index=False)
        clean_path = clean_path.with_suffix(".csv")
    else:
        cleaned_df.to_csv(clean_path.with_suffix(".csv"), index=False)
        clean_path = clean_path.with_suffix(".csv")

    # Create new file record
    clean_db_file = UploadedFileModel(
        session_id=db_file.session_id,
        filename=f"清洗后_{db_file.filename}",
        file_path=str(clean_path),
        file_type="csv",
        columns=cleaned_df.columns.tolist(),
        row_count=len(cleaned_df),
        field_definitions=db_file.field_definitions,
    )
    db.add(clean_db_file)
    db.commit()
    db.refresh(clean_db_file)

    preview = get_preview(cleaned_df, n_rows=5)

    return {
        "file_id": clean_db_file.id,
        "session_id": clean_db_file.session_id,
        "filename": clean_db_file.filename,
        "columns": preview["columns"],
        "preview_rows": preview["preview_rows"],
        "total_rows": preview["total_rows"],
        "cleaning_summary": summary,
    }


# ─── Auto Statistics ───────────────────────────────────────────────────────────────

@router.get("/{file_id}/auto-stats")
async def get_auto_statistics(file_id: int, db: Session = Depends(get_session)):
    """Compute automatic descriptive statistics for a file."""
    db_file = db.get(UploadedFileModel, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    try:
        df, _ = parse_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")

    return compute_auto_stats(df)
