import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse, Response
from sqlmodel import Session, select

from app.database import get_session
from app.models.file import UploadedFile as UploadedFileModel
from app.models.session import AnalysisSession
from app.services.report_service import generate_word_report_bytes, generate_pdf_report_bytes
from app.graph.stats_graph import run_graph_stream

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])


@router.get("/stream")
async def analyze_stream(
    session_id: int = Query(..., description="Session ID"),
    message: str = Query(..., description="Natural language analysis instruction"),
    file_id: Optional[int] = Query(None, description="Specific file ID (uses latest if omitted)"),
    x_field_definitions: Optional[str] = Header(default=None, alias="X-Field-Definitions"),
    db: Session = Depends(get_session),
):
    """
    Stream analysis results via Server-Sent Events (SSE).

    Events:
        - thinking: AI is reasoning about the intent
        - coding: AI is generating code
        - executing: Code is being executed
        - result: JSON result (text, table, chart)
        - paper_text: Thesis-ready formatted text
        - error: Execution error
        - done: Analysis complete
    """
    # Validate session
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the uploaded file for this session
    if file_id:
        db_file = db.get(UploadedFileModel, file_id)
        if not db_file or db_file.session_id != session_id:
            raise HTTPException(status_code=404, detail="File not found for this session")
    else:
        stmt = select(UploadedFileModel).where(
            UploadedFileModel.session_id == session_id
        ).order_by(UploadedFileModel.created_at.desc())
        db_file = db.exec(stmt).first()

    if not db_file:
        raise HTTPException(
            status_code=400,
            detail="No uploaded file found for this session. Please upload a file first.",
        )

    file_path = db_file.file_path
    if not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Uploaded file no longer exists on disk. Please re-upload.",
        )

    # Parse field definitions from header
    field_definitions = []
    if x_field_definitions:
        try:
            field_definitions = json.loads(x_field_definitions)
        except json.JSONDecodeError:
            field_definitions = db_file.field_definitions or []
    elif db_file.field_definitions:
        field_definitions = db_file.field_definitions

    # Build df_info from stored metadata
    df_info = {
        "columns": db_file.columns,
        "row_count": db_file.row_count,
        "dtypes": {},
        "field_definitions": field_definitions,
    }

    async def event_generator():
        async for sse_event in run_graph_stream(
            user_message=message,
            file_path=file_path,
            df_info=df_info,
        ):
            yield sse_event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Report Export ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/report")
async def export_report(
    session_id: int,
    format: str = Query("word", pattern="^(word|pdf)$"),
    file_id: Optional[int] = Query(None),
    db: Session = Depends(get_session),
):
    """
    Export analysis results as a Word (docx) or PDF report.
    Returns the report file as a downloadable attachment.
    """
    session = db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get uploaded file info
    if file_id:
        db_file = db.get(UploadedFileModel, file_id)
    else:
        stmt = select(UploadedFileModel).where(
            UploadedFileModel.session_id == session_id
        ).order_by(UploadedFileModel.created_at.desc())
        db_file = db.exec(stmt).first()

    # Collect chat messages as results for the report
    from app.models.chat_message import ChatMessage
    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()

    results = []
    for msg in messages:
        if msg.role == "assistant" and msg.content:
            results.append({
                "type": "text",
                "title": msg.status_label or "分析输出",
                "content": msg.content,
            })

    if format == "word":
        buf = generate_word_report_bytes(session, db_file, results)
        filename = f"统计报告_{session.id}.docx"
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    else:
        buf = generate_pdf_report_bytes(session, db_file, results)
        filename = f"统计报告_{session.id}.pdf"
        return Response(
            content=buf.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
