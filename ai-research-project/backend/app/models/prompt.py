from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime


class PromptTemplate(SQLModel, table=True):
    __tablename__ = "prompt_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    category: str = Field(max_length=64)
    description: str = Field(default="", max_length=1024)
    content: str = Field(default="")
    is_default: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
