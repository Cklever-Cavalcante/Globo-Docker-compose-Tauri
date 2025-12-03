import av
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MediaLoader:
    """
    Carrega vídeo e áudio usando PyAV para evitar I/O de disco repetitivo
    e subprocessos do FFmpeg.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.container = None
        self.audio_tracks = {} 
        self.metadata = {}
        
        try:
            self.container = av.open(file_path)
            self._parse_metadata()
            self._load_all_audio_tracks()
        except Exception as e:
            logger.error(f"Erro ao carregar mídia {file_path}: {e}")

    def _parse_metadata(self):
        self.metadata = {
            "streams": [],
            "format": self.container.format.name,
            "duration": float(self.container.duration) / av.time_base if self.container.duration else 0
        }
        for stream in self.container.streams:
            s_meta = {
                "index": stream.index,
                "type": stream.type,
                "codec": stream.codec_context.name,
                "channels": stream.codec_context.channels if stream.type == 'audio' else None
            }
            self.metadata["streams"].append(s_meta)

    def _load_all_audio_tracks(self, target_sr=16000):
        """
        Decodifica TODOS os streams de áudio para numpy arrays (float32).
        Padroniza para 16kHz mono para facilitar a IA.
        """
        audio_streams = [s for s in self.container.streams if s.type == 'audio']
        
        for i, stream in enumerate(audio_streams):
            try:
                resampler = av.AudioResampler(format='fltp', layout='mono', rate=target_sr)
                
                samples = []
                self.container.seek(0)
                
                for packet in self.container.demux(stream):
                    for frame in packet.decode():
                        frame.pts = None
                        out_frames = resampler.resample(frame)
                        for out_frame in out_frames:
                            samples.append(out_frame.to_ndarray())
                
                if samples:
                    full_track = np.concatenate(samples, axis=1).flatten()
                    self.audio_tracks[i] = full_track
                    logger.info(f"Áudio track {i} carregado: {len(full_track)} samples.")
                else:
                    self.audio_tracks[i] = np.array([])
                    
            except Exception as e:
                logger.error(f"Erro ao carregar track de áudio {i}: {e}")
                self.audio_tracks[i] = np.array([])

    def get_audio_track(self, index: int) -> np.ndarray:
        """Retorna o array numpy do áudio (track 0, 1, etc)."""
        return self.audio_tracks.get(index, np.array([]))

    def close(self):
        if self.container:
            self.container.close()