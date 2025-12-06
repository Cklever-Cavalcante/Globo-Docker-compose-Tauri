import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private config = {
    apiUrl: 'http://localhost:8000',
    apiBasePath: '/api/v1',
    wsUrl: 'http://localhost:8000',
    iaServiceUrl: 'http://localhost:8001'
  };

  constructor() {
    // Tenta carregar configurações do ambiente Tauri
    this.loadTauriConfig();
  }

  private async loadTauriConfig() {
    try {
      // @ts-ignore
      const { invoke } = await import('@tauri-apps/api/core');
      
      // Tenta obter configurações customizadas do Tauri
      const customConfig = await invoke('get_config');
      if (customConfig) {
        this.config = { ...this.config, ...customConfig };
      }
    } catch (error) {
      console.log('Usando configurações padrão (modo web)');
    }
  }

  getApiUrl(): string {
    return `${this.config.apiUrl}${this.config.apiBasePath}`;
  }

  getWebSocketUrl(): string {
    return this.config.wsUrl;
  }

  getIAServiceUrl(): string {
    return this.config.iaServiceUrl;
  }

  getFullConfig(): any {
    return this.config;
  }
}