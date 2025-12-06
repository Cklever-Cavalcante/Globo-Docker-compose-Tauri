import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

VIDEO_BASE_DIR = os.getenv("VIDEO_BASE_DIR", BASE_DIR / "video_ocorrencias")
THUMBNAIL_BASE_DIR = os.getenv("THUMBNAIL_BASE_DIR", BASE_DIR / "video_thumbnails")

DEFAULT_TEST_VIDEO = BASE_DIR / "teste21.mp4"
TEST_VIDEO_PATH = os.getenv("TEST_VIDEO_PATH", str(DEFAULT_TEST_VIDEO))

DB_HOST = os.getenv("POSTGRES_SERVER", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "root")
DB_NAME = os.getenv("POSTGRES_DB", "globo_monitoramento")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

IA_SERVICE_URL = os.getenv("IA_SERVICE_URL", "http://ia-service:8001/analyze_video")

LIMIT_C = int(os.getenv("LIMIT_C", 4))
LIMIT_B = int(os.getenv("LIMIT_B", 9))
LIMIT_A = int(os.getenv("LIMIT_A", 59))

MONITORING_MODE = os.getenv("MONITORING_MODE", "SRT") 
SRT_URL = os.getenv("SRT_URL", "srt://179.108.248.226:7058")

DEVICE_INDEX = int(os.getenv("VIDEO_DEVICE_ID", 0))
VIDEO_DEVICE = os.getenv("VIDEO_DEVICE_NAME", "DroidCam Video")
AUDIO_DEVICE = os.getenv("AUDIO_DEVICE_NAME", "Microfone (DroidCam Audio)")