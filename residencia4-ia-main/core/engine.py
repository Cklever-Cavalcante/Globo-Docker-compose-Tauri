import cv2
import time
import threading
import queue
import numpy as np
import logging
from typing import List
from core.interfaces import VideoDetector, AudioDetector
from core.media_loader import MediaLoader

logger = logging.getLogger(__name__)

class FrameProvider:
    """Lê frames em uma thread separada."""
    def __init__(self, video_path, queue_size=64):
        self.cap = cv2.VideoCapture(video_path)
        self.queue = queue.Queue(maxsize=queue_size)
        self.stopped = False
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True

    def start(self):
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if not self.queue.full():
                ret, frame = self.cap.read()
                if not ret:
                    self.stopped = True
                    return
                self.queue.put(frame)
            else:
                time.sleep(0.01)
        self.cap.release()

    def read(self):
        if self.stopped and self.queue.empty():
            return None
        try:
            return self.queue.get(timeout=1)
        except queue.Empty:
            return None
            
    def more(self):
        return not (self.stopped and self.queue.empty())

class AnalysisEngine:
    def __init__(self, video_path):
        self.video_path = video_path
        self.video_detectors: List[VideoDetector] = []
        self.audio_detectors: List[AudioDetector] = []
        self.resize_width = 640  
        logger.info("Carregando Media Context (PyAV)...")
        self.media_loader = MediaLoader(video_path)

    def add_video_detector(self, detector: VideoDetector):
        self.video_detectors.append(detector)

    def add_audio_detector(self, detector: AudioDetector):
        self.audio_detectors.append(detector)

    def run(self):
        logger.info(f"Iniciando Engine Single-Pass para: {self.video_path}")

        for det in self.audio_detectors:
            try:
                det.process_audio(self.media_loader)
            except Exception as e:
                logger.error(f"Erro no detector de áudio {det.name}: {e}")

        provider = FrameProvider(self.video_path).start()
        frame_idx = 0
        
        while provider.more():
            frame = provider.read()
            if frame is None: break

            frame_idx += 1
            timestamp = frame_idx / provider.fps

            h, w = frame.shape[:2]
            scale = self.resize_width / float(w)
            small_frame = cv2.resize(frame, None, fx=scale, fy=scale)
            gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

            for det in self.video_detectors:
                try:
                    det.process_frame(
                        full_frame=frame, 
                        small_frame=small_frame, 
                        small_gray=gray_frame, 
                        timestamp=timestamp, 
                        frame_idx=frame_idx
                    )
                except Exception as e:
                    logger.error(f"Erro no detector {det.name} frame {frame_idx}: {e}")

        # Limpeza
        self.media_loader.close()
        
        all_errors = []
        for det in self.video_detectors + self.audio_detectors:
            all_errors.extend(det.get_errors())
            
        logger.info(f"Análise finalizada. Total erros: {len(all_errors)}")
        return all_errors