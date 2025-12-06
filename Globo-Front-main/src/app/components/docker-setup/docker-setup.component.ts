import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-docker-setup',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="docker-setup-container">
      <div class="setup-card">
        <h2>🐳 Configurando Ambiente Docker</h2>
        
        <div class="setup-steps">
          <div class="step" [class.active]="currentStep === 1" [class.completed]="currentStep > 1">
            <div class="step-icon">{{ currentStep > 1 ? '✅' : '1' }}</div>
            <div class="step-content">
              <h3>Verificando Docker Desktop</h3>
              <p *ngIf="currentStep === 1">Verificando se Docker Desktop está instalado...</p>
              <p *ngIf="currentStep > 1" class="success">Docker Desktop verificado</p>
            </div>
          </div>

          <div class="step" [class.active]="currentStep === 2" [class.completed]="currentStep > 2">
            <div class="step-icon">{{ currentStep > 2 ? '✅' : '2' }}</div>
            <div class="step-content">
              <h3>Instalando Docker Desktop</h3>
              <p *ngIf="currentStep === 2">Instalando Docker Desktop (isso pode levar alguns minutos)...</p>
              <div *ngIf="currentStep === 2 && installationProgress" class="progress-bar">
                <div class="progress-fill" [style.width.%]="installationProgress"></div>
              </div>
              <p *ngIf="currentStep > 2" class="success">Docker Desktop instalado</p>
            </div>
          </div>

          <div class="step" [class.active]="currentStep === 3" [class.completed]="currentStep > 3">
            <div class="step-icon">{{ currentStep > 3 ? '✅' : '3' }}</div>
            <div class="step-content">
              <h3>Carregando Imagens Docker</h3>
              <p *ngIf="currentStep === 3">Carregando imagens do bundle...</p>
              <div *ngIf="currentStep === 3 && loadingProgress" class="progress-bar">
                <div class="progress-fill" [style.width.%]="loadingProgress"></div>
              </div>
              <p *ngIf="currentStep > 3" class="success">Imagens carregadas</p>
            </div>
          </div>

          <div class="step" [class.active]="currentStep === 4" [class.completed]="currentStep > 4">
            <div class="step-icon">{{ currentStep > 4 ? '✅' : '4' }}</div>
            <div class="step-content">
              <h3>Iniciando Serviços</h3>
              <p *ngIf="currentStep === 4">Iniciando PostgreSQL, Backend e IA Service...</p>
              <p *ngIf="currentStep > 4" class="success">Serviços iniciados</p>
            </div>
          </div>
        </div>

        <div *ngIf="errorMessage" class="error-message">
          <p>⚠️ {{ errorMessage }}</p>
          <button (click)="retrySetup()" class="retry-button">Tentar Novamente</button>
        </div>

        <div *ngIf="currentStep > 4" class="success-container">
          <h3>🎉 Ambiente Configurado!</h3>
          <p>Todos os serviços foram configurados com sucesso.</p>
          <button (click)="proceedToApp()" class="proceed-button">Ir para o Aplicativo</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .docker-setup-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
    }

    .setup-card {
      background: white;
      border-radius: 15px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.1);
      max-width: 600px;
      width: 100%;
    }

    h2 {
      text-align: center;
      color: #333;
      margin-bottom: 30px;
      font-size: 28px;
    }

    .setup-steps {
      margin-bottom: 30px;
    }

    .step {
      display: flex;
      align-items: center;
      margin-bottom: 20px;
      padding: 15px;
      border-radius: 10px;
      transition: all 0.3s ease;
      opacity: 0.6;
    }

    .step.active {
      opacity: 1;
      background: #f8f9fa;
      border-left: 4px solid #007bff;
    }

    .step.completed {
      opacity: 1;
      background: #e8f5e8;
      border-left: 4px solid #28a745;
    }

    .step-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #007bff;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      margin-right: 15px;
      flex-shrink: 0;
    }

    .step.completed .step-icon {
      background: #28a745;
    }

    .step-content h3 {
      margin: 0 0 5px 0;
      color: #333;
      font-size: 18px;
    }

    .step-content p {
      margin: 0;
      color: #666;
      font-size: 14px;
    }

    .step-content .success {
      color: #28a745;
      font-weight: 500;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: #e9ecef;
      border-radius: 4px;
      margin-top: 10px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #007bff, #0056b3);
      border-radius: 4px;
      transition: width 0.3s ease;
    }

    .error-message {
      background: #f8d7da;
      border: 1px solid #f5c6cb;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 20px;
      text-align: center;
    }

    .error-message p {
      color: #721c24;
      margin: 0 0 10px 0;
    }

    .retry-button {
      background: #dc3545;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
    }

    .retry-button:hover {
      background: #c82333;
    }

    .success-container {
      text-align: center;
      background: #d4edda;
      border: 1px solid #c3e6cb;
      border-radius: 8px;
      padding: 20px;
    }

    .success-container h3 {
      color: #155724;
      margin: 0 0 10px 0;
    }

    .success-container p {
      color: #155724;
      margin: 0 0 20px 0;
    }

    .proceed-button {
      background: #28a745;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 16px;
      font-weight: 500;
    }

    .proceed-button:hover {
      background: #218838;
    }
  `]
})
export class DockerSetupComponent implements OnInit {
  currentStep = 1;
  installationProgress = 0;
  loadingProgress = 0;
  errorMessage = '';

  constructor(private router: Router) {}

  async ngOnInit() {
    await this.startSetup();
  }

  async startSetup() {
    try {
      // Step 1: Verificar Docker Desktop
      this.currentStep = 1;
      const { invoke } = await import('@tauri-apps/api/core');
      
      // Step 2: Instalar Docker Desktop (se necessário)
      this.currentStep = 2;
      this.installationProgress = 30;
      
      try {
        await invoke('install_docker_desktop');
        this.installationProgress = 100;
      } catch (error) {
        console.log('Docker Desktop já instalado ou erro na instalação:', error);
        // Continuar mesmo se houver erro
      }
      
      this.currentStep = 3;
      this.loadingProgress = 50;
      
      // Step 3: Carregar imagens Docker
      await invoke('load_docker_images');
      this.loadingProgress = 100;
      
      this.currentStep = 4;
      
      // Step 4: Iniciar serviços
      await invoke('start_services');
      
      this.currentStep = 5;
      
    } catch (error) {
      this.errorMessage = `Erro durante configuração: ${error}`;
      console.error('Erro no setup:', error);
    }
  }

  retrySetup() {
    this.errorMessage = '';
    this.currentStep = 1;
    this.startSetup();
  }

  proceedToApp() {
    this.router.navigate(['/dashboard']);
  }
}