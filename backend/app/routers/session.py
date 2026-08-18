from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.session import AnalysisSession
from app.models.chat_message import ChatMessage

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: str = "未命名分析"


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class AddMessageRequest(BaseModel):
    role: str
    content: str
    status: Optional[str] = None
    status_label: Optional[str] = None


# ─── Session CRUD ──────────────────────────────────────────────────────────────────

@router.post("")
async def create_session(
    req: CreateSessionRequest,
    db: Session = Depends(get_session),
):
    """Create a new analysis session."""
    session = AnalysisSession(title=req.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("")
async def list_sessions(
    db: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[AnalysisSession]:
    """List all analysis sessions, most recent first."""
    sessions = db.exec(
        select(AnalysisSession)
        .order_by(AnalysisSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(sessions)


@router.get("/{session_id}")
async def get_session_by_id(
    session_id: int,
    db: Session = Depends(get_session),
):
    """Get a specific analysis session with its files and messages."""
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load associated files and messages
    files = db.exec(
        select("UploadedFile").where(
            "UploadedFile.session_id" == session_id
        )
    ).all()
    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()

    return {
        **session.model_dump(),
        "files": [f.model_dump() for f in files],
        "messages": [m.model_dump() for m in messages],
    }


@router.put("/{session_id}")
async def update_session(
    session_id: int,
    req: UpdateSessionRequest,
    db: Session = Depends(get_session),
):
    """Update a session's title or status."""
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    session.updated_at = datetime.now(timezone.utc)

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_session),
):
    """Delete a session, its uploaded files, and its chat messages."""
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated files from disk
    from sqlmodel import select as sm_select
    from app.models.file import UploadedFile as UploadedFileModel
    from pathlib import Path

    files = db.exec(
        sm_select(UploadedFileModel).where(UploadedFileModel.session_id == session_id)
    ).all()
    for f in files:
        file_path = Path(f.file_path)
        file_path.unlink(missing_ok=True)

    db.delete(session)
    db.commit()
    return {"detail": "ok"}


# ─── Chat Messages ─────────────────────────────────────────────────────────────────

@router.post("/{session_id}/messages")
async def add_chat_message(
    session_id: int,
    req: AddMessageRequest,
    db: Session = Depends(get_session),
):
    """Persist a chat message for this session."""
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msg = ChatMessage(
        session_id=session_id,
        role=req.role,
        content=req.content,
        status=req.status,
        status_label=req.status_label,
    )
    db.add(msg)
    session.updated_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/{session_id}/messages")
async def get_chat_messages(
    session_id: int,
    db: Session = Depends(get_session),
    limit: int = Query(200, ge=1, le=1000),
):
    """Get chat messages for a session."""
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    ).all()
    return list(messages)
