import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-initializer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-gray-900 flex items-center justify-center">
      <div class="bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4">
        <div class="text-center">
          <img src="assets/logo-globo.png" alt="Globo Monitor" class="h-16 mx-auto mb-6">
          
          <h1 class="text-2xl font-bold text-white mb-2">Globo Monitor</h1>
          <p class="text-gray-400 mb-6">Sistema de Monitoramento de Qualidade</p>
          
          <div class="space-y-4">
            <div class="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
              <span class="text-white">Docker Compose</span>
              <span class="px-2 py-1 text-xs rounded" 
                    [ngClass]="dockerStatus === 'running' ? 'bg-green-600 text-white' : 
                             dockerStatus === 'error' ? 'bg-red-600 text-white' : 
                             'bg-yellow-600 text-white'">
                {{ dockerStatusLabel }}
              </span>
            </div>
            
            <div class="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
              <span class="text-white">Backend API</span>
              <span class="px-2 py-1 text-xs rounded" 
                    [ngClass]="apiStatus === 'connected' ? 'bg-green-600 text-white' : 
                             apiStatus === 'error' ? 'bg-red-600 text-white' : 
                             'bg-yellow-600 text-white'">
                {{ apiStatusLabel }}
              </span>
            </div>
            
            <div class="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
              <span class="text-white">IA Service</span>
              <span class="px-2 py-1 text-xs rounded" 
                    [ngClass]="iaStatus === 'connected' ? 'bg-green-600 text-white' : 
                             iaStatus === 'error' ? 'bg-red-600 text-white' : 
                             'bg-yellow-600 text-white'">
                {{ iaStatusLabel }}
              </span>
            </div>
          </div>
          
          <div class="mt-6">
            <div *ngIf="!isReady" class="text-center">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              <p class="text-gray-400 mt-2">Iniciando serviços...</p>
            </div>
            
            <button *ngIf="isReady" 
                    (click)="proceedToApp()"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200">
              Iniciar Aplicação
            </button>
            
            <button *ngIf="hasError" 
                    (click)="retryInitialization()"
                    class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 mt-2">
              Tentar Novamente
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class InitializerComponent implements OnInit {
  dockerStatus: 'checking' | 'running' | 'stopped' | 'error' = 'checking';
  apiStatus: 'checking' | 'connected' | 'error' = 'checking';
  iaStatus: 'checking' | 'connected' | 'error' = 'checking';
  isReady = false;
  hasError = false;

  get dockerStatusLabel(): string {
    const labels = {
      checking: 'Verificando...',
      running: 'Executando',
      stopped: 'Parado',
      error: 'Erro'
    };
    return labels[this.dockerStatus];
  }

  get apiStatusLabel(): string {
    const labels = {
      checking: 'Verificando...',
      connected: 'Conectado',
      error: 'Erro'
    };
    return labels[this.apiStatus];
  }

  get iaStatusLabel(): string {
    const labels = {
      checking: 'Verificando...',
      connected: 'Conectado',
      error: 'Erro'
    };
    return labels[this.iaStatus];
  }

  constructor(private router: Router) {}

  ngOnInit() {
    this.initializeServices();
  }

  async initializeServices() {
    try {
      // Para Opção 1: Configurar Docker Environment primeiro
      await this.setupDockerEnvironment();
      
      // Inicia serviços Docker
      await this.startDockerServices();
      
      // Verifica conectividade
      await this.checkServicesHealth();
      
      this.isReady = true;
    } catch (error) {
      console.error('Erro na inicialização:', error);
      this.hasError = true;
    }
  }

  async setupDockerEnvironment() {
    try {
      // @ts-ignore
      const { invoke } = await import('@tauri-apps/api/core');
      
      console.log('Configurando ambiente Docker (Opção 1)...');
      const result = await invoke('setup_docker_environment');
      console.log('Docker environment setup result:', result);
      
    } catch (error) {
      console.error('Erro ao configurar Docker Environment:', error);
      // Não lançar erro, continuar com tentativa normal
    }
  }

  async startDockerServices() {
    try {
      // @ts-ignore
      const { invoke } = await import('@tauri-apps/api/core');
      
      this.dockerStatus = 'checking';
      const result = await invoke('start_services');
      console.log('Docker services started:', result);
      
      // Aguarda 10 segundos para os serviços iniciarem
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      this.dockerStatus = 'running';
    } catch (error) {
      console.error('Erro ao iniciar Docker:', error);
      this.dockerStatus = 'error';
      throw error;
    }
  }

  async checkServicesHealth() {
    try {
      // Verifica Backend API
      this.apiStatus = 'checking';
      const apiResponse = await fetch('http://localhost:8000/');
      this.apiStatus = apiResponse.ok ? 'connected' : 'error';
      
      // Verifica IA Service
      this.iaStatus = 'checking';
      const iaResponse = await fetch('http://localhost:8001/');
      this.iaStatus = iaResponse.ok ? 'connected' : 'error';
      
    } catch (error) {
      console.error('Erro ao verificar serviços:', error);
      this.apiStatus = 'error';
      this.iaStatus = 'error';
    }
  }

  proceedToApp() {
    this.router.navigate(['/dashboard']);
  }

  retryInitialization() {
    this.hasError = false;
    this.dockerStatus = 'checking';
    this.apiStatus = 'checking';
    this.iaStatus = 'checking';
    this.initializeServices();
  }
}