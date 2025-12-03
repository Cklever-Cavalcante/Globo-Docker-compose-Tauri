import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ToastComponent } from './components/toast/toast.component';
import { ApiService } from './services/api';      // Importar
import { ToastService } from './services/toast.service'; // Importar

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, ToastComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class AppComponent {
  title = 'globo-monitor-front';
  
  // Estado inicial da IA (padrão: ligado)
  isAiActive = true;

  constructor(
    private api: ApiService, 
    private toast: ToastService
  ) {}

  toggleAiStatus() {
    // Inverte o estado localmente primeiro (optimistic UI) ou espera a resposta
    const newState = !this.isAiActive;
    
    this.api.toggleAIProcessing(newState).subscribe({
      next: () => {
        this.isAiActive = newState;
        const statusMsg = newState ? 'ATIVADO' : 'PAUSADO';
        const type = newState ? 'success' : 'info'; //
        
        this.toast.show(`Processamento de IA ${statusMsg}`, type);
      },
      error: (err) => {
        // Se der erro, mantém o estado anterior e avisa
        // Em um cenário real, você reverteria o this.isAiActive aqui se tivesse mudado antes
        console.warn('Backend offline ou endpoint não configurado, simulando troca de estado...');
        
        // --- SIMULAÇÃO (Remova isso quando o backend estiver pronto) ---
        this.isAiActive = newState;
        const statusMsg = newState ? 'ATIVADO' : 'PAUSADO';
        const type = newState ? 'success' : 'info';
        this.toast.show(`[SIMULAÇÃO] IA ${statusMsg}`, type);
        // -------------------------------------------------------------
      }
    });
  }
}