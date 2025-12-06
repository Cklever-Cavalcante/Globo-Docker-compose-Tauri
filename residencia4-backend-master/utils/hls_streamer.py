import os
import subprocess
import time
import sys
from core.video_source import get_video_source
from database.db_manager import get_current_settings
import utils.config as config
import imageio_ffmpeg as ffmpeg_lib  

HLS_DIR_NAME = "hls_stream"
HLS_DIR = os.path.join(config.BASE_DIR, HLS_DIR_NAME)
PLAYLIST_FILE = os.path.join(HLS_DIR, "index.m3u8")

REL_PLAYLIST = f"{HLS_DIR_NAME}/index.m3u8"
REL_SEGMENT = f"{HLS_DIR_NAME}/segment%03d.ts"

UDP_BRIDGE_URL = "udp://127.0.0.1:23000?pkt_size=1316"

_process = None

def _get_current_mode():
    """Helper para obter o modo atual do DB de forma segura."""
    settings = get_current_settings()
    if settings:
        return settings['mode']
    return config.MONITORING_MODE

def _build_input_args():
    """
    Monta os argumentos de input baseados no modo atual.
    """
    source = get_video_source()
    current_mode = _get_current_mode()

    if current_mode == "SRT":
        return [
            "-fflags", "nobuffer", 
            "-probesize", "32M", 
            "-analyzeduration", "10M", 
            "-i", source
        ]

    elif current_mode == "DEVICE":
        if isinstance(source, (tuple, list)):
            video_device, audio_device = source
            dshow_input = f"video={video_device}:audio={audio_device}"
            print(f"[HLS] Tentando abrir dispositivos dshow: {dshow_input}")
            return [
                "-f", "dshow",
                "-rtbufsize", "100M",
                "-i", dshow_input
            ]
        else:
            print(f"[HLS] ERRO: Modo DEVICE mas source não é tupla: {source}")
            return []
    
    else:
        raise ValueError(f"Modo desconhecido ou não suportado pelo HLS: {current_mode}")


def start_hls():
    global _process
    
    current_mode = _get_current_mode()

    if current_mode == 'FILE':
        print("[HLS] Modo FILE detectado: Stream HLS desativado (Análise única).")
        return

    if is_stream_running():
        print("[HLS] Já existe um processo rodando. Reiniciando...")
        stop_hls()

    try:
        os.makedirs(HLS_DIR, exist_ok=True)
        ffmpeg_exe = ffmpeg_lib.get_ffmpeg_exe()
        input_args = _build_input_args()
        
        encoding_args = [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-g", "60",            
            "-sc_threshold", "0",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", "2",
            "-flags", "+global_header"
        ]

        tee_hls = f"[f=hls:hls_time=2:hls_list_size=5:hls_flags=delete_segments+append_list:hls_segment_filename={REL_SEGMENT}]{REL_PLAYLIST}"
        tee_udp = f"[f=mpegts:onfail=ignore]{UDP_BRIDGE_URL}"
        
        output_args = [
            *encoding_args,
            "-f", "tee",
            "-map", "0:v",     
            "-map", "0:a:0?", 
            f"{tee_hls}|{tee_udp}"
        ]

        cmd = [ffmpeg_exe, "-y", "-hide_banner", *input_args, *output_args]

        print("[HLS] Iniciando Ponte FFmpeg...")
        
        _process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
            cwd=os.getcwd() 
        )

        print(f"[HLS] FFmpeg iniciado (PID={_process.pid})")
        
        time.sleep(3)
        if _process.poll() is not None:
             print("[HLS] ERRO: O processo FFmpeg morreu imediatamente.")
             _process = None
             return

        for _ in range(15):
            if os.path.exists(PLAYLIST_FILE):
                print("[HLS] Sucesso! Playlist criada.")
                return
            time.sleep(1)

        print("[HLS] Aviso: Playlist demorou para aparecer.")

    except Exception as e:
        print(f"[HLS] ERRO CRÍTICO ao iniciar FFmpeg: {e}")
        stop_hls()
        raise


def stop_hls():
    global _process
    if _process:
        print("[HLS] Parando stream...")
        _process.terminate()
        try:
            _process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print("[HLS] Processo travou, forçando kill...")
            _process.kill()
        print("[HLS] Processo FFmpeg encerrado.")
        _process = None


def is_stream_running():
    global _process
    return _process is not None and _process.poll() is None


def get_playlist_url():
    return "http://localhost:8000/hls/index.m3u8"