from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.db_manager import SessionLocal, Occurrence
from schemas import StatusUpdate
from typing import List, Optional
from datetime import date, datetime
import os 
import csv
import io
from urllib.parse import quote
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

BASE_URL = "http://localhost:8000"

router = APIRouter(
    prefix="/api/v1/occurrences",
    tags=["Occurrences & History"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def apply_filters(query, start_date, end_date, fault_type, status, level, min_duration, max_duration):
    """Aplica os filtros comuns a todas as consultas de ocorrências."""
    if start_date:
        query = query.filter(Occurrence.start_time >= start_date)
        
    if end_date:
        query = query.filter(Occurrence.start_time <= end_date)

    if fault_type:
        query = query.filter(Occurrence.fault_type.ilike(f"%{fault_type}%"))

    if status:
        query = query.filter(Occurrence.status == status)

    if level:
        query = query.filter(Occurrence.level == level)

    if min_duration:
        query = query.filter(Occurrence.duration >= min_duration)

    if max_duration:
        query = query.filter(Occurrence.duration <= max_duration)
        
    return query

@router.get("/", summary="Lista Ocorrências (simplificado)")
def get_all_occurrences(db: Session = Depends(get_db)):
    """
    Retorna uma lista simplificada das ocorrências.
    """
    results = db.query(
        Occurrence.id,
        Occurrence.fault_type.label("titulo"),
        Occurrence.description.label("descricao"),
        Occurrence.duration.label("duracao"),
        Occurrence.start_time.label("data_hora"),
        Occurrence.video_path,
        Occurrence.thumbnail_path,
        Occurrence.status 
    ).order_by(Occurrence.id.desc()).all()

    occurrences = []

    for row in results:
        video_filename = os.path.basename(row.video_path) if row.video_path else None
        thumb_filename = os.path.basename(row.thumbnail_path) if row.thumbnail_path else None

        occurrences.append({
            "id": row.id,
            "titulo": row.titulo,
            "descricao": row.descricao,
            "duracao": row.duracao,
            "data_hora": row.data_hora,
            "status": row.status, 
            "video_url": f"{BASE_URL}/api/v1/videos/{quote(video_filename)}" if video_filename else None,
            "thumbnail_url": f"{BASE_URL}/api/v1/videos/thumbnail/{quote(thumb_filename)}" if thumb_filename else None
        })

    return occurrences

@router.get("/historico/", summary="Obtem Histórico de Ocorrências com Filtros")
def get_paginated_history(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fault_type: Optional[str] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,  
    min_duration: Optional[float] = None,  
    max_duration: Optional[float] = None,  
    page: int = 1,
    size: int = Query(default=20, gt=0, le=100)
):
    """
    Retorna uma lista paginada de ocorrências filtradas.
    """
    query = db.query(Occurrence)
 
    query = apply_filters(query, start_date, end_date, fault_type, status, level, min_duration, max_duration)

    paginated_query = query.order_by(Occurrence.id.desc()).limit(size).offset((page - 1) * size)
    results = paginated_query.all()

    occurrences_list = []
    for row in results:
        video_filename = os.path.basename(row.video_path) if row.video_path else None
        thumb_filename = os.path.basename(row.thumbnail_path) if row.thumbnail_path else None

        occurrences_list.append({
            "id": row.id,
            "titulo": row.fault_type,
            "descricao": row.description,
            "programa": row.program,
            "duracao": row.duration,
            "data_hora": row.start_time,
            "nivel": row.level,
            "tipo_falha": row.fault_type,
            "causa": row.cause,
            "acao": row.action,
            "notas": row.notes,
            "status": row.status,
            "thumbnail_url": f"{BASE_URL}/api/v1/videos/thumbnail/{quote(thumb_filename)}" if thumb_filename else None,
            "video_url": f"{BASE_URL}/api/v1/videos/{quote(video_filename)}" if video_filename else None
        })

    return {
        "page": page,
        "size": size,
        "total": query.count(),
        "data": occurrences_list
    }

@router.get("/export/csv", summary="Exportar Ocorrências para CSV")
def export_occurrences_csv(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fault_type: Optional[str] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,  
    min_duration: Optional[float] = None,  
    max_duration: Optional[float] = None
):
    """
    Gera e faz download de um arquivo CSV com as ocorrências filtradas.
    """
    query = db.query(Occurrence)
    query = apply_filters(query, start_date, end_date, fault_type, status, level, min_duration, max_duration)
    
    results = query.order_by(Occurrence.id.desc()).all()

    stream = io.StringIO()
    writer = csv.writer(stream)

    writer.writerow(["ID", "Data/Hora", "Programa", "Tipo de Falha", "Nível", "Duração (s)", "Status", "Descrição", "Causa", "Ação"])

    for row in results:
        writer.writerow([
            row.id,
            row.start_time.strftime("%Y-%m-%d %H:%M:%S") if row.start_time else "",
            row.program or "",
            row.fault_type or "",
            row.level or "",
            f"{row.duration:.2f}" if row.duration else "0",
            row.status or "",
            row.description or "",
            row.cause or "",
            row.action or ""
        ])

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    filename = f"ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

@router.get("/export/pdf", summary="Exportar Ocorrências para PDF")
def export_occurrences_pdf(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fault_type: Optional[str] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,  
    min_duration: Optional[float] = None,  
    max_duration: Optional[float] = None
):
    """
    Gera e faz download de um arquivo PDF com as ocorrências filtradas.
    """
    query = db.query(Occurrence)
    query = apply_filters(query, start_date, end_date, fault_type, status, level, min_duration, max_duration)
    
    results = query.order_by(Occurrence.id.desc()).all()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph(f"Relatório de Ocorrências - Projeto Globo", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    subtitle = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 12))

    data = [["ID", "Data", "Programa", "Falha", "Nível", "Dur.(s)", "Status"]]

    for row in results:
        prog_short = (row.program[:20] + '..') if row.program and len(row.program) > 20 else (row.program or "")
        fault_short = (row.fault_type[:25] + '..') if row.fault_type and len(row.fault_type) > 25 else (row.fault_type or "")
        
        data.append([
            str(row.id),
            row.start_time.strftime("%d/%m %H:%M") if row.start_time else "",
            prog_short,
            fault_short,
            row.level or "",
            f"{row.duration:.1f}" if row.duration else "0",
            row.status or ""
        ])

    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), 
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ])
    table.setStyle(style)
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    
    response = StreamingResponse(buffer, media_type="application/pdf")
    filename = f"relatorio_ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

