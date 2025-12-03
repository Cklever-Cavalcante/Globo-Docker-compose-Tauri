import socketio

origins = [
    "http://localhost:4200",  
]

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=origins)