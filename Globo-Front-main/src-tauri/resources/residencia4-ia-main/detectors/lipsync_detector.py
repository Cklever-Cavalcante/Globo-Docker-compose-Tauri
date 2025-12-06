import torch
import torch.nn as nn
import numpy as np
import cv2
import os
import math
import python_speech_features
import av
import logging
import datetime
import pytz
from typing import Optional, Dict, Any
from utils.error_classifier import classify_error, get_current_program

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYNCNET_MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'syncnet_v2.model')
SCHEDULE_FILE_PATH = "../utils/programacao_globo_2025.json"

class S(nn.Module):
    def __init__(self, num_layers_in_fc_layers=1024):
        super(S, self).__init__()
        self.__nFeatures__ = 24
        self.__nChs__ = 32
        self.__midChs__ = 32
        self.netcnnaud = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 1), stride=(1, 1)),

            nn.Conv2d(64, 192, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(192),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(1, 2)),

            nn.Conv2d(192, 384, kernel_size=(3, 3), padding=(1, 1)),
            nn.BatchNorm2d(384),
            nn.ReLU(inplace=True),

            nn.Conv2d(384, 256, kernel_size=(3, 3), padding=(1, 1)),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),

            nn.Conv2d(256, 256, kernel_size=(3, 3), padding=(1, 1)),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(2, 2)),

            nn.Conv2d(256, 512, kernel_size=(5, 4), padding=(0, 0)),
            nn.BatchNorm2d(512),
            nn.ReLU(),
        )
        self.netfcaud = nn.Sequential(
            nn.Linear(512, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, num_layers_in_fc_layers),
        )
        self.netfclip = nn.Sequential(
            nn.Linear(512, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, num_layers_in_fc_layers),
        )
        self.netcnnlip = nn.Sequential(
            nn.Conv3d(3, 96, kernel_size=(5, 7, 7), stride=(1, 2, 2), padding=0),
            nn.BatchNorm3d(96),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2)),

            nn.Conv3d(96, 256, kernel_size=(1, 5, 5), stride=(1, 2, 2), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1)),

            nn.Conv3d(256, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),

            nn.Conv3d(256, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),

            nn.Conv3d(256, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2)),

            nn.Conv3d(256, 512, kernel_size=(1, 6, 6), padding=0),
            nn.BatchNorm3d(512),
            nn.ReLU(inplace=True),
        )

    def forward_aud(self, x):
        mid = self.netcnnaud(x)
        mid = mid.view((mid.size()[0], -1))
        out = self.netfcaud(mid)
        return out

    def forward_lip(self, x):
        mid = self.netcnnlip(x)
        mid = mid.view((mid.size()[0], -1))
        out = self.netfclip(mid)
        return out

def calc_pdist(feat1, feat2, vshift=10):
    win_size = vshift * 2 + 1
    feat2p = torch.nn.functional.pad(feat2, (0, 0, vshift, vshift))
    dists = []
    for i in range(0, len(feat1)):
        dists.append(torch.nn.functional.pairwise_distance(feat1[[i], :].repeat(win_size, 1), feat2p[i:i + win_size, :]))
    return dists

class SyncNetInstance(torch.nn.Module):
    def __init__(self, dropout=0, num_layers_in_fc_layers=1024):
        super(SyncNetInstance, self).__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.__S__ = S(num_layers_in_fc_layers=num_layers_in_fc_layers).to(self.device)

    def _extract_audio_memory(self, videofile, target_sr=16000):
        try:
            container = av.open(videofile)
            audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
            
            if not audio_stream:
                logger.warning("Nenhum stream de áudio encontrado.")
                container.close()
                return None

            resampler = av.AudioResampler(format='s16', layout='mono', rate=target_sr)
            
            samples = []
            
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    frame.pts = None
                    out_frames = resampler.resample(frame)
                    for out_frame in out_frames:
                        samples.append(out_frame.to_ndarray())
            
            container.close()
            
            if not samples:
                return None
                
            full_audio = np.concatenate(samples, axis=1).flatten()
            return full_audio

        except Exception as e:
            logger.error(f"Erro PyAV na extração de áudio: {e}")
            return None

    def evaluate(self, opt, videofile):
        self.__S__.eval()
        
        images = []
        try:
            cap = cv2.VideoCapture(videofile)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                images.append(cv2.resize(frame, (224, 224)))
            cap.release()
        except Exception as e:
            logger.error(f"Erro ao ler frames com OpenCV: {e}")
            return None, None

        if not images:
            logger.warning("Nenhuma imagem extraída do vídeo.")
            return None, None

        audio = self._extract_audio_memory(videofile, target_sr=16000)
        
        if audio is None or len(audio) < 640:
             logger.warning("Áudio muito curto ou inexistente para análise.")
             return None, None

        try:
            im = np.stack(images, axis=3)
            im = np.expand_dims(im, axis=0)
            im = np.transpose(im, (0, 3, 4, 1, 2))
            imtv = torch.autograd.Variable(torch.from_numpy(im.astype(float)).float()).to(self.device)

            mfcc = zip(*python_speech_features.mfcc(audio, 16000))
            mfcc = np.stack([np.array(i) for i in mfcc])
            cc = np.expand_dims(np.expand_dims(mfcc, axis=0), axis=0)
            cct = torch.autograd.Variable(torch.from_numpy(cc.astype(float)).float()).to(self.device)

            min_length = min(len(images), math.floor(len(audio) / 640))
            lastframe = min_length - 5
            im_feat, cc_feat = [], []

            for i in range(0, lastframe, opt.batch_size):
                im_batch = [imtv[:, :, vframe:vframe + 5, :, :] for vframe in range(i, min(lastframe, i + opt.batch_size))]
                if not im_batch: 
                    break
                im_in = torch.cat(im_batch, 0)
                im_out = self.__S__.forward_lip(im_in)
                im_feat.append(im_out.data.cpu()) 
                
                cc_batch = [cct[:, :, :, vframe * 4:vframe * 4 + 20] for vframe in range(i, min(lastframe, i + opt.batch_size))]
                cc_in = torch.cat(cc_batch, 0)
                cc_out = self.__S__.forward_aud(cc_in)
                cc_feat.append(cc_out.data.cpu())

            if not im_feat or not cc_feat:
                return None, None

            im_feat = torch.cat(im_feat, 0)
            cc_feat = torch.cat(cc_feat, 0)
            dists = calc_pdist(im_feat, cc_feat, vshift=opt.vshift)
            mdist = torch.mean(torch.stack(dists, 1), 1)
            
            minval, minidx = torch.min(mdist, 0)
            offset = opt.vshift - minidx
            conf = torch.median(mdist) - minval
            
            return offset.numpy(), conf.numpy()
            
        except Exception as e:
            logger.error(f"Erro durante a avaliação SyncNet: {e}")
            return None, None

    def loadParameters(self, path):
        loaded_state = torch.load(path, map_location=self.device)
        self_state = self.__S__.state_dict()
        pretrained_dict = {k: v for k, v in loaded_state.items() if k in self_state}
        if not pretrained_dict:
            raise Exception("Nenhum parâmetro do modelo pré-treinado corresponde à arquitetura do modelo atual.")
        self_state.update(pretrained_dict)
        self.__S__.load_state_dict(self_state)

