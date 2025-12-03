import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { io, Socket } from 'socket.io-client';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api/v1';
  private socket: Socket;

  constructor(private http: HttpClient) {
    this.socket = io('http://localhost:8000', {
      transports: ['websocket']
    });
  }

  // --- WebSocket ---
  onNewOccurrence(): Observable<any> {
    return new Observable(observer => {
      this.socket.on('new_occurrence', (data) => {
        observer.next(data);
      });
    });
  }

  // --- Settings ---
  getMonitoringMode(): Observable<any> {
    return this.http.get(`${this.baseUrl}/settings/monitoring-mode`);
  }

  setMonitoringMode(data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/settings/monitoring-mode`, data);
  }

  // NOVO: Controle Global da IA
  toggleAIProcessing(active: boolean): Observable<any> {
    // Exemplo de endpoint. Ajuste conforme seu backend real.
    return this.http.put(`${this.baseUrl}/settings/ai-status`, { active });
  }

  listDevices(): Observable<any> {
    return this.http.get(`${this.baseUrl}/settings/devices`);
  }

  // --- Live Stream ---
  startLiveStream(): Observable<any> {
    return this.http.post(`${this.baseUrl}/live/start`, {});
  }

  getLiveStatus(): Observable<any> {
    return this.http.get(`${this.baseUrl}/live/status`);
  }

  // --- Ocorrências ---
  getRecentOccurrences(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/occurrences/`);
  }

  getHistory(filters: any, page: number = 1, size: number = 20): Observable<any> {
    let params = new HttpParams().set('page', page).set('size', size);
    Object.keys(filters).forEach(key => {
      if (filters[key]) params = params.set(key, filters[key]);
    });
    return this.http.get(`${this.baseUrl}/occurrences/historico/`, { params });
  }

  deleteHistory(filters: any): Observable<any> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params = params.set(key, filters[key]);
    });
    return this.http.delete(`${this.baseUrl}/occurrences/historico/`, { params });
  }

  updateStatus(id: number, status: string): Observable<any> {
    return this.http.put(`${this.baseUrl}/occurrences/${id}/status`, { status });
  }

  getOccurrenceById(id: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/occurrences/${id}`);
  }

  getExportUrl(type: 'csv' | 'pdf', filters: any): string {
    let params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return `${this.baseUrl}/occurrences/export/${type}?${params.toString()}`;
  }

  getDashboardSummary(range: string = 'today', start?: string, end?: string): Observable<any> {
    let params = new HttpParams().set('range', range);
    if (range === 'custom' && start && end) {
      params = params.set('start_date', start);
      params = params.set('end_date', end);
    }
    return this.http.get(`${this.baseUrl}/dashboard/summary`, { params });
  }
}