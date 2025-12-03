from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
import uuid
import logging
import torch
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from core.engine import AnalysisEngine
from detectors.detectors_v2 import (
    FreezeDetectorV2,
    SignalCutDetectorV2,
    LogoDetectorV2,
    SafeAreaDetectorV2,
    ArtesSobrepostasDetectorV2,
    ReporterParadoDetectorV2,
    FocusDetectorV2,
    FadeDetectorV2,
    ComercialCortadoDetectorV2,
    AudioMuteDetectorV2,
    AudioBaixoDetectorV2,
    PicoteDetectorV2,
    RuidoDetectorV2,
    EcoDetectorV2,
    StereoDetectorV2,
    SinalTesteDetectorV2,
    Surround51DetectorV2,
    SapAdDetectorV2,
    SapMudoDetectorV2
)

try:
    from detectors.lipsync_detector import analyze_lipsync
except ImportError:
    analyze_lipsync = None

try:
    from detectors.inteligibilidade_detector import (
        analyze_inteligibilidade_st, 
        analyze_inteligibilidade_sap_ad
    )
except ImportError:
    analyze_inteligibilidade_st = None
    analyze_inteligibilidade_sap_ad = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Serviço de Detecção IA Otimizado (Totalmente Paralelo)")

TEMP_DIR = os.getenv("TEMP_DIR", "temp_videos_ia")
os.makedirs(TEMP_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=min(32, (os.cpu_count() or 1) + 4))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Ambiente de Inferência detectado: {DEVICE}")

def run_legacy_task(func, video_path, task_name):
    """Função wrapper para rodar detectores standalone (Lipsync/Inteligibilidade)."""
    try:
        logger.info(f"[Task] Iniciando {task_name}...")
        result = func(video_path)
        logger.info(f"[Task] {task_name} finalizado.")
        return result
    except Exception as e:
        logger.error(f"Erro na execução de {task_name}: {e}")
        return None

def run_engine_task(engine):
    """Função wrapper para rodar o Engine Single-Pass."""
    try:
        logger.info("[Engine] Iniciando processamento Single-Pass...")
        results = engine.run()
        logger.info(f"[Engine] Finalizado. Encontrou {len(results)} ocorrências.")
        return results
    except Exception as e:
        logger.error(f"Erro fatal no Engine: {e}")
        return []

@app.post("/analyze_video")
async def analyze_video(video_file: UploadFile = File(...)):
    """
    Endpoint principal. Executa TUDO simultaneamente usando paralelismo.
    """
    file_id = str(uuid.uuid4())
    temp_video_path = os.path.join(TEMP_DIR, f"{file_id}_{video_file.filename}")
    
    all_errors = []

    try:
        logger.info(f"Recebendo arquivo: {video_file.filename}")
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        
        loop = asyncio.get_running_loop()
        tasks = []
        engine = AnalysisEngine(temp_video_path)
        engine.add_video_detector(FreezeDetectorV2())
        engine.add_video_detector(SignalCutDetectorV2())
        engine.add_video_detector(LogoDetectorV2())
        engine.add_video_detector(SafeAreaDetectorV2())
        engine.add_video_detector(ArtesSobrepostasDetectorV2())
        engine.add_video_detector(ReporterParadoDetectorV2())
        engine.add_video_detector(FocusDetectorV2())
        engine.add_video_detector(FadeDetectorV2())
        engine.add_video_detector(ComercialCortadoDetectorV2())

        engine.add_audio_detector(AudioMuteDetectorV2())
        engine.add_audio_detector(AudioBaixoDetectorV2())
        engine.add_audio_detector(PicoteDetectorV2())
        engine.add_audio_detector(RuidoDetectorV2())
        engine.add_audio_detector(EcoDetectorV2())
        engine.add_audio_detector(StereoDetectorV2())
        engine.add_audio_detector(SinalTesteDetectorV2())
        
        engine.add_audio_detector(Surround51DetectorV2())
        engine.add_audio_detector(SapAdDetectorV2())
        engine.add_audio_detector(SapMudoDetectorV2())


        tasks.append(
            loop.run_in_executor(executor, run_engine_task, engine)
        )

        if analyze_lipsync:
            tasks.append(
                loop.run_in_executor(
                    executor, run_legacy_task, analyze_lipsync, temp_video_path, "Lipsync"
                )
            )

        if analyze_inteligibilidade_st:
            tasks.append(
                loop.run_in_executor(
                    executor, run_legacy_task, analyze_inteligibilidade_st, temp_video_path, "Inteligibilidade ST"
                )
            )

        if analyze_inteligibilidade_sap_ad:
            tasks.append(
                loop.run_in_executor(
                    executor, run_legacy_task, analyze_inteligibilidade_sap_ad, temp_video_path, "Inteligibilidade SAP"
                )
            )

        logger.info(f"Disparando {len(tasks)} tarefas em paralelo...")

        results_list = await asyncio.gather(*tasks)
        
        for i, res in enumerate(results_list):
            if isinstance(res, list): 
                all_errors.extend(res)
            elif res: 
                all_errors.append(res)

        logger.info(f"Análise completa finalizada. Total de erros: {len(all_errors)}")
        return {"errors": all_errors}

    except Exception as e:
        logger.error(f"Erro crítico no processamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Arquivo removido: {temp_video_path}")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")