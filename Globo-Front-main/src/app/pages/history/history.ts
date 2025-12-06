import { Component, OnInit, ElementRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { ToastService } from '../../services/toast.service';
import { OccurrenceDetailsComponent } from '../../components/occurrence-details/occurrence-details';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, FormsModule, OccurrenceDetailsComponent],
  templateUrl: './history.html',
  styleUrls: ['./history.scss']
})
export class HistoryComponent implements OnInit {
  filters: any = { 
    start_date: '', 
    end_date: '', 
    status: '',
    fault_type: '',    
    level: '',         
    min_duration: '',  
    max_duration: ''   
  };
  
  historyData: any[] = [];
  selectedOccurrenceId: number | null = null;
  
  page = 1;
  pageSize = 20;
  total = 0;

  // Estado do Menu Dropdown
  isMenuOpen = false;

  constructor(
    private api: ApiService, 
    private toast: ToastService,
    private eRef: ElementRef
  ) {}

  ngOnInit() {
    this.loadData();
  }

  // Fecha o menu se clicar fora dele
  @HostListener('document:click', ['$event'])
  clickout(event: any) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.isMenuOpen = false;
    }
  }

  toggleMenu(event: Event) {
    event.stopPropagation();
    this.isMenuOpen = !this.isMenuOpen;
  }

  loadData() {
    this.api.getHistory(this.filters, this.page, this.pageSize).subscribe({
      next: (res) => {
        this.historyData = res.data;
        this.total = res.total;
      },
      error: (err) => console.error(err)
    });
  }

  deleteByFilter() {
    this.isMenuOpen = false;
    
    // Confirmação segura
    const confirmMessage = 
      '⚠️ ATENÇÃO: Esta ação excluirá todos os registros que correspondem aos filtros ativos atualmente.\n\n' +
      'Deseja prosseguir com a exclusão permanente?';

    if (!confirm(confirmMessage)) return;

    this.api.deleteHistory(this.filters).subscribe({
      next: (res: any) => {
        const count = res.deleted_count || 'vários';
        this.toast.show(`${count} registros excluídos com sucesso.`, 'success');
        this.loadData();
      },
      error: (err) => {
        this.toast.show('Erro ao excluir registros.', 'error');
      }
    });
  }

  approve(id: number) {
    if(!confirm('Aprovar ocorrência?')) return;
    this.api.updateStatus(id, 'Aprovado').subscribe(() => this.loadData());
  }

  reject(id: number) {
    if(!confirm('Rejeitar ocorrência?')) return;
    this.api.updateStatus(id, 'Rejeitado').subscribe(() => this.loadData());
  }

  download(type: 'csv' | 'pdf') {
    const url = this.api.getExportUrl(type, this.filters);
    window.open(url, '_blank');
  }

  changePage(delta: number) {
    const newPage = this.page + delta;
    if (newPage >= 1) {
      this.page = newPage;
      this.loadData();
    }
  }

  openDetails(id: number) { this.selectedOccurrenceId = id; }
  closeDetails() { this.selectedOccurrenceId = null; }
}