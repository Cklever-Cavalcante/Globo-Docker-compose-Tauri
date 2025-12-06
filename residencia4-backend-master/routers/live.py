import threading
from fastapi import APIRouter, HTTPException
from utils.hls_streamer import start_hls, get_playlist_url, is_stream_running

router = APIRouter(prefix="/api/v1/live", tags=["Live Stream"])

@router.post("/start")
def start_live():
    """
    Inicia a conversão para HLS em background e retorna imediatamente a playlist.
    """
    try:
        if is_stream_running():
            return {
                "playlist_url": get_playlist_url(),
                "message": "Stream já em execução."
            }

        thread = threading.Thread(target=start_hls, daemon=True)
        thread.start()

        return {
            "playlist_url": get_playlist_url(),
            "message": "Stream iniciado em background."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_status():
    """
    Retorna se o stream HLS está rodando.
    """
    return {"running": is_stream_running()}
