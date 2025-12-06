import requests
import os
import time
import threading
import subprocess
import shutil
import queue
from queue import Queue
import imageio_ffmpeg as ffmpeg_lib  
import cv2  

from core import video_source 
from database.db_manager import save_occurrence, get_current_settings
from utils import config 
from utils.config import IA_SERVICE_URL
from socket_instance import sio
from utils import hls_streamer 
from utils.hls_streamer import is_stream_running, UDP_BRIDGE_URL

stop_event = threading.Event()
monitoring_threads = []

CLIP_DURATION_SECONDS = 10
VIDEO_BUFFER_SECONDS = 4

clip_queue = Queue(maxsize=10)

def capture_thread(video_source_info, duration, current_mode):
    print(f"[Capture Thread] Iniciando captura contínua. Modo: {current_mode}")
    while not stop_event.is_set(): 
        temp_dir = config.BASE_DIR / "temp_clips"
        os.makedirs(temp_dir, exist_ok=True)
        temp_clip_path = os.path.join(temp_dir, f"clip_{int(time.time())}.mp4")
        
        if capture_clip(video_source_info, duration, temp_clip_path):
            try:
                clip_queue.put(temp_clip_path, block=False)
            except queue.Full:
                print(f"[Capture Thread] AVISO: Fila cheia. Descartando clipe.")
                try:
                    os.remove(temp_clip_path)
                except OSError:
                    pass
        else:
            time.sleep(1) 
    print("[Capture Thread] Encerrando captura.")

def analysis_thread():
    print("[Analysis Thread] Aguardando clipes...")
    while not stop_event.is_set(): 
        try:
            clip_path = clip_queue.get(timeout=1) 
            analyze_clip_from_path(clip_path)
            clip_queue.task_done()
        except queue.Empty:
            continue 
        except Exception as e:
            print(f"[Analysis Thread] ERRO no processamento: {e}")
    print("[Analysis Thread] Encerrando análise.")

def run_file_analysis_once(video_path):
    print(f"[Processor] Iniciando análise ONE-SHOT do arquivo: {video_path}")
    try:
        analyze_clip_from_path(video_path, is_temp_file=False)
        print("[Processor] Análise do arquivo concluída.")
    except Exception as e:
        print(f"[Processor] Erro na análise do arquivo: {e}")

def start_monitoring_threads():
    global monitoring_threads
    global stop_event

    settings = get_current_settings()
    current_mode = settings['mode'] if settings else config.MONITORING_MODE
    
    video_source_info = video_source.get_video_source() 

    if current_mode in ['SRT', 'DEVICE']:
        print(f"[Processor] Iniciando monitorização contínua em modo: {current_mode}")
        stop_event.clear()

        capturer = threading.Thread(
            target=capture_thread,
            args=(video_source_info, CLIP_DURATION_SECONDS, current_mode), 
            daemon=True,
            name="CaptureThread"
        )
        capturer.start()

        analyzer = threading.Thread(target=analysis_thread, daemon=True, name="AnalysisThread")
        analyzer.start()

        monitoring_threads.append(capturer)
        monitoring_threads.append(analyzer)
        print("[Processor] Threads iniciadas.")

    elif current_mode == 'FILE':
        print(f"[Processor] Modo FILE detectado. Análise única em Background.")
        file_thread = threading.Thread(
            target=run_file_analysis_once,
            args=(video_source_info,),
            daemon=True,
            name="FileAnalysisThread"
        )
        file_thread.start()

def stop_monitoring_threads():
    global monitoring_threads
    global stop_event

    if not monitoring_threads:
        return

    print("[Processor] Encerrando threads de monitorização...")
    stop_event.set()

    for thread in monitoring_threads:
        if thread.is_alive():
            thread.join(timeout=3)
    
    while not clip_queue.empty():
        try:
            clip_path = clip_queue.get_nowait()
            if os.path.exists(clip_path):
                os.remove(clip_path)
        except:
            pass
            
    monitoring_threads = []
    print("[Processor] Threads encerradas.")

def stop_and_restart_monitoring():
    print("[Processor] Reinício dinâmico solicitado...")
    
    was_hls_running = hls_streamer.is_stream_running()
    if was_hls_running:
        hls_streamer.stop_hls()

    stop_monitoring_threads()
    time.sleep(1)

    try:
        settings = get_current_settings()
        new_mode = settings['mode'] if settings else config.MONITORING_MODE

        if new_mode != 'FILE':
            if was_hls_running:
                print("[Processor] Reiniciando HLS...")
                hls_streamer.start_hls()
                time.sleep(2)
        else:
            print("[Processor] Novo modo é FILE. HLS desligado.")

        start_monitoring_threads()
        
        print("[Processor] Reinício bem-sucedido.")
        return True
    except Exception as e:
        print(f"[Processor] ERRO fatal ao reiniciar: {e}")
        return False

