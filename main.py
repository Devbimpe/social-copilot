from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import Base, engine, get_db
from models import Project, Document, AnalysisRun
from schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectWithChildren,
    DocumentCreate,
    DocumentRead,
    AnalysisRead,
)
#from openai_client import run_social_risk_analysis, build_project_summary
from ollama_client import run_social_risk_analysis, build_project_summary


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Social Risk Copilot API")


@app.get("/")
def root():
    return {"message": "Social Risk Copilot backend is running"}


@app.post("/projects", response_model=ProjectRead)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(
        title=project.title,
        description=project.description,
        diagnostic_context=project.diagnostic_context,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects


@app.get("/projects/{project_id}", response_model=ProjectWithChildren)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/projects/{project_id}/documents", response_model=DocumentRead)
def add_document(
    project_id: int,
    doc: DocumentCreate,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_doc = Document(
        project_id=project_id,
        filename=doc.filename,
        document_type=doc.document_type,
        text_content=doc.text_content,
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


@app.get(
    "/projects/{project_id}/documents",
    response_model=List[DocumentRead],
)
def list_documents(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs = db.query(Document).filter(Document.project_id == project_id).all()
    return docs


@app.post(
    "/projects/{project_id}/analysis",
    response_model=AnalysisRead,
)
def run_analysis(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs = db.query(Document).filter(Document.project_id == project_id).all()
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="Project has no documents yet",
        )

    project_summary = build_project_summary(
        project.title,
        project.description or "",
        project.diagnostic_context or "",
    )
    docs_text = [d.text_content for d in docs]

    output_json = run_social_risk_analysis(project_summary, docs_text)

    analysis = AnalysisRun(
        project_id=project_id,
        output_json=output_json,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@app.get(
    "/projects/{project_id}/analyses",
    response_model=List[AnalysisRead],
)
def list_analyses(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.project_id == project_id)
        .order_by(AnalysisRun.created_at.desc())
        .all()
    )
    return items


@app.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisRead,
)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

