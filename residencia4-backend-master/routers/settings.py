import re
import subprocess
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from enum import Enum
import imageio_ffmpeg as ffmpeg_lib 
from core.stream_processor import stop_and_restart_monitoring 
from database.db_manager import SessionLocal, SystemSetting
import utils.config as config 

class MonitoringMode(str, Enum):
    SRT = "SRT"
    DEVICE = "DEVICE"
    FILE = "FILE"

class ModeUpdate(BaseModel):
    mode: MonitoringMode
    video_device: str | None = None
    audio_device: str | None = None
    srt_url: str | None = None

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["Settings & Configuration"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/monitoring-mode", summary="Obtem o Modo de Monitorização Atual")
def get_monitoring_mode(db: Session = Depends(get_db)):
    """
    Retorna o modo de monitorização atual a partir da Base de Dados.
    """
    settings = db.query(SystemSetting).first()
    
    if not settings:
        raise HTTPException(status_code=500, detail="Configurações do sistema não inicializadas.")

    response = {
        "current_mode": settings.monitoring_mode
    }
    
    if settings.monitoring_mode == "SRT":
        response["srt_url"] = settings.srt_url
    elif settings.monitoring_mode == "DEVICE":
        response["video_device"] = settings.video_device
        response["audio_device"] = settings.audio_device
    elif settings.monitoring_mode == "FILE":
        response["test_video_path"] = config.TEST_VIDEO_PATH

    return response

@router.get("/devices", summary="Lista Dispositivos de Vídeo e Áudio")
def list_media_devices():
    """
    Lista os dispositivos disponíveis usando ffmpeg.
    """
    try:
        ffmpeg_exe = ffmpeg_lib.get_ffmpeg_exe() 

        command = [ffmpeg_exe, "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
        
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='ignore'
        )
        
        output = result.stderr
        video_devices = []
        audio_devices = []
        
        device_pattern = re.compile(r'"([^"]+)" \((\w+)\)')
        
        for line in output.splitlines():
            if "(video)" in line:
                match = device_pattern.search(line)
                if match:
                    video_devices.append(match.group(1))
            elif "(audio)" in line:
                match = device_pattern.search(line)
                if match:
                    audio_devices.append(match.group(1))
                    
        return {
            "video_devices": list(set(video_devices)), 
            "audio_devices": list(set(audio_devices)) 
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar dispositivos: {e}")

@router.put("/monitoring-mode", summary="Altera o Modo de Monitorização")
def set_monitoring_mode(mode_update: ModeUpdate, db: Session = Depends(get_db)):
    """
    Atualiza o modo de monitorização na Base de Dados e reinicia o processo.
    """
    if mode_update.mode == MonitoringMode.SRT and not mode_update.srt_url:
        raise HTTPException(status_code=400, detail="Para modo 'SRT', forneça 'srt_url'.")

    if mode_update.mode == MonitoringMode.DEVICE and (not mode_update.video_device or not mode_update.audio_device):
        raise HTTPException(status_code=400, detail="Para modo 'DEVICE', forneça dispositivos de vídeo e áudio.")

    settings = db.query(SystemSetting).first()
    if not settings:
        settings = SystemSetting()
        db.add(settings)
    
    settings.monitoring_mode = mode_update.mode.value

    if mode_update.srt_url:
        settings.srt_url = mode_update.srt_url
    
    if mode_update.video_device:
        settings.video_device = mode_update.video_device
        settings.audio_device = mode_update.audio_device

    try:
        db.commit()
        db.refresh(settings)
 
        restart_success = stop_and_restart_monitoring()

        msg = "Alterações aplicadas." if restart_success else "Configuração salva, mas falha ao reiniciar stream."
        
        return {
            "message": "Modo atualizado com sucesso.",
            "new_mode": settings.monitoring_mode,
            "action_required": msg
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao guardar na base de dados: {e}")