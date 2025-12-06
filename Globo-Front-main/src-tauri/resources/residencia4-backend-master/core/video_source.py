import utils.config as config  
from database.db_manager import get_current_settings

def get_video_source():
    """
    Retorna a fonte de vídeo (URL, Device ou Path) com base no estado atual do Banco de Dados.
    Se o banco não estiver acessível, usa o config.py como fallback.
    """
    settings = get_current_settings()

    mode = config.MONITORING_MODE
    srt_url = config.SRT_URL
    video_device = config.VIDEO_DEVICE
    audio_device = config.AUDIO_DEVICE
    test_path = config.TEST_VIDEO_PATH

    if settings:
        mode = settings['mode']
        srt_url = settings['srt_url'] or srt_url 
        video_device = settings['video_device'] or video_device
        audio_device = settings['audio_device'] or audio_device

    if mode == 'SRT':
        print(f"[Monitor] Usando a fonte de vídeo: Stream SRT ({srt_url}).")
        return srt_url
        
    elif mode == 'DEVICE':
        print(f"[Monitor] Usando a fonte de vídeo: DEVICE ({video_device} + {audio_device}).")
        return (video_device, audio_device)
        
    else: 
        print(f"[Monitor] Usando a fonte de vídeo: Pasta Local '{test_path}'.")
        return test_path