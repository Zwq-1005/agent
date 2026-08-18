from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.prompt import PromptTemplate

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


class CreatePromptRequest(BaseModel):
    name: str
    category: str = "custom"
    description: str = ""
    content: str = ""
    is_default: bool = False


class UpdatePromptRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None


@router.get("")
async def list_prompts(
    db: Session = Depends(get_session),
    category: Optional[str] = None,
) -> List[PromptTemplate]:
    """List all prompt templates, optionally filtered by category."""
    stmt = select(PromptTemplate)
    if category:
        stmt = stmt.where(PromptTemplate.category == category)
    stmt = stmt.order_by(PromptTemplate.category, PromptTemplate.created_at)
    prompts = db.exec(stmt).all()
    return list(prompts)


@router.get("/categories")
async def list_categories(db: Session = Depends(get_session)):
    """List distinct prompt categories."""
    prompts = db.exec(select(PromptTemplate.category).distinct()).all()
    return list(prompts)


@router.post("")
async def create_prompt(
    req: CreatePromptRequest,
    db: Session = Depends(get_session),
):
    """Create a new prompt template."""
    prompt = PromptTemplate(
        name=req.name,
        category=req.category,
        description=req.description,
        content=req.content,
        is_default=req.is_default,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}")
async def get_prompt(prompt_id: int, db: Session = Depends(get_session)):
    """Get a specific prompt template."""
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Template not found")
    return prompt


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: int,
    req: UpdatePromptRequest,
    db: Session = Depends(get_session),
):
    """Update a prompt template."""
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prompt, key, value)

    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: int, db: Session = Depends(get_session)):
    """Delete a prompt template."""
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(prompt)
    db.commit()
    return {"detail": "ok"}
