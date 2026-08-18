from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, JSON


class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, foreign_key="analysis_sessions.id")
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=1024)
    file_type: str = Field(max_length=16)  # csv, xlsx, json, sav, dta
    columns: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    row_count: int = Field(default=0)
    field_definitions: Optional[List[Dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    # Relationships
    session: Optional["AnalysisSession"] = Relationship(back_populates="files")
