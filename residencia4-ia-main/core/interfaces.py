from abc import ABC, abstractmethod
from typing import List, Any
import numpy as np

class BaseDetector(ABC):
    def __init__(self, name: str):
        self.name = name
        self.errors = []

    def get_errors(self) -> List[dict]:
        return self.errors

class VideoDetector(BaseDetector):
    @abstractmethod
    def process_frame(self, full_frame, small_frame, small_gray, timestamp: float, frame_idx: int):
        """Processa um único frame."""
        pass

class AudioDetector(BaseDetector):
    @abstractmethod
    def process_audio(self, media_loader):
        """
        Processa o áudio usando o MediaLoader já carregado na memória.
        """
        pass