def process_stream():
    start_monitoring_threads()

def capture_clip(default_source, duration, output_path):
    ffmpeg_exe = ffmpeg_lib.get_ffmpeg_exe()
    
    using_bridge = False
    current_source = default_source
    
    if hls_streamer.is_stream_running():
        current_source = UDP_BRIDGE_URL
        using_bridge = True

    command = []
    is_device_source = isinstance(current_source, (tuple, list))

    if using_bridge:
        command = [ffmpeg_exe, "-i", current_source, "-t", str(duration), "-c", "copy", "-y", output_path]
    elif is_device_source:
        video_device, audio_device = current_source
        command = [
            ffmpeg_exe, "-f", "dshow", "-rtbufsize", "100M",
            "-i", f"video={video_device}:audio={audio_device}", 
            "-t", str(duration), "-y", output_path
        ]
    else: 
        command = [
            ffmpeg_exe, "-i", current_source, "-t", str(duration), 
            "-c:v", "copy", "-c:a", "copy", "-y", output_path
        ]
    
    timeout = duration + 20
    try:
        result = subprocess.run(
            command, check=True, timeout=timeout, 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            return True
    except subprocess.TimeoutExpired:
        print(f"[Capture Func] Timeout (Bridge={using_bridge}).")
    except Exception as e:
        print(f"[Capture Func] Erro FFmpeg (Bridge={using_bridge}): {e}")
    
    return False

def trim_video_clip(input_path, output_path, start_time, duration):
    try:
        ffmpeg_exe = ffmpeg_lib.get_ffmpeg_exe()
        command = [
            ffmpeg_exe, "-i", str(input_path), "-ss", str(start_time), 
            "-t", str(duration), "-c", "copy", "-y", str(output_path) 
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[Processor] Trecho cortado: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"[Processor] ERRO ao cortar: {e}")
        return False

def analyze_clip_from_path(video_path: str, is_temp_file: bool = True):
    if not os.path.exists(video_path): return
    
    errors = []
    try:
        with open(video_path, "rb") as video_file:
            files = {'video_file': (os.path.basename(video_path), video_file, 'video/mp4')}
            response = requests.post(IA_SERVICE_URL, files=files, timeout=600)
        response.raise_for_status()
        result = response.json()
        errors = result.get("errors", [])
    except requests.exceptions.RequestException as e:
        print(f"[Processor] Erro de comunicação com IA: {e}")

    if errors:
        print(f"[Processor] DETECÇÕES: {len(errors)}")
        for i, error_data in enumerate(errors):
            try:
                event_start = error_data.get("event_start_time", 0)
                event_duration = error_data.get("event_duration", 5)
                trim_start = max(0, event_start - VIDEO_BUFFER_SECONDS)
                trim_duration = event_duration + (2 * VIDEO_BUFFER_SECONDS)
                
                nome_base = error_data.get('fault_type', 'ocorrencia').replace('/', '_').replace(' ', '_').lower()
                
                novo_nome = f"{nome_base}_{int(time.time())}_{i}.mp4"

                output_dir = str(config.VIDEO_BASE_DIR)
                permanent_path = os.path.join(output_dir, novo_nome)
                os.makedirs(output_dir, exist_ok=True)
                
                saved = False
                if trim_video_clip(video_path, permanent_path, trim_start, trim_duration):
                    error_data["video_path"] = permanent_path
                    saved = True
                else:
                    shutil.copy(video_path, permanent_path)
                    error_data["video_path"] = permanent_path
                    saved = True
                
                if saved:
                    saved_occurrence = save_occurrence(error_data)
                    if saved_occurrence:
                        sio.emit('new_occurrence', saved_occurrence.to_dict())

            except Exception as e:
                print(f"[Processor] CRÍTICO: Falha ao processar ocorrência {i+1} de {len(errors)}: {e}")

    if is_temp_file and os.path.exists(video_path):
        try:
            os.remove(video_path)
        except: 
            pass

def get_video_duration(video_path):
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened(): return CLIP_DURATION_SECONDS
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        if fps > 0: return float(frame_count / fps)
    except:
        pass
    return CLIP_DURATION_SECONDS