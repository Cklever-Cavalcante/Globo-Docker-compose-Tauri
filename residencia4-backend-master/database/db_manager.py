import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from utils.video_utils import generate_thumbnail
from utils.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, VIDEO_BASE_DIR, THUMBNAIL_BASE_DIR, DATABASE_URL

if not DATABASE_URL:
    print("[DB Manager] DATABASE_URL não encontrada. A usar a configuração local.")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SystemSetting(Base):
    """
    Tabela para armazenar o estado dinâmico do sistema.
    Só deve existir UMA linha nesta tabela.
    """
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    monitoring_mode = Column(String, default="FILE", nullable=False)  
    srt_url = Column(String, nullable=True)
    video_device = Column(String, nullable=True)
    audio_device = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Occurrence(Base):
    __tablename__ = "occurrences"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    program = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    level = Column(String, nullable=False)
    fault_type = Column(String, nullable=False)
    description = Column(String)
    cause = Column(String)
    action = Column(String)
    notes = Column(String)
    video_path = Column(String, nullable=True)
    event_start_time = Column(Float, nullable=True)
    status = Column(String, default="Não Validado", nullable=False)
    event_duration = Column(Float, nullable=True)
    thumbnail_path = Column(String, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'program': self.program,
            'duration': self.duration,
            'level': self.level,
            'fault_type': self.fault_type,
            'description': self.description,
            'cause': self.cause,
            'action': self.action,
            'notes': self.notes,
            'video_path': self.video_path,
            'event_start_time': self.event_start_time,
            'status': self.status,
            'event_duration': self.event_duration,
            'thumbnail_path': self.thumbnail_path
        }

def initialize_database():
    """Cria tabelas e garante que existe uma configuração inicial."""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        check_column_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'occurrences' AND column_name = 'thumbnail_path'")
        result = db.execute(check_column_query).fetchone()
        if not result:
            db.execute(text("ALTER TABLE occurrences ADD COLUMN thumbnail_path VARCHAR NULL"))
            db.commit()
            print("[DB Manager] Coluna 'thumbnail_path' adicionada.")

        settings = db.query(SystemSetting).first()
        if not settings:
            print("[DB Manager] Criando configurações padrão na BD...")
            default_settings = SystemSetting(
                monitoring_mode="FILE",
                srt_url="srt://127.0.0.1:7000",
                video_device="0",
                audio_device="default"
            )
            db.add(default_settings)
            db.commit()
    except Exception as e:
        print(f"[DB Manager] Erro na inicialização: {e}")
    finally:
        db.close()
    
    print("[DB Manager] Base de dados inicializada.")

def save_occurrence(fault_data: dict):
    """Guarda uma nova ocorrência."""
    db = SessionLocal()
    try:
        if 'event_duration' in fault_data:
            fault_data['duration'] = fault_data['event_duration']
            
        occurrence = Occurrence(**fault_data)
        db.add(occurrence)
        db.commit()
        db.refresh(occurrence)
        
        if occurrence.video_path:
            abs_video_path = os.path.join(VIDEO_BASE_DIR, os.path.basename(occurrence.video_path))
            thumbnail_path = generate_thumbnail(abs_video_path, THUMBNAIL_BASE_DIR)
            if thumbnail_path:
                occurrence.thumbnail_path = os.path.basename(thumbnail_path)
                db.commit()
        
        print(f"[DB Manager] Ocorrência '{fault_data.get('fault_type')}' guardada.")
        return occurrence 
    finally:
        db.close()

def get_last_occurrence():
    db = SessionLocal()
    try:
        return db.query(Occurrence).order_by(Occurrence.id.desc()).first()
    finally:
        db.close()

def get_current_settings():
    """Lê as configurações atuais (Thread-safe, cria nova sessão)."""
    db = SessionLocal()
    try:
        settings = db.query(SystemSetting).first()
        if settings:
            return {
                "mode": settings.monitoring_mode,
                "srt_url": settings.srt_url,
                "video_device": settings.video_device,
                "audio_device": settings.audio_device
            }
        return None
    finally:
        db.close()