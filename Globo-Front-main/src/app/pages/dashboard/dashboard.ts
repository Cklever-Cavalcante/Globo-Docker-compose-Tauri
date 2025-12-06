import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, FormsModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss']
})
export class DashboardComponent implements OnInit {
  @ViewChild(BaseChartDirective) chart: BaseChartDirective | undefined;
  
  summary: any = {};
  activeFilter: string = 'today';
  
  customStart: string = '';
  customEnd: string = '';
  
  totalOccurrences: number = 0;
  criticalOccurrences: number = 0;
  isLoading = false;

  // --- 1. CONFIGURAÇÃO: BARRA EMPILHADA (Status) ---
  public statusChartType: ChartType = 'bar';
  public statusChartOptions: ChartConfiguration['options'] = {
    indexAxis: 'y', 
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1E1E1E',
        titleColor: '#F47F20',
        bodyColor: '#E0E0E0',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        callbacks: {
           label: (context) => {
             const val = context.raw as number;
             const total = (context.chart.data.datasets as any).reduce((a:any, b:any) => a + b.data[0], 0);
             const pct = total > 0 ? ((val / total) * 100).toFixed(1) + '%' : '0%';
             return ` ${context.dataset.label}: ${val} (${pct})`;
           }
        }
      }
    },
    scales: {
      x: { stacked: true, display: false },
      y: { stacked: true, display: false } 
    },
    // TRUQUE VISUAL: borderColor igual ao fundo do card (#1E1E1E) cria separação entre as barras
    elements: { bar: { borderRadius: 4, borderWidth: 2, borderColor: '#1E1E1E' } } 
  };

  // --- 2. CONFIGURAÇÃO: BARRAS HORIZONTAIS (Áudio/Vídeo) ---
  public barChartOptions: ChartConfiguration['options'] = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1E1E1E',
        titleColor: '#F47F20',
        bodyColor: '#E0E0E0',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 10
      }
    },
    scales: {
      x: { 
        grid: { color: '#333333', tickLength: 0 }, 
        ticks: { color: '#6B7280', font: { size: 10 } },
        beginAtZero: true
      },
      y: { 
        grid: { display: false }, 
        ticks: { color: '#E5E7EB', font: { weight: 'bold', size: 11 }, autoSkip: false, mirror: false } 
      }
    },
    elements: { bar: { borderRadius: 4 } }
  };

  // --- 3. CONFIGURAÇÃO: SEVERIDADE ---
  public severityChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: { 
            title: (items) => items[0].label as string
        }
      }
    },
    scales: {
      y: { grid: { color: '#333333' }, ticks: { color: '#9CA3AF', stepSize: 1 } },
      x: { grid: { display: false }, ticks: { color: '#F3F4F6', font: { weight: 'bold', size: 10 } } }
    },
    elements: { bar: { borderRadius: 6 } }
  };

  public statusChartData: ChartData<'bar'> = { labels: ['Status'], datasets: [] };
  public severityChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  public videoChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  public audioChartData: ChartData<'bar'> = { labels: [], datasets: [] };

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.fetchData();
  }

  setFilter(range: string) {
    this.activeFilter = range;
    if (range !== 'custom') this.fetchData();
  }

  applyCustomFilter() {
    if (this.customStart && this.customEnd) this.fetchData();
    else alert('Selecione datas válidas.');
  }

  fetchData() {
    this.isLoading = true;
    this.api.getDashboardSummary(this.activeFilter, this.customStart, this.customEnd).subscribe({
      next: (res) => {
        this.summary = res;
        this.totalOccurrences = (res.fault_type_distribution || []).reduce((acc: number, curr: any) => acc + curr.count, 0);
        this.updateCharts(res);
        this.isLoading = false;
      },
      error: (err) => { console.error(err); this.isLoading = false; }
    });
  }

  updateCharts(res: any) {
    // 1. Status (Cores Ajustadas para maior distinção)
    const validated = res.total_validated_occurrences || 0;
    const rejected = res.status_distribution?.rejected || 0;
    const open = Math.max(0, this.totalOccurrences - (validated + rejected));

    // CORES NOVAS: Mais contraste hue, mas ainda suaves
    let statusItems = [
        { label: 'Validado', value: validated, color: '#34d399' }, // Emerald-400 (Verde azulado, distinto do amarelo)
        { label: 'Em Aberto', value: open, color: '#fbbf24' },     // Amber-400 (Mais para laranja/ouro que amarelo limão)
        { label: 'Rejeitado', value: rejected, color: '#f87171' }  // Red-400 (Vermelho suave)
    ];

    statusItems.sort((a, b) => b.value - a.value);

    this.statusChartData = {
      labels: ['Visão Geral'],
      datasets: statusItems.map(item => ({
          label: item.label,
          data: [item.value],
          backgroundColor: item.color,
          hoverBackgroundColor: item.color,
          barThickness: 50
      }))
    };

    // 2. Separação e Ordenação (Pareto)
    const audioKeywords = ['Audio', 'Som', 'Mudo', 'Volume', 'SAP', 'Loudness'];
    const rawFaults = res.fault_type_distribution || [];
    
    let audioFaults = rawFaults.filter((f: any) => audioKeywords.some(k => f.type.includes(k)));
    let videoFaults = rawFaults.filter((f: any) => !audioKeywords.some(k => f.type.includes(k)));

    audioFaults.sort((a: any, b: any) => b.count - a.count);
    videoFaults.sort((a: any, b: any) => b.count - a.count);

    this.audioChartData = {
      labels: audioFaults.map((x: any) => x.type),
      datasets: [{
        data: audioFaults.map((x: any) => x.count),
        label: 'Ocorrências',
        backgroundColor: '#8B5CF6',
        hoverBackgroundColor: '#7C3AED',
        barPercentage: 0.7,
        categoryPercentage: 0.9
      }]
    };

    this.videoChartData = {
      labels: videoFaults.map((x: any) => x.type),
      datasets: [{
        data: videoFaults.map((x: any) => x.count),
        label: 'Ocorrências',
        backgroundColor: '#F47F20', 
        hoverBackgroundColor: '#EA580C',
        barPercentage: 0.7,
        categoryPercentage: 0.9
      }]
    };

    // 3. Severidade
    const severityOrder = ['C', 'B', 'A', 'X'];
    const sevData = res.level_distribution || [];
    sevData.sort((a: any, b: any) => severityOrder.indexOf(a.level) - severityOrder.indexOf(b.level));
    
    const crit = sevData.find((x: any) => x.level === 'X');
    this.criticalOccurrences = crit ? crit.count : 0;

    const mapColor = (sigla: string) => {
        switch(sigla) {
          case 'C': return '#3B82F6';
          case 'B': return '#FACC15';
          case 'A': return '#F97316';
          case 'X': return '#EF4444';
          default: return '#666';
        }
    };
    
    const mapLabel = (sigla: string) => {
        switch(sigla) {
          case 'C': return 'Nível C (≤4s)';
          case 'B': return 'Nível B (5-9s)';
          case 'A': return 'Nível A (10-59s)';
          case 'X': return 'Nível X (≥60s)';
          default: return sigla;
        }
    };
    
    this.severityChartData = {
      labels: sevData.map((x: any) => mapLabel(x.level)),
      datasets: [{ 
        data: sevData.map((x: any) => x.count), 
        backgroundColor: sevData.map((x: any) => mapColor(x.level)),
        hoverBackgroundColor: sevData.map((x: any) => mapColor(x.level)),
        barPercentage: 0.6,
        borderRadius: 4
      }]
    };
  }
}