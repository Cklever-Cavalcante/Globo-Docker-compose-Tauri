import logging
import os
import datetime
import pytz
import torch
import numpy as np
import av
from typing import Optional, Dict, Any
from transformers import pipeline
from utils.error_classifier import classify_error, get_current_program

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MIN_VOLUME_DBFS = -50.0
MODEL_NAME = "jonatasgrosman/wav2vec2-large-xlsr-53-portuguese"
EXPECTED_SAMPLING_RATE = 16000
SCHEDULE_FILE_PATH = "../utils/programacao_globo_2025.json"

try:
    log.info(f"Carregando modelo de STT: {MODEL_NAME}...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    stt_pipeline = pipeline(
        "automatic-speech-recognition",
        model=MODEL_NAME,
        device=device
    )
    log.info(f"Modelo STT carregado com sucesso em: {device}")
except ImportError:
    log.error("Dependências (transformers, torch) não estão instaladas. Pulando detector de inteligibilidade.")
    stt_pipeline = None
except Exception as e:
    log.error(f"Erro ao carregar modelo STT ({MODEL_NAME}): {e}. O detector de inteligibilidade será desativado.")
    stt_pipeline = None

def _load_and_process_audio(video_path: str, stream_index: int) -> Optional[np.ndarray]:
    """
    Carrega um stream de áudio específico usando PyAV, converte para mono 16kHz
    e retorna como array numpy float32.
    """
    try:
        container = av.open(video_path)
        audio_streams = [s for s in container.streams if s.type == 'audio']
        
        if stream_index >= len(audio_streams):
            log.info(f"Stream de áudio índice {stream_index} não encontrado em {video_path}.")
            container.close()
            return None

        stream = audio_streams[stream_index]
        
        resampler = av.AudioResampler(format='fltp', layout='mono', rate=EXPECTED_SAMPLING_RATE)

        samples = []
        
        for packet in container.demux(stream):
            for frame in packet.decode():
                frame.pts = None
                out_frames = resampler.resample(frame)
                for out_frame in out_frames:
                    samples.append(out_frame.to_ndarray())
        
        container.close()

        if not samples:
            log.warning(f"Nenhum sample de áudio extraído do stream {stream_index}.")
            return None
            
        audio_data = np.concatenate(samples, axis=1).flatten()
        return audio_data

    except Exception as e:
        log.error(f"Erro PyAV ao carregar áudio (stream {stream_index}): {e}")
        return None

def _calculate_dbfs(audio_data: np.ndarray) -> float:
    if audio_data.size == 0:
        return -float('inf')
    
    rms = np.sqrt(np.mean(audio_data**2))
    
    if rms <= 1e-9:
        return -float('inf')
        
    return 20 * np.log10(rms)

