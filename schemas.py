from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    diagnostic_context: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class DocumentBase(BaseModel):
    filename: Optional[str] = None
    document_type: Optional[str] = None
    text_content: str


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    project_id: int

    class Config:
        orm_mode = True


class AnalysisCreate(BaseModel):
    pass


class AnalysisRead(BaseModel):
    id: int
    project_id: int
    created_at: datetime
    output_json: Optional[str] = None

    class Config:
        orm_mode = True


class ProjectWithChildren(ProjectRead):
    documents: List[DocumentRead] = []
    analyses: List[AnalysisRead] = []

