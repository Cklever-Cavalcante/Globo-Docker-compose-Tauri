from fastapi import FastAPI
import threading
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
from database.db_manager import initialize_database
from utils.hls_streamer import HLS_DIR 
from routers import occurrences, dashboard, settings, video_stream, live, notifications
from socket_instance import sio

app = FastAPI(
    title="PROJETO GLOBO - Backend Service",
    description="Serviço central que monitora streams de vídeo e fornece uma API para análise e consulta de ocorrências.",
    version="2.0.0"
)

app.mount('/socket.io', socketio.ASGIApp(sio))

origins = [
    "http://localhost:4200",
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

os.makedirs(HLS_DIR, exist_ok=True)
app.mount("/hls", StaticFiles(directory=str(HLS_DIR)), name="hls")

app.include_router(occurrences.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(video_stream.router)
app.include_router(live.router)
app.include_router(notifications.router)

@app.on_event("startup")
def startup_event():
    """
    Inicializa a base de dados (Seed Data) e inicia a monitorização contínua.
    """
    print("[Main] Iniciando PROJETO GLOBO...")
    
    initialize_database()

    from core.stream_processor import process_stream

    monitor_thread = threading.Thread(target=process_stream, daemon=True)
    monitor_thread.start()
    print("[Main] Sistema de monitorização contínua iniciado em segundo plano.")

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "ok", "service": "Backend Service is running"}