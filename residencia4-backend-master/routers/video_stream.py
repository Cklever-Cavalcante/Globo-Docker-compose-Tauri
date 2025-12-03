import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi import Response

router = APIRouter(
    prefix="/api/v1/videos",
    tags=["Video Stream"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_VIDEO_PATH = os.path.join(BASE_DIR, "video_ocorrencias")
VIDEO_BASE_DIR = os.getenv("VIDEO_BASE_DIR", DEFAULT_VIDEO_PATH)

THUMBNAIL_BASE_DIR = os.path.join(BASE_DIR, "video_thumbnails")

@router.get("/{filename}")
async def stream_video(filename: str):
    """
    Retorna um video especifico.
    """
    file_path = os.path.join(VIDEO_BASE_DIR, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    
    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="video/mp4")


@router.get("/thumbnail/{filename}")
def get_thumbnail(filename: str):
    """
    Retorna a miniatura de uma ocorrência.
    """
    file_path = os.path.join(THUMBNAIL_BASE_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Thumbnail não encontrada")
    headers = {"Cache-Control": "public, max-age=86400"}
    return FileResponse(file_path, media_type="image/jpeg")
