from fastapi import APIRouter
import socketio
from socket_instance import sio

router = APIRouter()

@sio.event
async def connect(sid, environ):
    """Evento chamado quando um cliente se conecta ao servidor Socket.IO"""
    print(f"Cliente conectado: {sid}")
    await sio.emit('connection_status', {'status': 'connected', 'sid': sid})

@sio.event
async def disconnect(sid):
    """Evento chamado quando um cliente se desconecta do servidor Socket.IO"""
    print(f"Cliente desconectado: {sid}")
    await sio.emit('connection_status', {'status': 'disconnected', 'sid': sid})

@sio.event
async def new_occurrence(sid, data):
    """Evento chamado quando uma nova ocorrência é detectada"""
    print(f"Nova ocorrência recebida: {data}")
    await sio.emit('new_occurrence', data)