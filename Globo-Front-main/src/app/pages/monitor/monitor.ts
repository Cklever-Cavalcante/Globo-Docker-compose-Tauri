import { Component, OnInit, ViewChild, ElementRef, OnDestroy, HostListener, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { ToastService } from '../../services/toast.service';
import { OccurrenceDetailsComponent } from '../../components/occurrence-details/occurrence-details';
import Hls from 'hls.js';

@Component({
  selector: 'app-monitor',
  standalone: true,
  imports: [CommonModule, FormsModule, OccurrenceDetailsComponent],
  templateUrl: './monitor.html',
  styleUrls: ['./monitor.scss']
})
export class MonitorComponent implements OnInit, OnDestroy {
  @ViewChild('videoPlayer') videoElement!: ElementRef<HTMLVideoElement>;
  
  settings: any = { mode: 'FILE', srt_url: '', video_device: '', audio_device: '' };
  videoDevices: string[] = [];
  audioDevices: string[] = [];
  
  recentOccurrences: any[] = [];
  selectedOccurrenceId: number | null = null;
  
  isPlaying = false;
  isMuted = true;
  isBeepMuted = false;
  
  private audioUnlocked = false;
  private refreshInterval: any; // <--- Variável para o timer

  hls: Hls | null = null;
  private alertSound = new Audio('assets/beep2.mp3');

  constructor(
    private api: ApiService, 
    private toast: ToastService,
    private ngZone: NgZone
  ) {}

  ngOnInit() {
    this.loadSettings();
    this.loadDevices();
    this.loadRecent(); // Carrega a primeira vez

    this.alertSound.volume = 0.5;

    // --- SOLUÇÃO POLLING (AUTO-REFRESH DE DADOS) ---
    // A cada 3 segundos, busca novas ocorrências silenciosamente
    this.ngZone.runOutsideAngular(() => {
      this.refreshInterval = setInterval(() => {
        this.ngZone.run(() => {
          this.checkForNewData();
        });
      }, 3000);
    });

    // Mantém o socket como "plano B" ou para notificações instantâneas se funcionar
    this.api.onNewOccurrence().subscribe(data => {
       this.handleNewOccurrence(data);
    });

    this.api.getLiveStatus().subscribe(res => {
      if(res.running) {
        setTimeout(() => this.initPlayer(), 1000);
      }
    });
  }

  // Lógica separada para verificar dados
  checkForNewData() {
    this.api.getRecentOccurrences().subscribe(newList => {
      // Se a lista nova for diferente da atual (ex: tem um item novo no topo)
      if (newList.length > 0 && this.recentOccurrences.length > 0) {
        const firstCurrent = this.recentOccurrences[0];
        const firstNew = newList[0];

        // Compara IDs para saber se chegou algo novo
        if (firstNew.id !== firstCurrent.id) {
          console.log('🔄 Polling: Nova ocorrência detectada!');
          this.recentOccurrences = newList.slice(0, 10);
          this.playBeep(); // Toca o som!
        }
      } else if (newList.length > 0 && this.recentOccurrences.length === 0) {
         // Primeira carga se estava vazio
         this.recentOccurrences = newList.slice(0, 10);
      }
    });
  }

  handleNewOccurrence(data: any) {
    this.ngZone.run(() => {
      // Evita duplicatas se o Polling já tiver pego
      if (this.recentOccurrences.some(o => o.id === data.id)) return;

      this.recentOccurrences.unshift(data);
      this.recentOccurrences = this.recentOccurrences.slice(0, 10);
      this.playBeep();
    });
  }

  ngOnDestroy() { 
    this.stopStreamLocal();
    // Limpa o timer para não travar o navegador
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  // ... (RESTO DO CÓDIGO PERMANECE IGUAL: unlockAudio, playBeep, toggleBeepMute, etc.) ...
  
  @HostListener('document:click')
  unlockAudio() {
    if (this.audioUnlocked) return;
    this.alertSound.play().then(() => {
      this.alertSound.pause();
      this.alertSound.currentTime = 0;
      this.audioUnlocked = true;
    }).catch(() => {});
  }

  playBeep() {
    if (this.isBeepMuted) return;
    this.alertSound.currentTime = 0;
    this.alertSound.play().catch(e => console.warn('Som bloqueado:', e));
  }

  toggleBeepMute() {
    this.isBeepMuted = !this.isBeepMuted;
    if (!this.isBeepMuted && !this.audioUnlocked) this.unlockAudio(); 
  }

  loadSettings() {
    this.api.getMonitoringMode().subscribe(res => {
        this.settings = { 
          mode: res.current_mode, 
          srt_url: res.srt_url || '', 
          video_device: res.video_device || '', 
          audio_device: res.audio_device || '' 
        };
    });
  }

  loadDevices() {
    this.api.listDevices().subscribe(res => {
      this.videoDevices = res.video_devices || [];
      this.audioDevices = res.audio_devices || [];
    });
  }

  loadRecent() {
    this.api.getRecentOccurrences().subscribe(res => {
      this.recentOccurrences = (res || []).slice(0, 10);
    });
  }

  setMode(mode: string) {
    this.settings.mode = mode;
    this.saveSettings(false);
  }

  saveSettings(showFeedback: boolean = true) {
    this.api.setMonitoringMode(this.settings).subscribe({
      next: (res) => {
        if(showFeedback) this.toast.show('Configurações salvas!', 'success');
        if(this.isPlaying) this.stopStreamLocal();
      },
      error: (err) => {
        if(showFeedback) this.toast.show('Erro ao salvar.', 'error');
      }
    });
  }

  startStream() {
    this.api.startLiveStream().subscribe({
      next: (res) => {
        this.toast.show('Iniciando transmissão...', 'info');
        setTimeout(() => this.initPlayer(), 3000);
      },
      error: (err) => {
        this.toast.show('Erro ao iniciar stream.', 'error');
      }
    });
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    if(this.videoElement?.nativeElement) {
      this.videoElement.nativeElement.muted = this.isMuted;
    }
  }

  initPlayer() {
    if (this.hls) this.hls.destroy();
    const video = this.videoElement.nativeElement;
    const hlsUrl = `http://localhost:8000/hls/index.m3u8?time=${Date.now()}`; 

    if (Hls.isSupported()) {
      this.hls = new Hls({ enableWorker: true, lowLatencyMode: true });
      this.hls.loadSource(hlsUrl);
      this.hls.attachMedia(video);
      this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.muted = this.isMuted;
        video.play().catch(() => {});
        this.isPlaying = true;
      });
      this.hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
           data.type === Hls.ErrorTypes.NETWORK_ERROR ? this.hls?.startLoad() : this.stopStreamLocal();
        }
      });
    } 
    else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = hlsUrl;
      video.addEventListener('loadedmetadata', () => {
        video.play();
        this.isPlaying = true;
      });
    }
  }

  stopStreamLocal() {
    if (this.hls) this.hls.destroy();
    if(this.videoElement?.nativeElement) {
      this.videoElement.nativeElement.pause();
      this.videoElement.nativeElement.removeAttribute('src');
      this.videoElement.nativeElement.load();
    }
    this.isPlaying = false;
  }

  openDetails(id: number) { this.selectedOccurrenceId = id; }
  closeDetails() { this.selectedOccurrenceId = null; }
}