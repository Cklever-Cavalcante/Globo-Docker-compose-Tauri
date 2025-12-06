import cv2
import numpy as np
import logging
import torch
import easyocr
import os
import json
from scipy.spatial.distance import cosine
from scipy.stats import pearsonr
from scipy.fft import rfft, rfftfreq, irfft
from ultralytics import YOLO
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from core.interfaces import VideoDetector, AudioDetector
from utils.error_classifier import classify_error, get_current_program

logger = logging.getLogger(__name__)

# =========================================================================
# CARREGAMENTO DE MODELOS GLOBAIS (SINGLETON)
# =========================================================================
EASYOCR_READER = None
try:
    logger.info("Carregando EasyOCR (Global)...")
    EASYOCR_READER = easyocr.Reader(['pt'], gpu=torch.cuda.is_available())
except Exception as e:
    logger.warning(f"EasyOCR não carregado: {e}")

YOLO_MODEL = None
try:
    logger.info("Carregando YOLO (Global)...")
    YOLO_MODEL = YOLO("yolov8n.pt")
except Exception as e:
    logger.warning(f"YOLO não carregado: {e}")

MOBILENET_MODEL = None
try:
    logger.info("Carregando MobileNetV2 (Global)...")
    MOBILENET_MODEL = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')
except Exception as e:
    logger.warning(f"MobileNetV2 não carregado: {e}")

SCHEDULE_PATH = "../utils/programacao_globo_2025.json"
TEMPLATE_PATH = os.path.join("models", "templates", "logo_globo.png")

# =========================================================================
# DETECTORES DE VÍDEO (PROCESSAMENTO FRAME A FRAME)
# =========================================================================

class FreezeDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Freeze")
        self.threshold = 50.0
        self.min_duration = 4.0
        self.static_count = 0
        self.potential_start = 0

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        laplacian_var = cv2.Laplacian(small_gray, cv2.CV_64F).var()
        
        if laplacian_var < self.threshold:
            if self.static_count == 0:
                self.potential_start = timestamp
            self.static_count += 1
        else:
            self._check_and_record()
            self.static_count = 0

    def _check_and_record(self):
        duration = self.static_count * 0.04  
        if duration >= self.min_duration:
            self.errors.append({
                "fault_type": "Freeze/Efeito Bloco",
                "duration": duration,
                "event_start_time": self.potential_start,
                "description": f"Imagem congelada detectada por {duration:.2f}s.",
                "level": classify_error("Freeze", duration),
                "program": get_current_program()
            })

class SignalCutDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Corte de Sinal")
        self.threshold = 15.0
        self.min_duration = 4.0
        self.black_count = 0
        self.start_time = 0

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        brightness = np.mean(small_gray)
        
        if brightness < self.threshold:
            if self.black_count == 0:
                self.start_time = timestamp
            self.black_count += 1
        else:
            if self.black_count > 0:
                duration = (timestamp - self.start_time)
                if duration >= self.min_duration:
                    self.errors.append({
                        "fault_type": "Corte de Sinal",
                        "duration": duration,
                        "event_start_time": self.start_time,
                        "description": "Tela preta detectada (Corte de Sinal).",
                        "level": classify_error("Corte de Sinal", duration),
                        "program": get_current_program()
                    })
            self.black_count = 0

class LogoDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Logo Errado")
        self.template = None
        self.mask = None
        self.load_template()
        self.missing_count = 0
        self.start_time = 0
        self.min_duration = 4.0
        self.frame_skip = 15  
        self.match_threshold = 0.1
        self.roi_y_start = 0.0
        self.roi_y_end = 0.20
        self.roi_x_start = 0.75
        self.roi_x_end = 1.0
        self.scales = np.linspace(0.4, 1.2, 10)

    def load_template(self):
        if os.path.exists(TEMPLATE_PATH):
            img = cv2.imread(TEMPLATE_PATH)
            if img is not None:
                self.template = img
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, self.mask = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)
                self.t_h, self.t_w = img.shape[:2]
            else:
                logger.error(f"Não foi possível ler template em {TEMPLATE_PATH}")

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        if self.template is None or frame_idx % self.frame_skip != 0:
            return

        h, w = full_frame.shape[:2]
        y1, y2 = int(h * self.roi_y_start), int(h * self.roi_y_end)
        x1, x2 = int(w * self.roi_x_start), int(w * self.roi_x_end)
        
        roi = full_frame[y1:y2, x1:x2]
        roi_h, roi_w = roi.shape[:2]
        
        found = False
        for scale in self.scales:
            tw, th = int(self.t_w * scale), int(self.t_h * scale)
            
            if th > roi_h or tw > roi_w or th == 0 or tw == 0: 
                continue
            
            resized_t = cv2.resize(self.template, (tw, th), interpolation=cv2.INTER_AREA)
            resized_m = cv2.resize(self.mask, (tw, th), interpolation=cv2.INTER_AREA)
            
            try:
                res = cv2.matchTemplate(roi, resized_t, cv2.TM_SQDIFF_NORMED, mask=resized_m)
                min_val, _, _, _ = cv2.minMaxLoc(res)
                if min_val <= self.match_threshold:
                    found = True
                    break
            except: continue

        if not found:
            if self.missing_count == 0: 
                self.start_time = timestamp
            self.missing_count += self.frame_skip
        else:
            self._close_occurrence(timestamp)

    def _close_occurrence(self, end_time=None):
        """Método auxiliar para registrar a ocorrência."""
        if self.missing_count > 0:

            duration = self.missing_count * (1.0/25.0) 
        
            if end_time is not None:
                duration = end_time - self.start_time

            if duration >= self.min_duration:
                self.errors.append({
                    "fault_type": "Logo Errado / Ausente",
                    "duration": duration,
                    "event_start_time": self.start_time,
                    "description": f"Logo da emissora não detectado por {duration:.2f}s.",
                    "level": classify_error("Logo Errado", duration),
                    "program": get_current_program()
                })
            self.missing_count = 0

    def get_errors(self):
        """
        Sobrescreve o método padrão para verificar falhas pendentes 
        (caso o vídeo acabe com o logo sumido).
        """
        if self.missing_count > 0:
            self._close_occurrence(end_time=None)
            
        return self.errors

class SafeAreaDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Safe Area")
        self.frame_skip = 10
        self.margin_pct = 0.05
        self.fault_count = 0
        self.start_time = 0
        self.last_text = ""

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        if EASYOCR_READER is None or frame_idx % self.frame_skip != 0:
            return

        results = EASYOCR_READER.readtext(small_frame, detail=1, paragraph=False)
        h, w = small_frame.shape[:2]
        
        margin_x, margin_y = w * self.margin_pct, h * self.margin_pct
        min_x, max_x = margin_x, w - margin_x
        min_y, max_y = margin_y, h - margin_y

        found_fault = False
        
        for (bbox, text, prob) in results:
            if prob < 0.4: continue
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            
            if min(xs) < min_x or max(xs) > max_x or min(ys) < min_y or max(ys) > max_y:
                found_fault = True
                self.last_text = text
                break
        
        if found_fault:
            if self.fault_count == 0: self.start_time = timestamp
            self.fault_count += 1
        else:
            duration = self.fault_count * (self.frame_skip / 25.0)
            if duration >= 4.0:
                self.errors.append({
                    "fault_type": "Arte Fora da Safe Area",
                    "description": f"Texto '{self.last_text}' fora da margem.",
                    "duration": duration,
                    "event_start_time": self.start_time,
                    "level": classify_error("Arte Fora da Safe Area", duration),
                    "program": get_current_program()
                })
            self.fault_count = 0

class ReporterParadoDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Reporter Parado")
        self.frame_skip = 5
        self.still_count = 0
        self.prev_gray = None
        self.start_time = 0
        self.motion_threshold = 2.5
        self.min_duration = 4.0

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        if YOLO_MODEL is None or frame_idx % self.frame_skip != 0:
            return

        current_gray = cv2.cvtColor(full_frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = current_gray
            return

        if self.prev_gray.shape != current_gray.shape:
            self.prev_gray = current_gray
            return

        results = YOLO_MODEL(full_frame, classes=[0], verbose=False, conf=0.5)
        is_still = False
        
        if len(results[0].boxes) > 0:
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
            areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
            idx = np.argmax(areas)
            x1, y1, x2, y2 = boxes[idx]
            mask = np.zeros_like(current_gray)
            mask[y1:y2, x1:x2] = 255
            flow = cv2.calcOpticalFlowFarneback(self.prev_gray, current_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            mean_motion = cv2.mean(mag, mask=mask)[0]
            
            if mean_motion < self.motion_threshold:
                is_still = True

        if is_still:
            if self.still_count == 0: self.start_time = timestamp
            self.still_count += self.frame_skip
        else:
            duration = self.still_count * (1.0/25.0) * self.frame_skip 
            if self.still_count > 0:
                duration = timestamp - self.start_time
            
            if duration >= self.min_duration:
                 self.errors.append({
                    "fault_type": "Repórter Parado",
                    "description": f"Repórter estático por {duration:.2f}s.",
                    "duration": duration,
                    "event_start_time": self.start_time,
                    "level": classify_error("Reporter Parado", duration),
                    "program": get_current_program()
                })
            self.still_count = 0
            
        self.prev_gray = current_gray

class FocusDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Fora de Foco")
        self.threshold = 100.0
        self.blur_count = 0
        self.start_time = 0
        self.min_duration = 4.0

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        var = cv2.Laplacian(small_gray, cv2.CV_64F).var()
        
        if var < self.threshold:
            if self.blur_count == 0: self.start_time = timestamp
            self.blur_count += 1
        else:
            duration = self.blur_count * 0.04
            if duration >= self.min_duration:
                self.errors.append({
                    "fault_type": "Fora de Foco",
                    "description": f"Imagem fora de foco por {duration:.2f}s.",
                    "duration": duration,
                    "event_start_time": self.start_time,
                    "level": classify_error("Fora de Foco", duration),
                    "program": get_current_program()
                })
            self.blur_count = 0

class FadeDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Fade")
        self.last_brightness = None
        self.fade_seq = 0
        self.direction = 0 
        self.start_time = 0

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        brightness = np.mean(small_gray)
        
        if self.last_brightness is not None:
            diff = brightness - self.last_brightness
            threshold = 5.0
            
            if abs(diff) > threshold:
                current_dir = 1 if diff > 0 else -1
                if self.fade_seq == 0:
                    self.start_time = timestamp
                    self.direction = current_dir
                    self.fade_seq = 1
                elif self.direction == current_dir:
                    self.fade_seq += 1
                else:
                    self.fade_seq = 0
            else:
                self._check_fade(timestamp)
                self.fade_seq = 0
        
        self.last_brightness = brightness

    def _check_fade(self, end_time):
        if self.fade_seq >= 5:
            duration = end_time - self.start_time
            f_type = "Fade-Out" if self.direction == 1 else "Fade-In"
            self.errors.append({
                "fault_type": f_type,
                "description": f"{f_type} detectado.",
                "duration": duration,
                "event_start_time": self.start_time,
                "level": classify_error("Fade", duration),
                "program": get_current_program()
            })

class ComercialCortadoDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Comercial Cortado")
        self.frame_skip = 3
        self.prev_embedding = None
        self.cuts = []
        self.last_fault_end_time = -100.0  
        self.current_fault_index = -1     

    def get_embedding(self, frame):
        resized = cv2.resize(frame, (224, 224))
        arr = preprocess_input(np.expand_dims(resized, axis=0))
        return MOBILENET_MODEL.predict(arr, verbose=0)

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        if MOBILENET_MODEL is None or frame_idx % self.frame_skip != 0:
            return

        curr_emb = self.get_embedding(small_frame)
        
        if self.prev_embedding is not None:
            dist = cosine(self.prev_embedding[0], curr_emb[0])
            
            if dist > 0.4: 
                self.cuts.append(timestamp)
                
                if len(self.cuts) >= 2:
                    start = self.cuts[-2]
                    end = self.cuts[-1]
                    duration = end - start

                    if 0.5 <= duration <= 10.0:
                        if (start - self.last_fault_end_time < 2.0) and (self.current_fault_index != -1):
                            last_error = self.errors[self.current_fault_index]
                            new_total_duration = last_error["duration"] + duration
                            last_error["duration"] = new_total_duration
                            last_error["description"] = f"Sequência de cortes abruptos detectada (Total: {new_total_duration:.2f}s)."
                            last_error["level"] = classify_error("Comercial Cortado", new_total_duration)
                            self.last_fault_end_time = end
                        else:
                            self.errors.append({
                                "fault_type": "Comercial Cortado",
                                "description": f"Corte abrupto de {duration:.2f}s.",
                                "duration": duration,
                                "event_start_time": start,
                                "level": classify_error("Comercial Cortado", duration),
                                "program": get_current_program()
                            })
                            self.current_fault_index = len(self.errors) - 1
                            self.last_fault_end_time = end
        
        self.prev_embedding = curr_emb

class ArtesSobrepostasDetectorV2(VideoDetector):
    def __init__(self):
        super().__init__("Artes Sobrepostas")
        self.frame_skip = 15
        self.fault_count = 0
        self.start_time = 0

    def _check_overlap(self, box1, box2):
        x_min = max(min(p[0] for p in box1), min(p[0] for p in box2))
        x_max = min(max(p[0] for p in box1), max(p[0] for p in box2))
        y_min = max(min(p[1] for p in box1), min(p[1] for p in box2))
        y_max = min(max(p[1] for p in box1), max(p[1] for p in box2))
        return x_max > x_min and y_max > y_min

    def process_frame(self, full_frame, small_frame, small_gray, timestamp, frame_idx):
        if EASYOCR_READER is None or frame_idx % self.frame_skip != 0:
            return

        results = EASYOCR_READER.readtext(small_frame, detail=1)
        found = False
        
        if len(results) > 1:
            valid = [r for r in results if r[2] >= 0.4]
            for i in range(len(valid)):
                for j in range(i+1, len(valid)):
                    if self._check_overlap(valid[i][0], valid[j][0]):
                        found = True
                        break
                if found: break
        
        if found:
            if self.fault_count == 0: self.start_time = timestamp
            self.fault_count += 1
        else:
            duration = self.fault_count * (self.frame_skip / 25.0)
            if duration >= 4.0:
                self.errors.append({
                    "fault_type": "Artes Sobrepostas",
                    "description": "Sobreposição de texto detectada.",
                    "duration": duration,
                    "event_start_time": self.start_time,
                    "level": classify_error("Artes Sobrepostas", duration),
                    "program": get_current_program()
                })
            self.fault_count = 0


# =========================================================================
# DETECTORES DE ÁUDIO OTIMIZADOS (NumPy Puro & MediaLoader)
# =========================================================================

class AudioMuteDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Audio Mudo")
        self.threshold_db = -50.0
        self.min_duration = 4.0

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(0)
        if samples.size == 0: return

        sr = 16000
        window_size = int(sr * 0.1) 
        num_windows = len(samples) // window_size
        if num_windows == 0: return
        
        trimmed = samples[:num_windows*window_size]
        windows = trimmed.reshape(-1, window_size)
        
        rms = np.sqrt(np.mean(windows**2, axis=1))

        db = 20 * np.log10(rms + 1e-9)
        
        silence_mask = db < self.threshold_db
        
        silence_seq = 0
        start_idx = 0
        
        for i, is_silent in enumerate(silence_mask):
            if is_silent:
                if silence_seq == 0: start_idx = i
                silence_seq += 1
            else:
                self._record(silence_seq, start_idx)
                silence_seq = 0
        self._record(silence_seq, start_idx)

    def _record(self, count, start_idx):
        dur = count * 0.1
        if dur >= self.min_duration:
            self.errors.append({
                "fault_type": "Ausência de Áudio",
                "description": f"Silêncio por {dur:.2f}s.",
                "duration": dur,
                "event_start_time": start_idx * 0.1,
                "level": classify_error("Ausencia de Audio", dur),
                "program": get_current_program()
            })

class AudioBaixoDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Audio Baixo")
        self.limiar = -35.0

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(0)
        if samples.size == 0: return

        rms = np.sqrt(np.mean(samples**2))
        dbfs = 20 * np.log10(rms + 1e-9)
        duration = len(samples) / 16000.0

        if -90 < dbfs < self.limiar:
            self.errors.append({
                "fault_type": "Audio Baixo",
                "description": f"Volume médio {dbfs:.2f} dBFS.",
                "duration": duration,
                "level": classify_error("Audio Baixo", duration),
                "program": get_current_program()
            })

class PicoteDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Audio Picote")
        self.threshold = 0.5
        self.duration_event = 4.0

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(0)
        if samples.size < 2: return
        diff = np.abs(np.diff(samples))
        peak_val = np.max(diff)
        
        if peak_val > self.threshold:
            peak_idx = np.argmax(diff)
            self.errors.append({
                "fault_type": "Audio Picote",
                "description": f"Picote detectado (variação {peak_val:.2f}).",
                "duration": self.duration_event,
                "event_start_time": peak_idx / 16000.0,
                "level": classify_error("Audio Picote", self.duration_event),
                "program": get_current_program()
            })

class RuidoDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Ruido e Distorcao")
        self.clip_thresh = 0.1
        self.hiss_thresh_energy = 0.005

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(0)
        if samples.size == 0: return
        
        duration = len(samples) / 16000.0

        clipped = np.sum(np.abs(samples) >= 0.99)
        pct_clip = (clipped / len(samples)) * 100
        
        if pct_clip > self.clip_thresh:
            self.errors.append({
                "fault_type": "Audio Distorcido",
                "description": f"Clipping: {pct_clip:.2f}% das amostras.",
                "duration": duration,
                "level": classify_error("Audio Distorcido", duration),
                "program": get_current_program()
            })
            return 

        rms = np.sqrt(np.mean(samples**2))
        db = 20 * np.log10(rms + 1e-9)

        if db < -30.0:
            yf = np.abs(rfft(samples))
            xf = rfftfreq(len(samples), 1/16000)
            
            idx = np.where((xf >= 8000) & (xf <= 16000))[0]
            if len(idx) > 0:
                energy = np.mean(yf[idx])
                if energy > self.hiss_thresh_energy:
                    self.errors.append({
                        "fault_type": "Audio Hiss/Ruido",
                        "description": f"Ruído de alta frequência (Hiss).",
                        "duration": duration,
                        "level": classify_error("Audio Hiss/Ruido", duration),
                        "program": get_current_program()
                    })

class EcoDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Audio Eco")
        self.threshold = 0.5
        self.delay_min = 0.05
        self.delay_max = 0.5

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(0)
        if samples.size == 0: return
        
        limit = 16000 * 30
        if len(samples) > limit:
            samples = samples[:limit]
        
        try:
            power = np.abs(rfft(samples))**2
            cepstrum = irfft(np.log(power + 1e-9)).real
            
            idx_min = int(self.delay_min * 16000)
            idx_max = int(self.delay_max * 16000)
            
            region = cepstrum[idx_min:idx_max]
            if len(region) == 0: return

            peak = np.max(region)
            
            if peak > self.threshold:
                self.errors.append({
                    "fault_type": "Audio Eco",
                    "description": f"Eco detectado (Pico: {peak:.2f}).",
                    "duration": len(samples)/16000.0,
                    "level": classify_error("Audio Eco", len(samples)/16000.0),
                    "program": get_current_program()
                })
        except: pass

class StereoDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Stereo Errado")

    def process_audio(self, media_loader):

        samples = media_loader.get_audio_track(0)
        
        if samples.ndim < 2: 
            return

        try:
            l = samples[0]
            r = samples[1]
            
            min_len = min(len(l), len(r))
            sample_len = min(min_len, 16000 * 10) 
            
            corr, _ = pearsonr(l[:sample_len], r[:sample_len])
            
            if corr > 0.99:
                 self.errors.append({
                    "fault_type": "Audio ST Errado Mono",
                    "description": "Canais idênticos (Mono em Stereo).",
                    "duration": len(l)/16000.0,
                    "level": classify_error("Audio ST Errado Mono", 0),
                    "program": get_current_program()
                })
            
            corr_inv, _ = pearsonr(l[:sample_len], -r[:sample_len])
            if corr_inv > 0.99:
                self.errors.append({
                    "fault_type": "Audio ST Errado Fase",
                    "description": "Canais em fase invertida.",
                    "duration": len(l)/16000.0,
                    "level": classify_error("Audio ST Errado Fase", 0),
                    "program": get_current_program()
                })
        except: pass

class SinalTesteDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("Sinal de Teste")

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(0)
        if samples.size == 0: return
        
        start = len(samples) // 2
        segment = samples[start : start+1000]
        
        if len(segment) < 1000: return
        
        yf = np.abs(rfft(segment))
        xf = rfftfreq(len(segment), 1/16000)
        
        idx = np.argmin(np.abs(xf - 1000))
        peak = yf[idx]
        mean = np.mean(yf)
        
        if peak > mean * 50:
            self.errors.append({
                "fault_type": "Sinal de Testes",
                "description": "Tom de 1kHz detectado.",
                "duration": len(samples)/16000.0,
                "level": classify_error("Sinal de Teste", len(samples)/16000.0),
                "program": get_current_program()
            })

# =========================================================================
# DETECTORES DE METADADOS (Otimizados com PyAV Metadata)
# =========================================================================

class MetadataAudioDetector(AudioDetector):
    def __init__(self, name):
        super().__init__(name)

    def process_audio(self, media_loader):
        pass

class Surround51DetectorV2(MetadataAudioDetector):
    def __init__(self):
        super().__init__("Ausencia 5.1")

    def process_audio(self, media_loader):

        streams = [s for s in media_loader.metadata.get('streams', []) if s['type'] == 'audio']
        if not streams: return

        ch = streams[0].get('channels', 0)
        if ch != 6:
            self.errors.append({
                "fault_type": "Audio 5.1 Ausencia",
                "description": f"Esperado 6 canais (5.1), encontrado {ch}.",
                "duration": 0,
                "level": "C",
                "program": get_current_program()
            })

class SapAdDetectorV2(MetadataAudioDetector):
    def __init__(self):
        super().__init__("SAP/AD Ausencia")

    def process_audio(self, media_loader):
        streams = [s for s in media_loader.metadata.get('streams', []) if s['type'] == 'audio']
        if len(streams) < 2:
             self.errors.append({
                "fault_type": "Audio SAP Ausencia",
                "description": "Faixa SAP/AD não encontrada.",
                "duration": 0,
                "level": "C",
                "program": get_current_program()
            })

class SapMudoDetectorV2(AudioDetector):
    def __init__(self):
        super().__init__("SAP Mudo")

    def process_audio(self, media_loader):
        samples = media_loader.get_audio_track(1)
        
        if samples.size == 0:
            return 
        
        rms = np.sqrt(np.mean(samples**2))
        db = 20 * np.log10(rms + 1e-9)
        
        duration = len(samples) / 16000.0
        
        if db < -60.0:
            self.errors.append({
                "fault_type": "Audio SAP Mudo",
                "description": "Faixa SAP está muda.",
                "duration": duration,
                "level": classify_error("Audio SAP Mudo", duration),
                "program": get_current_program()
            })