def analyze_inteligibilidade_st(video_path: str) -> Optional[Dict[str, Any]]:
    if stt_pipeline is None:
        return None
        
    log.info(f"Iniciando detecção de ST NÃO INTELIGÍVEL para: {video_path}")
    
    audio_float = _load_and_process_audio(video_path, 0)
    
    if audio_float is None or audio_float.size == 0:
        return None
        
    volume_dbfs = _calculate_dbfs(audio_float)
    duracao_total_seg = len(audio_float) / EXPECTED_SAMPLING_RATE
    
    if volume_dbfs < MIN_VOLUME_DBFS:
        log.info(f"Inteligibilidade ST: Áudio muito baixo ({volume_dbfs:.2f} dBFS). Pulando.")
        return None

    try:
        log.info("Inteligibilidade ST: Invocando modelo de IA...")
        transcription_result = stt_pipeline(
            {"sampling_rate": EXPECTED_SAMPLING_RATE, "raw": audio_float}
        )
        transcription = transcription_result["text"].strip()
        log.info(f"Inteligibilidade ST: Transcrição: '{transcription}'")

        if not transcription:
            tz = pytz.timezone('America/Sao_Paulo')
            event_start_datetime = datetime.datetime.now(tz) - datetime.timedelta(seconds=duracao_total_seg)
            
            program_name = get_current_program(
                target_datetime=event_start_datetime, 
                schedule_file_path=SCHEDULE_FILE_PATH
            )

            log.warning(f"Detecção: AUDIO_ST_NAO_INTELIGIVEL. Volume OK ({volume_dbfs:.2f} dBFS) mas sem transcrição.")
            
            detalhes = {
                "volume_st_dbfs": f"{volume_dbfs:.2f}",
                "transcricao_ia": "''"
            }
            
            return {
                "program": program_name, 
                "duration": duracao_total_seg,
                "level": classify_error("Audio ST Nao Inteligivel", duracao_total_seg),
                "fault_type": "Audio ST Nao Inteligivel",
                "description": f"Áudio ST não inteligível (Volume {volume_dbfs:.2f} dBFS, sem fala reconhecida).",
                "cause": "Análise IA",
                "action": "Não se aplica",
                "notes": f"Ocorrência detectada automaticamente. Detalhes: {detalhes}",
                "event_start_time": 0.0,
                "event_duration": duracao_total_seg
            }

        return None
        
    except Exception as e:
        log.error(f"Erro na inferência STT (ST): {e}")
        return None

def analyze_inteligibilidade_sap_ad(video_path: str) -> Optional[Dict[str, Any]]:
    if stt_pipeline is None:
        return None
        
    log.info(f"Iniciando detecção de SAP/AD NÃO INTELIGÍVEL para: {video_path}")
    
    audio_float = _load_and_process_audio(video_path, 1)
    
    if audio_float is None or audio_float.size == 0:
        log.info("Inteligibilidade SAP/AD: Stream 1 não encontrado ou vazio.")
        return None
        
    volume_dbfs = _calculate_dbfs(audio_float)
    duracao_total_seg = len(audio_float) / EXPECTED_SAMPLING_RATE
    
    if volume_dbfs < MIN_VOLUME_DBFS:
        log.info(f"Inteligibilidade SAP/AD: Áudio baixo ({volume_dbfs:.2f} dBFS). Pulando.")
        return None

    try:
        log.info("Inteligibilidade SAP/AD: Invocando modelo de IA...")
        transcription_result = stt_pipeline(
            {"sampling_rate": EXPECTED_SAMPLING_RATE, "raw": audio_float}
        )
        transcription = transcription_result["text"].strip()
        log.info(f"Inteligibilidade SAP/AD: Transcrição: '{transcription}'")

        if not transcription:
            tz = pytz.timezone('America/Sao_Paulo')
            event_start_datetime = datetime.datetime.now(tz) - datetime.timedelta(seconds=duracao_total_seg)
            
            program_name = get_current_program(
                target_datetime=event_start_datetime, 
                schedule_file_path=SCHEDULE_FILE_PATH
            )

            log.warning(f"Detecção: AUDIO_SAP_NAO_INTELIGIVEL. Volume OK ({volume_dbfs:.2f} dBFS) mas sem transcrição.")
            
            detalhes = {
                "volume_sap_dbfs": f"{volume_dbfs:.2f}",
                "transcricao_ia": "''"
            }
            
            return {
                "program": program_name, 
                "duration": duracao_total_seg,
                "level": classify_error("Audio SAP Nao Inteligivel", duracao_total_seg),
                "fault_type": "Audio SAP Nao Inteligivel",
                "description": f"Áudio SAP não inteligível (Volume {volume_dbfs:.2f} dBFS, sem fala reconhecida).",
                "cause": "Análise IA",
                "action": "Não se aplica",
                "notes": f"Ocorrência detectada automaticamente. Detalhes: {detalhes}",
                "event_start_time": 0.0,
                "event_duration": duracao_total_seg
            }

        return None
        
    except Exception as e:
        log.error(f"Erro na inferência STT (SAP): {e}")
        return None