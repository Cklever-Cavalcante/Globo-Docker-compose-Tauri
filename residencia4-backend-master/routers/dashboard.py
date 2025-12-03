from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db_manager import SessionLocal, Occurrence
from datetime import datetime, timedelta, time
from typing import Optional

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard Analytics"]
)

VIDEO_FAULT_TYPES = {
    "Artes Sobrepostas", "Comercial Cortado", "Fade-Out", "Fade-In", 
    "Fora de Foco", "Freeze/Efeito Bloco", "Erro de LipSync", 
    "Logo Errado / Ausente", "Corte de Sinal", "Repórter Parado", 
    "Arte Fora da Safe Area"
}

AUDIO_FAULT_TYPES = {
    "Audio Baixo", "Ausência de Áudio", "Audio 5.1 Ausencia C", "Audio Eco", 
    "Audio ST Nao Inteligivel", "Audio Picote", "Audio Distorcido", 
    "Audio SAP Ausencia", "Audio SAP Mudo", "Sinal de Testes", 
    "Audio ST Ausencia L", "Audio ST Ausencia R", 
    "Audio 5.1 Ausencia", "Audio Hiss/Ruido"
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary", summary="Obtem Resumo de Dados para o Dashboard")
def get_dashboard_summary(
    range: str = Query("today", description="Range de data: today, 7days, 30days, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna dados agregados filtrados pelo período selecionado.
    """
    now = datetime.now()
 
    if range == "today":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        previous_start = period_start - timedelta(days=1)
        previous_end = period_end - timedelta(days=1)
        
    elif range == "7days":
        period_end = now
        period_start = now - timedelta(days=7)
        previous_start = period_start - timedelta(days=7)
        previous_end = period_start
        
    elif range == "30days":
        period_end = now
        period_start = now - timedelta(days=30)
        previous_start = period_start - timedelta(days=30)
        previous_end = period_start
        
    elif range == "custom" and start_date and end_date:
        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d")
            d_end = datetime.strptime(end_date, "%Y-%m-%d")
            
            period_start = d_start.replace(hour=0, minute=0, second=0)
            period_end = d_end.replace(hour=23, minute=59, second=59)
            delta = period_end - period_start
            previous_end = period_start - timedelta(seconds=1)
            previous_start = previous_end - delta
        except ValueError:
            period_start = now.replace(hour=0, minute=0, second=0)
            period_end = now
            previous_start = period_start - timedelta(days=1)
            previous_end = period_end - timedelta(days=1)
    else:
        period_start = now.replace(hour=0, minute=0, second=0)
        period_end = now
        previous_start = period_start - timedelta(days=1)
        previous_end = period_end - timedelta(days=1)

    def filter_date(query, start, end):
        return query.filter(Occurrence.start_time >= start, Occurrence.start_time <= end)

    total_validated = filter_date(db.query(func.count(Occurrence.id)), period_start, period_end)\
        .filter(Occurrence.status == 'Aprovado').scalar()

    current_period_count = filter_date(db.query(func.count(Occurrence.id)), period_start, period_end).scalar()
    previous_period_count = filter_date(db.query(func.count(Occurrence.id)), previous_start, previous_end).scalar()

    # 3. Distribuição por Tipo de Falha (No período selecionado)
    count_by_type = filter_date(db.query(Occurrence.fault_type, func.count(Occurrence.id)), period_start, period_end)\
        .group_by(Occurrence.fault_type).all()
    
    fault_type_distribution = []
    for f_type, count in count_by_type:
        category = "Outros"
        if f_type in VIDEO_FAULT_TYPES:
            category = "Video"
        elif f_type in AUDIO_FAULT_TYPES:
            category = "Audio"
        
        fault_type_distribution.append({
            "type": f_type,   
            "count": count,    
            "category": category 
        })

    open_occurrences_count = filter_date(db.query(func.count(Occurrence.id)), period_start, period_end)\
        .filter(Occurrence.status == 'Não Validado').scalar()
        
    rejected_occurrences_count = filter_date(db.query(func.count(Occurrence.id)), period_start, period_end)\
        .filter(Occurrence.status == 'Rejeitado').scalar()

    count_by_level = filter_date(db.query(Occurrence.level, func.count(Occurrence.id)), period_start, period_end)\
        .group_by(Occurrence.level).all()
        
    level_distribution = [{"level": lvl, "count": count} for lvl, count in count_by_level]

    return {
        "total_validated_occurrences": total_validated,
        "monthly_comparison": { 
            "current_month": current_period_count, 
            "previous_month": previous_period_count
        },
        "fault_type_distribution": fault_type_distribution, 
        "status_distribution": {
            "validated": total_validated, 
            "open": open_occurrences_count,
            "rejected": rejected_occurrences_count
        },
        "completed_today": total_validated, 
        "level_distribution": level_distribution,
        "debug_period": { 
            "start": period_start,
            "end": period_end
        }
    }