@router.get("/{occurrence_id}", summary="Obtem detalhes de uma Ocorrência")
def get_occurrence_by_id(occurrence_id: int, db: Session = Depends(get_db)):
    """
    Retorna todas as informações de uma ocorrência específica pelo seu ID.
    """
    occurrence = db.query(
        Occurrence.id,
        Occurrence.fault_type,
        Occurrence.description,
        Occurrence.program,
        Occurrence.duration,
        Occurrence.start_time,
        Occurrence.level,
        Occurrence.cause,
        Occurrence.action,
        Occurrence.notes,
        Occurrence.status,
        Occurrence.video_path,
        Occurrence.thumbnail_path  
    ).filter(Occurrence.id == occurrence_id).first()
    
    if occurrence is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
 
    video_filename = os.path.basename(occurrence.video_path) if occurrence.video_path else None
    thumb_filename = os.path.basename(occurrence.thumbnail_path) if occurrence.thumbnail_path else None 
 
    response = {
        "id": occurrence.id,
        "titulo": occurrence.fault_type if occurrence.fault_type is not None else "",
        "descricao": occurrence.description if occurrence.description is not None else "",
        "programa": occurrence.program if occurrence.program is not None else "",
        "duracao": occurrence.duration if occurrence.duration is not None else "",
        "data_hora": occurrence.start_time if occurrence.start_time is not None else "",
        "nivel": occurrence.level if occurrence.level is not None else "",
        "tipo_falha": occurrence.fault_type if occurrence.fault_type is not None else "",
        "causa": occurrence.cause if occurrence.cause is not None else "",
        "acao": occurrence.action if occurrence.action is not None else "",
        "notas": occurrence.notes if occurrence.notes is not None else "",
        "status": occurrence.status if occurrence.status is not None else "",
        "video_url": f"{BASE_URL}/api/v1/videos/{quote(video_filename)}" if video_filename else None,
        "thumbnail_url": f"{BASE_URL}/api/v1/videos/thumbnail/{quote(thumb_filename)}" if thumb_filename else None 
    }

    return response

@router.put("/{occurrence_id}/status", summary="Atualiza Status de uma Ocorrência")
def update_occurrence_status(occurrence_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    """
    Atualiza o status de uma ocorrência.
    """
    occurrence = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
    if occurrence is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    occurrence.status = status_update.status.value
    db.commit()
    db.refresh(occurrence)
    
    if occurrence.video_path:
        occurrence.video_path = occurrence.video_path.replace(os.path.sep, '/')
        
    return {"message": "Status atualizado com sucesso", "occurrence": occurrence}

@router.delete("/historico/", summary="Excluir Ocorrências em Massa por Filtro")
def delete_occurrences_history(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fault_type: Optional[str] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,  
    min_duration: Optional[float] = None,  
    max_duration: Optional[float] = None
):
    """
    Exclui ocorrências em massa baseando-se nos filtros fornecidos.
    ATENÇÃO: Ação destrutiva.
    """
    query = db.query(Occurrence)
 
    query = apply_filters(query, start_date, end_date, fault_type, status, level, min_duration, max_duration)

    deleted_count = query.delete(synchronize_session=False)
    
    db.commit()

    return {
        "message": "Registros excluídos com sucesso.",
        "deleted_count": deleted_count
    }