class SyncNetOptions:
    def __init__(self):
        self.tmp_dir = 'tmp_syncnet'
        self.reference = 'analysis'
        self.batch_size = 20
        self.vshift = 15

syncnet_model = None
try:
    if os.path.exists(SYNCNET_MODEL_PATH):
        syncnet_model = SyncNetInstance()
        syncnet_model.loadParameters(SYNCNET_MODEL_PATH)
        logger.info(f"Modelo SyncNet carregado com sucesso (Device: {syncnet_model.device}).")
    else:
        logger.warning(f"AVISO: Modelo SyncNet não encontrado em '{SYNCNET_MODEL_PATH}'.")
except Exception as e:
    syncnet_model = None
    logger.error(f"ERRO ao carregar o modelo SyncNet: {e}")

def get_video_duration(video_path):
    try:
        with av.open(video_path) as container:
            if container.duration:
                return float(container.duration) / av.time_base
            else:
                return 5.0
    except Exception:
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            return frame_count / fps if fps > 0 else 5.0
        except:
            return 5.0

def analyze_lipsync(video_path: str) -> Optional[Dict[str, Any]]:
    if not syncnet_model:
        logger.warning("Aviso: Detecção de lipsync desativada (modelo não carregado).")
        return None

    logger.info(f"Iniciando a detecção de lipsync com SyncNet para o vídeo: {video_path}")
    
    try:
        opt = SyncNetOptions()
        result = syncnet_model.evaluate(opt, video_path)
        
        if not result or result[0] is None:
            logger.info("INFO: Não foi possível calcular lipsync (vídeo curto ou sem áudio).")
            return None
            
        offset, conf = result
        offset_val = float(offset)
        conf_val = float(conf)

        logger.info(f"DEBUG: Offset detectado: {offset_val} | Confiança: {conf_val}")

        if abs(offset_val) > 4 and conf_val > 3.0:
            clip_duration = get_video_duration(video_path)
            tz = pytz.timezone('America/Sao_Paulo')
            event_start_datetime = datetime.datetime.now(tz) - datetime.timedelta(seconds=clip_duration)

            program_name = get_current_program(
                target_datetime=event_start_datetime, 
                schedule_file_path=SCHEDULE_FILE_PATH
            )

            logger.warning(f"LIPSYNC: Dessincronia detectada (Offset: {offset_val}, Conf: {conf_val}). Programa: {program_name}")
            
            fault_data = {
                "program": program_name, 
                "duration": clip_duration,
                "level": classify_error("Lipsync", clip_duration),
                "fault_type": "Erro de LipSync",
                "description": "Dessincronia de áudio e vídeo detectada por IA.",
                "cause": "Análise de SyncNet",
                "action": "Não se aplica",
                "notes": f"Detecção de Lipsync com offset de {offset_val:.2f} frames e confiança de {conf_val:.2f}. Início Real Estimado: {event_start_datetime.strftime('%Y-%m-%d %H:%M:%S %Z%z')}",
                "event_start_time": 0.0, 
                "event_duration": clip_duration
            }
            return fault_data
        else:
            logger.info("INFO: Sincronia de áudio e vídeo considerada aceitável.")
            return None
        
    except Exception as e:
        logger.error(f"ERRO na execução do SyncNet para o vídeo '{video_path}': {e}")
        return None